# =================================================================================================
# Stage 1: Base Image
# 包含构建和运行都必需的基础环境，如CUDA、Python运行时等。
# =================================================================================================
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04 AS base

# 设置持久化的环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/workspace \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 安装最小化的运行时依赖，并配置环境
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        # Python 运行环境
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        # 基础运行工具 (根据你的应用实际需求调整)
        ffmpeg \
        libsm6 \
        libxext6 \
        libreoffice \
        pandoc \
        # 语言环境
        locales && \
    # 更新 python 的软链接
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    # 设置语言环境
    locale-gen C.UTF-8 && \
    # 清理APT缓存
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# =================================================================================================
# Stage 2: Builder Stage
# 专门用于编译、安装依赖和下载模型。此阶段的产物将被拷贝到最终镜像，但其本身不会成为最终镜像。
# =================================================================================================
FROM base AS builder

# 安装 uv
RUN curl -LsSf https://gitee.com/wangnov/uv-custom/releases/download/0.7.19/uv-installer-custom.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 1. 仅复制依赖文件，最大化利用缓存
COPY pyproject.toml uv.lock ./ 

# 2. 创建虚拟环境并安装依赖
RUN uv venv -p python3.11 && \
    uv sync --frozen --no-install-project && \
    uv cache clean

# 3. 复制所有项目代码
COPY . .

RUN uv sync

# 4. 下载模型
RUN bash -c "source .venv/bin/activate && mineru-models-download -s modelscope -m all"

# =================================================================================================
# Stage 3: Final Image
# 从干净的 base 镜像开始，只拷贝必要产物，构建一个轻量、安全的生产镜像。
# =================================================================================================
FROM base AS final

WORKDIR /workspace

RUN curl -LsSf https://gitee.com/wangnov/uv-custom/releases/download/0.7.19/uv-installer-custom.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 从 builder 阶段拷贝源代码和下载好的模型
COPY --from=builder /workspace /workspace
COPY --from=builder /root/.cache/modelscope/hub /root/.cache/modelscope/hub
COPY --from=builder /root/mineru.json /root/mineru.json

# 设置 PATH，将虚拟环境的 bin 目录加入，这样可以直接执行 venv 内的命令
ENV PATH="/workspace/.venv/bin:$PATH"

# 设置启动脚本权限
RUN chmod +x /workspace/start_services.sh

# 设置入口点
ENTRYPOINT ["/bin/bash", "-c", "source /workspace/.venv/bin/activate && exec \"$@\"", "--"]

