# autowiki

**LLM 驱动的个人知识库编译器**  
把 `raw/` 里的原始文档（文章、论文、代码、图片、数据集等）自动编译成结构化的 Obsidian-ready Markdown wiki。  
所有内容由 LLM 维护，你几乎不用手动编辑。查询、输出、linting、归档全部自动化。

这是我在原帖里描述的系统，现在以极简、可复用、可扩展的形式实现。  
遵循第一性原理：文件即真相，LLM 是编译器，Postgres + pgvector 只做快速索引，无复杂 RAG。

---

## 特性

- **增量编译**：只处理变更的文件，时间戳 + 内容 hash 双保险
- **本地 / OpenAI embedding 可切换**：默认 OpenAI 1536 维，也支持 sentence-transformers 本地 384 维（零 token 消耗）
- **图像原生支持**：自动复制到 `wiki/assets/` 并用 GPT-4o vision 生成结构化描述
- **Agent Q&A**：支持向量搜索、读文件、列概念、生成 Matplotlib 图表，输出自动归档回 wiki
- **Linting**：自动发现不一致、缺失信息、生成新文章候选和下一步问题建议
- **Obsidian 原生**：纯 Markdown、[[links]]、![[assets/xxx.png]]、Marp 幻灯片格式
- **并行处理**：ingest 和 compile 均使用 ThreadPoolExecutor，10k+ 文档依然流畅
- **状态一览**：`status` 命令快速查看知识库健康指标
- **幂等 & 可扩展**：所有操作可重复运行，后续可直接封装成 Docker / FastAPI / 多代理 swarm

---

## 快速开始

```bash
# 1. 克隆或保存代码
#    git clone <your-repo> && cd autowiki

# 2. 安装依赖
pip install openai psycopg2-binary "pgvector[psycopg2]" typer[all] python-dotenv matplotlib sentence-transformers

# 3. 准备 Postgres + pgvector
#    createdb llmkb
#    psql -d llmkb -c "CREATE EXTENSION vector;"

# 4. 配置 .env（复制下面模板）
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/llmkb
USE_LOCAL_EMBED=false
OPENAI_EMBED_MODEL=text-embedding-3-small
LOCAL_EMBED_MODEL=all-MiniLM-L6-v2
EOF

# 5. 初始化数据库
python autowiki.py setup

# 6. 放入原始数据
mkdir -p raw
# 把文章、论文、图片等复制到 raw/

# 7. 摄入 & 编译
python autowiki.py ingest raw/
python autowiki.py compile

# 8. 开始提问
python autowiki.py query "解释 Software 2.0 的核心思想并生成 Marp 幻灯片"
```

所有生成的 `.md` 文件和 `assets/` 直接在 Obsidian 中打开即可使用。

---

## 可用命令

```bash
python autowiki.py --help

setup          # 创建/重建数据库表（切换 embedding 维度时必须执行）
ingest <path>  # 摄入单个文件或整个目录（支持并行）
compile        # 增量编译 raw/ → wiki/（--force 强制全量）
query "问题"   # Agent 完整问答，自动归档输出
lint           # 健康检查 + 新文章候选 + 修复建议
status         # 显示文档数、概念数、wiki 文件数
```

---

## 配置（.env）

| 参数                  | 说明                              | 默认值 |
|-----------------------|-----------------------------------|--------|
| DATABASE_URL          | Postgres 连接字符串               | -      |
| USE_LOCAL_EMBED       | true=使用本地 embedding           | false  |
| OPENAI_EMBED_MODEL    | OpenAI embedding 模型             | text-embedding-3-small |
| LOCAL_EMBED_MODEL     | 本地 sentence-transformers 模型   | all-MiniLM-L6-v2 |

---

## 项目结构

```
.
├── raw/           # 原始数据（永远不要手动修改）
├── wiki/          # LLM 生成的知识库（Obsidian vault）
│   ├── *.md
│   └── assets/
├── autowiki.py    # 全部代码（单文件）
├── .env
└── README.md
```

---

## 为什么这样设计

- **简单**：单文件，无框架，无多余抽象
- **高效**：只处理变更的文件，并行执行
- **可扩展**：每个函数都可独立 import，后续可直接加 FastAPI、Docker、多代理 swarm、合成数据导出
- **规范**：所有输出都是标准 Markdown + Obsidian 链接
- **面向未来**：wiki 越大，越容易导出成合成数据集做微调（下一步自然演进）

---

## 后续探索方向（已准备好）

- Docker 一键部署
- FastAPI + Web UI
- 多代理 swarm（自动迭代 compile → lint → query）
- 合成数据生成 + transformers 微调流水线
- 本地 LLM 完全离线模式（llama.cpp / vLLM）
