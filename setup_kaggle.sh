#!/usr/bin/env bash
# ==============================================================================
# 🚀 KAGGLE AUTOMATED OLLAMA & LLM DEPLOYER (ALL-IN-ONE)
# Modèle par défaut : Qwen3.8-27B TURBO Fable Cold Fusion Heretic Uncensored (GGUF Q4_K_M)
#
# ⚡ Lancement direct dans une cellule Kaggle Notebook :
#   !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
#
# 🎯 Options d'utilisation :
#   1. Modèle par défaut (Recommandé 27B Turbo ~17 Go) :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
#
#   2. Avec suppression d'un ancien modèle pour libérer l'espace disque :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "default" "all"
#
#   3. Avec un lien direct GGUF ou dépôt Hugging Face :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "https://huggingface.co/.../model.gguf"
#
#   4. Avec un modèle Ollama standard :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "qwen:7b"
#
#   5. Recherche de modèles Hugging Face (<50 Go) :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--search" "qwen coder"
#
#   6. Modèles populaires Hugging Face (<50 Go) :
#      !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--popular"
# ==============================================================================

set -e

# Configuration des ports et logs
OLLAMA_PORT=11434
CLOUDFLARE_LOG="/tmp/cloudflared.log"
OLLAMA_LOG="/tmp/ollama.log"
MAX_SIZE_GB=50.0

# Couleurs ANSI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Modèle recommandé par défaut
DEFAULT_MODEL_NAME="DavidAU Qwen 3.8 27B TURBO Uncensored (Q4_K_M)"
DEFAULT_MODEL_URL="https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF/resolve/main/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf"
DEFAULT_MODEL_ALIAS="qwen3.8-27b-turbo"

# Nettoyage propre lors de l'arrêt (Ctrl+C ou interruption de la cellule Kaggle)
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des services en cours...${NC}"
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    pkill -f "ollama serve" 2>/dev/null || true
    echo -e "${GREEN}✓ Services arrêtés proprement.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

banner() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🚀 KAGGLE OLLAMA & LLM ALL-IN-ONE AUTOMATED DEPLOYER          ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
}

# ------------------------------------------------------------------------------
# Fonctions Utilitaires & Explorateur Hugging Face
# ------------------------------------------------------------------------------

show_help() {
    banner
    echo -e "${BOLD}UTILISATION :${NC}"
    echo -e "  bash setup_kaggle.sh [MODELE_OU_URL] [MODELE_A_SUPPRIMER_OU_ALL]"
    echo -e "  bash setup_kaggle.sh --search <mot_cle>"
    echo -e "  bash setup_kaggle.sh --popular"
    echo -e "  bash setup_kaggle.sh --list"
    echo -e "  bash setup_kaggle.sh --status"
    echo ""
    echo -e "${BOLD}EXEMPLES KAGGLE :${NC}"
    echo -e "  1. Lancement automatique par défaut :"
    echo -e "     !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash"
    echo -e "  2. Nettoyer les anciens modèles et installer Qwen 27B Turbo :"
    echo -e "     !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- \"default\" \"all\""
    echo -e "  3. Installer un modèle via URL GGUF ou Hugging Face :"
    echo -e "     !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- \"https://huggingface.co/unsloth/Qwen3.8-27B-GGUF\""
    echo -e "  4. Rechercher des modèles Hugging Face (<50 Go) :"
    echo -e "     !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- \"--search\" \"coder\""
    exit 0
}

