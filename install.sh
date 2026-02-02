#!/bin/bash
##############################################################################
#
#  TURING SMART SCREEN — INSTALADOR (Regata OS / openSUSE)
#
#  Uso:
#    git clone https://github.com/marquimRcc/turing-smart-screen-python-regataos-opensuse
#    cd turing-smart-screen-python-regataos-opensuse
#    bash install.sh
#
#  O que este script faz:
#    1. Verifica pré-requisitos (OS, Python, disco)
#    2. Instala dependências do sistema via zypper
#    3. Cria ambiente virtual Python 3.11
#    4. Instala dependências Python + PyQt5 + suporte AMD GPU
#    5. Configura regras udev para USB
#    6. Instala serviço systemd (nível de usuário)
#    7. Instala aplicativo de bandeja do sistema
#    8. Configura inicialização automática
#    9. Executa assistente de configuração (opcional)
#
##############################################################################

set -euo pipefail

# ── Cores ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers de output ────────────────────────────────────────
_step=0
_total_steps=8

step() {
    (( _step++ ))
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  [${_step}/${_total_steps}] $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

ok()   { echo -e "  ${GREEN}✔${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✘${NC} $1"; }
info() { echo -e "  ${BLUE}ℹ${NC} $1"; }

die() {
    echo ""
    fail "$1"
    echo ""
    exit 1
}

# ── Detectar diretório do repositório ────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
VENV_DIR="$REPO_DIR/venv"

# Validar que estamos dentro do repositório clonado
if [ ! -f "$REPO_DIR/main.py" ] || [ ! -d "$REPO_DIR/tray" ]; then
    die "Este script deve ser executado de dentro do repositório clonado.
    Uso:
      git clone https://github.com/marquimRcc/turing-smart-screen-python-regataos-opensuse
      cd turing-smart-screen-python-regataos-opensuse
      bash install.sh"
fi

# ── Banner ───────────────────────────────────────────────────
clear
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║                                                       ║"
echo "  ║        TURING SMART SCREEN — INSTALADOR               ║"
echo "  ║        Regata OS / openSUSE Edition                   ║"
echo "  ║                                                       ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Verificar que NÃO é root ────────────────────────────────
if [ "$EUID" -eq 0 ]; then
    die "NÃO execute como root (sudo).
    Execute como seu usuário normal: bash install.sh
    O script pedirá a senha sudo quando necessário."
fi

##############################################################################
# ETAPA 1: PRÉ-REQUISITOS
##############################################################################
step "Verificando pré-requisitos"

# OS check
if [ -f /etc/os-release ]; then
    . /etc/os-release
    info "Sistema: ${PRETTY_NAME:-$ID}"
else
    warn "Não foi possível determinar o sistema operacional"
fi

# Python 3.11
if command -v python3.11 &>/dev/null; then
    PY_VER=$(python3.11 --version 2>&1)
    ok "Python encontrado: $PY_VER"
else
    die "Python 3.11 não encontrado.
    Instale com: sudo zypper install python311"
fi

# Disk space (need at least 500MB)
AVAIL_MB=$(df -m "$REPO_DIR" | awk 'NR==2 {print $4}')
if [ "$AVAIL_MB" -ge 500 ]; then
    ok "Espaço em disco: ${AVAIL_MB}MB disponíveis"
else
    warn "Espaço em disco baixo: ${AVAIL_MB}MB (recomendado: 500MB+)"
fi

# GPU detection
HAS_AMD_GPU=false
if lspci 2>/dev/null | grep -i "VGA\|3D\|Display" | grep -qi "AMD\|ATI\|Radeon"; then
    HAS_AMD_GPU=true
    GPU_NAME=$(lspci | grep -i "VGA\|3D\|Display" | grep -i "AMD\|ATI\|Radeon" | head -1 | sed 's/.*: //')
    ok "GPU AMD detectada: $GPU_NAME"
else
    info "GPU AMD não detectada (pyamdgpuinfo não será instalado)"
fi

# Show repo location
info "Repositório: $REPO_DIR"

##############################################################################
# ETAPA 2: DEPENDÊNCIAS DO SISTEMA
##############################################################################
step "Instalando dependências do sistema"

PACKAGES=(
    python311
    python311-devel
    python311-pip
    libusb-1_0-devel
    libhidapi-devel
    gcc-c++
    git-core
    lm_sensors
    xdg-utils
)

info "Pacotes: ${PACKAGES[*]}"
echo ""

sudo zypper install -y "${PACKAGES[@]}" 2>&1 | while IFS= read -r line; do
    # Show only meaningful lines
    case "$line" in
        *"already installed"*|*"já instalado"*) ok "$line" ;;
        *"Installing:"*|*"Instalando:"*)        info "$line" ;;
        *"Nothing to do"*|*"Nada a fazer"*)     ok "$line" ;;
    esac
done

ok "Dependências do sistema instaladas"

##############################################################################
# ETAPA 3: PERMISSÕES USB E SENSORES
##############################################################################
step "Configurando permissões USB e sensores"

