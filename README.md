# 🚀 Installation Ollama + LLM sur Kaggle Notebooks

**Projet complet**: Scripts automatisés pour installer et configurer un LLM (Qwen 7B) avec Ollama sur Kaggle Notebooks, avec tunnel Cloudflare pour accès public.

---

## 📦 Fichiers Fournis

### 1. **setup_kaggle.sh** ⚡ Ultra-rapide (Recommandé GitHub / 1 seule commande)
- **Description**: Script Bash autonome tout-en-un conçu pour être lancé directement depuis GitHub sur Kaggle
- **Avantages**:
  - ✅ **1 seule commande** à exécuter dans Kaggle (`!curl -fsSL https://raw.githubusercontent.com/... | bash`)
  - ✅ Détection automatique du matériel GPU (NVIDIA T4/P100) et de la VRAM
  - ✅ Support natif du modèle **Qwen 3.6 27B Uncensored** (Hugging Face GGUF)
  - ✅ Démarrage propre du serveur Ollama avec vérification de santé
  - ✅ Tunnel Cloudflare automatique avec extraction et affichage de l'URL publique
  - ✅ Maintien en vie du serveur et arrêt propre lors de l'interruption

**Utilisation directe dans une cellule Kaggle**:
```bash
!curl -fsSL https://raw.githubusercontent.com/VOTRE_USER/VOTRE_REPO/main/setup_kaggle.sh | bash
```

---

### 2. **kaggle_llm_setup.py**
- **Description**: Script Python complet et professionnel
- **Avantages**:
  - ✅ Entièrement automatisé
  - ✅ Gestion complète des erreurs
  - ✅ Rapport formaté en couleurs
  - ✅ Tunnel Cloudflare intégré
  - ✅ Installation de tous les modèles
  - ✅ Tests automatiques

**Utilisation**:
```bash
python3 kaggle_llm_setup.py
```

Ou dans Kaggle Notebook:
```python
exec(open('kaggle_llm_setup.py').read())
```

---

### 2. **kaggle_prompt_simple.py**
- **Description**: Script simple pour copier-coller dans Kaggle
- **Avantages**:
  - ✅ Rapide à exécuter
  - ✅ Facile à comprendre
  - ✅ Pas de dépendances externes
  - ✅ Adapté aux débutants

**Utilisation**:
1. Ouvrir un Kaggle Notebook
2. Créer une nouvelle cellule
3. Copier-coller le code
4. Exécuter

---

### 3. **DOCUMENTATION_KAGGLE_OLLAMA.md**
- **Description**: Guide complet en français
- **Contient**:
  - Installation étape par étape
  - Commandes détaillées
  - 50+ exemples d'utilisation
  - Troubleshooting
  - API REST expliquée
  - Fonction helper réutilisables

---

### 4. **kaggle_notebook_template.ipynb**
- **Description**: Template Kaggle Notebook prêt à l'emploi
- **Avantages**:
  - ✅ Format Jupyter natif
  - ✅ Cellules organisées
  - ✅ Explications incluses
  - ✅ Tests automatiques
  - ✅ Fonction helper intégrée

**Utilisation**:
1. Créer un nouveau Notebook sur Kaggle
2. Importer ce fichier (ou copier-coller les cellules)
3. Exécuter ordre ordre

---

## 🎯 Choix Rapide: Quel fichier utiliser?

| Situation | Fichier | Temps |
|-----------|---------|--------|
| **Je veux juste que ça marche** | `kaggle_llm_setup.py` | 15 min |
| **Je suis débutant** | `kaggle_notebook_template.ipynb` | 20 min |
| **Je veux un copier-coller simple** | `kaggle_prompt_simple.py` | 15 min |
| **Je veux apprendre en détail** | `DOCUMENTATION_KAGGLE_OLLAMA.md` | ∞ |
| **Je veux tout comprendre** | Tous les fichiers | 30 min |

---

## 🚀 Démarrage Rapide (1 commande)

### Option A: En une seule commande depuis GitHub (Recommandé)

