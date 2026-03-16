import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

class TestTasker:
    
    def test_cleanup_with_exception(self):
        """Тест обработки исключений в cleanup"""
        from src.tasker.mytask import cleanup_unused_cache
        
        with patch('src.database.SessionLocal') as mock_session:
            mock_session.side_effect = Exception("DB Error")
            cleanup_unused_cache() 
    
    def test_top_with_empty_db(self, client):
        """Тест top_in_cache с пустой БД"""
        from src.tasker.mytask import top_in_cache
        client.delete("/links/debug/all")
        top_in_cache()