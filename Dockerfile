# syntax=docker/dockerfile:1.7
ARG BUILD_DATE
ARG VERSION=dev
ARG MT5_SETUP_URL="https://download.terminal.free/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
ARG PYTHON_VERSION=3.9.13
ARG PYTHON_SETUP_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
ARG UV_VERSION=0.10.11
ARG UV_WINDOWS_ZIP_URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-pc-windows-msvc.zip"
ARG WINE_VERSION=10.0.0.0~bookworm-1

FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm

ARG BUILD_DATE
ARG VERSION
ARG MT5_SETUP_URL
ARG PYTHON_VERSION
ARG PYTHON_SETUP_URL
ARG UV_VERSION
ARG UV_WINDOWS_ZIP_URL
ARG WINE_VERSION

LABEL org.opencontainers.image.title="metatrader5-service"
LABEL org.opencontainers.image.description="MetaTrader 5 with Wine and KasmVNC"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.version="${VERSION}"

ENV TITLE=MetaTrader5 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    WINEDEBUG=-all \
    WINEARCH=win64 \
    WINEDLLOVERRIDES=winemenubuilder.exe=d \
    WINEPREFIX=/config/.wine \
    MT5_INSTALLER_DIR=/opt/installers \
    WINE_GECKO_DIR=/opt/wine-offline/gecko \
    WINE_MONO_DIR=/opt/wine-offline/mono \
    MT5_SETUP_URL=${MT5_SETUP_URL} \
    PYTHON_VERSION=${PYTHON_VERSION} \
    PYTHON_SETUP_URL=${PYTHON_SETUP_URL} \
    UV_VERSION=${UV_VERSION} \
    UV_WINDOWS_ZIP_URL=${UV_WINDOWS_ZIP_URL} \
    MT5_CMD_OPTIONS=

RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        gnupg2 \
        git \
        gosu \
        locales \
        p7zip-full \
        sudo \
        tzdata \
        xvfb \
        xauth \
        cabextract \
        winbind \
        procps \
        psmisc \
        unzip \
        zenity \
    && mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -O /etc/apt/sources.list.d/winehq-bookworm.sources https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources \
    && apt-get update \
    && apt-get install -y --install-recommends \
        "winehq-stable=${WINE_VERSION}" \
        "wine-stable=${WINE_VERSION}" \
        "wine-stable-amd64=${WINE_VERSION}" \
        "wine-stable-i386:i386=${WINE_VERSION}" \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && mkdir -p /opt/installers /opt/wine-offline/gecko /opt/wine-offline/mono /config \
    && mkdir -p /usr/share/wine \
    && rm -rf /usr/share/wine/gecko /usr/share/wine/mono \
    && ln -sfn /opt/wine-offline/gecko /usr/share/wine/gecko \
    && ln -sfn /opt/wine-offline/mono /usr/share/wine/mono \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=644 scripts/lib/common.sh /scripts/lib/common.sh
COPY --chmod=755 scripts/build/download-offline-assets.sh /scripts/build/download-offline-assets.sh
COPY --chmod=755 scripts/build/install-mt5.sh /scripts/build/install-mt5.sh
COPY --chmod=755 scripts/build/install-python.sh /scripts/build/install-python.sh
COPY --chmod=755 scripts/build/install-uv.sh /scripts/build/install-uv.sh
COPY --chmod=755 scripts/build/prepare-mt5-resource.sh /scripts/build/prepare-mt5-resource.sh
COPY --chmod=755 scripts/build/preinstall-runtime.sh /scripts/build/preinstall-runtime.sh

RUN --mount=type=bind,source=resource,target=/resource,readonly \
    /scripts/build/preinstall-runtime.sh

COPY --chmod=755 scripts/runtime/bootstrap-prefix.sh /scripts/runtime/bootstrap-prefix.sh
COPY --chmod=755 scripts/runtime/http-env.sh /scripts/runtime/http-env.sh
COPY --chmod=755 scripts/runtime/http-start.sh /scripts/runtime/http-start.sh
COPY --chmod=755 scripts/runtime/http-stop.sh /scripts/runtime/http-stop.sh
COPY --chmod=755 scripts/runtime/http-restart.sh /scripts/runtime/http-restart.sh
COPY --chmod=755 scripts/runtime/http-sync-deps.sh /scripts/runtime/http-sync-deps.sh
COPY --chmod=755 scripts/runtime/launch-mt5.sh /scripts/runtime/launch-mt5.sh
COPY --chmod=755 scripts/runtime/start-mt5.sh /scripts/runtime/start-mt5.sh
COPY --chmod=755 scripts/runtime/healthcheck.sh /scripts/runtime/healthcheck.sh
COPY root /

RUN chmod 755 /scripts /scripts/build /scripts/runtime /scripts/lib \
    && chmod 755 /scripts/build/download-offline-assets.sh \
        /scripts/build/install-mt5.sh \
        /scripts/build/install-python.sh \
        /scripts/build/install-uv.sh \
        /scripts/build/prepare-mt5-resource.sh \
        /scripts/build/preinstall-runtime.sh \
        /scripts/runtime/bootstrap-prefix.sh \
        /scripts/runtime/http-env.sh \
        /scripts/runtime/http-start.sh \
        /scripts/runtime/http-stop.sh \
        /scripts/runtime/http-restart.sh \
        /scripts/runtime/http-sync-deps.sh \
        /scripts/runtime/launch-mt5.sh \
        /scripts/runtime/start-mt5.sh \
        /scripts/runtime/healthcheck.sh \
    && chmod 644 /scripts/lib/common.sh

EXPOSE 3000 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD /scripts/runtime/healthcheck.sh
