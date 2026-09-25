#!/usr/bin/env bash
# ==============================================================================
# 🚀 KAGGLE AUTOMATED OLLAMA & LLM DEPLOYER
# Modèle par défaut : Qwen3.8-27B TURBO Fable Cold Fusion Heretic Uncensored (GGUF Q4_K_M via Hugging Face)
#
# ⚡ Lancement direct dans une cellule Kaggle :
# !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
# ==============================================================================

set -e

# Modèle par défaut (modifiable via premier argument ou variable d'environnement MODEL)
MODEL="${1:-${MODEL:-"hf.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF:Q4_K_M"}}"

# Modèle à supprimer pour libérer l'espace disque (2e argument ou variable DELETE_MODEL)
# Valeurs possibles : nom du modèle, "all" (supprime tous les autres), ou vide
DELETE_MODEL="${2:-${DELETE_MODEL:-""}}"

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
echo -e "${BOLD}Modèle cible :${NC} ${YELLOW}${MODEL}${NC}"
if [ -n "$DELETE_MODEL" ]; then
    echo -e "${BOLD}Modèle à supprimer :${NC} ${RED}${DELETE_MODEL}${NC}"
fi
echo ""

# ------------------------------------------------------------------------------
# 0. Vérification du matériel (GPU Kaggle)
# ------------------------------------------------------------------------------
echo -e "${BLUE}[0/7] 🔍 Détection du matériel GPU...${NC}"
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
echo -e "\n${BLUE}[1/7] 📦 Installation des prérequis système (zstd, curl, wget, aria2)...${NC}"
apt-get update -qq >/dev/null 2>&1 || true
apt-get install -y -qq zstd curl wget procps aria2 >/dev/null 2>&1 || apt-get install -y -qq zstd curl wget procps >/dev/null 2>&1
echo -e "${GREEN}✓ Dépendances installées.${NC}"

# ------------------------------------------------------------------------------
# 2. Installation d'Ollama
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/7] 🦙 Installation d'Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1
fi
OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "installé")
echo -e "${GREEN}✓ Ollama opérationnel (${OLLAMA_VERSION})${NC}"

# ------------------------------------------------------------------------------
# 3. Démarrage du service Ollama
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/7] ⚙️ Démarrage du serveur Ollama...${NC}"
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
# 4. Gestion de l'espace disque et suppression d'un ancien modèle
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/7] 🧹 Vérification du disque et suppression d'ancien(s) modèle(s)...${NC}"
FREE_DISK_BEFORE=$(df -h / | awk 'NR==2 {print $4}')
echo -e "Espace disque disponible actuel : ${BOLD}${GREEN}${FREE_DISK_BEFORE}${NC}"

if [ -n "$DELETE_MODEL" ]; then
    echo -e "${YELLOW}Demande de suppression reçue : ${DELETE_MODEL}${NC}"
    if [ "$DELETE_MODEL" = "all" ]; then
        echo -e "${YELLOW}Suppression de TOUS les modèles existants pour faire de la place...${NC}"
        ollama list | awk 'NR>1 {print $1}' | while read -r m; do
            if [ -n "$m" ] && [ "$m" != "$MODEL" ]; then
                echo -e "  → Suppression de $m..."
                ollama rm "$m" || true
            fi
        done
        echo -e "${GREEN}✓ Nettoyage complet terminé.${NC}"
    else
        echo -e "  → Vérification du modèle : ${DELETE_MODEL}..."
        if ollama list | grep -q "$DELETE_MODEL"; then
            ollama rm "$DELETE_MODEL" && echo -e "${GREEN}✓ Modèle ${DELETE_MODEL} supprimé avec succès !${NC}"
        else
            echo -e "${YELLOW}ℹ️ Le modèle ${DELETE_MODEL} n'est pas installé (rien à supprimer).${NC}"
        fi
    fi
    FREE_DISK_AFTER=$(df -h / | awk 'NR==2 {print $4}')
    echo -e "Espace disque après nettoyage : ${BOLD}${GREEN}${FREE_DISK_AFTER}${NC}"
else
    echo -e "ℹ️ Aucun modèle à supprimer configuré."
    echo -e "   Astuce: Si vous manquez de place, relancez avec un 2e argument: \`bash setup_kaggle.sh <modele> <modele_a_supprimer_ou_all>\`"
