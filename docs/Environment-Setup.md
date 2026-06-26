# TalentSense HR 简历推荐系统 - 环境准备清单

**版本**：v2.5
**日期**：2026-06-26
**对接文档**：
- [MVP-Design.md](./MVP-Design.md)（需求设计）
- [API-Design.md](./API-Design.md)（接口契约）
- [Backend-Design.md](./Backend-Design.md)（后端开发）
- [Frontend-Design.md](./Frontend-Design.md)（前端开发）

> 本文档列出项目启动前需要准备的全部环境、依赖、开发工具与模型，开发者可按清单逐项核对。

---

## 一、硬件环境

| 类别 | 最低配置 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **CPU** | 8 核 | 16 核+ | 大模型推理/批量解析时 CPU 密集 |
| **内存** | 16 GB | 32 GB+ | BGE-M3(~2GB) + BGE-Reranker(~1GB) + Milvus + MongoDB + Redis + MinIO |
| **GPU** | 无（CPU 推理） | NVIDIA GPU（CUDA） | 有 GPU 可加速嵌入与重排，CPU 也可跑 |
| **显存** | — | 8 GB+ | GPU 推理时建议 8GB 以上 |
| **磁盘** | 50 GB 可用空间 | 100 GB+ SSD | 模型文件 + 简历文件存储 + Docker 镜像 |
| **网络** | 可访问外网 | 稳定外网 | 下载模型、Docker 镜像、LLM API 调用 |

---

## 二、操作系统

| 系统 | 版本 | 支持状态 |
|------|------|---------|
| Windows | 10 / 11 | ✅ 开发用 |
| macOS | 12+ | ✅ 开发用 |
| Linux | Ubuntu 20.04+ / CentOS 8+ | ✅ 生产部署 |

> 推荐 Windows 11 开发 + Linux 生产部署。Docker Desktop 需开启 WSL2（Windows）。

---

## 三、开发工具

### 3.1 必备工具

| 工具 | 版本要求 | 用途 | 下载地址 |
|------|---------|------|---------|
| **Git** | 2.30+ | 版本控制 | https://git-scm.com |
| **Docker Desktop** | 24.0+ | 基础设施容器化 | https://www.docker.com/products/docker-desktop |
| **Docker Compose** | v2.20+ | 多服务编排 | Docker Desktop 自带 |
| **Python** | 3.11.x | 后端运行时 | https://www.python.org |
| **Node.js** | 18.x / 20.x LTS | 前端运行时 | https://nodejs.org |
| **npm** / **pnpm** | npm 9+ / pnpm 8+ | 包管理 | Node.js 自带 npm |
| **VS Code** | 最新稳定版 | 代码编辑器 | https://code.visualstudio.com |

### 3.2 VS Code 推荐插件

| 插件 | 用途 |
|------|------|
| **Python** (Microsoft) | Python 语法/调试/Linting |
| **Pylance** | Python 类型检查 |
| **Volar** (Vue Language Features) | Vue3 + TypeScript 支持 |
| **TypeScript Vue Plugin** | Vue 中 TS 支持 |
| **ESLint** | JS/TS 代码检查 |
| **Prettier** | 代码格式化 |
| **DotENV** | .env 文件高亮 |
| **REST Client** | 直接发 HTTP 请求测试 API |
| **Docker** | Docker 容器管理 |
| **MongoDB for VS Code** | MongoDB 数据浏览 |

---

## 四、Docker 基础设施（9 服务）

