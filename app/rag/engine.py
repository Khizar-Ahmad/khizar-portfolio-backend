import chromadb
from chromadb.utils import embedding_functions
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, List
import re
from app.config import settings

# ─── ChromaDB client (local, free) ───────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

# Free local embeddings (sentence-transformers, runs on CPU)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="portfolio_knowledge",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},
)

# ─── Groq LLM (free tier — llama3 70b) ───────────────────────────────────────
def get_llm():
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set. Get a free key at https://console.groq.com")
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=800,
    )


# ─── Knowledge management ─────────────────────────────────────────────────────
def upsert_document(doc_id: str, text: str, metadata: dict):
    """Add or update a document in ChromaDB."""
    # Chunk text if too long
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{**metadata, "chunk_index": i, "doc_id": doc_id} for i in range(len(chunks))]

    # Delete old chunks for this doc first
    try:
        existing = collection.get(where={"doc_id": doc_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    collection.add(documents=chunks, ids=ids, metadatas=metas)


def delete_document(doc_id: str):
    """Remove all chunks for a document."""
    try:
        existing = collection.get(where={"doc_id": doc_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def retrieve_context(query: str, n_results: int = 5) -> List[str]:
    """Semantic search over portfolio knowledge."""
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        return [d for d in docs if d]
    except Exception:
        return []


# ─── LangGraph RAG Agent ──────────────────────────────────────────────────────
class AgentState(TypedDict):
    query: str
    context: List[str]
    answer: str
    query_type: Literal["profile", "off_topic"]


def router_node(state: AgentState) -> AgentState:
    llm = get_llm()
#     prompt = f"""You are a classifier. Determine if this question is about a person's professional profile, portfolio, career, projects, skills, experience, or background.

# Question: {state['query']}

# Reply with exactly one word: PROFILE or OFF_TOPIC"""
    print('State_query',state["query"])
    
    prompt = f"""You are a classifier for a personal portfolio chatbot. 
    
Classify as PROFILE if the question is about: the person, their skills, experience, projects, background, career, education, contact info, or anything someone might ask when visiting a portfolio website.

Classify as OFF_TOPIC only if it's clearly unrelated (e.g. weather, cooking, news, math problems).

When in doubt, choose PROFILE.

Question: {state['query']}

Reply with exactly one word: PROFILE or OFF_TOPIC"""
    try:
        response = llm.invoke(prompt)
        print('LLM response',response)

        text = response.content.strip().upper()
        query_type = "profile" if "PROFILE" in text else "off_topic"
    except Exception:
        query_type = "profile"
    return {**state, "query_type": query_type}


def retriever_node(state: AgentState) -> AgentState:
    print('State_query',state["query"])
    context = retrieve_context(state["query"])
    print("context: ",context)
    return {**state, "context": context}


def synthesizer_node(state: AgentState) -> AgentState:
    llm = get_llm()
    print('state_query: ',state["query"])

    context_text = "\n\n".join(state["context"]) if state["context"] else "No specific information found."
    prompt = f"""You are a professional portfolio assistant. Answer questions about this person based ONLY on the provided context. Be warm, confident, and specific. If the context doesn't cover something, say so honestly.

CONTEXT ABOUT THE PERSON:
{context_text}

QUESTION: {state['query']}

Give a natural, conversational response (2-4 sentences). Be specific with details from the context."""
    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
        print('answer: ',answer)

    except Exception as e:
        answer = f"I had trouble retrieving that information right now. Please try again shortly."
    return {**state, "answer": answer}


def off_topic_node(state: AgentState) -> AgentState:
    llm = get_llm()
    prompt = f"""You are a witty portfolio assistant who only knows about one specific person. Someone just asked you this off-topic question: "{state['query']}"

Give a charming, brief response (2-3 sentences) that:
1. Acknowledges you can't help with that topic
2. Makes a clever connection back to the portfolio owner's skills/work
3. Invites them to ask about the person instead

Be playful, not robotic. Don't be apologetic, be witty."""
    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception:
        answer = "That's a bit outside my expertise! I'm built to talk about this portfolio — ask me about projects, skills, or experience and I'll shine."
    return {**state, "answer": answer}


def route_condition(state: AgentState) -> str:
    return state["query_type"]


# Build the LangGraph
def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("retriever", retriever_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("off_topic", off_topic_node)
    builder.set_entry_point("router")
    builder.add_conditional_edges("router", route_condition, {
        "profile": "retriever",
        "off_topic": "off_topic",
    })
    builder.add_edge("retriever", "synthesizer")
    builder.add_edge("synthesizer", END)
    builder.add_edge("off_topic", END)
    return builder.compile()


rag_graph = build_graph()


async def ask_agent(query: str) -> str:
    """Main entry point for chat queries."""
    try:
        print(query)
        result = rag_graph.invoke({
            "query": query,
            "context": [],
            "answer": "",
            "query_type": "profile",
        })
        print('result',result)
        return result["answer"]
    except Exception as e:
        print("ASK_AGENT ERROR:", e)  # <-- change this
        import traceback
        traceback.print_exc()  
        return "I'm having a moment — please try again shortly!"