# udev rules
UDEV_SRC="$REPO_DIR/config/99-turing-screen.rules"
UDEV_DST="/etc/udev/rules.d/99-turing-screen.rules"

if [ -f "$UDEV_SRC" ]; then
    sudo cp "$UDEV_SRC" "$UDEV_DST"
    sudo udevadm control --reload-rules 2>/dev/null || true
    sudo udevadm trigger 2>/dev/null || true
    ok "Regras udev instaladas: $UDEV_DST"
else
    warn "Arquivo de regras udev não encontrado: $UDEV_SRC"
fi

# Add user to dialout group (as backup)
if groups "$USER" | grep -q "\bdialout\b"; then
    ok "Usuário já está no grupo dialout"
else
    sudo usermod -a -G dialout "$USER"
    ok "Usuário adicionado ao grupo dialout"
    warn "IMPORTANTE: Faça logout/login para ativar as permissões do grupo"
fi

# Sensors detection
if command -v sensors-detect &>/dev/null; then
    info "Executando detecção de sensores..."
    if sudo sensors-detect --auto &>/dev/null; then
        ok "Sensores detectados e configurados"
    else
        warn "Detecção automática falhou. Execute manualmente: sudo sensors-detect"
    fi
fi

##############################################################################
# ETAPA 4: AMBIENTE VIRTUAL PYTHON
##############################################################################
step "Configurando ambiente virtual Python"

# Remove old venv if exists
if [ -d "$VENV_DIR" ]; then
    info "Removendo ambiente virtual anterior..."
    rm -rf "$VENV_DIR"
fi

info "Criando ambiente virtual com Python 3.11..."
python3.11 -m venv "$VENV_DIR"
ok "Ambiente virtual criado: $VENV_DIR"

info "Atualizando pip..."
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel --quiet
ok "pip atualizado"

##############################################################################
# ETAPA 5: DEPENDÊNCIAS PYTHON
##############################################################################
step "Instalando dependências Python"

# Project requirements
if [ -f "$REPO_DIR/requirements.txt" ]; then
    info "Instalando requirements.txt..."
    "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt" --quiet
    ok "Dependências do projeto instaladas"
else
    warn "requirements.txt não encontrado — pulando"
fi

# PyQt5 for the tray app
info "Instalando PyQt5 (aplicativo de bandeja)..."
"$VENV_DIR/bin/pip" install PyQt5 --quiet
ok "PyQt5 instalado"

# AMD GPU support
if [ "$HAS_AMD_GPU" = true ]; then
    info "Instalando suporte para GPU AMD..."
    if "$VENV_DIR/bin/pip" install pyamdgpuinfo --quiet 2>/dev/null; then
        ok "pyamdgpuinfo instalado"
    else
        warn "Falha ao instalar pyamdgpuinfo (pode exigir headers AMD)"
    fi
fi

ok "Todas as dependências Python instaladas"

##############################################################################
# ETAPA 6: SERVIÇO SYSTEMD
##############################################################################
step "Instalando serviço systemd"

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_USER_DIR/turing-screen.service"
SERVICE_TEMPLATE="$REPO_DIR/systemd/turing-screen.service.in"

mkdir -p "$SYSTEMD_USER_DIR"

if [ -f "$SERVICE_TEMPLATE" ]; then
    # Replace placeholders
    sed "s|@TURING_DIR@|$REPO_DIR|g" "$SERVICE_TEMPLATE" > "$SERVICE_FILE"
    ok "Serviço instalado: $SERVICE_FILE"

    # Reload systemd
    systemctl --user daemon-reload
    ok "systemd recarregado"

    # Enable service (starts on boot)
    systemctl --user enable turing-screen.service 2>/dev/null || true
    ok "Serviço habilitado para iniciar com o sistema"
else
    warn "Template de serviço não encontrado: $SERVICE_TEMPLATE"
fi

##############################################################################
# ETAPA 7: APLICATIVO DE BANDEJA (TRAY)
##############################################################################
step "Instalando aplicativo de bandeja do sistema"

# Install icon
ICON_SRC="$REPO_DIR/assets/icons/turing-tray.svg"
ICON_DST_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_DST="$ICON_DST_DIR/turing-smart-screen.svg"

mkdir -p "$ICON_DST_DIR"
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DST"
    ok "Ícone instalado: $ICON_DST"
fi

# Update icon cache (best-effort)
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# Autostart entry for the tray app
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/turing-screen-tray.desktop"
AUTOSTART_TEMPLATE="$REPO_DIR/desktop/turing-screen-tray.desktop.in"

mkdir -p "$AUTOSTART_DIR"
if [ -f "$AUTOSTART_TEMPLATE" ]; then
    sed "s|@TURING_DIR@|$REPO_DIR|g" "$AUTOSTART_TEMPLATE" > "$AUTOSTART_FILE"
    chmod +x "$AUTOSTART_FILE"
    ok "Autostart da bandeja: $AUTOSTART_FILE"
fi

