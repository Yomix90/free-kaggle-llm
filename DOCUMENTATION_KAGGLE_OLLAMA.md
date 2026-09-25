# 🤖 Installation d'Ollama + LLM sur Kaggle Notebooks
## Guide Complet d'Installation et Utilisation

---

## 📋 Table des matières
1. [Configuration rapide](#configuration-rapide)
2. [Script complet](#script-complet)
3. [Commandes détaillées](#commandes-détaillées)
4. [Modèles disponibles](#modèles-disponibles)
5. [Utilisation de l'API](#utilisation-de-lapi)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Configuration Rapide

### Option 0 : ⚡ Ultra-rapide en 1 seule commande (Recommandé)

Collez simplement cette commande dans une cellule Kaggle Notebook :

```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
```

*(Ou pour supprimer un ancien modèle pour libérer ~17 Go)* :
```bash
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash -s -- "hf.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF:Q4_K_M" "all"
```

---

### Option 1: Copier-coller simple (Recommandé avec explorateur Hugging Face)

Ouvrez un **Kaggle Notebook** et exécutez le code du fichier [`kaggle_prompt_simple.py`](file:///c:/Users/USF/Desktop/FREE%20LLM/kaggle_prompt_simple.py).

✨ **Fonctionnalités intégrées :**
- **Explorateur interactif Hugging Face** : Liste les modèles GGUF les plus populaires.
- **Filtre strict < 50 Go** : N'affiche que les modèles qui tiennent sur le disque Kaggle (~50 Go max).
- **Recherche par mot-clé** : Qwen, DeepSeek, Mistral, Llama, Coder, etc.
- **Collage direct de lien** : Collez directement une URL de fichier `.gguf` (ex: `https://huggingface.co/.../resolve/main/...gguf`) ou une URL de dépôt Hugging Face.
- **Vérification automatique de taille** avant téléchargement (évite l'erreur `no space left on device`).
- **Téléchargement multi-thread accéléré** (aria2c 16 connexions).

---

## 🔧 Script Complet

### Utilisation du script Python principal

**Avantages:**
- ✅ Installation complètement automatisée
- ✅ Gestion des erreurs
- ✅ Tunnel Cloudflare intégré (accès public)
- ✅ Rapports détaillés
- ✅ Plusieurs modèles testés

**Installation:**

```bash
# Télécharger le script depuis GitHub
wget https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/kaggle_llm_setup.py

# Exécuter
python3 kaggle_llm_setup.py
```

**Ou dans Kaggle Notebook:**

```python
# Charger et exécuter le script
exec(open('/kaggle/input/votre-dataset/kaggle_llm_setup.py').read())
```

---

## 📝 Commandes Détaillées

### Installation étape par étape

#### 1️⃣ Mettre à jour le système
```bash
!apt-get update
!apt-get upgrade -y
```

#### 2️⃣ Installer Zstandard (compression)
```bash
!apt-get install -y zstd
```

#### 3️⃣ Installer Ollama
```bash
!curl -fsSL https://ollama.com/install.sh | sh
```

#### 4️⃣ Vérifier l'installation
```bash
!ollama --version
```

#### 5️⃣ Démarrer le service Ollama
```python
import subprocess
import time

ollama = subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(5)
print(f"Ollama en cours d'exécution (PID: {ollama.pid})")
```

#### 6️⃣ Télécharger un modèle
```bash
# Modèle recommandé (7B)
!ollama pull qwen:7b

# Autres options
!ollama pull mistral:7b
!ollama pull llama2:7b
```

#### 7️⃣ Exécuter le modèle
```bash
!ollama run qwen:7b "Explique-moi la physique quantique"
```

---

## 🧠 Modèles Disponibles

### Modèles Recommandés pour Kaggle

| Modèle | Taille | Vitesse | Qualité | Cas d'usage |
|--------|--------|---------|---------|------------|
| **Qwen 3.8 27B TURBO Uncensored (DavidAU)** | ~17 GB | ⚡⚡⚡ (MTP) | ⭐⭐⭐⭐⭐ | **Recommandé Ultime** - Code, raisonnement, non-censuré |
| **qwen:7b** | 5.2 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Équilibre optimal pour débuter |
| mistral:7b | 4.1 GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Très rapide, léger |
| llama2:7b | 3.8 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Populaire, fiable |
| neural-chat:7b | 4.7 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Chat optimisé |
| dolphin-mixtral | 26 GB | ⚡ | ⭐⭐⭐⭐⭐ | Haute performance |
| orca2:13b | 7.7 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Très intelligent |

### Télécharger un modèle

```bash
# Modèle DavidAU Qwen 3.8 27B Turbo Uncensored (GGUF Q4_K_M)
!ollama pull hf.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF:Q4_K_M

# Autres modèles standards
!ollama pull qwen:7b
!ollama pull mistral:7b
```

### Lister les modèles installés et leur taille
```bash
!ollama list
```

### 🗑️ Supprimer un modèle pour libérer l'espace disque (Indispensable pour 27B)

> 💡 **Rappel Kaggle :**  
> L'espace disque d'un notebook Kaggle est limité. Un modèle 27B en Q4_K_M pèse **~17 Go**. Si vous avez déjà téléchargé un autre modèle volumineux, vous rencontrerez l'erreur `no space left on device`.  
> Supprimez toujours les modèles inutiles avant d'en télécharger un nouveau !

```bash
# 1. Vérifier l'espace disque restant
!df -h /

# 2. Supprimer un modèle précis
!ollama rm hf.co/theLittleStone/Qwen3.6-27B-AEON-Ultimate-Uncensored-MTP-i1-GGUF:Q4_K_M
!ollama rm qwen:7b

# 3. Supprimer TOUS les modèles installés pour repartir à zéro :
!ollama list | awk 'NR>1 {print $1}' | xargs -I {} ollama rm {}

# 4. Vérifier le nouvel espace libre
!df -h /
```

---

## 🔌 Utilisation de l'API

### API REST de base

#### Générer du texte
```python
import requests
import json

url = "http://localhost:11434/api/generate"

data = {
    "model": "qwen:7b",
    "prompt": "Qui a inventé l'électricité?",
    "stream": False
}

response = requests.post(url, json=data)
print(response.json()['response'])
```

#### API avec streaming
```python
import requests

url = "http://localhost:11434/api/generate"
data = {
    "model": "qwen:7b",
    "prompt": "Raconte-moi une histoire courte",
    "stream": True
}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(json.loads(line).get('response', ''), end='', flush=True)
```

#### Chat (conversation)
```python
url = "http://localhost:11434/api/chat"

data = {
    "model": "qwen:7b",
    "messages": [
        {"role": "user", "content": "Bonjour, comment ça va?"},
        {"role": "assistant", "content": "Bonjour! Ça va bien, merci!"},
        {"role": "user", "content": "Qui es-tu?"}
    ],
    "stream": False
}

response = requests.post(url, json=data)
print(response.json()['message']['content'])
```

### Utiliser avec cURL
```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "qwen:7b",
    "prompt": "Bonjour",
    "stream": false
  }'
```

---

## 🌐 Tunnel Cloudflare (Accès Public)

### Installation de Cloudflared
```bash
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
!rm cloudflared-linux-amd64.deb
```

### Créer un tunnel
```python
import subprocess
import time

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

# Lire la sortie pour obtenir l'URL publique
for i in range(50):
    line = cloudflared.stdout.readline()
    print(line.rstrip())
```

### Résultat
Vous obtiendrez une URL comme:
```
https://xxxx-yyyy-zzzz.trycloudflare.com
```

### Utiliser l'URL publique
```bash
curl https://xxxx-yyyy-zzzz.trycloudflare.com/api/generate \
  -d '{"model": "qwen:7b", "prompt": "Bonjour"}'
```

---

## 📊 Fonction Helper pour utiliser Ollama

### Créer une fonction réutilisable
```python
import subprocess
import json

def query_ollama(prompt, model="qwen:7b", stream=False):
    """
    Interroger Ollama simplement
    
    Args:
        prompt (str): La question/prompt
        model (str): Modèle à utiliser
        stream (bool): Streaming activé?
    
    Returns:
        str: La réponse du modèle
    """
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout
    except Exception as e:
        return f"Erreur: {str(e)}"

# Utilisation
reponse = query_ollama("Explique-moi la relativité", model="qwen:7b")
print(reponse)
```

### Classe pour interactions avancées
```python
import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
    
    def generate(self, prompt, model="qwen:7b"):
        """Génération simple"""
        url = f"{self.base_url}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=data)
        return response.json()['response']
    
    def chat(self, messages, model="qwen:7b"):
        """Chat avec historique"""
        url = f"{self.base_url}/api/chat"
        data = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        response = requests.post(url, json=data)
        return response.json()['message']['content']
    
    def list_models(self):
        """Lister les modèles disponibles"""
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        return response.json()['models']

# Utilisation
client = OllamaClient()

# Générer
print(client.generate("Qui a écrit Hamlet?"))

# Chat
messages = [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour! Comment je peux t'aider?"},
    {"role": "user", "content": "Dis-moi un fait amusant"}
]
print(client.chat(messages))

# Lister les modèles
print(client.list_models())
```

---

## 🔍 Troubleshooting

### Problème: "ollama: command not found"
**Solution:**
```bash
!curl -fsSL https://ollama.com/install.sh | sh
# Attendre 30 secondes
import time
time.sleep(30)
!ollama --version
```

### Problème: "Port 11434 déjà utilisé"
**Solution:**
```bash
# Trouver le processus
!lsof -i :11434

# Arrêter le processus
!kill -9 <PID>
```

### Problème: "Modèle trop volumineux"
**Solution:** Utiliser un modèle plus petit
```bash
!ollama pull mistral:7b  # Plus petit (4.1 GB)
!ollama pull neural-chat:7b  # Léger (4.7 GB)
```

### Problème: "Timeout lors du téléchargement"
**Solution:** 
- Réessayer avec une meilleure connexion
- Utiliser un petit modèle d'abord
- Augmenter le timeout:
```python
subprocess.run("ollama pull qwen:7b", shell=True, timeout=600)
```

### Problème: "Cloudflared ne trouve pas d'URL"
**Solution:**
```bash
# Vérifier que Ollama tourne
!curl http://localhost:11434/api/tags

# Réinstaller cloudflared
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
```

---

## 📚 Ressources Supplémentaires

- **Ollama Documentation**: https://ollama.com
- **Modèles Hugging Face**: https://huggingface.co
- **Kaggle Notebooks**: https://kaggle.com/code
- **API Ollama**: http://localhost:11434/api

---

## 💡 Conseils Pratiques

1. **Tester avec un petit modèle d'abord**
   - Commencer par `qwen:7b` ou `mistral:7b`
   - Passer à des modèles plus gros une fois maîtrisé

2. **Gérer les ressources**
   - Arrêter Ollama quand pas utilisé
   - Utiliser un modèle adapté à la taille mémoire

3. **Sauvegarder les résultats**
   - Exporter les réponses du modèle
   - Garder un journal des prompts efficaces

4. **Optimiser les prompts**
   - Être spécifique dans les instructions
   - Fournir du contexte quand possible
   - Utiliser des exemples (few-shot learning)

---

## 🎓 Exemples d'Utilisation

### Traduction
```python
prompt = "Traduis cette phrase en français: 'The quantum realm is fascinating'"
reponse = query_ollama(prompt)
print(reponse)
```

### Résumé
```python
text = "Lorem ipsum dolor sit amet..."
prompt = f"Fais un résumé court de ce texte: {text}"
reponse = query_ollama(prompt)
print(reponse)
```

### Extraction d'information
```python
prompt = """Extrait les noms et dates de ce texte:
Marie et Jean se sont mariés le 15 juin 2020.
Pierre a déménagé le 3 octobre 2021."""
reponse = query_ollama(prompt)
print(reponse)
```

### Code Python
```python
prompt = "Écris une fonction Python qui inverse une liste"
reponse = query_ollama(prompt)
print(reponse)
```

---

**Créé pour Kaggle Notebooks - Mis à jour: Septembre 2026**
