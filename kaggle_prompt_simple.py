# ================================================================
# PROMPT POUR KAGGLE NOTEBOOKS - OLLAMA LLM SETUP AVEC HUGGING FACE
# Copier-coller ce code dans une cellule Kaggle Notebook
#
# ✨ NOUVEAUTÉS :
#  1. Explorateur de modèles Hugging Face filtré par taille (< 50 Go)
#  2. Recherche par mots-clés (Qwen, DeepSeek, Mistral, Llama, Coder...)
#  3. Option pour COLLER DIRECTEMENT UN LIEN Hugging Face (URL ou repo)
#  4. Téléchargement ultra-rapide multi-thread (aria2c 16 connexions)
# ================================================================

import subprocess
import time
import os
import re
import sys
import json
import urllib.request
import urllib.parse

# Assurer l'encodage UTF-8 sur tous les terminaux
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ================================================================
# ⚙️ CONFIGURATION DU MODÈLE ET DU STOCKAGE
# ================================================================
# Option 1 : Laisser vide ("") pour ouvrir le MENU INTERACTIF
#            (permet de parcourir HF < 50 Go, chercher, ou coller un lien)
# Option 2 : Coller directement ici votre lien ou ID de modèle :
#   - URL directe GGUF : "https://huggingface.co/.../resolve/main/...gguf"
#   - URL dépôt HF     : "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF"
#   - ID Dépôt         : "unsloth/Qwen3.8-27B-GGUF:Q4_K_M"
#   - Modèle Ollama    : "llama3.1:8b"
MODEL_OR_URL = os.environ.get("MODEL", "")

# Limite stricte de taille en Go (l'espace disque disponible sur Kaggle est de ~50 Go)
MAX_SIZE_GB = float(os.environ.get("MAX_SIZE_GB", 50.0))

# Suppression d'un ancien modèle pour libérer l'espace disque ("all", nom exact, ou "")
DELETE_MODEL = os.environ.get("DELETE_MODEL", "")

# Modèle recommandé par défaut (haute performance, non-censuré, ~17.2 Go < 50 Go)
DEFAULT_RECOMMENDED = {
    "name": "Qwen 3.8 27B TURBO Uncensored (Q4_K_M)",
    "url": "https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF/resolve/main/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf",
    "alias": "qwen3.8-27b-turbo",
    "size_gb": 17.23
}


# ================================================================
# 🛠️ FONCTIONS UTILITAIRES & API HUGGING FACE
# ================================================================

