"""
问答引擎 - 极简实现
"""
import re
from pathlib import Path

from .database import db
from .llm_client import LLMClient


class QAEngine:
    """极简问答引擎"""
    
    def __init__(self, api_key):
        self.llm = LLMClient(api_key)
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def answer(self, question):
        """回答问题"""
        if not question.strip():
            return {"answer": "问题不能为空", "sources": []}
        
        # 查找相关文章
        articles = db.get_articles()
        relevant = self._find_relevant(question, articles)
        
        # 生成答案
        answer_text = self._generate_answer(question, relevant)
        
        # 保存结果
        output_file = self._save_output(question, answer_text)
        
        return {
            "answer": answer_text,
            "output_file": output_file,
            "sources": [a.get('title', '') for a in relevant]
        }
    
    def _find_relevant(self, question, articles):
        """查找相关文章"""
        if not articles:
            return []
        
        # 简单关键词匹配
        question_words = set(question.lower().split())
        
        relevant = []
        for article in articles:
            content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            
            # 计算匹配度
            score = 0
            for word in question_words:
                if len(word) > 2:
                    if word in article.get('title', '').lower():
                        score += 3
                    if word in content:
                        score += 1
            
            if score > 0:
                relevant.append((article, score))
        
        # 按分数排序
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [article for article, score in relevant[:3]]
    
    def _generate_answer(self, question, articles):
        """生成答案"""
        if not articles:
            return f"# 回答: {question}\n\n抱歉，知识库中没有相关信息。"
        
        # 构建上下文
        context = "\n".join([
            f"文章: {a.get('title', '')}\n内容: {a.get('content', '')[:500]}"
            for a in articles
        ])
        
        prompt = f"基于以下知识回答: {question}\n\n知识库内容:\n{context}"
        
        return self.llm.generate_text(prompt, "提供准确简洁的答案")
    
    def _save_output(self, question, answer):
        """保存输出"""
        # 生成安全文件名
        safe_name = re.sub(r'[^\w\s-]', '', question)[:20].strip()
        safe_name = safe_name.replace(' ', '_') or 'query'
        
        file_path = self.output_dir / f"{safe_name}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(answer)
        
        return str(file_path)
    
    def check_health(self):
        """健康检查"""
        articles = db.get_articles()
        
        if not articles:
            return {
                "status": "empty",
                "message": "知识库为空，请先摄入文档"
            }
        
        # 简单检查
        issues = []
        
        # 检查文章内容
        for article in articles:
            content = article.get('content', '')
            if len(content) < 50:
                issues.append(f"文章 '{article.get('title', '')}' 内容过短")
        
        return {
            "status": "healthy" if not issues else "needs_improvement",
            "article_count": len(articles),
            "issues": issues[:3]
        }