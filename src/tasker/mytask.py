

from src.database import SessionLocal, Link, cache_get, cache_set, cache_delete

from sqlalchemy import desc
from datetime import datetime, timedelta


def cleanup_unused_cache():
    db = SessionLocal()
    try:       
        cutoff = datetime.now() - timedelta(days=1)
        unused_links = db.query(Link).filter(
            Link.last_used < cutoff,
            Link.is_active == True
        ).all()
        
        deleted_count = 0
        for link in unused_links:
            if cache_delete(f"link:{link.short_code}"):
                deleted_count += 1
        
        print(f"Очистка завершена. Удалено из кэша: {deleted_count}\n")
        
    except Exception as e:
        print(f"Ошибка при очистке кэша: {e}")
    finally:
        db.close()

def top_in_cache():
    db = SessionLocal()
    try:        
        
        top_links = db.query(Link).filter(
            Link.is_active == True
        ).order_by(
            desc(Link.clicks)
        ).limit(50).all()
        
        if not top_links:
            return
        
        top_data = []
        for link in top_links:
            link_cache = cache_get(f"{link.short_code}")
            clicks = link_cache["clicks"] if link_cache else link.clicks
            if not bool(link_cache):
                cache_set(f"{link.short_code}", {"url": link.original_url, "clicks": link.clicks})     
    except Exception as e:
        print(f"Ошибка при обновлении топа: {e}")
    finally:
        db.close()
        
