import os
import json
import datetime
import base64
from pathlib import Path
from typing import List, Dict, Optional
import concurrent.futures
import typer
import psycopg2
from psycopg2.extras import DictCursor
from pgvector.psycopg2 import register_vector
from openai import OpenAI
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from io import BytesIO

load_dotenv()
app = typer.Typer()
client = OpenAI()

RAW_DIR = Path("raw")
WIKI_DIR = Path("wiki")
ASSETS_DIR = WIKI_DIR / "assets"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(WIKI_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ==================== 配置 ====================
USE_LOCAL_EMBED = os.getenv("USE_LOCAL_EMBED", "false").lower() == "true"
EMBED_DIM = 384 if USE_LOCAL_EMBED else 1536
EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2") if USE_LOCAL_EMBED else os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

if USE_LOCAL_EMBED:
    try:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(EMBED_MODEL)
        def embed(text: str) -> list[float]:
            return _local_model.encode(text[:8000]).tolist()
    except ImportError:
        raise ImportError("请执行 pip install sentence-transformers")
else:
    def embed(text: str) -> list[float]:
        resp = client.embeddings.create(model=EMBED_MODEL, input=text[:8000])
        return resp.data[0].embedding

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    register_vector(conn)
    return conn

# ====================== SETUP ======================
@app.command()
def setup():
    """创建或重建表（切换 embedding 维度时必须执行）"""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(f"""
            DROP TABLE IF EXISTS documents CASCADE;
            DROP TABLE IF EXISTS concepts CASCADE;
            DROP TABLE IF EXISTS links CASCADE;
            DROP TABLE IF EXISTS meta CASCADE;

            CREATE TABLE documents (
                id SERIAL PRIMARY KEY,
                raw_path TEXT UNIQUE,
                title TEXT,
                content TEXT,
                embedding VECTOR({EMBED_DIM}),
                summary TEXT,
                last_updated TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE concepts (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                md_path TEXT,
                embedding VECTOR({EMBED_DIM}),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE links (
                from_md TEXT,
                to_md TEXT,
                PRIMARY KEY (from_md, to_md)
            );
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TIMESTAMP
            );
        """)
    conn.commit()
    print(f"✅ 数据库已就绪（embedding 维度：{EMBED_DIM}）")

# ====================== INGEST ======================
def _process_file(f: Path):
    if not f.is_file():
        return
    if f.suffix.lower() not in {".md", ".txt", ".pdf", ".png", ".jpg", ".jpeg"}:
        return

    dest = RAW_DIR / f.name
    if dest.exists() and dest.stat().st_mtime >= f.stat().st_mtime:
        return  # 已是最新的

    import shutil
    shutil.copy(f, dest)

    if f.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        # 图像 → vision 描述 + 复制到 assets
        asset_path = ASSETS_DIR / f.name
        shutil.copy(dest, asset_path)
        with open(asset_path, "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode()
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "请用详细、结构化的 Markdown 描述这张图片，适合放入个人知识库 wiki。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }]
        )
        content = resp.choices[0].message.content
    else:
        with open(dest, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()

    emb = embed(content)
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO documents (raw_path, title, content, embedding, last_updated)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (raw_path) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                last_updated = NOW()
        """, (str(dest), f.stem, content, emb))
    conn.commit()
    print(f"✅ Ingested {dest}")

@app.command()
def ingest(path: str = typer.Argument(..., help="文件或目录")):
    p = Path(path)
    files = list(p.rglob("*")) if p.is_dir() else [p]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(_process_file, files)
    print("Ingest 完成")

# ====================== COMPILE ======================
def _llm_compile(raw_path: str, content: str, existing_concepts: List[str]) -> Dict:
    prompt = f"""You are the wiki compiler. Raw: {raw_path}

{content[:15000]}

Existing concepts: {existing_concepts[:60]}

Output valid JSON only:
{{
  "summary": "200字以内摘要",
  "concepts": ["概念1", "概念2"],
  "backlinks": ["existing-concept.md"],
  "full_md": "完整的 Obsidian Markdown（含 [[links]]、#tags、![[assets/xxx.png]]、Marp --- 分隔符等）"
}}"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a precise wiki compiler."},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)

