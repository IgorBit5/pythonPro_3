from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
from src.schems import LinkCreate, LinkUpdate
from src.database import SessionLocal, Link, cache_get, cache_set, cache_delete, get_db
from src.schems import LinkCreate, LinkUpdate
from sqlalchemy import desc

router = APIRouter(prefix="/links", tags=["links"])

@router.post("/shorten", status_code=201)
def create_link(data: LinkCreate, db: Session = Depends(get_db)):
    if data.original_url:
        exists = db.query(Link).filter(Link.original_url == data.original_url, Link.is_active == True).first()
        if exists:
            raise HTTPException(400, "Такая на данный url уже существует")
         
    if data.custom_url:
        short_code = data.custom_url
        exists = db.query(Link).filter(Link.short_code == short_code).first()
        if exists:
            raise HTTPException(400, "Такая ссылка уже существует")
    else:
        max_attempts = 10
        for attempt in range(max_attempts):
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            exists = db.query(Link).filter(Link.short_code == short_code).first()
            if not exists:
                break
        else:
            raise HTTPException(500, "Не удалось сгенерировать уникальный код")

    link = Link(
        short_code=short_code,
        original_url=data.original_url,
        expires_at=data.expires_at,
        project=data.project
    )
    db.add(link)
    db.commit()
    
    cache_set(f"{short_code}", {"url": data.original_url})
    
    return {
        "short_code": short_code,
        "original_url": data.original_url,
        "expires_at": data.expires_at,
        "project": data.project
    }

@router.get("/{short_code}")
def redirect(short_code: str, db: Session = Depends(get_db)):
    
    cached = cache_get(f"{short_code}")
    if cached:
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if link:
            if link.expires_at and link.expires_at < datetime.now():
                db.delete(link)  # <-- УДАЛЯЕМ, а не деактивируем
                db.commit()
                cache_delete(f"{short_code}")
                raise HTTPException(410, "Срок действия ссылки истек")
            
            link.clicks += 1
            link.last_used = datetime.now()
            db.commit()
        return {"url": cached["url"]}
    
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(404, "Не найдена ссылка")
    
    if link.expires_at and link.expires_at < datetime.now():
        db.delete(link)  
        db.commit()
        raise HTTPException(410, "Срок действия ссылки истек")
    
    link.clicks += 1
    link.last_used = datetime.now()
    db.commit()
    
    cache_set(f"{short_code}", {"url": link.original_url})
    
    return {"url": link.original_url}

@router.delete("/{short_code}", status_code=204)
def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(404, "Link not found")
    
    db.delete(link)
    db.commit()
    cache_delete(f"{short_code}")  # Очищаем кэш

@router.put("/{short_code}")
def update_link(short_code: str, data: LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(404, "Link not found")
    
    link.original_url = data.original_url
    link.clicks = 0
    db.commit()
    
    cache_set(f"{short_code}", {"url": link.original_url})
    
    return {"short_code": short_code, "new_url": data.original_url}

@router.get("/{short_code}/stats")
def get_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(404, "Link not found")
    
    return {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "clicks": link.clicks,
        "last_used": link.last_used,
        "expires_at": link.expires_at
    }

# 6. ПОИСК по оригинальному URL
@router.get("/search")
def search(original_url: str, db: Session = Depends(get_db)):
    links = db.query(Link).filter(Link.original_url == original_url).all()
    return [
        {
            "short_code": l.short_code,
            "created_at": l.created_at,
            "clicks": l.clicks,
            "project": l.project
        } for l in links
    ]


@router.post("/cleanup-unused")
def cleanup_unused(days: int = 30, db: Session = Depends(get_db)):
    cutoff = datetime.now() - timedelta(days=days)
    
    # Ссылки без переходов за N дней
    unused = db.query(Link).filter(
        Link.last_used < cutoff,
        Link.is_active == True
    ).all()
    
    for link in unused:
        link.is_active = False
        cache_delete(f"{link.short_code}")
    
    db.commit()
    return {"deactivated": len(unused)}


@router.get("/expired")
def get_expired(db: Session = Depends(get_db)):
    expired = db.query(Link).filter(
        Link.is_active == False
    ).all()
    
    return [
        {
            "short_code": l.short_code,
            "original_url": l.original_url,
            "expires_at": l.expires_at,
            "last_used": l.last_used
        } for l in expired
    ]

@router.get("/projects/{project}")
def get_project_links(project: str, db: Session = Depends(get_db)):
    links = db.query(Link).filter(Link.project == project).all()
    return [
        {
            "short_code": l.short_code,
            "original_url": l.original_url,
            "clicks": l.clicks,
            "created_at": l.created_at
        } for l in links
    ]