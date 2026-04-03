"""
LLM客户端 - 极简实现
"""
import openai
import json


class LLMClient:
    """极简LLM客户端"""
    
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_text(self, prompt, system_prompt=""):
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成失败: {str(e)}"
    
    def create_article(self, documents, concept):
        """创建wiki文章"""
        if not documents:
            return {
                "title": concept,
                "content": f"# {concept}\n\n相关信息待补充。",
                "summary": f"关于{concept}的概述"
            }
        
        # 提取文档内容
        content_samples = " ".join([doc.get('content', '')[:300] for doc in documents[:2]])
        
        prompt = f"基于以下内容为'{concept}'创建wiki文章:\n{content_samples}"
        
        response = self.generate_text(prompt, "创建简洁的wiki文章")
        
        # 尝试解析JSON，失败则使用默认格式
        try:
            result = json.loads(response)
            if "title" in result and "content" in result:
                return result
        except:
            pass
        
        return {
            "title": concept,
            "content": f"# {concept}\n\n{response}",
            "summary": response[:100] + "..."
        }