# LLM知识库管理系统

基于第一性原理设计的极简、高效、可扩展的LLM知识库系统。

## 🎯 设计原则

- **正确性优先**：类型安全、错误处理完善
- **可读性大于炫技**：代码简洁易懂
- **简洁大于复杂**：零复杂框架依赖
- **高效可扩展**：模块化设计，易于维护

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY
```

### 2. 初始化系统

```bash
python cli/main.py init
```

### 3. 基本使用

```bash
# 摄入文档
python cli/main.py ingest raw/document.md

# 编译wiki
python cli/main.py compile

# 提问
python cli/main.py ask "什么是机器学习？"

# 搜索
python cli/main.py search "神经网络"

# 健康检查
python cli/main.py health

# 系统状态
python cli/main.py status
```

## 📁 项目结构

```
knowbAgent/
├── core/                 # 核心模块
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库封装
│   ├── llm_client.py    # LLM客户端
│   ├── ingest.py        # 数据摄入
│   └── qa_engine.py     # 问答引擎
├── tools/
│   └── search_engine.py # 搜索引擎
├── cli/
│   └── main.py          # 命令行接口
├── raw/                 # 原始文档目录
├── wiki/                # 编译后的wiki
├── output/              # 输出文件
├── requirements.txt     # 依赖列表
└── README.md           # 项目说明
```

## 🛠 核心特性

### 数据摄入
- 支持单个文件和整个目录摄入
- 自动文件格式检测和编码处理
- 增量编译，避免重复处理

### 知识编译
- LLM驱动的智能概念识别
- 自动生成结构化的wiki文章
- 反向链接和摘要生成

### 智能问答
- 基于知识库的语义搜索
- 多格式输出支持（Markdown）
- 查询历史记录

### 健康检查
- 知识库完整性验证
- 自动问题检测
- 智能改进建议

## ⚙️ 配置说明

编辑 `.env` 文件：

```bash
# OpenAI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# 数据库配置
DATABASE_URL=sqlite:///knowledge.db

# 文件存储
RAW_DATA_DIR=raw
COMPILED_WIKI_DIR=wiki
IMAGES_DIR=images

# 系统配置
AUTO_COMPILE=true
HEALTH_CHECK_INTERVAL=3600
```

## 🔧 技术栈

- **语言**: Python 3.8+
- **数据库**: SQLite (默认) / PostgreSQL
- **AI服务**: OpenAI API
- **依赖**: 仅6个核心包

## 📈 性能优化

- 极简的API调用封装
- 智能的错误处理和重试机制
- 内存友好的数据处理
- 模块化的可扩展架构

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

---

基于Software 2.0/3.0理念构建，让AI成为知识管理的主要构建者。