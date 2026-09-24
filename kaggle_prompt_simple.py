# ════════════════════════════════════════════════════════════════
# PROMPT POUR KAGGLE NOTEBOOKS - OLLAMA LLM SETUP
# Copier-coller ce code dans une cellule Kaggle Notebook
# ════════════════════════════════════════════════════════════════

import subprocess
import time
import os
import re

# Modèle LLM à déployer (modifiable)
MODEL = os.environ.get(
    "MODEL", 
    "hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M"
)

print("=" * 70)
print("INSTALLATION OLLAMA + LLM SUR KAGGLE")
print(f"Modèle ciblé : {MODEL}")
print("=" * 70)

# ── ÉTAPE 1: Installation de Zstandard ──────────────────────────
print("\n[1/7] Installation de Zstandard...")
subprocess.run("apt-get update && apt-get install -y zstd", shell=True, capture_output=True)
print("✓ Zstandard installé")

# ── ÉTAPE 2: Installation d'Ollama ──────────────────────────────
print("\n[2/7] Installation d'Ollama...")
subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, capture_output=True)
print("✓ Ollama installé")

# ── ÉTAPE 3: Vérification d'Ollama ──────────────────────────────
print("\n[3/7] Vérification d'Ollama...")
result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
print(f"✓ {result.stdout.strip()}")

# ── ÉTAPE 4: Démarrage d'Ollama en arrière-plan ──────────────────
print("\n[4/7] Démarrage d'Ollama...")
ollama_process = subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(5)
print(f"✓ Ollama démarré (PID: {ollama_process.pid})")

# ── ÉTAPE 5: Téléchargement du modèle LLM ──────────────────────
print(f"\n[5/7] Téléchargement du modèle {MODEL}...")
print("(Cela peut prendre 5-15 minutes selon la taille du modèle)")
subprocess.run(f"ollama pull {MODEL}", shell=True)
print(f"✓ Modèle {MODEL} téléchargé")

# ── ÉTAPE 6: Test du modèle ──────────────────────────────────────
print("\n[6/7] Test du modèle...")
test_result = subprocess.run(
    f'echo "Bonjour, dis-moi ton nom" | ollama run {MODEL}',
    shell=True,
    capture_output=True,
    text=True,
    timeout=120
)
print("✓ Modèle fonctionne correctement")
print(f"Réponse: {test_result.stdout[:200]}...")

# ── ÉTAPE 7: Installation de Cloudflared ────────────────────────
print("\n[7/7] Installation de Cloudflared (tunnel public)...")
subprocess.run(
    "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
    shell=True,
    capture_output=True
)
subprocess.run("dpkg -i cloudflared-linux-amd64.deb", shell=True, capture_output=True)
subprocess.run("rm cloudflared-linux-amd64.deb", shell=True, capture_output=True)
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
     Modèle: {MODEL}
  
  🌐 Tunnel Cloudflare Public:
     (URL affichée ci-dessus avec trycloudflare.com)

📝 COMMANDES UTILES:

  # Lister les modèles
  !ollama list
  
  # Exécuter le modèle
  !ollama run {MODEL}
  
  # API REST
  !curl http://localhost:11434/api/generate -d '{{"model":"{MODEL}", "prompt":"Bonjour"}}'
  
  # Télécharger un autre modèle
  !ollama pull mistral:7b
  
  # Arrêter Ollama
  import os
  os.system("pkill ollama")

🔧 MODÈLES ALTERNATIFS:

  - qwen:7b          (Recommandé)
  - mistral:7b       (Rapide)
  - llama2:7b        (Populaire)
  - neural-chat:7b   (Chat optimisé)
  - dolphin-mixtral  (Haute performance)

📚 RESSOURCES:

  • Documentation Ollama: https://ollama.com
  • Modèles Hugging Face: https://huggingface.co
  • API Ollama: http://localhost:11434/api/generate

⚠️  NOTE: Le tunnel Cloudflare restera actif tant que ce notebook s'exécute.
"""

print(summary)

print("\nVous pouvez maintenant utiliser Ollama dans d'autres cellules!")
print("Exemple:")
print("─" * 70)
print("""
import subprocess
import json

def query_ollama(prompt, model="qwen:7b"):
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    return result.stdout

response = query_ollama("Explique-moi la physique quantique en français")
print(response)
""")
print("─" * 70)
