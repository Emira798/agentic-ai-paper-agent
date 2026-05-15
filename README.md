# 多AI智能体自动写论文系统

基于FastAPI的多AI智能体协作系统，能够自动规划研究流程、执行文献调研、撰写和编辑学术论文。系统使用PostgreSQL存储任务状态和结果，支持Tavily、arXiv、维基百科等研究工具。
本项目包含Docker配置，可在单个容器中运行**PostgreSQL数据库 + FastAPI应用**（适用于本地开发和测试）。

## 功能特性

* `/` - 提供简洁的用户界面（Jinja2模板）来启动论文写作任务
* `/generate_report` - 启动多线程AI智能体协作流程（规划器→研究员/撰写员/编辑员）
* `/task_progress/{task_id}` - 实时查看每个步骤/子步骤的执行状态
* `/task_status/{task_id}` - 获取最终状态和完整的论文报告

---

## 项目结构

```
.
├─ main.py                      # FastAPI主应用入口
├─ src/
│  ├─ planning_agent.py         # 规划智能体：planner_agent(), executor_agent_step()
│  ├─ agents.py                 # 研究智能体：research_agent, writer_agent, editor_agent
│  └─ research_tools.py         # 研究工具：tavily_search_tool, arxiv_search_tool, wikipedia_search_tool
├─ templates/
│  └─ index.html                # 用户界面页面
├─ static/                      # 静态资源文件（CSS/JS）
├─ docker/
│  └─ entrypoint.sh             # 启动脚本：启动Postgres，准备数据库，然后启动Uvicorn
├─ requirements.txt             # Python依赖包
├─ Dockerfile                   # Docker配置文件
└─ README.md                    # 项目说明文档
```

> 确保 `templates/index.html` 和（可选）`static/` 目录存在并被复制到Docker镜像中。

---

## 环境要求

* **Docker**（Windows/macOS上的Docker Desktop，或Linux上的Docker引擎）

* 在 `.env` 文件中配置API密钥：

  ```
  OPENAI_API_KEY=你的OpenAI-API密钥
  TAVILY_API_KEY=你的Tavily-API密钥
  ```

* Python依赖包（Docker会自动从 `requirements.txt` 安装）：

  * `fastapi`, `uvicorn`, `sqlalchemy`, `python-dotenv`, `jinja2`, `requests`, `wikipedia` 等
  * 以及 `aisuite` 客户端所需的其他库

---

## 环境变量

应用启动时**只读取 `DATABASE_URL`**。

* 容器入口点为本地开发设置了合理的默认值：

  ```
  postgresql://app:local@127.0.0.1:5432/appdb
  ```

* 使用Tavily搜索：

  * 通过 `.env` 文件或 `-e` 参数提供 `TAVILY_API_KEY`

可选参数（用于覆盖入口点的默认设置）：

* `POSTGRES_USER`（默认值：`app`）
* `POSTGRES_PASSWORD`（默认值：`local`）
* `POSTGRES_DB`（默认值：`appdb`）

---

## 构建和运行（本地开发）

### 1) 构建Docker镜像

```bash
docker build -t ai-paper-writer .
```

### 2) 运行容器（前台模式）

```bash
docker run --rm -it  -p 8000:8000  -p 5432:5432  --name ai-paper  --env-file .env  ai-paper-writer
```

你应该看到类似以下的日志：

```
🚀 Starting Postgres cluster 17/main...
✅ Postgres is ready
CREATE ROLE
CREATE DATABASE
🔗 DATABASE_URL=postgresql://app:local@127.0.0.1:5432/appdb
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3) 访问应用

* 用户界面：[http://localhost:8000/](http://localhost:8000/)
* API文档：[http://localhost:8000/docs](http://localhost:8000/docs)

---

## API快速开始

### 启动论文写作任务

```bash
curl -X POST http://localhost:8000/generate_report \
  -H "Content-Type: application/json" \
  -d '{"prompt": "人工智能在科学研究中的应用", "model":"openai:gpt-4o"}'
# 返回: {"task_id": "UUID..."}
```

### 查看任务进度

```bash
curl http://localhost:8000/task_progress/<任务ID>
```

### 获取最终状态和论文

```bash
curl http://localhost:8000/task_status/<任务ID>
```

---

## 故障排除

**打开 [http://localhost:8000](http://localhost:8000) 时看不到内容或出现错误**

* 确认容器内存在 `templates/index.html`：

  ```bash
  docker exec -it ai-paper bash -lc "ls -l /app/templates && ls -l /app/static || true"
  ```
* 加载页面时查看日志：

  ```bash
  docker logs -f ai-paper
  ```

**容器启动时要求Postgres密码**

* 入口点使用 **UNIX socket + peer认证** 进行管理员任务（无需密码）
  确保没有在脚本中调用 `psql -h 127.0.0.1 -U postgres`，而应使用：

  ```bash
  su -s /bin/bash postgres -c "psql -c '...'"
  ```

**`DATABASE_URL not set` 错误**

* 入口点会导出默认的DSN。如果覆盖了它，请确保它是有效的：

  ```
  postgresql://<用户名>:<密码>@<主机>:<端口>/<数据库名>
  ```

**重启后表消失**

* 在 `main.py` 中，启动时会调用 `Base.metadata.drop_all(...)`
  注释掉或添加环境变量保护：

  ```python
  if os.getenv("RESET_DB_ON_STARTUP") == "1":
      Base.metadata.drop_all(bind=engine)
  ```

**Tavily / arXiv / Wikipedia 错误**

* 提供 `TAVILY_API_KEY` 并确保网络访问正常，在根目录的 `.env` 文件中配置：
```
# OpenAI API密钥
OPENAI_API_KEY=你的OpenAI-API密钥
TAVILY_API_KEY=你的Tavily-API密钥
```

* Wikipedia有时会有速率限制；可以稍后重试或优雅地处理异常

---

## 开发提示

* **热重载**（可选）：开发时，如果挂载代码可以运行带 `--reload` 的Uvicorn：

  ```bash
  docker run --rm -it -p 8000:8000 -p 5432:5432 \
    -v "$PWD":/app \
    --name ai-paper ai-paper-writer \
    bash -lc "pg_ctlcluster \$(psql -V | awk '{print \$3}' | cut -d. -f1) main start && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
  ```

* **从主机连接数据库：**

  ```bash
  psql "postgresql://app:local@localhost:5432/appdb"
  ```

---
