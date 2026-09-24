# ════════════════════════════════════════════════════════════════
# PROMPT POUR KAGGLE NOTEBOOKS - OLLAMA LLM SETUP
# Copier-coller ce code dans une cellule Kaggle Notebook
#
# ⚡ OU EN 1 SEULE COMMANDE BASH DANS KAGGLE :
# !curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
# ════════════════════════════════════════════════════════════════

import subprocess
import time
import os
import re

# Modèle LLM cible à déployer
MODEL = os.environ.get(
    "MODEL", 
    "hf.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF:Q4_K_M"
)

# Option de suppression d'un ancien modèle pour libérer l'espace disque Kaggle (~17 Go nécessaires)
# Valeurs possibles :
#   - Nom précis à supprimer, ex: "hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M"
#   - "all" pour supprimer tous les autres modèles installés
#   - "" ou None pour désactiver la suppression
DELETE_MODEL = os.environ.get(
    "DELETE_MODEL", 
    "hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M"
)

def get_free_disk():
    """Retourne l'espace disque disponible sur la partition principale"""
    try:
        res = subprocess.run("df -h / | awk 'NR==2 {print $4}'", shell=True, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "N/A"

print("=" * 70)
print("INSTALLATION OLLAMA + LLM SUR KAGGLE")
print(f"Modèle cible à installer : {MODEL}")
if DELETE_MODEL:
    print(f"Modèle ciblé pour suppression : {DELETE_MODEL}")
print(f"Espace disque disponible initial : {get_free_disk()}")
print("=" * 70)

# ── ÉTAPE 1: Installation de Zstandard ──────────────────────────
print("\n[1/8] Installation de Zstandard...")
subprocess.run("apt-get update -qq && apt-get install -y -qq zstd", shell=True, capture_output=True)
print("✓ Zstandard installé")

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

# ── ÉTAPE 5: Suppression d'un ancien modèle pour libérer l'espace disque ──
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
                if m_name != MODEL:
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

# ── ÉTAPE 6: Téléchargement du modèle LLM ──────────────────────
print(f"\n[6/8] Téléchargement du modèle {MODEL}...")
print(f"(Taille estimée ~17 Go. Espace libre avant téléchargement : {get_free_disk()})")
print("(Cela peut prendre 5-15 minutes selon la bande passante Kaggle)")
pull_res = subprocess.run(f"ollama pull {MODEL}", shell=True)
if pull_res.returncode == 0:
    print(f"✓ Modèle {MODEL} téléchargé avec succès")
    print(f"✓ Espace disque restant : {get_free_disk()} libre")
else:
    print(f"❌ Échec du téléchargement. Vérifiez l'espace disque ({get_free_disk()} libre).")

# ── ÉTAPE 7: Test du modèle ──────────────────────────────────────
print("\n[7/8] Test du modèle...")
try:
    test_result = subprocess.run(
        f'echo "Bonjour, qui es-tu ?" | ollama run {MODEL}',
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
print("─" * 70)

for i in range(50):
    line = cloudflared.stdout.readline()
    if line:
        print(line.rstrip())
        if "trycloudflare.com" in line or "cloudflared.com" in line:
            print("✓ URL PUBLIQUE TROUVÉE - Voir ci-dessus!")

print("─" * 70)

# ── Résumé final ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("✓ INSTALLATION COMPLÉTÉE AVEC SUCCÈS!")
print("=" * 70)

summary = f"""
📋 INFORMATIONS DE CONNEXION:

  🖥️  Ollama Local:
     URL: http://localhost:11434
     Modèle actif: {MODEL}
     Espace disque restant: {get_free_disk()}
  
  🌐 Tunnel Cloudflare Public:
     (Consultez l'URL *.trycloudflare.com affichée ci-dessus)

📝 COMMANDES UTILES:

  # Lister les modèles et leur taille
  !ollama list
  
  # Supprimer un modèle pour libérer de la place
  !ollama rm <nom_du_modele>
  # Ex: !ollama rm hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M
  
  # Exécuter le modèle en invite de commande
  !ollama run {MODEL}
  
  # API REST locale
  !curl http://localhost:11434/api/generate -d '{{"model":"{MODEL}", "prompt":"Bonjour", "stream":false}}'
  
  # Arrêter Ollama proprement
  !pkill -f "ollama serve"

📚 RESSOURCES:
  • Modèle: {MODEL}
  • Documentation Ollama: https://ollama.com
  • Hugging Face DavidAU: https://huggingface.co/DavidAU

⚠️  NOTE: Le tunnel Cloudflare et Ollama restent actifs tant que cette cellule s'exécute.
"""

print(summary)

print("\nExemple d'utilisation Python dans les cellules suivantes :")
print("─" * 70)
print(f"""
import requests

url = "http://localhost:11434/api/generate"
data = {{
    "model": "{MODEL}",
    "prompt": "Explique les principes clés du machine learning en 3 points.",
    "stream": False
}}

response = requests.post(url, json=data)
print(response.json().get("response"))
""")
print("─" * 70)
