"""
搜索引擎 - 极简实现
"""
from ..knowai.database import db


class SearchEngine:
    """极简搜索引擎"""
    
    def search(self, query, limit=5):
        """搜索文章"""
        articles = db.get_articles()
        
        if not articles:
            return []
        
        # 简单关键词匹配
        query_words = set(query.lower().split())
        
        results = []
        for article in articles:
            score = self._score_article(article, query_words)
            if score > 0:
                results.append({
                    "title": article.get('title', ''),
                    "score": score,
                    "preview": article.get('content', '')[:100] + '...'
                })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _score_article(self, article, query_words):
        """计算文章相关度"""
        score = 0
        
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
        for word in query_words:
            if len(word) > 2:  # 忽略短词
                if word in title:
                    score += 3
                if word in content:
                    score += 1
        
        return score
    
    def get_stats(self):
        """获取统计信息"""
        articles = db.get_articles()
        
        if not articles:
            return {"total": 0, "message": "知识库为空"}
        
        # 简单统计
        total_chars = sum(len(a.get('content', '')) for a in articles)
        
        return {
            "total_articles": len(articles),
            "avg_length": total_chars // len(articles) if articles else 0,
            "status": "healthy" if len(articles) > 0 else "empty"
        }