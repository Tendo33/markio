# =================================================================================================
# Stage 1: Base Image
# 包含构建和运行都必需的基础环境，如CUDA、Python运行时等。
# =================================================================================================
# MinerU 4 + vLLM 0.28 resolve to torch 2.13 (CUDA 13 wheels) on Linux, so the base
# image moved from CUDA 12.4 / Ubuntu 22.04 to CUDA 13.0 / Ubuntu 24.04.
# Host requirement: NVIDIA driver >= 580.
FROM nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04 AS base

# 设置持久化的环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/workspace \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    MINERU_HOME=/root/.mineru

# 安装最小化的运行时依赖，并配置环境
# Ubuntu 24.04 uses deb822 sources in /etc/apt/sources.list.d/ubuntu.sources
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g; s/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/ubuntu.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates \
        # 基础运行工具 (根据你的应用实际需求调整)
        ffmpeg \
        libsm6 \
        libxext6 \
        libreoffice \
        pandoc \
        # 语言环境
        locales && \
    # 设置语言环境
    locale-gen C.UTF-8 && \
    # 清理APT缓存
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# =================================================================================================
# Stage 2: Frontend Builder
# 单独构建 Vue console，避免镜像依赖仓库中已有的静态产物。
# =================================================================================================
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm run build

# =================================================================================================
# Stage 2: Builder Stage
# 专门用于编译、安装依赖和下载模型。此阶段的产物将被拷贝到最终镜像，但其本身不会成为最终镜像。
# =================================================================================================
FROM base AS builder

# 安装 uv（需要能读取 lock revision 5 的新版本 uv）
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /usr/local/bin/

# 1. 仅复制依赖文件，最大化利用缓存
COPY pyproject.toml uv.lock ./ 

# 2. 创建虚拟环境并安装依赖
# Ubuntu 24.04 没有 python3.11 apt 包，使用 uv 托管的 CPython 3.11
RUN uv python install 3.11 && \
    uv venv -p 3.11 && \
    uv sync --frozen --no-install-project && \
    uv cache clean

# 3. 复制所有项目代码
COPY . .

RUN uv sync --frozen

# 4. 下载模型（MinerU 4：按 tier 下载到 $MINERU_HOME/models）
#    standard = pipeline 小模型 + VLM 模型，覆盖 markio 的 pipeline/vlm/hybrid 引擎
RUN bash -c "source .venv/bin/activate && mineru-models-download --tier standard -s modelscope"

# =================================================================================================
# Stage 3: Final Image
# 从干净的 base 镜像开始，只拷贝必要产物，构建一个轻量、安全的生产镜像。
# =================================================================================================
FROM base AS final

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /usr/local/bin/

# 从 builder 阶段拷贝源代码和下载好的模型
COPY --from=builder /workspace /workspace
COPY --from=frontend-builder /frontend/dist /workspace/markio/webapp
COPY --from=builder /opt/uv-python /opt/uv-python
COPY --from=builder /root/.mineru /root/.mineru

# 镜像内已预置模型，运行时只读本地模型
ENV MINERU_MODEL_SOURCE=local

# 设置 PATH，将虚拟环境的 bin 目录加入，这样可以直接执行 venv 内的命令
ENV PATH="/workspace/.venv/bin:$PATH"

# 设置启动脚本权限
RUN chmod +x /workspace/start_services.sh

# 设置入口点
ENTRYPOINT ["/bin/bash", "-c", "source /workspace/.venv/bin/activate && exec \"$@\"", "--"]
CMD ["python", "markio/main.py"]
