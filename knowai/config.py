"""
配置管理模块 - 极简实现
遵循正确性优先、可读性大于炫技的原则
"""
import os


class Config:
    """极简配置管理"""
    
    def __init__(self):
        # 核心配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # 文件路径配置
        self.raw_data_dir = os.getenv("RAW_DATA_DIR", "raw")
        self.compiled_wiki_dir = os.getenv("COMPILED_WIKI_DIR", "wiki")
        
        # 系统配置
        self.auto_compile = os.getenv("AUTO_COMPILE", "true").lower() == "true"
        
        # 验证必要配置
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 环境变量必须设置")
    
    def validate(self) -> bool:
        """验证配置有效性"""
        return bool(self.openai_api_key.strip())


# 全局配置实例
config = Config()