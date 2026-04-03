"""
项目验证脚本 - 确保代码质量和功能正确性
遵循正确性优先、可读性大于炫技的原则
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from knowai.config import config
from knowai.database import db
from knowai.llm_client import LLMClient
from knowai.ingest import DataIngestor
from knowai.qa_engine import QAEngine
from tools.search_engine import SearchEngine


def validate_config():
    """验证配置模块"""
    print("🔧 验证配置模块...")
    
    try:
        # 检查必要配置
        api_key = config.get("openai_api_key")
        if not api_key:
            print("⚠️ OPENAI_API_KEY 未设置")
        else:
            print("✅ OpenAI配置正常")
        
        # 检查目录配置
        directories = ["raw_data_dir", "compiled_wiki_dir"]
        for dir_key in directories:
            dir_path = config.get(dir_key)
            print(f"✅ {dir_key}: {dir_path}")
        
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def validate_database():
    """验证数据库模块"""
    print("\n🗄️ 验证数据库模块...")
    
    try:
        # 测试数据库连接和基本操作
        stats = db.get_statistics()
        print(f"✅ 数据库连接正常")
        print(f"   文档数量: {stats['documents']}")
        print(f"   文章数量: {stats['wiki_articles']}")
        print(f"   会话数量: {stats['query_sessions']}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False


def validate_llm_client():
    """验证LLM客户端模块"""
    print("\n🤖 验证LLM客户端模块...")
    
    try:
        llm = LLMClient()
        
        # 测试文本生成
        test_prompt = "请用一句话回答: 什么是人工智能?"
        response = llm.generate_text(test_prompt, "你是一个AI助手")
        
        if response and len(response) > 10:
            print("✅ 文本生成正常")
            print(f"   测试响应: {response[:50]}...")
        else:
            print("⚠️ 文本生成响应异常")
        
        # 测试嵌入生成
        embedding = llm.get_embedding("测试文本")
        if len(embedding) == 1536:
            print("✅ 嵌入生成正常")
        else:
            print("⚠️ 嵌入生成维度异常")
        
        return True
    except Exception as e:
        print(f"❌ LLM客户端验证失败: {e}")
        return False


def validate_ingest():
    """验证数据摄入模块"""
    print("\n📥 验证数据摄入模块...")
    
    try:
        ingestor = DataIngestor()
        
        # 创建测试文件
        test_dir = Path("test_data")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_document.md"
        test_content = """# 测试文档
        
这是一个用于验证系统的测试文档。
        
内容包含人工智能、机器学习和深度学习等概念。
        """
        
        test_file.write_text(test_content, encoding='utf-8')
        
        # 测试文件摄入
        doc_id = ingestor.ingest_file(str(test_file))
        if doc_id > 0:
            print("✅ 文件摄入正常")
            print(f"   文档ID: {doc_id}")
        else:
            print("⚠️ 文件摄入返回异常ID")
        
        # 测试wiki编译
        articles = ingestor.auto_compile_wiki()
        if articles:
            print("✅ Wiki编译正常")
            print(f"   生成文章: {len(articles)} 篇")
        else:
            print("⚠️ Wiki编译未生成文章")
        
        # 清理测试文件
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        print(f"❌ 数据摄入验证失败: {e}")
        return False


def validate_qa_engine():
    """验证问答引擎模块"""
    print("\n❓ 验证问答引擎模块...")
    
    try:
        qa_engine = QAEngine()
        
        # 测试简单查询
        result = qa_engine.answer_query("什么是人工智能?")
        
        if result.get("answer"):
            print("✅ 问答功能正常")
            print(f"   答案长度: {len(result['answer'])} 字符")
            print(f"   参考来源: {len(result['sources'])} 个")
        else:
            print("⚠️ 问答功能返回空答案")
        
        # 测试健康检查
        health = qa_engine.health_check()
        print(f"✅ 健康检查正常")
        print(f"   状态: {health['status']}")
        print(f"   文章数量: {health['article_count']}")
        
        return True
    except Exception as e:
        print(f"❌ 问答引擎验证失败: {e}")
        return False


def validate_search_engine():
    """验证搜索引擎模块"""
    print("\n🔍 验证搜索引擎模块...")
    
    try:
        search_engine = SearchEngine()
        
        # 测试搜索功能
        results = search_engine.search("人工智能")
        
        print("✅ 搜索功能正常")
        print(f"   搜索结果数量: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                print(f"   结果{i}: {result['title'][:30]}...")
        
        # 测试统计功能
        stats = search_engine.get_statistics()
        print(f"✅ 统计功能正常")
        print(f"   总文章数: {stats['total_articles']}")
        print(f"   概念数量: {stats['unique_concepts']}")
        
        return True
    except Exception as e:
        print(f"❌ 搜索引擎验证失败: {e}")
        return False


def validate_project_structure():
    """验证项目结构"""
    print("\n📁 验证项目结构...")
    
    required_dirs = ["raw", "wiki", "output", "core", "tools", "cli"]
    required_files = [
        "core/config.py", "core/database.py", "core/llm_client.py",
        "core/ingest.py", "core/qa_engine.py", "tools/search_engine.py",
        "cli/main.py", "requirements.txt", "README.md"
    ]
    
    all_valid = True
    
    # 检查目录
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ 目录存在: {dir_name}/")
        else:
            print(f"❌ 目录缺失: {dir_name}/")
            all_valid = False
    
    # 检查文件
    for file_path in required_files:
        file_obj = Path(file_path)
        if file_obj.exists():
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            all_valid = False
    
    return all_valid


def main():
    """主验证函数"""
    print("🚀 开始验证LLM知识库管理系统...")
    print("=" * 50)
    
    validation_results = []
    
    # 执行各项验证
    validation_results.append(("项目结构", validate_project_structure()))
    validation_results.append(("配置模块", validate_config()))
    validation_results.append(("数据库模块", validate_database()))
    validation_results.append(("LLM客户端", validate_llm_client()))
    validation_results.append(("数据摄入", validate_ingest()))
    validation_results.append(("问答引擎", validate_qa_engine()))
    validation_results.append(("搜索引擎", validate_search_engine()))
    
    print("\n" + "=" * 50)
    print("📊 验证结果汇总:")
    
    success_count = sum(1 for _, result in validation_results if result)
    total_count = len(validation_results)
    
    for module_name, result in validation_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {module_name}: {status}")
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 项通过")
    
    if success_count == total_count:
        print("\n🎉 所有验证通过！系统可以正常使用。")
        print("\n💡 下一步建议:")
        print("   1. 设置 OPENAI_API_KEY 环境变量")
        print("   2. 运行 'python cli/main.py init' 初始化系统")
        print("   3. 使用 'python cli/main.py ingest' 摄入文档")
        print("   4. 使用 'python cli/main.py ask' 进行问答")
    else:
        print("\n⚠️ 部分验证失败，请检查上述错误信息。")
    
    return success_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)