hf_search() {
    local query="$1"
    banner
    echo -e "${BLUE}🔍 Recherche sur Hugging Face pour : ${YELLOW}${query}${NC} (Filtre strict < 50 Go)..."
    python3 -c "
import urllib.request, urllib.parse, json, sys

query = '''${query}'''
url = f'https://huggingface.co/api/models?search={urllib.parse.quote(query)}&filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=30'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    found = 0
    print('\n' + '='*70)
    for m in data:
        rid = m.get('id', '')
        dls = m.get('downloads', 0)
        likes = m.get('likes', 0)
        gguf = m.get('gguf') or {}
        tsize = gguf.get('totalFileSize') or gguf.get('total') or 0
        size_gb = round(tsize / (1024**3), 2) if tsize else None
        if size_gb and size_gb > 50.0:
            continue
        size_str = f'{size_gb} Go' if size_gb else 'Taille variée'
        print(f'• {rid:<50} | {size_str:<12} | ⬇️ {dls} | ❤️ {likes}')
        found += 1
        if found >= 12:
            break
    print('='*70)
    if found == 0:
        print('Aucun modèle GGUF < 50 Go trouvé pour cette recherche.')
    else:
        print('\n👉 Pour installer un de ces modèles, copiez son identifiant :')
        print('   !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- \"https://huggingface.co/<identifiant>\"')
except Exception as e:
    print(f'Erreur recherche HF: {e}')
"
    exit 0
}

hf_popular() {
    banner
    echo -e "${BLUE}🌟 Modèles GGUF les plus populaires sur Hugging Face (Filtre strict < 50 Go)...${NC}"
    python3 -c "
import urllib.request, json

url = 'https://huggingface.co/api/models?filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=35'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    found = 0
    print('\n' + '='*70)
    for m in data:
        rid = m.get('id', '')
        dls = m.get('downloads', 0)
        likes = m.get('likes', 0)
        gguf = m.get('gguf') or {}
        tsize = gguf.get('totalFileSize') or gguf.get('total') or 0
        size_gb = round(tsize / (1024**3), 2) if tsize else None
        if size_gb and size_gb > 50.0:
            continue
        size_str = f'{size_gb} Go' if size_gb else 'Taille variée'
        print(f'• {rid:<50} | {size_str:<12} | ⬇️ {dls} | ❤️ {likes}')
        found += 1
        if found >= 12:
            break
    print('='*70)
    print('\n👉 Pour installer un de ces modèles :')
    print('   !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- \"https://huggingface.co/<identifiant>\"')
except Exception as e:
    print(f'Erreur HF: {e}')
"
    exit 0
}

list_models() {
    echo -e "${BLUE}📋 Modèles Ollama installés dans la session courante :${NC}"
    if command -v ollama &> /dev/null; then
        ollama list
    else
        echo "Ollama n'est pas encore installé."
    fi
    exit 0
}

show_status() {
    echo -e "${BLUE}🔍 État du système Kaggle :${NC}"
    echo -e "• Disque libre : $(df -h / | awk 'NR==2 {print $4}')"
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
    fi
    if command -v ollama &> /dev/null; then
        echo -e "\n• Modèles Ollama :"
        ollama list
    fi
    exit 0
}

# ------------------------------------------------------------------------------
# Traitement des arguments de commande
# ------------------------------------------------------------------------------
PARAM1="${1:-${MODEL:-""}}"
PARAM2="${2:-${DELETE_MODEL:-""}}"

case "$PARAM1" in
    --help|-h)
        show_help
        ;;
    --search)
        hf_search "${2:-qwen}"
        ;;
    --popular)
        hf_popular
        ;;
    --list)
        list_models
        ;;
    --status)
        show_status
        ;;
esac

# Modèle cible
if [ -z "$PARAM1" ] || [ "$PARAM1" = "default" ]; then
    TARGET_MODEL="default"
else
    TARGET_MODEL="$PARAM1"
fi
DELETE_TARGET="$PARAM2"

banner
echo -e "${BOLD}Modèle cible :${NC} ${YELLOW}${TARGET_MODEL}${NC}"
if [ -n "$DELETE_TARGET" ]; then
    echo -e "${BOLD}Modèle(s) à supprimer :${NC} ${RED}${DELETE_TARGET}${NC}"
fi
echo ""

# ------------------------------------------------------------------------------
# 0. Vérification du matériel GPU (NVIDIA Kaggle)
# ------------------------------------------------------------------------------
echo -e "${BLUE}[0/7] 🔍 Détection du matériel GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n 1)
    GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    echo -e "${GREEN}✓ GPU détecté : ${GPU_COUNT}x ${GPU_NAME}${NC}"