Dans une cellule Kaggle Notebook :
```bash
!curl -fsSL https://raw.githubusercontent.com/VOTRE_USER/VOTRE_REPO/main/setup_kaggle.sh | bash
```
*(Ou pour spécifier un autre modèle)* :
```bash
!curl -fsSL https://raw.githubusercontent.com/VOTRE_USER/VOTRE_REPO/main/setup_kaggle.sh | bash -s -- "mistral:7b"
```

### Option B: Script Python direct dans Kaggle Notebook

```python
import subprocess
import time

# 1. Installer
!apt-get install -y zstd
!curl -fsSL https://ollama.com/install.sh | sh

# 2. Démarrer
ollama = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

# 3. Télécharger le modèle
!ollama pull qwen:7b

# 4. Utiliser
!echo "Bonjour" | ollama run qwen:7b
```

### Option B: Script complet

```bash
python3 kaggle_llm_setup.py
```

---

## 📋 Ce que l'installation Configure

### Composants Installés
- ✅ **Ollama** - Runtime pour LLMs
- ✅ **Qwen 7B** - Modèle LLM haute performance (~5.2 GB)
- ✅ **Zstandard** - Compression
- ✅ **Cloudflared** - Tunnel public (optionnel)

### Après Installation
- 🖥️ **API locale**: http://localhost:11434
- 🌐 **Tunnel public**: https://xxxx.trycloudflare.com
- 📦 **Modèle chargé**: Qwen 7B (7 milliards de paramètres)

---

## 💻 Utilisation Post-Installation

### Ligne de commande
```bash
# Lancer le modèle
ollama run qwen:7b "Bonjour, comment ça va?"

# Lister les modèles
ollama list

# Télécharger un autre modèle
ollama pull mistral:7b
```

### Python - Simple
```python
import subprocess

result = subprocess.run(
    ["ollama", "run", "qwen:7b", "Explique-moi la physique"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

### Python - API REST
```python
import requests

response = requests.post("http://localhost:11434/api/generate", json={
    "model": "qwen:7b",
    "prompt": "Bonjour",
    "stream": False
})
print(response.json()['response'])
```

### Python - Classe Helper
```python
from kaggle_notebook_template import OllamaHelper

ollama = OllamaHelper()
response = ollama.generate("Dis-moi une blague")
print(response)
```

---

## 🧠 Modèles Disponibles

Vous pouvez installer d'autres modèles après l'installation initiale:

```bash
# Légers et rapides
!ollama pull mistral:7b       # 4.1 GB - Le plus rapide
!ollama pull neural-chat:7b   # 4.7 GB - Optimisé chat

# Équilibré
!ollama pull qwen:7b          # 5.2 GB - Recommandé
!ollama pull llama2:7b        # 3.8 GB - Populaire

# Puissants
!ollama pull dolphin-mixtral  # 26 GB - Très performance
!ollama pull orca2:13b        # 7.7 GB - Intelligent
```

---

## 🔍 Troubleshooting Rapide

### "ollama: command not found"
```bash
curl -fsSL https://ollama.com/install.sh | sh
# Attendre 30 secondes
```

### "Port 11434 already in use"
```bash
# Trouver et arrêter le processus
lsof -i :11434
kill -9 <PID>
```

### "Timeout" lors du téléchargement
- Réessayer
- Utiliser un modèle plus petit (mistral:7b)
- Augmenter le timeout (600 secondes)

### "Cloudflared n'affiche pas d'URL"
```bash
# Vérifier que Ollama tourne
curl http://localhost:11434/api/tags

