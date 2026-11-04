# =================================================================================================
# Runtime base is the CUDA runtime image. The devel image is only the builder:
# the final stage does not need nvcc or the CUDA headers.
# MinerU 4 + vLLM 0.28 resolve to torch 2.13 (CUDA 13 wheels) on Linux.
# Host requirement: NVIDIA driver >= 580.
# =================================================================================================
ARG CUDA_RUNTIME=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04
ARG CUDA_DEVEL=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04

FROM ${CUDA_RUNTIME} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/workspace \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    MINERU_HOME=/root/.mineru

# Ubuntu 24.04 uses deb822 sources in /etc/apt/sources.list.d/ubuntu.sources
# APT 镜像走 HTTPS（可用 --build-arg APT_MIRROR=archive.ubuntu.com 切换）
ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn
RUN sed -i "s#http://archive.ubuntu.com#https://${APT_MIRROR}#g; s#http://security.ubuntu.com#https://${APT_MIRROR}#g" /etc/apt/sources.list.d/ubuntu.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates \
        ffmpeg \
        libsm6 \
        libxext6 \
        libreoffice \
        pandoc \
        locales && \
    locale-gen C.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# =================================================================================================
# Frontend. Node matches CI. The Vite outDir is /markio/webapp.
# =================================================================================================
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@10.29.2 --activate && pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm run build

# =================================================================================================
# Builder. Devel is required while native wheels are resolved; it is not the
# published image. INSTALL_MODELS=0 skips the ModelScope download.
# =================================================================================================
FROM ${CUDA_DEVEL} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/workspace \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    MINERU_HOME=/root/.mineru

ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn
RUN sed -i "s#http://archive.ubuntu.com#https://${APT_MIRROR}#g; s#http://security.ubuntu.com#https://${APT_MIRROR}#g" /etc/apt/sources.list.d/ubuntu.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates \
        ffmpeg \
        libsm6 \
        libxext6 \
        libreoffice \
        pandoc \
        locales && \
    locale-gen C.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock ./

RUN uv python install 3.11 && \
    uv venv -p 3.11 && \
    uv sync --frozen --no-install-project && \
    uv cache clean

COPY . .

RUN uv sync --frozen

ARG INSTALL_MODELS=1
RUN mkdir -p /root/.mineru && \
    if [ "$INSTALL_MODELS" = "1" ]; then \
      bash -c "source .venv/bin/activate && \
        mineru-models-download --tier standard --small-backend torch --vlm-engine vllm -s modelscope && \
        mineru-models-download --tier standard --small-backend onnx --vlm-engine llama-cpp -s modelscope"; \
    fi

# =================================================================================================
# Final image. Runtime CUDA only, plus the venv, console, and optional models.
# =================================================================================================
FROM runtime AS final

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /usr/local/bin/

COPY --from=builder /workspace /workspace
COPY --from=frontend-builder /markio/webapp /workspace/markio/webapp
COPY --from=builder /opt/uv-python /opt/uv-python
COPY --from=builder /root/.mineru /root/.mineru

ENV MINERU_MODEL_SOURCE=local
ENV PATH="/workspace/.venv/bin:$PATH"

RUN chmod +x /workspace/start_services.sh

ENTRYPOINT ["/bin/bash", "-c", "source /workspace/.venv/bin/activate && exec \"$@\"", "--"]
CMD ["python", "markio/main.py"]
