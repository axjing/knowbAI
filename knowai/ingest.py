"""
数据摄入模块 - 极简实现
"""
import os
from pathlib import Path

from .database import db
from .llm_client import LLMClient


class DataIngestor:
    """极简数据摄入器"""
    
    def __init__(self, api_key):
        self.llm = LLMClient(api_key)
        self.raw_dir = Path("raw")
        self.wiki_dir = Path("wiki")
        
        # 创建目录
        self.raw_dir.mkdir(exist_ok=True)
        self.wiki_dir.mkdir(exist_ok=True)
    
    def ingest_file(self, file_path):
        """摄入文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        # 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except:
                return None
        
        # 保存到数据库
        return db.save_document(str(file_path), content)
    
    def ingest_folder(self, folder_path):
        """摄入文件夹"""
        folder = Path(folder_path)
        
        if not folder.exists():
            return []
        
        doc_ids = []
        
        # 支持的文件类型
        extensions = {'.md', '.txt', '.py', '.js', '.html', '.css', '.json'}
        
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                doc_id = self.ingest_file(file_path)
                if doc_id:
                    doc_ids.append(doc_id)
                    print(f"已摄入: {file_path.name}")
        
        return doc_ids
    
    def compile_wiki(self):
        """编译wiki"""
        documents = db.get_documents()
        
        if not documents:
            return []
        
        # 简单概念识别
        concepts = self._find_concepts(documents)
        
        article_paths = []
        
        for concept in concepts:
            article = self._create_article(concept, documents)
            if article:
                path = self._save_article(article, concept)
                article_paths.append(path)
                print(f"已生成文章: {concept}")
        
        return article_paths
    
    def _find_concepts(self, documents):
        """识别概念"""
        if len(documents) < 3:
            return ["general"]
        
        # 简单的关键词提取
        words = []
        for doc in documents[:5]:
            content = doc.get('content', '')
            words.extend([w.lower() for w in content.split() if len(w) > 3])
        
        # 过滤常见词
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have'}
        meaningful = [w for w in words if w not in common_words]
        
        # 取前2个高频词
        from collections import Counter
        top_words = Counter(meaningful).most_common(2)
        
        return [word for word, count in top_words] if top_words else ["general"]
    
    def _create_article(self, concept, documents):
        """创建文章"""
        # 找到相关文档
        related = [doc for doc in documents if concept in doc.get('content', '').lower()]
        
        if not related:
            return None
        
        return self.llm.create_article(related, concept)
    
    def _save_article(self, article, concept):
        """保存文章"""
        safe_name = "".join(c for c in concept if c.isalnum())
        file_path = self.wiki_dir / f"{safe_name}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(article["content"])
        
        # 保存到数据库
        db.save_article(article["title"], article["content"], str(file_path))
        
        return str(file_path)