# Réinstaller
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
```

Voir `DOCUMENTATION_KAGGLE_OLLAMA.md` pour plus de troubleshooting.

---

## 📊 Capacités du Modèle Qwen 7B

Le modèle Qwen 7B peut:
- ✅ Répondre à des questions
- ✅ Écrire du code
- ✅ Traduire
- ✅ Résumer du texte
- ✅ Analyser des données
- ✅ Avoir une conversation
- ✅ Générer du contenu créatif

Limitations:
- ⚠️ Peut faire des erreurs sur des sujets très spécialisés
- ⚠️ Connaissance s'arrête avant sa date d'entraînement
- ⚠️ Peut être lent sur des requêtes complexes
- ⚠️ 7B = Plus léger mais moins puissant qu'un gros modèle

---

## 🌐 Partager avec un Tunnel Cloudflare

L'installation configure automatiquement Cloudflare. Cela permet:
- 🌍 Accès public via URL HTTPS
- 🔐 Sécurisé par Cloudflare
- ⚡ Sans configuration complexe
- 🔄 Reste actif tant que le script s'exécute

**URL Result**:
```
https://xxxx-yyyy-zzzz.trycloudflare.com
```

Utilisable de n'importe où:
```bash
curl https://xxxx-yyyy-zzzz.trycloudflare.com/api/generate \
  -d '{"model":"qwen:7b","prompt":"Bonjour"}'
```

---

## 📚 Ressources Supplémentaires

- **Ollama Docs**: https://ollama.com
- **Modèles HuggingFace**: https://huggingface.co
- **Kaggle**: https://kaggle.com
- **API Reference**: http://localhost:11434/api (après installation)

---

## 🎓 Exemples de Cas d'Utilisation

### 1. Chatbot Local
```python
messages = [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour!"},
]
# Voir l'API Chat dans la doc
```

### 2. Extraction d'Information
```python
text = "Marie a 25 ans et vit à Paris"
prompt = f"Extrait les noms et âges: {text}"
```

### 3. Traduction
```python
prompt = "Traduis en français: The quantum realm is fascinating"
```

### 4. Génération de Code
```python
prompt = "Écris une fonction Python pour inverser une liste"
```

### 5. Résumé Automatique
```python
prompt = f"Résume ce texte en 50 mots: {long_text}"
```

---

## ⚙️ Configuration Système Requise

**Kaggle Notebooks fourni par défaut**:
- CPU: Oui (ou GPU en option)
- RAM: 16 GB
- Disque: 20+ GB libre
- Internet: Oui

**Recommandé**:
- GPU P100 (optionnel, rend plus rapide)
- Temps d'exécution augmenté (Kaggle settings)
- Connexion stable Internet

---

## 📝 Notes Importantes

1. **Ollama continue de tourner**: Le service reste actif tant que le notebook s'exécute
2. **Port 11434**: Utilisé pour Ollama
3. **Téléchargements**: Les modèles sont volumineux (3-30 GB)
4. **Temps d'exécution**: Ollama prend du temps pour répondre (30-60s)
5. **Stockage**: Le modèle occupera plusieurs GB du disque

---

## 🤝 Support

Si vous avez des problèmes:

1. Vérifier la documentation (`DOCUMENTATION_KAGGLE_OLLAMA.md`)
2. Consulter la section Troubleshooting
3. Essayer un modèle plus petit d'abord
4. Vérifier la connexion Internet
5. Réessayer l'installation

---

## 🐙 Comment publier ce projet sur votre GitHub

Pour pouvoir utiliser le lien `raw.githubusercontent.com` sur Kaggle :

1. Créez un nouveau dépôt public sur [GitHub](https://github.com/new) (ex: `free-kaggle-llm`).
2. Ouvrez votre terminal dans ce dossier et exécutez :
```bash
git init
git add .
git commit -m "feat: ajout du script automatisé setup_kaggle.sh avec Qwen 3.6 27B"
git branch -M main
git remote add origin https://github.com/VOTRE_PSEUDO/free-kaggle-llm.git
git push -u origin main
```
3. Votre commande Kaggle devient immédiatement :
```bash
!curl -fsSL https://raw.githubusercontent.com/VOTRE_PSEUDO/free-kaggle-llm/main/setup_kaggle.sh | bash
```

---

## 📄 Licence

Ces scripts sont fournis à titre d'exemple. Utilisez-les librement!

---

## 🎉 Prochaines Étapes

1. **Choisir un fichier** (voir ci-dessus)
2. **Exécuter l'installation**
3. **Attendre 15-20 minutes**
4. **Commencer à utiliser Ollama!**

Bon amusement! 🚀

---

**Dernière mise à jour**: Septembre 2026  
**Créé pour**: Kaggle Notebooks  
**Contact**: Voir https://kaggle.com