else
    echo -e "${RED}⚠️ ATTENTION : Aucun GPU NVIDIA détecté !${NC}"
    echo -e "${YELLOW}👉 Activez l'accélérateur GPU (GPU T4 x2 recommandé) dans le panneau de droite de Kaggle.${NC}"
fi

# ------------------------------------------------------------------------------
# 1. Dépendances système
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/7] 📦 Installation des prérequis système (aria2, zstd, curl, wget)...${NC}"
apt-get update -qq >/dev/null 2>&1 || true
apt-get install -y -qq zstd curl wget procps aria2 python3 >/dev/null 2>&1 || apt-get install -y -qq zstd curl wget procps python3 >/dev/null 2>&1
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
# 4. Gestion de l'espace disque et suppression d'anciens modèles
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/7] 🧹 Vérification du disque et nettoyage...${NC}"
FREE_DISK_BEFORE=$(df -h / | awk 'NR==2 {print $4}')
echo -e "Espace disque disponible : ${BOLD}${GREEN}${FREE_DISK_BEFORE}${NC}"

if [ -n "$DELETE_TARGET" ]; then
    echo -e "${YELLOW}Demande de suppression reçue : ${DELETE_TARGET}${NC}"
    if [ "$DELETE_TARGET" = "all" ]; then
        echo -e "${YELLOW}Suppression de TOUS les modèles existants pour libérer le disque...${NC}"
        ollama list | awk 'NR>1 {print $1}' | while read -r m; do
            if [ -n "$m" ]; then
                echo -e "  → Suppression de $m..."
                ollama rm "$m" || true
            fi
        done
        echo -e "${GREEN}✓ Nettoyage complet terminé.${NC}"
    else
        echo -e "  → Suppression de : ${DELETE_TARGET}..."
        ollama rm "$DELETE_TARGET" 2>/dev/null && echo -e "${GREEN}✓ Modèle supprimé.${NC}" || echo -e "${YELLOW}Modèle non trouvé (rien à supprimer).${NC}"
    fi
    echo -e "Espace disque après nettoyage : ${BOLD}${GREEN}$(df -h / | awk 'NR==2 {print $4}')${NC}"
fi

# ------------------------------------------------------------------------------
# 5. Résolution et Téléchargement du Modèle
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/7] 📥 Téléchargement et intégration du modèle...${NC}"

WORK_DIR="/kaggle/working"
[ ! -d "$WORK_DIR" ] && WORK_DIR="/tmp"
GGUF_FILE="${WORK_DIR}/model_temp.gguf"
MODELFILE_PATH="${WORK_DIR}/Modelfile"

GGUF_DOWNLOAD_URL=""
FINAL_ALIAS=""

if [ "$TARGET_MODEL" = "default" ] || [[ "$TARGET_MODEL" == *"DavidAU"* && "$TARGET_MODEL" == *"Qwen3.8-27B-TURBO"* ]]; then
    FINAL_ALIAS="$DEFAULT_MODEL_ALIAS"
    GGUF_DOWNLOAD_URL="$DEFAULT_MODEL_URL"
    echo -e "${CYAN}Modèle recommandé sélectionné : ${DEFAULT_MODEL_NAME}${NC}"
    echo -e "Source : ${GGUF_DOWNLOAD_URL}"
elif [[ "$TARGET_MODEL" == *"http"* && "$TARGET_MODEL" == *".gguf"* ]]; then
    # URL directe vers un .gguf
    GGUF_DOWNLOAD_URL="${TARGET_MODEL/\/blob\//\/resolve\/}"
    GGUF_DOWNLOAD_URL="${GGUF_DOWNLOAD_URL%%\?*}"
    RAW_NAME=$(basename "$GGUF_DOWNLOAD_URL" .gguf)
    FINAL_ALIAS=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | tr -c '[:alnum:]._-' '-' | cut -c 1-40 | sed 's/-$//')
