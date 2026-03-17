#!/bin/bash
# Setup: instala todas as dependências em modo usuário (sem sudo)
set -e

echo "=== Instalando pip (modo usuário) ==="
python3 -m ensurepip --user 2>/dev/null || true
python3 -m pip install --upgrade pip --user --quiet

echo "=== Baixando ffmpeg (binário estático) ==="
FFMPEG_DIR="$HOME/.local/bin"
mkdir -p "$FFMPEG_DIR"

if ! command -v ffmpeg &>/dev/null; then
    echo "Baixando ffmpeg estático..."
    FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    TMP=$(mktemp -d)
    curl -L "$FFMPEG_URL" -o "$TMP/ffmpeg.tar.xz" --progress-bar
    tar -xf "$TMP/ffmpeg.tar.xz" -C "$TMP"
    cp "$TMP"/ffmpeg-*-amd64-static/ffmpeg "$FFMPEG_DIR/"
    cp "$TMP"/ffmpeg-*-amd64-static/ffprobe "$FFMPEG_DIR/"
    rm -rf "$TMP"
    echo "ffmpeg instalado em $FFMPEG_DIR"
else
    echo "ffmpeg já disponível: $(which ffmpeg)"
fi

# Garante que ~/.local/bin está no PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "=== Verificando dependências de build ==="
# Função: instala dependências via yum (Amazon Linux, RHEL, CentOS)
install_build_deps_yum() {
    local PKGS="gcc gcc-c++ make python3-devel"
    if command -v dnf &>/dev/null; then
        [ "$EUID" -eq 0 ] && dnf install -y -q $PKGS || sudo dnf install -y -q $PKGS
    else
        [ "$EUID" -eq 0 ] && yum install -y -q $PKGS || sudo yum install -y -q $PKGS
    fi
}
# Função: instala dependências via apt (Debian/Ubuntu)
install_build_deps_apt() {
    [ "$EUID" -eq 0 ] && apt-get update -qq && apt-get install -y -qq build-essential python3-dev gcc g++ \
        || { sudo apt-get update -qq; sudo apt-get install -y -qq build-essential python3-dev gcc g++; }
}

if ! command -v gcc &>/dev/null; then
    echo "AVISO: gcc não encontrado. Tentando instalar dependências de build..."
    if command -v apt-get &>/dev/null; then
        echo "Tentando instalar com apt-get (pode pedir senha)..."
        install_build_deps_apt && echo "Dependências de build instaladas."
    elif command -v dnf &>/dev/null || command -v yum &>/dev/null; then
        echo "Tentando instalar com yum/dnf (Amazon Linux / AlmaLinux / RHEL — pode pedir senha)..."
        if ! install_build_deps_yum 2>/dev/null; then
            echo "Falha na instalação automática. Execute manualmente no terminal:"
            command -v dnf &>/dev/null && echo "  sudo dnf install -y gcc gcc-c++ make python3-devel" || echo "  sudo yum install -y gcc gcc-c++ make python3-devel"
            exit 1
        fi
        echo "Dependências de build instaladas."
    else
        echo "ERRO: gcc não encontrado e nenhum gerenciador de pacotes (apt/yum/dnf) disponível."
        echo "Amazon Linux / AlmaLinux / RHEL: sudo dnf install -y gcc gcc-c++ make python3-devel"
        echo "  (ou com yum: sudo yum install -y gcc gcc-c++ make python3-devel)"
        echo "Debian/Ubuntu: sudo apt-get install -y build-essential python3-dev gcc g++"
        exit 1
    fi
else
    echo "gcc encontrado: $(which gcc)"
fi

# Verifica python3-dev / python3-devel (headers necessários para compilar extensões)
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))" 2>/dev/null || echo "")
if [ -z "$PYTHON_INCLUDE" ] || [ ! -f "$PYTHON_INCLUDE/Python.h" ]; then
    echo "AVISO: headers Python não encontrados. Tentando instalar..."
    if command -v apt-get &>/dev/null; then
        [ "$EUID" -eq 0 ] && apt-get install -y -qq python3-dev || sudo apt-get install -y -qq python3-dev
    elif command -v dnf &>/dev/null || command -v yum &>/dev/null; then
        install_build_deps_yum
    fi
else
    echo "Headers Python encontrados."
fi

echo "=== Instalando dependências Python ==="
pip install --user --quiet \
    yt-dlp \
    pydub \
    numpy \
    scipy \
    tqdm

echo ""
echo "=== Instalando TTS (Coqui XTTS v2) ==="
echo "AVISO: pacote pesado (~500MB), aguarde..."
pip install --user --quiet TTS

echo ""
echo "=== Setup concluído! ==="
echo "Execute os scripts na ordem:"
echo "  python3 1_download.py"
echo "  python3 2_prepare.py"
echo "  python3 3_synthesize.py"
