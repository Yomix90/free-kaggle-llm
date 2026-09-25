# 🚀 Free Kaggle LLM Deployer (All-in-One)

> **Déployez et exécutez des LLM haute performance (Qwen 3.8 27B TURBO, DeepSeek, Mistral, Llama...) sur Kaggle Notebooks en 1 seule commande avec Ollama et un tunnel public Cloudflare gratuit.**

---

## ⚡ Lancement Ultra-Rapide (1 seule commande)

Ouvrez un **Kaggle Notebook** (avec accélérateur **GPU T4 x2** activé dans le panneau de droite), créez une cellule et exécutez :

```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
```

Le script s'occupe de **tout** automatiquement :
1. ✅ Détecte vos GPU NVIDIA (2x Tesla T4, 29.1 Go VRAM).
2. ✅ Installe et démarre le serveur Ollama.
3. ✅ Télécharge le modèle recommandé **Qwen 3.8 27B TURBO Uncensored** (~17.2 Go) avec `aria2c` multi-threads (16 connexions).
4. ✅ Configure automatiquement `PARAMETER num_predict 4096` et `num_ctx 8192` (évite la coupure de réponse *"Response reached its output limit"*).
5. ✅ Déploie un tunnel public Cloudflare et affiche votre URL `https://xxxx.trycloudflare.com`.
6. ✅ Maintient le serveur actif.

---

## 🎯 Options & Commandes

### 1. Modèle par défaut (Recommandé)
```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
```
*Modèle installé : DavidAU Qwen 3.8 27B TURBO Uncensored (GGUF Q4_K_M).*

---

### 2. Libérer le disque avant d'installer (Supprimer les anciens modèles)
Pour éviter l'erreur `no space left on device` sur Kaggle :

```bash
# Supprimer TOUS les anciens modèles pour repartir à zéro :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "default" "all"

# Supprimer un modèle spécifique :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "default" "ancien-modele"
```

---

### 3. Installer n'importe quel modèle Hugging Face
Vous pouvez passer directement une URL de fichier `.gguf` ou l'URL d'un dépôt Hugging Face (le script sélectionnera automatiquement la meilleure version compatible < 50 Go) :

```bash
# Lien direct .gguf :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q4_K_M.gguf"

# Lien de dépôt Hugging Face complet :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF"
```

---

### 4. Installer un modèle officiel Ollama
```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "qwen:7b"
```

---

### 5. Rechercher des modèles sur Hugging Face (< 50 Go)
Pour trouver des modèles GGUF populaires compatibles avec le disque de Kaggle :

```bash
# Recherche par mot-clé :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--search" "qwen coder"

# Modèles populaires du moment :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--popular"
```

---

### 6. Vérifier l'état du système & des modèles
```bash
# État GPU, VRAM et espace disque :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--status"

# Lister les modèles installés :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--list"
```

---

## 🔌 Utilisation & Connexion à l'IA

Dès que le script a terminé, il affiche votre **URL publique Cloudflare** (`https://xxxx.trycloudflare.com`).

### En Python (dans une autre cellule ou depuis votre PC)
```python
import requests

# URL Cloudflare ou locale http://localhost:11434
url = "https://xxxx-yyyy-zzzz.trycloudflare.com/api/generate"

data = {
    "model": "qwen3.8-27b-turbo",
    "prompt": "Explique les concepts clés de l'IA en 3 points.",
    "stream": False,
    "options": {
        "num_predict": 4096,  # Empêche la coupure (output limit)
        "num_ctx": 8192       # Contexte étendu
    }
}

response = requests.post(url, json=data)
print(response.json().get("response"))
```

### Dans Open WebUI / LM Studio / Chatbox
Dans les paramètres de votre application :
* **Ollama Base URL** : `https://xxxx-yyyy-zzzz.trycloudflare.com`
* Le modèle `qwen3.8-27b-turbo` apparaîtra directement dans la liste.

---

## 🛠️ Dépannage Fréquent

### "Response reached its output limit and may be incomplete"
* **Cause :** Ollama ou votre interface client bride par défaut la réponse à 128 tokens ou 512 tokens.
* **Solution :** Le script injecte automatiquement `PARAMETER num_predict 4096` dans le `Modelfile`. Dans vos requêtes Python, ajoutez toujours `"options": {"num_predict": 4096, "num_ctx": 8192}`.

### "no space left on device"
* **Cause :** Un ancien modèle occupe le disque du notebook.
* **Solution :** Relancez avec `bash -s -- "default" "all"` pour nettoyer tous les anciens fichiers avant d'installer le nouveau modèle.

### Crash ou lenteur extrême
* **Cause :** Le notebook tourne sur CPU au lieu du GPU.
* **Solution :** Dans Kaggle, allez dans le panneau latéral droit ➡️ *Notebook options* ➡️ *Accelerator* ➡️ Choisissez **GPU T4 x2**.

---

## 📁 Structure du Projet

```text
free-kaggle-llm/
├── setup_kaggle.sh   # 🚀 Script Bash tout-en-un autonome (déploiement, modèles, tunnel)
├── README.md         # 📖 Documentation complète
└── .gitignore        # Fichiers ignorés
```