fi

# ------------------------------------------------------------------------------
# 5. Téléchargement du modèle
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/7] 📥 Téléchargement et chargement du modèle (peut prendre quelques minutes selon la taille)...${NC}"
echo -e "${YELLOW}Cible : ${MODEL}${NC}"

# Vérifier si le modèle est une URL directe GGUF ou le modèle DavidAU par défaut
if [[ "$MODEL" == *"http"* && "$MODEL" == *".gguf"* ]] || [[ "$MODEL" == *"DavidAU"* && "$MODEL" == *"Qwen3.8-27B-TURBO"* ]]; then
    if [[ "$MODEL" == *"http"* ]]; then
        GGUF_URL="${MODEL/\/blob\//\/resolve\/}"
        GGUF_URL="${GGUF_URL%%\?*}"
        RAW_NAME=$(basename "$GGUF_URL" .gguf)
        MODEL_ALIAS=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | tr -c '[:alnum:]._-' '-' | cut -c 1-40 | sed 's/-$//')
    else
        MODEL_ALIAS="qwen3.8-27b-turbo"
        GGUF_URL="https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF/resolve/main/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf"
    fi

    WORK_DIR="/kaggle/working"
    [ ! -d "$WORK_DIR" ] && WORK_DIR="/tmp"
    GGUF_FILE="${WORK_DIR}/model_temp.gguf"
    MODELFILE_PATH="${WORK_DIR}/Modelfile"

    echo -e "${CYAN}🚀 Téléchargement direct accéléré multi-connexions (aria2c 16 threads)...${NC}"
    echo -e "   URL : ${GGUF_URL}"
    
    if command -v aria2c &> /dev/null; then
        aria2c -x 16 -s 16 -k 1M -c "$GGUF_URL" -d "$WORK_DIR" -o "model_temp.gguf"
    else
        wget -c --progress=bar:force:noscroll "$GGUF_URL" -O "$GGUF_FILE"
    fi

    echo -e "\n${BLUE}⚙️ Importation automatique dans Ollama sous l'alias : ${BOLD}${GREEN}${MODEL_ALIAS}${NC}..."
    cat << EOF > "$MODELFILE_PATH"
FROM ${GGUF_FILE}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 4096
PARAMETER num_ctx 8192
EOF

    ollama create "$MODEL_ALIAS" -f "$MODELFILE_PATH"

    echo -e "${YELLOW}🧹 Nettoyage du fichier temporaire pour libérer l'espace disque...${NC}"
    rm -f "$GGUF_FILE" "$MODELFILE_PATH"
    
    # Remplacer MODEL par l'alias pour tous les tests et commandes suivants
    MODEL="$MODEL_ALIAS"
    echo -e "${GREEN}✓ Modèle ${MODEL} créé et opérationnel dans Ollama !${NC}"
else
    # Téléchargement standard Ollama
    ollama pull "$MODEL"
    echo -e "${GREEN}✓ Modèle téléchargé avec succès !${NC}"
fi

# ------------------------------------------------------------------------------
# 6. Installation de Cloudflared (Tunnel)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[6/7] 🌐 Configuration du tunnel public Cloudflare...${NC}"
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
# 7. Récapitulatif et Accès
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

echo -e "\n${BOLD}🗑️ COMMANDE POUR SUPPRIMER UN MODÈLE :${NC}"
echo -e "   ${CYAN}ollama rm <nom_du_modele>${NC}"

echo -e "\n${BOLD}📋 EXEMPLE DE REQUÊTE CURL DISTANTE :${NC}"
if [ -n "$PUBLIC_URL" ]; then
    echo -e "${CYAN}curl ${PUBLIC_URL}/api/generate -d '{\"model\": \"${MODEL}\", \"prompt\": \"Bonjour !\", \"stream\": false}'${NC}"
else
    echo -e "${CYAN}curl http://127.0.0.1:${OLLAMA_PORT}/api/generate -d '{\"model\": \"${MODEL}\", \"prompt\": \"Bonjour !\", \"stream\": false}'${NC}"
fi

echo -e "\n${BOLD}🐍 EXEMPLE PYTHON DANS UNE CELLULE KAGGLE SUIVANTE :${NC}"
cat << EOF
import requests

url = "http://localhost:11434/api/generate"
data = {
    "model": "${MODEL}",
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