@app.command()
def compile(force: bool = False):
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT value FROM meta WHERE key = 'last_compile'")
        last = cur.fetchone()
        last_ts = last['value'] if last else datetime.datetime(1900, 1, 1)

        cur.execute("""
            SELECT raw_path, content FROM documents 
            WHERE last_updated > %s OR %s = true
        """, (last_ts, force))
        docs = cur.fetchall()

        cur.execute("SELECT name FROM concepts")
        existing_concepts = [r['name'] for r in cur.fetchall()]

    def compile_one(doc):
        try:
            data = _llm_compile(doc['raw_path'], doc['content'], existing_concepts)
            md_path = WIKI_DIR / Path(doc['raw_path']).with_suffix('.md').name
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(data["full_md"])

            conn_local = get_db()
            with conn_local.cursor() as cur:
                for c in data["concepts"]:
                    emb = embed(c)
                    cur.execute("""
                        INSERT INTO concepts (name, md_path, embedding)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (name) DO UPDATE SET embedding = EXCLUDED.embedding
                    """, (c, str(md_path), emb))
                for b in data.get("backlinks", []):
                    cur.execute("INSERT INTO links (from_md, to_md) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                               (str(md_path), b))
            conn_local.commit()
            print(f"✅ Compiled → {md_path}")
            return True
        except Exception as e:
            print(f"❌ Compile failed {doc['raw_path']}: {e}")
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(compile_one, docs))

    with conn.cursor() as cur:
        cur.execute("INSERT INTO meta (key, value) VALUES ('last_compile', NOW()) ON CONFLICT (key) DO UPDATE SET value = NOW()")
    conn.commit()
    print("Compile 完成")

# ====================== AGENT TOOLS ======================
def _agent_tools():
    return [
        {"type": "function", "function": {"name": "search_kb", "description": "向量搜索 wiki", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 10}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "read_md", "description": "读取完整 Markdown 文件", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "list_concepts", "description": "列出所有概念", "parameters": {"type": "object", "properties": {}}}},
        {"type": "function", "function": {"name": "generate_plot", "description": "生成 Matplotlib 图像", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "filename": {"type": "string"}}, "required": ["code", "filename"]}}}
    ]

def _execute_tool(name: str, args: Dict):
    conn = get_db()
    if name == "search_kb":
        q = args["query"]
        emb = embed(q)
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT md_path, content FROM documents ORDER BY embedding <=> %s LIMIT %s", (emb, args.get("k", 10)))
            return cur.fetchall()
    elif name == "read_md":
        try:
            return Path(args["path"]).read_text(encoding="utf-8")
        except:
            return "File not found."
    elif name == "list_concepts":
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM concepts")
            return [r[0] for r in cur.fetchall()]
    elif name == "generate_plot":
        try:
            exec(args["code"], {"plt": plt, "BytesIO": BytesIO})
            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=200)
            plt.close()
            img_path = ASSETS_DIR / args["filename"]
            with open(img_path, "wb") as f:
                f.write(buf.getvalue())
            return f"![[{img_path.relative_to(WIKI_DIR)}]]"
        except Exception as e:
            return f"Plot error: {e}"
    return None

# ====================== QUERY ======================
@app.command()
def query(question: str):
    messages = [
        {"role": "system", "content": "你是知识库智能代理。使用工具检索、研究、生成最终 Markdown 报告（支持 Marp 幻灯片格式）。"},
        {"role": "user", "content": question}
    ]

    for _ in range(10):
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=_agent_tools(),
            tool_choice="auto"
        )
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            break
        for tc in msg.tool_calls:
            result = _execute_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

    final_md = messages[-1].content
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = WIKI_DIR / f"query-{timestamp}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Query Report\n\n**Question:** {question}\n\n{final_md}")
    print(f"✅ 答案已归档至 {out_path}")
    typer.echo(final_md)

# ====================== LINT ======================
@app.command()
def lint():
    """健康检查 + 生成新文章候选 + 修复建议"""
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT md_path, content FROM documents LIMIT 30")
        docs = cur.fetchall()
    content_sample = "\n\n".join([f"{d['md_path']}\n{d['content'][:3000]}" for d in docs])

    prompt = f"""Wiki 健康检查。找出不一致、缺失信息、有趣连接。
生成：
1. 3 个新文章候选（标题 + 简要理由）
2. 具体修复建议
3. 接下来值得问的 3 个问题

{content_sample}"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "你是严格的 wiki linter。"}, {"role": "user", "content": prompt}]
    )
    print(resp.choices[0].message.content)

# ====================== STATUS ======================
@app.command()
def status():
    """知识库状态一览"""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents"); docs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM concepts"); concepts = cur.fetchone()[0]
    wiki_files = len(list(WIKI_DIR.rglob("*.md")))
    print(f"📊 Documents: {docs} | Concepts: {concepts} | Wiki files: {wiki_files}")

if __name__ == "__main__":
    app()