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
2. ✅ Installe et démarre le serveur Ollama avec **Flash Attention** activé.
3. ✅ Télécharge le modèle recommandé **Qwen 3.8 27B TURBO Uncensored** (~17.2 Go) avec `aria2c` multi-threads (16 connexions).
4. ✅ Configure automatiquement `PARAMETER num_predict 4096` et un **contexte étendu `num_ctx 32768`** (32k tokens, compatible avec les agents IA de code type Cline, Roo Code, Continue).
5. ✅ Déploie un tunnel public Cloudflare et affiche votre URL `https://xxxx.trycloudflare.com`.
6. ✅ Maintient le serveur actif.

---

## 🎯 Options & Commandes

### 1. Modèle par défaut (Recommandé avec 32k de contexte)
```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
```
*Modèle installé : DavidAU Qwen 3.8 27B TURBO Uncensored (GGUF Q4_K_M) avec 32 768 tokens de contexte.*

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

### 3. Personnaliser la taille du contexte (Ex: 32k, 48k ou 64k)
Passez la taille de contexte souhaitée en 3ème argument :

```bash
# Définir un contexte spécifique (ex: 32768 tokens) sans supprimer de modèle :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "default" "none" "32768"
```

---

### 4. Choisir n'importe quel modèle Hugging Face

Vous disposez de **4 méthodes simples** pour choisir votre modèle Hugging Face (URL d'un fichier `.gguf`, lien d'un dépôt complet, ou identifiant `owner/repo`) :

#### Méthode A : Renseigner la variable `HF_URL` directement dans `setup_kaggle.sh`
Ouvrez le fichier `setup_kaggle.sh` et collez votre lien à la ligne 42 :
```bash
HF_URL="https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF"
```
Puis lancez simplement :
```bash
!bash setup_kaggle.sh
```

#### Méthode B : Passer le lien en argument ou avec `--hf` dans votre notebook Kaggle
```bash
# Avec l'option explicite --hf :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- --hf "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF"

# Ou avec un lien direct vers un fichier .gguf précis :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Ou simplement avec l'identifiant du repo :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "bartowski/Qwen2.5-Coder-14B-Instruct-GGUF"
```

#### Méthode C : Via le menu interactif de sélection (`--choose`)
Affiche un menu pour choisir parmi une sélection de modèles populaires ou coller votre lien :
```bash
!bash setup_kaggle.sh --choose
```

#### Méthode D : Via variable d'environnement
```bash
!HF_URL="https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF" bash setup_kaggle.sh
```

---

### 5. Installer un modèle officiel Ollama
```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "qwen2.5-coder:7b"
```

---

### 6. Rechercher des modèles sur Hugging Face (< 50 Go)
Pour trouver des modèles GGUF populaires compatibles avec le disque de Kaggle :

```bash
# Recherche par mot-clé :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--search" "qwen coder"

# Modèles populaires du moment :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--popular"
```

---

### 7. Vérifier l'état du système & des modèles
```bash
# État GPU, VRAM et espace disque :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--status"

# Lister les modèles installés :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "--list"
```

---

## 🔌 Utilisation & Connexion à l'IA

Dès que le script a terminé, il affiche votre **URL publique Cloudflare** (`https://xxxx.trycloudflare.com`).

### Dans Cline / Roo Code / Cursor / Continue (Agents IA VS Code)
* **Fournisseur (Provider)** : `Ollama` ou `OpenAI Compatible`
* **Base URL** : `https://xxxx.trycloudflare.com` (ou `https://xxxx.trycloudflare.com/v1`)
* **Model ID** : `qwen3.8-27b-turbo`
* **Context Window** : Indiquez `32768` (essentiel pour éviter les erreurs de compaction et `ContextOverflowError` !)

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
        "num_ctx": 32768      # Contexte étendu (32k tokens)
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

### "exceed_context_size_error" ou "Compaction exhausted: context still exceeds model limits"
* **Cause :** Votre outil client (ex: Cline, Roo Code, Continue) a envoyé une requête (ex: 18 202 tokens de code/fichiers/historique) qui dépasse la taille de contexte configurée dans Ollama (8192 tokens par défaut auparavant). Même après 3 tentatives de compaction, la requête reste trop volumineuse.
* **Solution 1 (Kaggle déjà en cours d'exécution, sans redémarrer ni re-télécharger) :**
  Dans une nouvelle cellule de votre notebook Kaggle, exécutez ces 3 lignes :
  ```bash
  !ollama show --modelfile qwen3.8-27b-turbo > /tmp/Modelfile
  !sed -i 's/num_ctx [0-9]*/num_ctx 32768/' /tmp/Modelfile
  !ollama create qwen3.8-27b-turbo -f /tmp/Modelfile
  ```
  Le modèle est instantanément mis à jour à 32 768 tokens (aucun re-téléchargement).
* **Solution 2 (Configuration du client VS Code) :**
  Dans les paramètres de votre extension (Cline, Roo Code ou Continue) ➡️ Configuration du modèle ➡️ Champ **Context Window** : mettez `32768`.

### "Response reached its output limit and may be incomplete"
* **Cause :** Ollama ou votre interface client bride par défaut la réponse à 128 tokens ou 512 tokens.
* **Solution :** Le script injecte automatiquement `PARAMETER num_predict 4096` dans le `Modelfile`. Dans vos requêtes directes, ajoutez `"options": {"num_predict": 4096}`.

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
