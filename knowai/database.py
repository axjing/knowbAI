"""
数据库模块 - 极简实现
遵循正确性优先、可读性大于炫技的原则
"""
import sqlite3
import json
import os
from pathlib import Path


class Database:
    """极简数据库封装"""
    
    def __init__(self, db_path: str = "knowledge.db"):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库"""
        with self._get_connection() as conn:
            # 文档表
            conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 文章表
            conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                file_path TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
    
    def save_document(self, file_path: str, content: str) -> int:
        """保存文档"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO documents (file_path, content)
            VALUES (?, ?)
            """, (file_path, content))
            conn.commit()
            return cursor.lastrowid
    
    def get_documents(self):
        """获取所有文档"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM documents").fetchall()
            return [dict(row) for row in rows]
    
    def save_article(self, title: str, content: str, file_path: str) -> int:
        """保存文章"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO articles (title, content, file_path)
            VALUES (?, ?, ?)
            """, (title, content, file_path))
            conn.commit()
            return cursor.lastrowid
    
    def get_articles(self):
        """获取所有文章"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM articles").fetchall()
            return [dict(row) for row in rows]
    
    def get_stats(self):
        """获取统计信息"""
        with self._get_connection() as conn:
            doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            article_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            return {"documents": doc_count, "articles": article_count}


# 全局数据库实例
db = Database()