# Application menu entry
APPS_DIR="$HOME/.local/share/applications"
APP_FILE="$APPS_DIR/turing-smart-screen.desktop"
APP_TEMPLATE="$REPO_DIR/desktop/turing-screen.desktop.in"

mkdir -p "$APPS_DIR"
if [ -f "$APP_TEMPLATE" ]; then
    sed "s|@TURING_DIR@|$REPO_DIR|g" "$APP_TEMPLATE" > "$APP_FILE"
    chmod +x "$APP_FILE"
    ok "Entrada no menu: $APP_FILE"
fi

# Update desktop database
update-desktop-database "$APPS_DIR" 2>/dev/null || true

##############################################################################
# ETAPA 8: CONFIGURAÇÃO INICIAL
##############################################################################
step "Configuração inicial"

CONFIGURE_PY="$REPO_DIR/configure.py"

if [ -f "$CONFIGURE_PY" ]; then
    echo ""
    info "O assistente de configuração permite selecionar:"
    info "  • Modelo do display (3.5\", 5\", 7\"...)"
    info "  • Porta USB"
    info "  • Tema inicial"
    echo ""
    read -rp "  Deseja executar o assistente de configuração agora? (S/n): " RUN_CONFIG
    RUN_CONFIG=${RUN_CONFIG:-S}

    if [[ "$RUN_CONFIG" =~ ^[Ss]$ ]]; then
        echo ""
        info "Iniciando assistente..."
        echo ""
        "$VENV_DIR/bin/python3.11" "$CONFIGURE_PY" || {
            warn "O assistente terminou com erro. Execute manualmente depois:"
            warn "  cd $REPO_DIR && ./venv/bin/python3.11 configure.py"
        }
        echo ""
        ok "Configuração concluída"
    else
        info "Pulado. Execute depois: cd $REPO_DIR && ./venv/bin/python3.11 configure.py"
    fi
else
    warn "configure.py não encontrado"
fi

##############################################################################
# RESUMO FINAL
##############################################################################
echo ""
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║           INSTALAÇÃO CONCLUÍDA COM SUCESSO!           ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "  ${BOLD}Componentes instalados:${NC}"
echo -e "    ${GREEN}✔${NC} Ambiente virtual Python 3.11"
echo -e "    ${GREEN}✔${NC} Dependências do projeto"
echo -e "    ${GREEN}✔${NC} Regras udev (permissão USB)"
echo -e "    ${GREEN}✔${NC} Serviço systemd (turing-screen)"
echo -e "    ${GREEN}✔${NC} Aplicativo de bandeja do sistema"
echo -e "    ${GREEN}✔${NC} Entrada no menu de aplicativos"
if [ "$HAS_AMD_GPU" = true ]; then
echo -e "    ${GREEN}✔${NC} Suporte AMD GPU (pyamdgpuinfo)"
fi
echo ""
echo -e "  ${BOLD}Comandos úteis:${NC}"
echo ""
echo -e "    ${CYAN}Iniciar display:${NC}"
echo -e "      systemctl --user start turing-screen"
echo ""
echo -e "    ${CYAN}Parar display:${NC}"
echo -e "      systemctl --user stop turing-screen"
echo ""
echo -e "    ${CYAN}Ver status:${NC}"
echo -e "      systemctl --user status turing-screen"
echo ""
echo -e "    ${CYAN}Ver logs:${NC}"
echo -e "      journalctl --user -u turing-screen -f"
echo ""
echo -e "    ${CYAN}Reconfigurar display:${NC}"
echo -e "      cd $REPO_DIR && ./venv/bin/python3.11 configure.py"
echo ""
echo -e "    ${CYAN}Desinstalar:${NC}"
echo -e "      bash $REPO_DIR/uninstall.sh"
echo ""

# Warnings
NEEDS_LOGOUT=false
if ! groups "$USER" | grep -q "\bdialout\b"; then
    NEEDS_LOGOUT=true
fi

if [ "$NEEDS_LOGOUT" = true ]; then
    echo -e "  ${YELLOW}${BOLD}⚠ AÇÃO NECESSÁRIA:${NC}"
    echo -e "  ${YELLOW}  Faça LOGOUT e LOGIN para ativar permissões USB.${NC}"
    echo ""
fi

# Ask to start now
echo ""
read -rp "  Deseja iniciar o display agora? (S/n): " START_NOW
START_NOW=${START_NOW:-S}

if [[ "$START_NOW" =~ ^[Ss]$ ]]; then
    echo ""
    if systemctl --user start turing-screen 2>/dev/null; then
        ok "Display iniciado!"
    else
        warn "Falha ao iniciar o display. Verifique a conexão USB e execute:"
        echo -e "      systemctl --user status turing-screen"
    fi
fi

# Always start the tray app so the user sees it right away
info "Iniciando aplicativo de bandeja do sistema..."
nohup "$VENV_DIR/bin/python3.11" "$REPO_DIR/tray/main.py" &>/dev/null &
disown
ok "Ícone da bandeja ativo no painel do sistema!"

echo ""
ok "Instalação finalizada!"
echo ""
