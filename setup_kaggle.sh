#!/usr/bin/env bash
# ==============================================================================
# 🚀 KAGGLE AUTOMATED OLLAMA & LLM DEPLOYER
# Modèle par défaut : Qwen3.6-27B Uncensored (GGUF Q4_K_M via Hugging Face)
# ==============================================================================

set -e

# Modèle par défaut (modifiable via premier argument ou variable d'environnement MODEL)
MODEL="${1:-${MODEL:-"hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M"}}"
OLLAMA_PORT=11434
CLOUDFLARE_LOG="/tmp/cloudflared.log"
OLLAMA_LOG="/tmp/ollama.log"

# Couleurs ANSI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des services en cours...${NC}"
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    pkill -f "ollama serve" 2>/dev/null || true
    echo -e "${GREEN}✓ Services arrêtés proprement.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     🚀 KAGGLE OLLAMA LLM AUTOMATED DEPLOYER - GITHUB RUNNER       ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${BOLD}Modèle sélectionné :${NC} ${YELLOW}${MODEL}${NC}\n"

# ------------------------------------------------------------------------------
# 0. Vérification du matériel (GPU Kaggle)
# ------------------------------------------------------------------------------
echo -e "${BLUE}[0/6] 🔍 Détection du matériel GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n 1)
    GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    echo -e "${GREEN}✓ GPU détecté : ${GPU_COUNT}x ${GPU_NAME}${NC}"
else
    echo -e "${RED}⚠️ ATTENTION : Aucun GPU NVIDIA détecté !${NC}"
    echo -e "${YELLOW}👉 Pour ce modèle 27B, activez l'accélérateur GPU (GPU T4 x2 recommandé) dans le panneau de droite de Kaggle.${NC}"
fi

# ------------------------------------------------------------------------------
# 1. Dépendances système
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/6] 📦 Installation des prérequis système (zstd, curl, wget)...${NC}"
apt-get update -qq >/dev/null 2>&1 || true
apt-get install -y -qq zstd curl wget procps >/dev/null 2>&1
echo -e "${GREEN}✓ Dépendances installées.${NC}"

# ------------------------------------------------------------------------------
# 2. Installation d'Ollama
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/6] 🦙 Installation d'Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1
fi
OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "installé")
echo -e "${GREEN}✓ Ollama opérationnel (${OLLAMA_VERSION})${NC}"

# ------------------------------------------------------------------------------
# 3. Démarrage du service Ollama
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/6] ⚙️ Démarrage du serveur Ollama...${NC}"
pkill -f "ollama serve" 2>/dev/null || true
sleep 1
nohup ollama serve > "$OLLAMA_LOG" 2>&1 &
OLLAMA_PID=$!

# Attendre que le port soit actif
echo -n "En attente de la disponibilité de l'API locale"
for i in {1..30}; do
    if curl -s "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Serveur Ollama actif sur http://127.0.0.1:${OLLAMA_PORT} (PID: ${OLLAMA_PID})${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ "$i" -eq 30 ]; then
        echo -e "\n${RED}✗ Erreur : Le serveur Ollama n'a pas répondu dans les temps. Logs :${NC}"
        cat "$OLLAMA_LOG"
        exit 1
    fi
done

# ------------------------------------------------------------------------------
# 4. Téléchargement du modèle
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/6] 📥 Téléchargement du modèle (peut prendre quelques minutes selon la taille)...${NC}"
echo -e "${YELLOW}Cible : ${MODEL}${NC}"
ollama pull "$MODEL"
echo -e "${GREEN}✓ Modèle téléchargé avec succès !${NC}"

# ------------------------------------------------------------------------------
# 5. Installation de Cloudflared (Tunnel)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/6] 🌐 Configuration du tunnel public Cloudflare...${NC}"
if ! command -v cloudflared &> /dev/null; then
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
    dpkg -i /tmp/cloudflared.deb >/dev/null 2>&1
    rm -f /tmp/cloudflared.deb
fi

# Démarrage du tunnel Cloudflare
pkill -f "cloudflared tunnel" 2>/dev/null || true
rm -f "$CLOUDFLARE_LOG"
nohup cloudflared tunnel --url "http://127.0.0.1:${OLLAMA_PORT}" --http-host-header "localhost:${OLLAMA_PORT}" > "$CLOUDFLARE_LOG" 2>&1 &
CLOUDFLARED_PID=$!

echo -n "Génération de l'URL publique"
PUBLIC_URL=""
for i in {1..40}; do
    if [ -f "$CLOUDFLARE_LOG" ]; then
        URL_MATCH=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$CLOUDFLARE_LOG" | head -n 1 || true)
        if [ -n "$URL_MATCH" ]; then
            PUBLIC_URL="$URL_MATCH"
            break
        fi
    fi
    echo -n "."
    sleep 1
done

echo ""
if [ -n "$PUBLIC_URL" ]; then
    echo -e "${GREEN}✓ Tunnel Cloudflare opérationnel !${NC}"
else
    echo -e "${YELLOW}⚠️ Impossible de récupérer automatiquement l'URL du tunnel. Consultez $CLOUDFLARE_LOG.${NC}"
fi

# ------------------------------------------------------------------------------
# 6. Récapitulatif et Accès
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}               🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !                ${NC}"
echo -e "${CYAN}═════════════════════════════════════════════════════════════════════${NC}"

if [ -n "$PUBLIC_URL" ]; then
    echo -e "\n${BOLD}🔗 URL PUBLIQUE API CLOUDFLARE :${NC}"
    echo -e "   ${BOLD}${CYAN}${PUBLIC_URL}${NC}"
fi

echo -e "\n${BOLD}🏠 URL LOCALE KAGGLE :${NC}"
echo -e "   http://127.0.0.1:${OLLAMA_PORT}"

echo -e "\n${BOLD}🤖 MODÈLE CHARGÉ :${NC}"
echo -e "   ${YELLOW}${MODEL}${NC}"

echo -e "\n${BOLD}📋 EXEMPLE DE REQUÊTE CURL DISTANTE :${NC}"
if [ -n "$PUBLIC_URL" ]; then
    echo -e "${CYAN}curl ${PUBLIC_URL}/api/generate -d '{\"model\": \"${MODEL}\", \"prompt\": \"Bonjour !\", \"stream\": false}'${NC}"
else
    echo -e "${CYAN}curl http://127.0.0.1:${OLLAMA_PORT}/api/generate -d '{\"model\": \"${MODEL}\", \"prompt\": \"Bonjour !\", \"stream\": false}'${NC}"
fi

echo -e "\n${BOLD}🐍 EXEMPLE PYTHON DANS UNE CELLULE KAGGLE SUIVANTE :${NC}"
cat << 'EOF'
import requests

url = "http://localhost:11434/api/generate"
data = {
    "model": "hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M",
    "prompt": "Explique la relativité générale en 3 phrases.",
    "stream": False
}
resp = requests.post(url, json=data)
print(resp.json().get("response"))
EOF

echo -e "\n${YELLOW}ℹ️ Le serveur et le tunnel restent actifs tant que cette cellule s'exécute.${NC}"
echo -e "${YELLOW}   Pour arrêter, cliquez sur Stop / Interrompre la cellule.${NC}\n"

# Maintien du processus en vie
while kill -0 "$CLOUDFLARED_PID" 2>/dev/null && kill -0 "$OLLAMA_PID" 2>/dev/null; do
    sleep 2
done
