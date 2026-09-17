from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List
from app.models.database import get_db, HeroProfile, Experience, Project, Skill
from app.auth import AdminRequired
from app.rag.engine import upsert_document, delete_document

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ─── Pydantic schemas ─────────────────────────────────────────────────────────
class HeroUpdate(BaseModel):
    name: str
    title: str
    tagline: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_url: Optional[str] = None
    profile_picture: Optional[str] = None
    location: Optional[str] = None
    years_experience: Optional[str] = None


class ExperienceCreate(BaseModel):
    company: str
    company_url: Optional[str] = None
    role: str
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    technologies: List[str] = []
    location: Optional[str] = None
    order_index: int = 0


class ProjectCreate(BaseModel):
    name: str
    description: str
    long_description: Optional[str] = None
    technologies: List[str] = []
    live_url: Optional[str] = None
    github_url: Optional[str] = None
    images: List[str] = []
    is_featured: bool = False
    order_index: int = 0


class SkillCreate(BaseModel):
    category: str
    name: str
    proficiency: int = 80
    order_index: int = 0


# ─── Hero / Profile ───────────────────────────────────────────────────────────
@router.get("/hero")
async def get_hero(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HeroProfile))
    hero = result.scalars().first()
    if not hero:
        return {}
    return {
        "id": hero.id, "name": hero.name, "title": hero.title,
        "tagline": hero.tagline, "bio": hero.bio, "email": hero.email,
        "github_url": hero.github_url, "linkedin_url": hero.linkedin_url,
        "resume_url": hero.resume_url, "profile_picture": hero.profile_picture,
        "location": hero.location, "years_experience": hero.years_experience,
    }


@router.put("/hero", dependencies=[AdminRequired])
async def update_hero(data: HeroUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HeroProfile))
    hero = result.scalars().first()
    if not hero:
        hero = HeroProfile(id="hero-main")
        db.add(hero)
    for k, v in data.dict().items():
        setattr(hero, k, v)
    await db.commit()
    text = f"""
Name: {data.name}
Title: {data.title}
Tagline: {data.tagline or ''}
Bio: {data.bio or ''}
Location: {data.location or ''}
Years of Experience: {data.years_experience or ''}
Email: {data.email or ''}
GitHub: {data.github_url or ''}
LinkedIn: {data.linkedin_url or ''}
""".strip()
    upsert_document("hero-profile", text, {"type": "hero", "name": data.name})
    return {"success": True}


# ─── Experiences ──────────────────────────────────────────────────────────────
@router.get("/experiences")
async def get_experiences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experience).order_by(Experience.order_index, Experience.created_at.desc())
    )
    exps = result.scalars().all()
    return [
        {
            "id": e.id, "company": e.company, "company_url": e.company_url,
            "role": e.role, "start_date": e.start_date, "end_date": e.end_date,
            "is_current": e.is_current, "description": e.description,
            "technologies": e.technologies or [], "location": e.location,
            "order_index": e.order_index,
        }
        for e in exps
    ]


@router.post("/experiences", dependencies=[AdminRequired])
async def create_experience(data: ExperienceCreate, db: AsyncSession = Depends(get_db)):
    exp = Experience(**data.dict())
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    _embed_experience(exp)
    return {"id": exp.id, "success": True}


@router.put("/experiences/{exp_id}", dependencies=[AdminRequired])
async def update_experience(exp_id: str, data: ExperienceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).where(Experience.id == exp_id))
    exp = result.scalars().first()
    if not exp:
        raise HTTPException(404, "Experience not found")
    for k, v in data.dict().items():
        setattr(exp, k, v)
    await db.commit()
    _embed_experience(exp)
    return {"success": True}


@router.delete("/experiences/{exp_id}", dependencies=[AdminRequired])
async def delete_experience(exp_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).where(Experience.id == exp_id))
    exp = result.scalars().first()
    if not exp:
        raise HTTPException(404, "Experience not found")
    delete_document(f"experience-{exp_id}")
    await db.delete(exp)
    await db.commit()
    return {"success": True}


def _embed_experience(exp):
    end = exp.end_date if not exp.is_current else "Present"
    tech = ", ".join(exp.technologies or [])
    text = f"""Work Experience:
Company: {exp.company}
Role / Position: {exp.role}
Duration: {exp.start_date} to {end}
Location: {exp.location or ''}
Technologies Used: {tech}
Description: {exp.description or ''}""".strip()
    upsert_document(f"experience-{exp.id}", text, {"type": "experience", "company": exp.company})


# ─── Projects ─────────────────────────────────────────────────────────────────
@router.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).order_by(Project.order_index, Project.created_at.desc())
    )
    projs = result.scalars().all()
    return [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "long_description": p.long_description, "technologies": p.technologies or [],
            "live_url": p.live_url, "github_url": p.github_url,
            "images": p.images or [], "is_featured": p.is_featured,
            "order_index": p.order_index,
        }
        for p in projs
    ]


@router.post("/projects", dependencies=[AdminRequired])
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    proj = Project(**data.dict())
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    _embed_project(proj)
    return {"id": proj.id, "success": True}


@router.put("/projects/{proj_id}", dependencies=[AdminRequired])
async def update_project(proj_id: str, data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == proj_id))
    proj = result.scalars().first()
    if not proj:
        raise HTTPException(404, "Project not found")
    for k, v in data.dict().items():
        setattr(proj, k, v)
    await db.commit()
    _embed_project(proj)
    return {"success": True}


@router.delete("/projects/{proj_id}", dependencies=[AdminRequired])
async def delete_project(proj_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == proj_id))
    proj = result.scalars().first()
    if not proj:
        raise HTTPException(404, "Project not found")
    delete_document(f"project-{proj_id}")
    await db.delete(proj)
    await db.commit()
    return {"success": True}


def _embed_project(proj):
    tech = ", ".join(proj.technologies or [])
    text = f"""Project: {proj.name}
Description: {proj.description}
{('Detailed Description: ' + proj.long_description) if proj.long_description else ''}
Technologies: {tech}
{'Live Demo: ' + proj.live_url if proj.live_url else 'Status: Not yet deployed'}
{'GitHub Repository: ' + proj.github_url if proj.github_url else ''}""".strip()
    upsert_document(f"project-{proj.id}", text, {"type": "project", "name": proj.name})


# ─── Skills ───────────────────────────────────────────────────────────────────
@router.get("/skills")
async def get_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.order_index))
    skills = result.scalars().all()
    return [
        {"id": s.id, "category": s.category, "name": s.name,
         "proficiency": s.proficiency, "order_index": s.order_index}
        for s in skills
    ]


@router.post("/skills", dependencies=[AdminRequired])
async def create_skill(data: SkillCreate, db: AsyncSession = Depends(get_db)):
    skill = Skill(**data.dict())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    await _embed_all_skills(db)
    return {"id": skill.id, "success": True}


@router.delete("/skills/{skill_id}", dependencies=[AdminRequired])
async def delete_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalars().first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    await db.delete(skill)
    await db.commit()
    await _embed_all_skills(db)
    return {"success": True}


async def _embed_all_skills(db: AsyncSession):
    result = await db.execute(select(Skill))
    skills = result.scalars().all()
    by_cat: dict = {}
    for s in skills:
        by_cat.setdefault(s.category, []).append(s.name)
    lines = [f"{cat}: {', '.join(names)}" for cat, names in by_cat.items()]
    text = "Technical Skills:\n" + "\n".join(lines)
    upsert_document("skills-overview", text, {"type": "skills"})
