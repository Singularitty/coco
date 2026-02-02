FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# Toggle big stuff
ARG INSTALL_DBGSYM=0
ARG INSTALL_DEBUG_TOOLS=0

# If you truly need llvm-18-dev, set LLVM_DEV_MAJOR=18
# Default keeps everything on LLVM 14 to avoid bloat.
ARG LLVM_DEV_MAJOR=14

# For reproducible noninteractive apt
ENV DEBIAN_FRONTEND=noninteractive

# (Optional) If your dbg-deb setup is needed for dbgsym, keep it.
COPY setup-dbg-debs.sh /setup-dbg-debs.sh
RUN bash -x /setup-dbg-debs.sh || true

# Base packages (keep this lean; add optional blocks below)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      sudo \
      fish zsh \
      nano vim \
      cmake g++ \
      python3 python3-pip \
      wget curl git zip \
      jq \
      # LLVM/Clang toolchain (stick to one major by default)
      llvm-14-dev llvm-14-tools clang-14 clang-format \
      # Course tooling
      csmith libcsmith-dev \
 && if [ "${LLVM_DEV_MAJOR}" = "18" ]; then \
      apt-get install -y --no-install-recommends llvm-18-dev ; \
    fi \
 && if [ "${INSTALL_DEBUG_TOOLS}" = "1" ]; then \
      apt-get install -y --no-install-recommends gdb lldb-14 valgrind ; \
    fi \
 && if [ "${INSTALL_DBGSYM}" = "1" ]; then \
      apt-get install -y --no-install-recommends \
        llvm-14-dbgsym llvm-14-dev-dbgsym llvm-14-tools-dbgsym llvm-14-runtime-dbgsym clang-14-dbgsym ; \
    fi \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install *fixed* creduce (do NOT install Ubuntu creduce above)
COPY install-creduce.sh /install-creduce.sh
RUN bash -x /install-creduce.sh \
 && rm -f /install-creduce.sh \
 && rm -rf /tmp/* /var/tmp/*

# Python deps (avoid pip cache bloat)
RUN pip3 install --no-cache-dir --break-system-packages lark llvmlite

# Make clang default to clang-14
RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-14 40 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-14 40

# User setup
RUN userdel -r ubuntu 2>/dev/null || true \
 && useradd coco -u 1000 -m -s /bin/bash \
 && echo "coco ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER coco
ENV LLVM_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer-14
