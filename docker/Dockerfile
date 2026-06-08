FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV BLENDER_VERSION=4.2.0
ENV BLENDER_DIR=/opt/blender

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    wget python3 python3-pip \
    libgomp1 libglu1-mesa libxi6 libxrender1 \
    libxkbcommon0 libsm6 libice6 libx11-6 \
    libxxf86vm1 libxfixes3 libxext6 \
    libegl1 libdrm2 libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Blender 4.2 LTS 설치
RUN wget -q \
    "https://download.blender.org/release/Blender4.2/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && tar -xJf blender-${BLENDER_VERSION}-linux-x64.tar.xz -C /opt \
    && mv /opt/blender-${BLENDER_VERSION}-linux-x64 ${BLENDER_DIR} \
    && rm blender-${BLENDER_VERSION}-linux-x64.tar.xz

ENV PATH="${BLENDER_DIR}:${PATH}"

# VRM Addon for Blender v4.2.2 다운로드 및 설치
RUN wget -q -O /tmp/vrm_addon.zip \
    "https://github.com/saturday06/VRM-Addon-for-Blender/releases/download/v4.2.2/VRM_Addon_for_Blender-4_2_2.zip"

COPY docker/install_vrm.py /tmp/install_vrm.py
RUN blender --background --python /tmp/install_vrm.py && \
    rm /tmp/vrm_addon.zip /tmp/install_vrm.py

# 앱 설치
WORKDIR /app
COPY scripts/vroid_to_glb.py /app/vroid_to_glb.py
COPY docker/server.py /app/server.py

RUN pip3 install --no-cache-dir flask flask-cors

EXPOSE 8080
CMD ["python3", "server.py"]
