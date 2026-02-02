#!/bin/bash
##############################################################################
#
#  TURING SMART SCREEN — DESINSTALADOR (Regata OS / openSUSE)
#
#  Remove todos os componentes instalados pelo install.sh.
#  O código-fonte (repositório) NÃO é removido por padrão.
#
##############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
info() { echo -e "  ${BLUE}ℹ${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"

echo ""
echo -e "${RED}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║         TURING SMART SCREEN — DESINSTALADOR           ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "  ${BOLD}Serão removidos:${NC}"
echo "    • Serviço systemd (turing-screen)"
echo "    • Autostart da bandeja do sistema"
echo "    • Entrada no menu de aplicativos"
echo "    • Ícone do aplicativo"
echo "    • Regras udev"
echo "    • Configurações do tray (~/.config/turing-screen)"
echo "    • Ambiente virtual Python (venv/)"
echo ""
echo -e "  ${BLUE}O código-fonte do repositório NÃO será removido.${NC}"
echo ""

read -rp "  Continuar com a desinstalação? (s/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo ""
    info "Desinstalação cancelada."
    exit 0
fi

echo ""

# ── 1. Parar e desabilitar serviço ───────────────────────────
info "Parando serviço..."
systemctl --user stop turing-screen 2>/dev/null && ok "Serviço parado" || true
systemctl --user disable turing-screen 2>/dev/null && ok "Serviço desabilitado" || true

SERVICE_FILE="$HOME/.config/systemd/user/turing-screen.service"
if [ -f "$SERVICE_FILE" ]; then
    rm -f "$SERVICE_FILE"
    ok "Removido: $SERVICE_FILE"
fi
systemctl --user daemon-reload 2>/dev/null || true

# ── 2. Remover autostart e desktop entries ───────────────────
AUTOSTART_FILE="$HOME/.config/autostart/turing-screen-tray.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    ok "Removido: $AUTOSTART_FILE"
fi

APP_FILE="$HOME/.local/share/applications/turing-smart-screen.desktop"
if [ -f "$APP_FILE" ]; then
    rm -f "$APP_FILE"
    ok "Removido: $APP_FILE"
fi

# ── 3. Remover ícone ─────────────────────────────────────────
ICON_FILE="$HOME/.local/share/icons/hicolor/scalable/apps/turing-smart-screen.svg"
if [ -f "$ICON_FILE" ]; then
    rm -f "$ICON_FILE"
    ok "Removido: $ICON_FILE"
fi
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# ── 4. Remover regras udev ──────────────────────────────────
UDEV_FILE="/etc/udev/rules.d/99-turing-screen.rules"
if [ -f "$UDEV_FILE" ]; then
    sudo rm -f "$UDEV_FILE"
    sudo udevadm control --reload-rules 2>/dev/null || true
    ok "Removido: $UDEV_FILE"
fi

# ── 5. Remover configurações do tray ────────────────────────
CONFIG_DIR="$HOME/.config/turing-screen"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    ok "Removido: $CONFIG_DIR"
fi

# ── 6. Remover ambiente virtual ──────────────────────────────
VENV_DIR="$REPO_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    ok "Removido: $VENV_DIR"
fi

# ── 7. Oferecer remoção do repositório ───────────────────────
echo ""
read -rp "  Deseja também remover o repositório ($REPO_DIR)? (s/N): " DEL_REPO
if [[ "$DEL_REPO" =~ ^[Ss]$ ]]; then
    # Safety: confirm with full path
    read -rp "  Confirmar remoção de $REPO_DIR? (digite SIM): " CONFIRM_DEL
    if [ "$CONFIRM_DEL" = "SIM" ]; then
        rm -rf "$REPO_DIR"
        ok "Repositório removido"
    else
        info "Remoção do repositório cancelada"
    fi
else
    info "Repositório mantido em: $REPO_DIR"
fi

echo ""
echo -e "${GREEN}${BOLD}  Desinstalação concluída!${NC}"
echo ""
