"""
LLM知识库管理系统 - 极简CLI
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from knowai.database import db
from knowai.ingest import DataIngestor
from knowai.qa_engine import QAEngine
from tools.search_engine import SearchEngine


def main():
    """主程序"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    # 获取API密钥
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key and command != 'init':
        print("错误: 请设置 OPENAI_API_KEY 环境变量")
        return
    
    # 命令处理
    if command == 'init':
        init()
    elif command == 'ingest':
        if len(sys.argv) < 3:
            print("用法: python main.py ingest <文件或目录>")
            return
        ingest(api_key, sys.argv[2])
    elif command == 'compile':
        compile_wiki(api_key)
    elif command == 'ask':
        if len(sys.argv) < 3:
            print("用法: python main.py ask <问题>")
            return
        ask(api_key, ' '.join(sys.argv[2:]))
    elif command == 'search':
        if len(sys.argv) < 3:
            print("用法: python main.py search <关键词>")
            return
        search(' '.join(sys.argv[2:]))
    elif command == 'status':
        status()
    else:
        show_help()


def show_help():
    """显示帮助"""
    print("""
LLM知识库管理系统

使用方法:
  python main.py init                   初始化系统
  python main.py ingest <路径>          摄入文件或目录
  python main.py compile                编译wiki
  python main.py ask "问题"             提问
  python main.py search "关键词"        搜索
  python main.py status                 查看状态

环境变量:
  OPENAI_API_KEY=你的API密钥

示例:
  export OPENAI_API_KEY=sk-...
  python main.py init
  python main.py ingest raw/document.md
  python main.py ask "什么是人工智能？"
""")


def init():
    """初始化系统"""
    print("初始化系统...")
    
    # 创建目录
    for dir_name in ["raw", "wiki", "output"]:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"创建目录: {dir_name}/")
    
    print("系统初始化完成")


def ingest(api_key, path):
    """摄入文件或目录"""
    ingestor = DataIngestor(api_key)
    path_obj = Path(path)
    
    if not path_obj.exists():
        print(f"路径不存在: {path}")
        return
    
    if path_obj.is_file():
        # 单个文件
        doc_id = ingestor.ingest_file(path)
        if doc_id:
            print(f"已摄入文件: {path}")
            # 自动编译
            articles = ingestor.compile_wiki()
            print(f"生成文章: {len(articles)} 篇")
        else:
            print("摄入失败")
    
    elif path_obj.is_dir():
        # 整个目录
        doc_ids = ingestor.ingest_folder(path)
        print(f"已摄入文件: {len(doc_ids)} 个")
        
        articles = ingestor.compile_wiki()
        print(f"生成文章: {len(articles)} 篇")


def compile_wiki(api_key):
    """编译wiki"""
    ingestor = DataIngestor(api_key)
    articles = ingestor.compile_wiki()
    
    if articles:
        print(f"编译完成，生成 {len(articles)} 篇文章")
        for article in articles[:3]:  # 显示前3个
            print(f"  - {Path(article).name}")
    else:
        print("没有文档可编译")


def ask(api_key, question):
    """提问"""
    qa = QAEngine(api_key)
    result = qa.answer(question)
    
    print(f"答案已生成")
    print(f"输出文件: {result['output_file']}")
    
    if result['sources']:
        print("参考文章:")
        for source in result['sources']:
            print(f"  - {source}")


def search(query):
    """搜索"""
    engine = SearchEngine()
    results = engine.search(query)
    
    if not results:
        print("未找到相关结果")
        return
    
    print(f"找到 {len(results)} 个结果:")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   预览: {result['preview']}")
        print(f"   相关度: {result['score']}")


def status():
    """查看状态"""
    # 数据库统计
    stats = db.get_stats()
    print("知识库状态:")
    print(f"  文档数量: {stats['documents']}")
    print(f"  文章数量: {stats['articles']}")
    
    # 文件统计
    for dir_name in ["raw", "wiki", "output"]:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = len(list(dir_path.glob("*")))
            print(f"  {dir_name}/ 文件数: {files}")
    
    # 搜索统计
    engine = SearchEngine()
    search_stats = engine.get_stats()
    print(f"  知识库状态: {search_stats['status']}")


if __name__ == '__main__':
    main()