使用 `docker-compose.yml` 一键启动，所有服务均来自 [MVP-Design.md 参考项目2](./MVP-Design.md#参考项目2hrcopilot-v20--已有基础设施)。

| 服务 | 镜像 | 端口 | 用途 | 数据卷 |
|------|------|------|------|--------|
| **Milvus** | milvusdb/milvus:v2.4.x | 19530 (gRPC) / 9091 (metrics) | 向量数据库 | milvus_data |
| **Milvus Standalone** | — | — | Milvus 独立部署模式 | — |
| **etcd** | quay.io/coreos/etcd:v3.5.5 | 2379 | Milvus 元数据 | etcd_data |
| **MinIO** | minio/minio:latest | 9000 (API) / 9001 (Console) | 对象存储 | minio_data |
| **MongoDB** | mongo:7.0 | 27017 | 业务数据库 | mongo_data |
| **Redis** | redis:7-alpine | 6379 | 缓存 | redis_data |
| **Nginx** | nginx:alpine | 80 / 443 | 反向代理（可选） | — |

### 4.1 默认连接信息

| 服务 | 地址 | 账号 | 密码 |
|------|------|------|------|
| Milvus | `localhost:19530` | — | — |
| MongoDB | `mongodb://localhost:27017` | — | — |
| Redis | `redis://localhost:6379/0` | — | — |
| MinIO API | `http://localhost:9000` | minioadmin | minioadmin |
| MinIO Console | `http://localhost:9001` | minioadmin | minioadmin |

> 生产环境请务必修改默认密码。

### 4.2 docker-compose.yml 参考

复用 HRCopilot v2.0 的 `docker-compose.yml`，确保包含 Milvus 2.4+、MongoDB 7.0、Redis 7+、MinIO。

```bash
# 启动全部基础设施
docker-compose up -d

# 查看状态
docker-compose ps

# 停止
docker-compose down
```

---

## 五、AI 模型（需提前下载）

### 5.1 嵌入与重排模型（本地部署）

| 模型 | 大小 | 存储位置 | 用途 | 下载来源 |
|------|------|---------|------|---------|
| **BGE-M3** | ~2.2 GB | `backend/models/bge-m3/` | 多语言嵌入（Dense 1024 维 + Sparse） | HuggingFace / ModelScope |
| **BGE-Reranker-v2-m3** | ~1.2 GB | `backend/models/bge-reranker-v2-m3/` | CrossEncoder 精排 | HuggingFace / ModelScope |

**下载方式（二选一）**：

方式一：HuggingFace（需外网）
```bash
# BGE-M3
git lfs install
git clone https://huggingface.co/BAAI/bge-m3 backend/models/bge-m3

# BGE-Reranker-v2-m3
git clone https://huggingface.co/BAAI/bge-reranker-v2-m3 backend/models/bge-reranker-v2-m3
```

方式二：ModelScope（国内推荐，速度快）
```python
from modelscope import snapshot_download

# BGE-M3
snapshot_download('AI-ModelScope/bge-m3', cache_dir='./backend/models')

# BGE-Reranker-v2-m3
snapshot_download('Xorbits/bge-reranker-v2-m3', cache_dir='./backend/models')
```

> 模型使用 **延迟加载**（见 [Backend-Design.md 3.4](./Backend-Design.md#34-嵌入与重排延迟加载)），启动时不加载，首次检索时加载，节省启动内存。

### 5.2 OCR 模型（RapidOCR 自动下载）

| 模型 | 说明 |
|------|------|
| RapidOCR (onnxruntime) | 首次运行时自动下载，约 20MB |

RapidOCR Python 库首次初始化时自动下载 onnx 模型到用户目录，无需手动准备。

### 5.3 LLM 大模型（API 调用，非本地部署）

| 模型 | 服务商 | 用途 | 获取方式 |
|------|--------|------|---------|
| **qwen-plus** / **qwen-max** | 阿里 DashScope | 对话/评分/Query改写/邮件生成/面试题/JD解析 | 开通 DashScope，获取 API Key |
| **gpt-4o-mini** / **gpt-4o** | OpenAI | 同上（可选，需兼容 OpenAI 格式的 API） | 自行申请 |

**DashScope 开通步骤**：
1. 访问 https://dashscope.aliyun.com 注册并开通
2. 创建 API-KEY（`sk-xxxx`）
3. 复制到 `.env` 的 `LLM_API_KEY`
4. 测试：确保 `LLM_BASE_URL` 为 `https://dashscope.aliyuncs.com/compatible-mode/v1`

> 项目使用 **AsyncOpenAI 兼容协议**，理论上支持任何 OpenAI 兼容的 LLM API，只需改 `LLM_BASE_URL` 和 `LLM_API_KEY`。

---

## 六、后端 Python 依赖

### 6.1 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| fastapi | 0.115+ | Web 框架 |
| uvicorn | 0.30+ | ASGI 服务器 |
| pydantic | 2.x | 数据校验 |
| pydantic-settings | 2.x | 配置管理 |
| motor | 3.x | MongoDB 异步驱动 |
| redis | 5.x | Redis 异步客户端 |
| pymilvus | 2.4+ | Milvus 客户端 |
| minio | 7.x | MinIO 客户端 |
| openai | 1.x | AsyncOpenAI 客户端 |
| langchain | 0.3+ | RAG 框架 |
| langgraph | 0.2+ | Agent 状态机 |
| FlagEmbedding / FlagModel | 1.2+ | BGE-M3 + BGE-Reranker |
| rapidocr-onnxruntime | 1.3+ | OCR |
| pymupdf | 1.24+ | PDF 解析 |
| python-docx | 1.1+ | DOCX 解析 |
| aiosmtplib | 3.x | 异步邮件 |
| openpyxl | 3.1+ | Excel 导出 |
| python-jose | 3.x | JWT |
| passlib | 1.7 | 密码哈希 |
| tenacity | 8.x | 重试 |
| loguru | 0.7+ | 日志 |
| python-multipart | 0.0.9 | 文件上传 |

### 6.2 requirements.txt 示例

```txt
# Web 框架
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2

# 数据库
motor==3.5.1
redis==5.0.8
pymilvus==2.4.5
minio==7.2.10

# LLM / RAG
openai==1.51.0
langchain==0.3.0
langgraph==0.2.39
FlagEmbedding==1.2.11

# OCR / 文档解析
rapidocr-onnxruntime==1.3.24
pymupdf==1.24.10
python-docx==1.1.2

# 邮件 / Excel
aiosmtplib==3.0.2
openpyxl==3.1.5

# 认证 / 工具
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
tenacity==9.0.0
loguru==0.7.2
python-multipart==0.0.12
```

### 6.3 安装命令

```bash
cd backend
pip install -r requirements.txt
```

> 建议使用虚拟环境（venv / conda）隔离依赖。

---

## 七、前端 npm 依赖

### 7.1 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| vue | 3.4+ | 前端框架 |
| vue-router | 4.2+ | 路由 |
| pinia | 2.1+ | 状态管理 |
| element-plus | 2.6+ | UI 组件库 |
| @element-plus/icons-vue | 2.x | 图标 |
| axios | 1.6+ | HTTP 请求 |
| echarts | 5.5+ | 图表（数据看板） |
| vue-echarts | 7.x | Vue ECharts 封装（可选） |
| pdfjs-dist | 4.0+ | PDF 预览 |
| typescript | 5.0+ | 类型系统 |
| vite | 5.0+ | 构建工具 |
| sass | 1.70+ | CSS 预处理器 |

### 7.2 package.json 示例

```json
{
  "name": "talentsense-frontend",
  "version": "2.5.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.6.0",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.8",
    "echarts": "^5.5.0",
    "pdfjs-dist": "^4.0.379"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vue-tsc": "^2.0.0",
    "sass": "^1.72.0"
  }
}
```

### 7.3 安装命令

```bash
cd frontend
npm install
# 或使用 pnpm
pnpm install
```

---

## 八、环境变量配置

### 8.1 后端 .env

复制 `backend/.env.example` 为 `.env`，填入实际值：

```env
# ===== 服务 =====
APP_NAME=TalentSense HR
DEBUG=true
API_V1_PREFIX=/api/v1

# ===== MongoDB =====
MONGO_URI=mongodb://localhost:27017
MONGO_DB=talentsense

# ===== Redis =====
REDIS_URL=redis://localhost:6379/0

# ===== Milvus =====
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=resumes

# ===== MinIO =====
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=resumes
MINIO_SECURE=false

# ===== LLM (DashScope 兼容 OpenAI) =====
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# ===== JWT =====
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== 模型路径 =====
BGE_M3_PATH=./models/bge-m3
BGE_RERANKER_PATH=./models/bge-reranker-v2-m3

# ===== 检索参数 =====
HYBRID_DENSE_WEIGHT=1.0
HYBRID_SPARSE_WEIGHT=0.7
RETRIEVE_TOP_K=20
RERANK_TOP_K=10
```

### 8.2 前端 .env

```env
# .env.development
VITE_API_BASE=/api/v1
VITE_PDFJS_WORKER=/pdf.worker.min.js
```

---

## 九、环境准备检查清单

启动开发前，请逐项确认：

### 9.1 基础工具

- [ ] Git 已安装，可正常 clone
- [ ] Docker Desktop 已安装并启动
- [ ] Docker Compose 可用（`docker-compose --version`）
- [ ] Python 3.11 已安装（`python --version`）
- [ ] Node.js 18+ 已安装（`node --version`）
- [ ] npm / pnpm 可用（`npm --version`）

### 9.2 Docker 基础设施

- [ ] `docker-compose up -d` 全部服务启动成功
- [ ] Milvus 端口 19530 可连接
- [ ] MongoDB 端口 27017 可连接（可用 MongoDB Compass 测试）
- [ ] Redis 端口 6379 可连接（`redis-cli ping`）
- [ ] MinIO Console 可访问（http://localhost:9001）
- [ ] MinIO 已创建 `resumes` bucket

### 9.3 AI 模型

- [ ] BGE-M3 模型已下载到 `backend/models/bge-m3/`（含 config.json / model.safetensors 等）
- [ ] BGE-Reranker-v2-m3 已下载到 `backend/models/bge-reranker-v2-m3/`
- [ ] DashScope API Key 已获取，已填入 `.env` 的 `LLM_API_KEY`
- [ ] LLM 连通性测试通过（可跑一个简单的 chat 验证）

### 9.4 后端依赖

- [ ] Python 虚拟环境已创建并激活
- [ ] `pip install -r requirements.txt` 安装成功，无报错
- [ ] `uvicorn app.main:app --reload --port 8000` 可正常启动
- [ ] 访问 http://localhost:8000/docs 可打开 Swagger 文档

### 9.5 前端依赖

- [ ] `npm install` 安装成功
- [ ] `npm run dev` 可正常启动
- [ ] 访问 http://localhost:5173 可打开页面
- [ ] 登录接口可正常调用（测试 Token 获取）

### 9.6 连通性验证

- [ ] 后端 → MongoDB：可读写
- [ ] 后端 → Redis：可读写
- [ ] 后端 → Milvus：可连接，Collection 可创建
- [ ] 后端 → MinIO：可上传/下载文件
- [ ] 后端 → LLM API：可正常调用 chat completion
- [ ] 后端 → 嵌入模型：BGE-M3 encode 不报错
- [ ] 后端 → 重排模型：Reranker 不报错
- [ ] 前端 → 后端：API 请求正常（浏览器 Network 200）

---

## 十、常见问题

### Q1: BGE-M3 模型太大，下载慢？
A: 用 ModelScope 国内镜像下载，或从公司内网模型仓库拷贝。

### Q2: Docker 启动 Milvus 失败？
A: 确保 Docker 内存 ≥ 4GB（Milvus + etcd 至少需要 4GB），Windows 下在 Docker Desktop Settings → Resources 调整。

### Q3: 首次检索很慢？
A: 正常，首次调用触发模型加载（延迟加载设计），加载后检索就快了。

### Q4: DashScope API 调用失败？
A: 检查 `LLM_BASE_URL` 是否为 `https://dashscope.aliyuncs.com/compatible-mode/v1`（兼容模式），模型名是否为 `qwen-plus` / `qwen-max`。

### Q5: PDF 解析中文乱码？
A: PyMuPDF 对中文支持良好，若乱码检查 PDF 是否为扫描件（扫描件走 OCR 路径）。

### Q6: 内存不够用怎么办？
A: 1) 使用 GPU 推理（显存分担）；2) 减小 `RETRIEVE_TOP_K`；3) 关闭不用的 Docker 服务。