def get_free_disk():
    """Retourne l'espace disque disponible sur la partition principale"""
    try:
        res = subprocess.run("df -h / | awk 'NR==2 {print $4}'", shell=True, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "N/A"

def safe_input(prompt, default=""):
    """Saisie utilisateur compatible Jupyter/Kaggle avec repli automatique"""
    try:
        val = input(prompt).strip()
        return val if val else default
    except Exception:
        print(f"{default} (sélection automatique)")
        return default

def sanitize_alias(name):
    """Crée un alias propre et court compatible avec la CLI Ollama"""
    name = re.sub(r'\.gguf$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9_\-\.]+', '-', name).lower().strip('-')
    if 'qwen3.8-27b' in name:
        return 'qwen3.8-27b-turbo'
    if len(name) > 40:
        name = name[:40].rstrip('-')
    return name or "custom-model"

def check_direct_url_size(url):
    """Vérifie la taille en Go d'un fichier distant via requête HTTP HEAD"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as resp:
            cl = resp.headers.get('Content-Length')
            if cl:
                return round(int(cl) / (1024**3), 2)
    except Exception:
        pass
    return None

def fetch_popular_hf_models(limit=12, max_size_gb=MAX_SIZE_GB):
    """Récupère les modèles GGUF les plus populaires sur Hugging Face filtrés par taille"""
    url = "https://huggingface.co/api/models?filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=40"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération Hugging Face : {e}")
        return []

    models = []
    for m in data:
        repo_id = m.get('id', '')
        downloads = m.get('downloads', 0)
        likes = m.get('likes', 0)
        gguf = m.get('gguf') or {}
        t_size = gguf.get('totalFileSize') or gguf.get('total') or 0
        size_gb = round(t_size / (1024**3), 2) if t_size else None

        # Filtre strict : Ne conserver que ceux dont la taille connue est <= MAX_SIZE_GB
        if size_gb and size_gb > max_size_gb:
            continue

        models.append({
            'id': repo_id,
            'downloads': downloads,
            'likes': likes,
            'size_gb': size_gb
        })
        if len(models) >= limit:
            break
    return models

def search_hf_models(query, limit=12, max_size_gb=MAX_SIZE_GB):
    """Recherche des modèles GGUF sur Hugging Face par mot-clé avec filtre < 50 Go"""
    encoded_q = urllib.parse.quote(query.strip())
    url = f"https://huggingface.co/api/models?search={encoded_q}&filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=35"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"⚠️ Erreur lors de la recherche Hugging Face : {e}")
        return []

    models = []
    for m in data:
        repo_id = m.get('id', '')
        downloads = m.get('downloads', 0)
        likes = m.get('likes', 0)
        gguf = m.get('gguf') or {}
        t_size = gguf.get('totalFileSize') or gguf.get('total') or 0
        size_gb = round(t_size / (1024**3), 2) if t_size else None

        if size_gb and size_gb > max_size_gb:
            continue

        models.append({
            'id': repo_id,
            'downloads': downloads,
            'likes': likes,
            'size_gb': size_gb
        })
        if len(models) >= limit:
            break
    return models

def get_hf_repo_ggufs(repo_id, max_size_gb=MAX_SIZE_GB):
    """Récupère tous les fichiers GGUF d'un dépôt Hugging Face avec leur taille (< 50 Go)"""
    url = f"https://huggingface.co/api/models/{repo_id}/tree/main?recursive=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            files = json.loads(resp.read().decode())
    except Exception as e:
        print(f"⚠️ Impossible d'explorer le dépôt {repo_id} : {e}")
        return []

    ggufs = []
    max_bytes = max_size_gb * (1024**3)
    for f in files:
        path = f.get('path', '')
        size = f.get('size', 0)
        if path.lower().endswith('.gguf') and size > 0 and size <= max_bytes:
            fname = path.split('/')[-1]
            # Ignorer les petits fichiers auxiliaires de quantification s'il y a d'autres fichiers
            if fname.lower().startswith(('imatrix', 'mmproj')):
                continue
            is_split = bool(re.search(r'-\d{5}-of-\d{5}\.gguf$', fname, re.IGNORECASE))
            ggufs.append({
                'path': path,
                'filename': fname,
                'size_bytes': size,
                'size_gb': round(size / (1024**3), 2),
                'is_split': is_split,
                'download_url': f"https://huggingface.co/{repo_id}/resolve/main/{path}"
            })

    # Trier par taille croissante (sans parties fractionnées en priorité)
    ggufs.sort(key=lambda x: (x['is_split'], x['size_bytes']))
    return ggufs

def pick_recommended_gguf(ggufs):
    """Sélectionne intelligemment la meilleure quantification GGUF (Q4_K_M ou équivalent)"""
    if not ggufs:
        return None
    patterns = ['Q4_K_M', 'q4_k_m', 'Q5_K_M', 'q5_k_m', 'Q4_0', 'q4_0', 'Q4_K_S', 'Q6_K']
    for pat in patterns:
        for g in ggufs:
            if pat in g['filename']:
                return g
    # Repli : fichier médian
    return ggufs[len(ggufs) // 2]


# ================================================================
# 🎯 SÉLECTEUR INTERACTIF DE MODÈLE
# ================================================================

def resolve_direct_or_repo(target, max_size_gb=MAX_SIZE_GB):
    """Analyse et résout un lien ou identifiant de modèle (URL, repo, fichier)"""
    target = target.strip()
    target = target.split('?')[0].rstrip('/')

    # CAS 1 : Lien direct vers un fichier .gguf
    if '.gguf' in target.lower() and ('http://' in target or 'https://' in target):
        url = target.replace('/blob/', '/resolve/')
        fname = url.split('/')[-1]
        print(f"🔍 Analyse du lien direct : {fname}...")
        size_gb = check_direct_url_size(url)
        if size_gb:
            print(f"📊 Taille du fichier détectée : {size_gb} Go (Limite: {max_size_gb} Go)")
            if size_gb > max_size_gb:
                print(f"⚠️ ATTENTION : Ce modèle dépasse {max_size_gb} Go ! Il risque de saturer Kaggle.")
            else:
                print(f"✓ Taille conforme (< {max_size_gb} Go)")
        alias = sanitize_alias(fname)
        return {
            "type": "direct_url",
            "url": url,
            "filename": fname,
            "alias": alias,
            "size_gb": size_gb or "N/A"
        }

    # CAS 2 : URL ou ID de dépôt Hugging Face
    clean_repo = re.sub(r'^(?:https?://(?:www\.)?huggingface\.co/|hf\.co/)', '', target)
    repo_parts = clean_repo.split(':')
    repo_id = repo_parts[0]
    tag = repo_parts[1] if len(repo_parts) > 1 else None

    if '/' in repo_id and not repo_id.endswith('.gguf'):
        print(f"🔍 Recherche des fichiers GGUF dans {repo_id} (< {max_size_gb} Go)...")
        ggufs = get_hf_repo_ggufs(repo_id, max_size_gb=max_size_gb)
        if ggufs:
            chosen = None
            if tag:
                # Chercher la quantification demandée
                for g in ggufs:
                    if tag.lower() in g['filename'].lower():
                        chosen = g
                        break
            if not chosen:
                print(f"\n📦 Fichiers GGUF disponibles dans {repo_id} (< {max_size_gb} Go) :")
                rec = pick_recommended_gguf(ggufs)
                for idx, g in enumerate(ggufs, 1):
                    is_rec = " ⭐ [Recommandé]" if g == rec else ""
                    print(f"  [{idx:2d}] {g['filename']} ({g['size_gb']} Go){is_rec}")
                
                choice = safe_input(f"\nChoisissez un fichier [1-{len(ggufs)}, Entrée pour recommandé] : ")
                if choice.isdigit() and 1 <= int(choice) <= len(ggufs):
                    chosen = ggufs[int(choice) - 1]
                else:
                    chosen = rec

            alias = sanitize_alias(chosen['filename'])
            print(f"✓ Sélectionné : {chosen['filename']} ({chosen['size_gb']} Go)")
            return {
                "type": "direct_url",
                "url": chosen['download_url'],
                "filename": chosen['filename'],
                "alias": alias,
                "size_gb": chosen['size_gb']
            }
        else:
            print(f"⚠️ Aucun fichier GGUF < {max_size_gb} Go trouvé dans {repo_id}.")
            print("Tentative via Ollama pull standard...")
            return {"type": "ollama_pull", "model": target, "alias": target, "size_gb": "< 50 Go"}

    # CAS 3 : Nom de modèle classique Ollama (ex: llama3.1:8b, mistral)
    return {"type": "ollama_pull", "model": target, "alias": target, "size_gb": "Ollama Library"}

def interactive_model_selector():
    """Menu interactif de sélection du modèle"""
    print("\n" + "=" * 70)
    print("🤗 SÉLECTION DU MODÈLE HUGGING FACE (Filtre strict : < 50 Go)")
    print("=" * 70)
    print("  [1] 🔥 Parcourir les modèles Hugging Face populaires (< 50 Go)")
    print("  [2] 🔍 Rechercher un modèle sur Hugging Face par mot-clé (< 50 Go)")
    print("  [3] 🔗 Coller directement un lien Hugging Face (URL repo ou fichier .gguf)")
    print("  [4] ⚡ Utiliser le modèle recommandé par défaut (Qwen 3.8 27B TURBO ~17 Go)")
    print("=" * 70)

    choice = safe_input("👉 Entrez votre choix [1, 2, 3, ou 4 - Défaut: 4] : ", default="4")

    # Option 1 : Parcourir les modèles populaires
    if choice == "1":
        print("\n⏳ Chargement des modèles Hugging Face les plus téléchargés (< 50 Go)...")
        models = fetch_popular_hf_models(limit=10)
        if models:
            print("\n📋 Modèles populaires disponibles :")
            print("-" * 70)
            for idx, m in enumerate(models, 1):
                sz = f"~{m['size_gb']} Go" if m['size_gb'] else "< 50 Go"
                print(f"  [{idx:2d}] {m['id']:<45} | {sz:<9} | ⬇️ {m['downloads']:,}")
            print("-" * 70)
            pick = safe_input(f"Choisissez un modèle [1-{len(models)}] ou Entrée pour défaut : ")
            if pick.isdigit() and 1 <= int(pick) <= len(models):
                selected_repo = models[int(pick) - 1]['id']
                return resolve_direct_or_repo(selected_repo)
        else:
            print("⚠️ Impossible de charger la liste. Utilisation du modèle recommandé.")

    # Option 2 : Recherche par mot-clé
    elif choice == "2":
        keyword = safe_input("🔎 Entrez un mot-clé (ex: qwen, deepseek, coder, mistral, llama) : ")
        if keyword:
            print(f"\n⏳ Recherche de '{keyword}' sur Hugging Face (< 50 Go)...")
            results = search_hf_models(keyword, limit=10)
            if results:
                print(f"\n📋 Résultats pour '{keyword}' (< 50 Go) :")
                print("-" * 70)
                for idx, m in enumerate(results, 1):
                    sz = f"~{m['size_gb']} Go" if m['size_gb'] else "< 50 Go"
                    print(f"  [{idx:2d}] {m['id']:<45} | {sz:<9} | ⬇️ {m['downloads']:,}")
                print("-" * 70)
                pick = safe_input(f"Choisissez un modèle [1-{len(results)}] : ")
                if pick.isdigit() and 1 <= int(pick) <= len(results):
                    selected_repo = results[int(pick) - 1]['id']
                    return resolve_direct_or_repo(selected_repo)
            else:
                print(f"⚠️ Aucun modèle trouvé pour '{keyword}'.")

    # Option 3 : Coller directement un lien
    elif choice == "3":
        print("\n📋 Formats supportés :")
        print("  • Lien direct .gguf : https://huggingface.co/.../resolve/main/...Q4_K_M.gguf")
        print("  • Lien dépôt       : https://huggingface.co/unsloth/Qwen3.8-27B-GGUF")
        print("  • ID de modèle     : unsloth/Qwen3.8-27B-GGUF:Q4_K_M ou llama3.1:8b")
        pasted = safe_input("👉 Collez votre lien ou nom de modèle : ")
        if pasted:
            return resolve_direct_or_repo(pasted)

    # Option 4 ou Repli : Modèle par défaut
    print(f"\n⚡ Sélection du modèle par défaut : {DEFAULT_RECOMMENDED['name']} (~{DEFAULT_RECOMMENDED['size_gb']} Go)")
    return {
        "type": "direct_url",
        "url": DEFAULT_RECOMMENDED['url'],
        "filename": "qwen3.8-27b.gguf",
        "alias": DEFAULT_RECOMMENDED['alias'],
        "size_gb": DEFAULT_RECOMMENDED['size_gb']
    }


def main():
    # ════════════════════════════════════════════════════════════
    # 🚀 INITIALISATION DU MODÈLE
    # ════════════════════════════════════════════════════════════

    if MODEL_OR_URL.strip():
        print(f"ℹ️ Configuration MODEL détectée : {MODEL_OR_URL}")
        selected_target = resolve_direct_or_repo(MODEL_OR_URL, max_size_gb=MAX_SIZE_GB)
    else:
        selected_target = interactive_model_selector()

    active_model = selected_target['alias']
    print("\n" + "=" * 70)
    print("RÉCAPITULATIF DE LA CONFIGURATION KAGGLE")
    print("=" * 70)
    print(f"Modèle actif       : {active_model}")
    print(f"Type d'importation : {selected_target['type']}")
    print(f"Taille estimée     : {selected_target.get('size_gb', 'N/A')} Go (Limite Kaggle : {MAX_SIZE_GB} Go)")
    if DELETE_MODEL:
        print(f"Modèle ciblé suppr : {DELETE_MODEL}")
    print(f"Espace disque libre: {get_free_disk()}")
    print("=" * 70)


    # ── ÉTAPE 1: Installation des prérequis ─────────────────────────
    print("\n[1/8] Installation des prérequis (zstd, aria2)...")
    subprocess.run(
        "apt-get update -qq && (apt-get install -y -qq zstd aria2 || apt-get install -y -qq zstd)",
        shell=True,
        capture_output=True
    )
    print("✓ Dépendances installées")

    # ── ÉTAPE 2: Installation d'Ollama ──────────────────────────────
    print("\n[2/8] Installation d'Ollama...")
    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, capture_output=True)
    print("✓ Ollama installé")

    # ── ÉTAPE 3: Vérification d'Ollama ──────────────────────────────
    print("\n[3/8] Vérification d'Ollama...")
    result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
    print(f"✓ {result.stdout.strip()}")

    # ── ÉTAPE 4: Démarrage d'Ollama en arrière-plan ──────────────────
    print("\n[4/8] Démarrage d'Ollama...")
    subprocess.run("pkill -f 'ollama serve'", shell=True, capture_output=True)
    time.sleep(1)
    ollama_process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)
    print(f"✓ Ollama démarré (PID: {ollama_process.pid})")

    # ── ÉTAPE 5: Gestion du stockage et suppression ─────────────────
    print(f"\n[5/8] Gestion du stockage (Espace actuel : {get_free_disk()} libre)...")
    if DELETE_MODEL:
        list_check = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        installed_output = list_check.stdout.strip()
        print("Modèles actuellement détectés dans Ollama :")
        print(installed_output if installed_output else "  (Aucun modèle présent)")

        if DELETE_MODEL.strip().lower() == "all":
            print("Nettoyage de TOUS les modèles existants pour maximiser l'espace...")
            lines = installed_output.split("\n")[1:]
            for line in lines:
                parts = line.split()
                if parts:
                    m_name = parts[0]
                    if m_name != active_model:
                        print(f"  → Suppression de {m_name}...")
                        subprocess.run(f"ollama rm {m_name}", shell=True)
            print(f"✓ Nettoyage terminé. Nouvel espace libre : {get_free_disk()}")
        else:
            if DELETE_MODEL in installed_output:
                print(f"→ Suppression de l'ancien modèle : {DELETE_MODEL}...")
                del_res = subprocess.run(f"ollama rm {DELETE_MODEL}", shell=True, capture_output=True, text=True)
                if del_res.returncode == 0:
                    print(f"✓ Modèle {DELETE_MODEL} supprimé avec succès !")
                    print(f"✓ Espace disque après suppression : {get_free_disk()} libre")
                else:
                    print(f"⚠️ Erreur lors de la suppression : {del_res.stderr.strip()}")
            else:
                print(f"ℹ️ Le modèle '{DELETE_MODEL}' n'est pas présent sur le disque (rien à supprimer).")
    else:
        print("ℹ️ Aucune suppression demandée (DELETE_MODEL non configuré).")

    # ── ÉTAPE 6: Téléchargement et chargement du modèle ─────────────
    print(f"\n[6/8] Téléchargement et chargement du modèle...")
    print(f"(Espace libre avant téléchargement : {get_free_disk()})")

    work_dir = "/kaggle/working" if os.path.exists("/kaggle/working") else "/tmp"

    if selected_target['type'] == "direct_url":
        gguf_url = selected_target['url']
        raw_filename = selected_target['filename']
        temp_gguf = os.path.join(work_dir, "model_temp.gguf")
        modelfile = os.path.join(work_dir, "Modelfile")

        print(f"🚀 Téléchargement multi-connexions accéléré (aria2c 16 threads)...")
        print(f"   Source : {gguf_url}")
        print(f"   Taille : {selected_target.get('size_gb', 'N/A')} Go")

        download_cmd = (
            f"aria2c -x 16 -s 16 -k 1M -c '{gguf_url}' -d '{work_dir}' -o 'model_temp.gguf' "
            f"|| wget -c --progress=bar:force '{gguf_url}' -O '{temp_gguf}'"
        )
        dl_res = subprocess.run(download_cmd, shell=True)

        if dl_res.returncode == 0 and os.path.exists(temp_gguf):
            print(f"\n⚙️ Création et intégration dans Ollama sous l'alias : {active_model}...")
            with open(modelfile, "w") as f:
                f.write(f"FROM {temp_gguf}\nPARAMETER temperature 0.7\nPARAMETER top_p 0.9\nPARAMETER num_predict 4096\nPARAMETER num_ctx 8192\n")

            subprocess.run(f"ollama create {active_model} -f {modelfile}", shell=True)

            print(f"🧹 Nettoyage du fichier temporaire pour libérer l'espace disque immédiat...")
            if os.path.exists(temp_gguf):
                os.remove(temp_gguf)
            if os.path.exists(modelfile):
                os.remove(modelfile)

            print(f"✓ Modèle '{active_model}' créé avec succès dans Ollama !")
            print(f"✓ Espace disque disponible après nettoyage : {get_free_disk()}")
        else:
            print("❌ Échec du téléchargement du fichier GGUF.")
    else:
        # Cas ollama pull standard
        print(f"Téléchargement via Ollama pull ({active_model})...")
        pull_res = subprocess.run(f"ollama pull {active_model}", shell=True)
        if pull_res.returncode == 0:
            print(f"✓ Modèle {active_model} téléchargé avec succès")
            print(f"✓ Espace disque restant : {get_free_disk()} libre")
        else:
            print(f"❌ Échec du téléchargement. Vérifiez l'espace disque ({get_free_disk()} libre).")

    # ── ÉTAPE 7: Test du modèle ──────────────────────────────────────
    print("\n[7/8] Test du modèle...")
    try:
        test_result = subprocess.run(
            f'echo "Bonjour, qui es-tu ?" | ollama run {active_model}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=180
        )
        if test_result.returncode == 0:
            print("✓ Modèle fonctionne correctement")
            print(f"Réponse: {test_result.stdout[:250]}...")
        else:
            print(f"⚠️ Avertissement test: {test_result.stderr.strip()}")
    except Exception as e:
        print(f"⚠️ Exception lors du test : {e}")

    # ── ÉTAPE 8: Installation de Cloudflared ────────────────────────
    print("\n[8/8] Installation de Cloudflared (tunnel public)...")
    subprocess.run(
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
        shell=True,
        capture_output=True
    )
    subprocess.run("dpkg -i cloudflared-linux-amd64.deb", shell=True, capture_output=True)
    subprocess.run("rm -f cloudflared-linux-amd64.deb", shell=True, capture_output=True)
    print("✓ Cloudflared installé")

    # ── Création du tunnel Cloudflare ──────────────────────────────
    print("\n" + "=" * 70)
    print("CRÉATION DU TUNNEL CLOUDFLARE (accès public)")
    print("=" * 70)

    cloudflared = subprocess.Popen(
        [
            "cloudflared",
            "tunnel",
            "--url", "http://127.0.0.1:11434",
            "--http-host-header", "localhost:11434"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(8)

    print("\nTunnel Cloudflare en cours de création...")
    print("-" * 70)

    for i in range(50):
        line = cloudflared.stdout.readline()
        if line:
            print(line.rstrip())
            if "trycloudflare.com" in line or "cloudflared.com" in line:
                print("✓ URL PUBLIQUE TROUVÉE - Voir ci-dessus!")

    print("-" * 70)

    # ── Résumé final ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("✓ INSTALLATION COMPLÉTÉE AVEC SUCCÈS!")
    print("=" * 70)

    summary = f"""
📋 INFORMATIONS DE CONNEXION:

  🖥️  Ollama Local:
     URL: http://localhost:11434
     Modèle actif: {active_model}
     Espace disque restant: {get_free_disk()}
  
  🌐 Tunnel Cloudflare Public:
     (Consultez l'URL *.trycloudflare.com affichée ci-dessus)

📝 COMMANDES UTILES:

  # Lister les modèles et leur taille
  !ollama list
  
  # Supprimer un modèle pour libérer de la place
  !ollama rm <nom_du_modele>
  
  # Exécuter le modèle en invite de commande
  !ollama run {active_model}
  
  # API REST locale
  !curl http://localhost:11434/api/generate -d '{{"model":"{active_model}", "prompt":"Bonjour", "stream":false}}'
  
  # Arrêter Ollama proprement
  !pkill -f "ollama serve"

📚 RESSOURCES:
  • Modèle actif: {active_model}
  • Hugging Face: https://huggingface.co
  • Documentation Ollama: https://ollama.com

⚠️  NOTE: Le tunnel Cloudflare et Ollama restent actifs tant que cette cellule s'exécute.
"""

    print(summary)

    print("\nExemple d'utilisation Python dans les cellules suivantes :")
    print("-" * 70)
    print(f"""
import requests

url = "http://localhost:11434/api/generate"
data = {{
    "model": "{active_model}",
    "prompt": "Explique les principes clés du machine learning en 3 points.",
    "stream": False,
    "options": {{
        "num_predict": 4096,  # Empêche la coupure (output limit)
        "num_ctx": 8192       # Contexte étendu
    }}
}}

response = requests.post(url, json=data)
print(response.json().get("response"))
""")
    print("-" * 70)


if __name__ == "__main__":
    main()
