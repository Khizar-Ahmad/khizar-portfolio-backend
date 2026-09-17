from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.routers import portfolio, chat, auth

app = FastAPI(
    title="Portfolio API",
    description="Backend for personal portfolio with RAG agent",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(portfolio.router)
app.include_router(chat.router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup():
    # Ensure chroma dir exists
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    print("✅ ChromaDB ready")
    print(f"🚀 Portfolio API running on http://{settings.APP_HOST}:{settings.APP_PORT}")


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Portfolio API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