elif [[ "$TARGET_MODEL" == *"huggingface.co/"* || "$TARGET_MODEL" == *"hf.co/"* ]]; then
    # URL ou ID de repo Hugging Face -> résolution automatique via Python de la meilleure version Q4_K_M
    echo -e "${BLUE}🔍 Analyse automatique du dépôt Hugging Face pour trouver le meilleur fichier GGUF (< 50 Go)...${NC}"
    RESOLVED=$(python3 -c "
import urllib.request, json, re, sys

target = '''${TARGET_MODEL}'''.strip()
clean = re.sub(r'^(?:https?://(?:www\.)?huggingface\.co/|hf\.co/)', '', target).rstrip('/')
repo_id = clean.split(':')[0]

url = f'https://huggingface.co/api/models/{repo_id}/tree/main?recursive=true'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        files = json.loads(resp.read().decode())
    ggufs = []
    for f in files:
        path = f.get('path', '')
        size = f.get('size', 0)
        if path.lower().endswith('.gguf') and 0 < size <= 50 * (1024**3):
            fname = path.split('/')[-1]
            if fname.lower().startswith(('imatrix', 'mmproj')):
                continue
            is_split = bool(re.search(r'-\d{5}-of-\d{5}\.gguf$', fname, re.IGNORECASE))
            ggufs.append({'path': path, 'size': size, 'is_split': is_split, 'url': f'https://huggingface.co/{repo_id}/resolve/main/{path}'})
    
    if not ggufs:
        sys.exit(1)

    # Trouver Q4_K_M en priorité
    picked = None
    for pat in ['Q4_K_M', 'q4_k_m', 'Q5_K_M', 'Q4_0', 'Q4_K_S']:
        for g in ggufs:
            if pat in g['path']:
                picked = g
                break
        if picked:
            break
    if not picked:
        picked = sorted(ggufs, key=lambda x: (x['is_split'], x['size']))[len(ggufs)//2]

    fname = picked['path'].split('/')[-1]
    alias = re.sub(r'\.gguf$', '', fname, flags=re.I)
    alias = re.sub(r'[^a-zA-Z0-9_\-\.]+', '-', alias).lower().strip('-')[:40].rstrip('-')
    print(f'{picked[\"url\"]} {alias}')
except Exception:
    sys.exit(1)
" || true)

    if [ -n "$RESOLVED" ]; then
        GGUF_DOWNLOAD_URL=$(echo "$RESOLVED" | awk '{print $1}')
        FINAL_ALIAS=$(echo "$RESOLVED" | awk '{print $2}')
        echo -e "${GREEN}✓ Fichier GGUF résolu : ${FINAL_ALIAS}${NC}"
        echo -e "   URL : ${GGUF_DOWNLOAD_URL}"
    fi
fi

# Exécution du téléchargement
if [ -n "$GGUF_DOWNLOAD_URL" ]; then
    echo -e "\n${CYAN}🚀 Téléchargement multi-connexions accéléré (aria2c 16 threads)...${NC}"
    rm -f "$GGUF_FILE" "$MODELFILE_PATH"

    if command -v aria2c &> /dev/null; then
        aria2c -x 16 -s 16 -k 1M -c "$GGUF_DOWNLOAD_URL" -d "$WORK_DIR" -o "model_temp.gguf" || \
        wget -c --progress=bar:force:noscroll "$GGUF_DOWNLOAD_URL" -O "$GGUF_FILE"
    else
        wget -c --progress=bar:force:noscroll "$GGUF_DOWNLOAD_URL" -O "$GGUF_FILE"
    fi

    echo -e "\n${BLUE}⚙️ Création du modèle Ollama '${BOLD}${GREEN}${FINAL_ALIAS}${NC}' avec paramètres optimisés...${NC}"
    cat << EOF > "$MODELFILE_PATH"
FROM ${GGUF_FILE}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 4096
PARAMETER num_ctx 8192
EOF

    ollama create "$FINAL_ALIAS" -f "$MODELFILE_PATH"

    echo -e "${YELLOW}🧹 Nettoyage des fichiers temporaires pour libérer l'espace disque...${NC}"
    rm -f "$GGUF_FILE" "$MODELFILE_PATH"
    
    MODEL="$FINAL_ALIAS"
    echo -e "${GREEN}✓ Modèle '${MODEL}' créé avec succès dans Ollama !${NC}"
    echo -e "✓ Espace disque libre restant : ${GREEN}$(df -h / | awk 'NR==2 {print $4}')${NC}"
else
    # Cas d'un modèle officiel Ollama (ex: qwen:7b, llama3.1:8b)
    MODEL="$TARGET_MODEL"
    echo -e "Téléchargement via Ollama pull standard (${MODEL})..."
    ollama pull "$MODEL"
    echo -e "${GREEN}✓ Modèle ${MODEL} téléchargé avec succès !${NC}"
fi

# ------------------------------------------------------------------------------
# 6. Installation et Démarrage du Tunnel Cloudflare
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[6/7] 🌐 Configuration du tunnel public Cloudflare...${NC}"
if ! command -v cloudflared &> /dev/null; then
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
    dpkg -i /tmp/cloudflared.deb >/dev/null 2>&1
    rm -f /tmp/cloudflared.deb
fi

pkill -f "cloudflared tunnel" 2>/dev/null || true
rm -f "$CLOUDFLARE_LOG"
nohup cloudflared tunnel --url "http://127.0.0.1:${OLLAMA_PORT}" --http-host-header "localhost:${OLLAMA_PORT}" > "$CLOUDFLARE_LOG" 2>&1 &
CLOUDFLARED_PID=$!

echo -n "Génération de l'URL publique Cloudflare"
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
    echo -e "${YELLOW}⚠️ URL en cours de génération. Consultez : $CLOUDFLARE_LOG${NC}"
fi

# ------------------------------------------------------------------------------
# 7. Test Automatique et Récapitulatif
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[7/7] 🧪 Test rapide d'inférence...${NC}"
TEST_RESP=$(curl -s "http://127.0.0.1:${OLLAMA_PORT}/api/generate" -d "{\"model\": \"${MODEL}\", \"prompt\": \"Dis bonjour en 1 mot\", \"stream\": false, \"options\": {\"num_predict\": 10}}" | grep -oE '"response":"[^"]*"' | cut -d'"' -f4 || echo "OK")
echo -e "${GREEN}✓ Réponse du modèle : \"${TEST_RESP}\"${NC}"

echo -e "\n${CYAN}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}               🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !                ${NC}"
echo -e "${CYAN}═════════════════════════════════════════════════════════════════════${NC}"

if [ -n "$PUBLIC_URL" ]; then
    echo -e "\n${BOLD}🔗 URL PUBLIQUE API CLOUDFLARE :${NC}"
    echo -e "   ${BOLD}${CYAN}${PUBLIC_URL}${NC}"
fi

echo -e "\n${BOLD}🏠 URL LOCALE KAGGLE :${NC}"
echo -e "   http://127.0.0.1:${OLLAMA_PORT}"

echo -e "\n${BOLD}🤖 MODÈLE ACTIF :${NC}"
echo -e "   ${YELLOW}${MODEL}${NC}"

echo -e "\n${BOLD}📋 EXEMPLE REQUÊTE PYTHON (sans coupure de réponse) :${NC}"
cat << EOF
import requests

url = "${PUBLIC_URL:-http://localhost:11434}/api/generate"
data = {
    "model": "${MODEL}",
    "prompt": "Explique les concepts clés de l'IA en 3 points.",
    "stream": False,
    "options": {
        "num_predict": 4096,  # Empêche la coupure (output limit)
        "num_ctx": 8192       # Contexte étendu
    }
}
response = requests.post(url, json=data)
print(response.json().get("response"))
EOF

echo -e "\n${YELLOW}ℹ️ Le serveur et le tunnel restent actifs tant que cette cellule s'exécute.${NC}"
echo -e "${YELLOW}   Pour arrêter, cliquez sur Stop / Interrompre la cellule Kaggle.${NC}\n"

# Maintien du processus en vie
while kill -0 "$CLOUDFLARED_PID" 2>/dev/null && kill -0 "$OLLAMA_PID" 2>/dev/null; do
    sleep 2
done
