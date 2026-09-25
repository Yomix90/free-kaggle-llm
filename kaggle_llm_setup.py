#!/usr/bin/env python3
"""
Script d'installation et configuration d'Ollama + LLM sur Kaggle Notebooks
Installe toutes les dépendances, configure Ollama, gère l'espace disque / suppression de modèles,
et intègre un explorateur de modèles Hugging Face filtré par taille (< 50 Go) avec collage direct de liens.

⚡ Commande 1-Clic pour Kaggle Notebook :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
"""

import subprocess
import time
import os
import sys
import json
import re
import urllib.request
import urllib.parse

DEFAULT_MODEL_URL = "https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF/resolve/main/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf"
MAX_SIZE_GB_DEFAULT = 50.0


class HuggingFaceExplorer:
    """Gestionnaire d'exploration et de validation des modèles Hugging Face (< 50 Go)"""
    def __init__(self, max_size_gb=MAX_SIZE_GB_DEFAULT):
        self.max_size_gb = float(max_size_gb)

    def check_direct_url_size(self, url):
        """Vérifie la taille en Go d'un fichier distant via requête HEAD"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
            with urllib.request.urlopen(req, timeout=10) as resp:
                cl = resp.headers.get('Content-Length')
                if cl:
                    return round(int(cl) / (1024**3), 2)
        except Exception:
            pass
        return None

    def fetch_popular_models(self, limit=12):
        """Récupère les modèles GGUF les plus populaires avec taille < 50 Go"""
        url = "https://huggingface.co/api/models?filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=40"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"⚠️ Erreur lors de l'accès à Hugging Face : {e}")
            return []

        models = []
        for m in data:
            repo_id = m.get('id', '')
            downloads = m.get('downloads', 0)
            likes = m.get('likes', 0)
            gguf = m.get('gguf') or {}
            t_size = gguf.get('totalFileSize') or gguf.get('total') or 0
            size_gb = round(t_size / (1024**3), 2) if t_size else None

            if size_gb and size_gb > self.max_size_gb:
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

    def search_models(self, query, limit=12):
        """Recherche par mot-clé filtrée par taille < 50 Go"""
        encoded_q = urllib.parse.quote(query.strip())
        url = f"https://huggingface.co/api/models?search={encoded_q}&filter=gguf&expand=gguf&sort=downloads&direction=-1&limit=35"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"⚠️ Erreur recherche Hugging Face : {e}")
            return []

        models = []
        for m in data:
            repo_id = m.get('id', '')
            downloads = m.get('downloads', 0)
            likes = m.get('likes', 0)
            gguf = m.get('gguf') or {}
            t_size = gguf.get('totalFileSize') or gguf.get('total') or 0
            size_gb = round(t_size / (1024**3), 2) if t_size else None

            if size_gb and size_gb > self.max_size_gb:
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

    def get_repo_ggufs(self, repo_id):
        """Liste tous les fichiers GGUF d'un dépôt avec leur taille (< 50 Go)"""
        url = f"https://huggingface.co/api/models/{repo_id}/tree/main?recursive=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                files = json.loads(resp.read().decode())
        except Exception as e:
            print(f"⚠️ Impossible d'explorer {repo_id} : {e}")
            return []

        ggufs = []
        max_bytes = self.max_size_gb * (1024**3)
        for f in files:
            path = f.get('path', '')
            size = f.get('size', 0)
            if path.lower().endswith('.gguf') and size > 0 and size <= max_bytes:
                fname = path.split('/')[-1]
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

        ggufs.sort(key=lambda x: (x['is_split'], x['size_bytes']))
        return ggufs

    @staticmethod
    def sanitize_alias(name):
        """Génère un alias court et valide pour Ollama"""
        name = re.sub(r'\.gguf$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[^a-zA-Z0-9_\-\.]+', '-', name).lower().strip('-')
        if 'qwen3.8-27b' in name:
            return 'qwen3.8-27b-turbo'
        if len(name) > 40:
            name = name[:40].rstrip('-')
        return name or "custom-model"

    @staticmethod
    def pick_recommended(ggufs):
        """Choisit la meilleure quantification par défaut"""
        if not ggufs:
            return None
        patterns = ['Q4_K_M', 'q4_k_m', 'Q5_K_M', 'q5_k_m', 'Q4_0', 'q4_0', 'Q4_K_S', 'Q6_K']
        for pat in patterns:
            for g in ggufs:
                if pat in g['filename']:
                    return g
        return ggufs[len(ggufs) // 2]

    def resolve_target(self, target):
        """Analyse et résout un lien ou identifiant de modèle (URL, repo, fichier)"""
        target = target.strip().split('?')[0].rstrip('/')

        # 1. URL directe vers un .gguf
        if '.gguf' in target.lower() and ('http://' in target or 'https://' in target):
            url = target.replace('/blob/', '/resolve/')
            fname = url.split('/')[-1]
            size_gb = self.check_direct_url_size(url)
            alias = self.sanitize_alias(fname)
            return {
                "type": "direct_url",
                "url": url,
                "filename": fname,
                "alias": alias,
                "size_gb": size_gb or "N/A"
            }

        # 2. Dépôt Hugging Face
        clean = re.sub(r'^(?:https?://(?:www\.)?huggingface\.co/|hf\.co/)', '', target)
        parts = clean.split(':')
        repo_id = parts[0]
        tag = parts[1] if len(parts) > 1 else None

        if '/' in repo_id and not repo_id.endswith('.gguf'):
            ggufs = self.get_repo_ggufs(repo_id)
            if ggufs:
                chosen = None
                if tag:
                    for g in ggufs:
                        if tag.lower() in g['filename'].lower():
                            chosen = g
                            break
                if not chosen:
                    chosen = self.pick_recommended(ggufs)
                alias = self.sanitize_alias(chosen['filename'])
                return {
                    "type": "direct_url",
                    "url": chosen['download_url'],
                    "filename": chosen['filename'],
                    "alias": alias,
                    "size_gb": chosen['size_gb']
                }

        # 3. Modèle Ollama classique
        return {
            "type": "ollama_pull",
            "model": target,
            "alias": target,
            "size_gb": "Ollama Library"
        }

    def interactive_menu(self):
        """Affiche le menu de sélection de modèle"""
        print("\n" + "═" * 70)
        print("🤗 SÉLECTION DU MODÈLE HUGGING FACE (Filtre strict : < 50 Go)")
        print("═" * 70)
        print("  [1] 🔥 Parcourir les modèles Hugging Face populaires (< 50 Go)")
        print("  [2] 🔍 Rechercher un modèle sur Hugging Face par mot-clé (< 50 Go)")
        print("  [3] 🔗 Coller directement un lien Hugging Face (URL repo ou fichier .gguf)")
        print("  [4] ⚡ Modèle recommandé par défaut (Qwen 3.8 27B TURBO ~17 Go)")
        print("═" * 70)

        try:
            choice = input("👉 Entrez votre choix [1-4, Défaut: 4] : ").strip()
        except Exception:
            choice = "4"
        if not choice:
            choice = "4"

        if choice == "1":
            print("\n⏳ Chargement des modèles populaires (< 50 Go)...")
            models = self.fetch_popular_models(limit=10)
            if models:
                print("─" * 70)
                for idx, m in enumerate(models, 1):
                    sz = f"~{m['size_gb']} Go" if m['size_gb'] else "< 50 Go"
                    print(f"  [{idx:2d}] {m['id']:<45} | {sz:<9} | ⬇️ {m['downloads']:,}")
                print("─" * 70)
                try:
                    p = input(f"Choisissez un modèle [1-{len(models)}] : ").strip()
                    if p.isdigit() and 1 <= int(p) <= len(models):
                        return self.resolve_target(models[int(p) - 1]['id'])
                except Exception:
                    pass

        elif choice == "2":
            try:
                kw = input("🔎 Entrez un mot-clé (ex: qwen, deepseek, coder, mistral) : ").strip()
            except Exception:
                kw = ""
            if kw:
                results = self.search_models(kw, limit=10)
                if results:
                    print("─" * 70)
                    for idx, m in enumerate(results, 1):
                        sz = f"~{m['size_gb']} Go" if m['size_gb'] else "< 50 Go"
                        print(f"  [{idx:2d}] {m['id']:<45} | {sz:<9} | ⬇️ {m['downloads']:,}")
                    print("─" * 70)
                    try:
                        p = input(f"Choisissez un modèle [1-{len(results)}] : ").strip()
                        if p.isdigit() and 1 <= int(p) <= len(results):
                            return self.resolve_target(results[int(p) - 1]['id'])
                    except Exception:
                        pass

        elif choice == "3":
            try:
                pasted = input("👉 Collez votre lien ou nom de modèle : ").strip()
                if pasted:
                    return self.resolve_target(pasted)
            except Exception:
                pass

        # Défaut
        return {
            "type": "direct_url",
            "url": DEFAULT_MODEL_URL,
            "filename": "qwen3.8-27b.gguf",
            "alias": "qwen3.8-27b-turbo",
            "size_gb": 17.23
        }


class KaggleLLMSetup:
    def __init__(self):
        self.colors = {
            'GREEN': '\033[92m',
            'BLUE': '\033[94m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'END': '\033[0m'
        }
        self.hf_explorer = HuggingFaceExplorer()
        self.target_info = None

    def log_step(self, step_num, message):
        """Affiche une étape formatée"""
        print(f"\n{self.colors['BLUE']}[ÉTAPE {step_num}]{self.colors['END']} {message}")

    def log_success(self, message):
        """Affiche un message de succès"""
        print(f"{self.colors['GREEN']}✓ {message}{self.colors['END']}")

    def log_error(self, message):
        """Affiche un message d'erreur"""
        print(f"{self.colors['RED']}✗ {message}{self.colors['END']}")

    def get_free_disk(self):
        """Retourne l'espace disque disponible"""
        try:
            res = subprocess.run("df -h / | awk 'NR==2 {print $4}'", shell=True, capture_output=True, text=True)
            return res.stdout.strip()
        except Exception:
            return "N/A"

    def run_command(self, command, description, shell=True):
        """Exécute une commande shell avec gestion d'erreur"""
        try:
            if isinstance(command, str):
                result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=600)
            else:
                result = subprocess.run(command, shell=False, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                self.log_success(description)
                return True, result.stdout
            else:
                self.log_error(f"{description} - Erreur: {result.stderr}")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            self.log_error(f"{description} - Timeout après 10 minutes")
            return False, "Timeout"
        except Exception as e:
            self.log_error(f"{description} - Exception: {str(e)}")
            return False, str(e)

    def step_1_update_system(self):
        self.log_step(1, "Mise à jour du système")
        success, _ = self.run_command(
            "apt-get update -qq && apt-get upgrade -y -qq",
            "Mise à jour des paquets"
        )
        return success

    def step_2_install_zstandard(self):
        self.log_step(2, "Installation des dépendances (Zstandard, Aria2)")
        success, _ = self.run_command(
            "apt-get install -y -qq zstd aria2 || apt-get install -y -qq zstd",
            "Installation des prérequis"
        )
        return success

    def step_3_install_ollama(self):
        self.log_step(3, "Installation d'Ollama")
        success, _ = self.run_command(
            "curl -fsSL https://ollama.com/install.sh | sh",
            "Téléchargement et installation d'Ollama"
        )
        return success

    def step_4_verify_ollama(self):
        self.log_step(4, "Vérification d'Ollama")
        success, _ = self.run_command(
            "ollama --version",
            "Vérification de la version d'Ollama"
        )
        return success

    def step_5_start_ollama_service(self):
        self.log_step(5, "Démarrage du service Ollama")
        print(f"{self.colors['YELLOW']}→ Démarrage d'Ollama en arrière-plan...{self.colors['END']}")
        try:
            subprocess.run("pkill -f 'ollama serve'", shell=True, capture_output=True)
            time.sleep(1)
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)
            self.log_success(f"Ollama démarré (PID: {self.ollama_process.pid})")
            return True
        except Exception as e:
            self.log_error(f"Erreur au démarrage d'Ollama: {str(e)}")
            return False

    def step_delete_model(self, model_to_delete):
        self.log_step("5b", f"Suppression de modèle pour libérer le disque (Espace actuel: {self.get_free_disk()})")
        if not model_to_delete:
            return True

        if model_to_delete.strip().lower() == "all":
            print(f"{self.colors['YELLOW']}→ Nettoyage de TOUS les anciens modèles...{self.colors['END']}")
            success, out = self.run_command("ollama list", "Listing des modèles")
            if success and out.strip():
                lines = out.strip().split("\n")[1:]
                for l in lines:
                    parts = l.split()
                    if parts:
                        m_name = parts[0]
                        self.run_command(f"ollama rm {m_name}", f"Suppression de {m_name}")
        else:
            print(f"{self.colors['YELLOW']}→ Tentative de suppression de: {model_to_delete}{self.colors['END']}")
            _, out = self.run_command("ollama list", "Vérification des modèles installés")
            if model_to_delete in out:
                self.run_command(f"ollama rm {model_to_delete}", f"Suppression du modèle {model_to_delete}")
            else:
                print(f"{self.colors['YELLOW']}ℹ️ Le modèle {model_to_delete} n'est pas présent (aucun fichier à supprimer).{self.colors['END']}")

        print(f"{self.colors['GREEN']}✓ Espace disque disponible après nettoyage : {self.get_free_disk()}{self.colors['END']}")
        return True

    def step_6_pull_model(self, target_info=None):
        if not target_info:
            target_info = self.target_info

        alias = target_info['alias']
        self.active_model = alias
        self.log_step(6, f"Téléchargement et intégration du modèle : {alias}")
        print(f"{self.colors['YELLOW']}→ Espace disque disponible : {self.get_free_disk()}{self.colors['END']}")

        if target_info['type'] == 'direct_url':
            gguf_url = target_info['url']
            work_dir = "/kaggle/working" if os.path.exists("/kaggle/working") else "/tmp"
            temp_gguf = os.path.join(work_dir, "model_temp.gguf")
            modelfile = os.path.join(work_dir, "Modelfile")

            print(f"{self.colors['BLUE']}🚀 Téléchargement multi-connexions accéléré (aria2c 16 threads)...{self.colors['END']}")
            print(f"   URL : {gguf_url}")
            print(f"   Taille estimée : {target_info.get('size_gb', 'N/A')} Go (< 50 Go)")

            download_cmd = (
                f"aria2c -x 16 -s 16 -k 1M -c '{gguf_url}' -d '{work_dir}' -o 'model_temp.gguf' "
                f"|| wget -c --progress=bar:force '{gguf_url}' -O '{temp_gguf}'"
            )
            self.run_command(download_cmd, "Téléchargement du fichier GGUF")

            print(f"{self.colors['BLUE']}⚙️ Création du modèle Ollama '{alias}'...{self.colors['END']}")
            with open(modelfile, "w") as f:
                f.write(f"FROM {temp_gguf}\nPARAMETER temperature 0.7\nPARAMETER top_p 0.9\n")

            success, _ = self.run_command(f"ollama create {alias} -f {modelfile}", f"Création du modèle {alias}")

            print(f"{self.colors['YELLOW']}🧹 Nettoyage du fichier temporaire...{self.colors['END']}")
            if os.path.exists(temp_gguf):
                os.remove(temp_gguf)
            if os.path.exists(modelfile):
                os.remove(modelfile)

            print(f"{self.colors['GREEN']}✓ Espace disque restant : {self.get_free_disk()}{self.colors['END']}")
            return success
        else:
            print(f"{self.colors['YELLOW']}→ Téléchargement via Ollama pull ({alias})...{self.colors['END']}")
            success, output = self.run_command(
                f"ollama pull {alias}",
                f"Téléchargement du modèle {alias}",
                shell=True
            )
            if success:
                print(f"{self.colors['GREEN']}✓ Espace disque restant : {self.get_free_disk()}{self.colors['END']}")
            return success

    def step_7_test_model(self, model=None):
        target = getattr(self, 'active_model', model or "custom-model")
        self.log_step(7, f"Test du modèle {target}")
        print(f"{self.colors['YELLOW']}→ Envoi d'une requête de test...{self.colors['END']}")
        try:
            result = subprocess.run(
                f'echo "Bonjour, qui es-tu ?" | ollama run {target}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                self.log_success("Modèle fonctionne correctement")
                print(f"{self.colors['YELLOW']}Réponse du modèle:\n{result.stdout[:250]}...{self.colors['END']}")
                return True
            else:
                self.log_error(f"Erreur du modèle: {result.stderr}")
                return False
        except Exception as e:
            self.log_error(f"Erreur au test: {str(e)}")
            return False

    def step_8_install_cloudflared(self):
        self.log_step(8, "Installation de Cloudflared")
        success, _ = self.run_command(
            "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cf.deb && dpkg -i /tmp/cf.deb && rm -f /tmp/cf.deb",
            "Installation de Cloudflared"
        )
        return success

    def step_9_create_cloudflare_tunnel(self, port=11434):
        self.log_step(9, "Création du tunnel Cloudflare")
        try:
            self.cloudflared_process = subprocess.Popen(
                [
                    "cloudflared",
                    "tunnel",
                    "--url", f"http://127.0.0.1:{port}",
                    "--http-host-header", f"localhost:{port}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            time.sleep(8)
            tunnel_url = None
            for i in range(35):
                line = self.cloudflared_process.stdout.readline()
                if line:
                    print(line.rstrip())
                    if "cloudflared.com" in line or "trycloudflare.com" in line:
                        tunnel_url = line.strip()

            self.log_success("Tunnel Cloudflare démarré")
            if tunnel_url:
                print(f"\n{self.colors['GREEN']}=== URL D'ACCÈS PUBLIC ==={self.colors['END']}")
                print(f"{tunnel_url}")
                print(f"{self.colors['GREEN']}=======================\n{self.colors['END']}")
            return True
        except Exception as e:
            self.log_error(f"Erreur création tunnel: {str(e)}")
            return False

    def step_10_display_summary(self):
        target = getattr(self, 'active_model', 'custom-model')
        self.log_step(10, "Résumé de l'installation")
        summary = f"""
{self.colors['GREEN']}╔════════════════════════════════════════════════════╗
║          INSTALLATION COMPLÉTÉE AVEC SUCCÈS           ║
╚════════════════════════════════════════════════════════╝{self.colors['END']}

{self.colors['BLUE']}📋 INFORMATIONS DE CONNEXION:{self.colors['END']}
  🖥️  Ollama (Local)   : http://localhost:11434
  🤖 Modèle actif     : {target}
  💾 Disque libre     : {self.get_free_disk()}

{self.colors['BLUE']}📝 COMMANDES RAPIDES:{self.colors['END']}
  !ollama list
  !ollama run {target}
  !curl http://localhost:11434/api/generate -d '{{"model": "{target}", "prompt": "Bonjour", "stream": false}}'
        """
        print(summary)

    def run_full_setup(self, target_info=None, delete_model=None, skip_model_test=False):
        self.target_info = target_info
        model_name = target_info['alias']

        print(f"{self.colors['BLUE']}{'='*60}")
        print("  SETUP COMPLET OLLAMA + LLM POUR KAGGLE NOTEBOOKS")
        print(f"  Modèle : {model_name} (Taille: {target_info.get('size_gb', 'N/A')} Go)")
        print(f"{'='*60}{self.colors['END']}\n")

        steps = [
            (self.step_1_update_system, "Mise à jour du système"),
            (self.step_2_install_zstandard, "Installation de Zstandard"),
            (self.step_3_install_ollama, "Installation d'Ollama"),
            (self.step_4_verify_ollama, "Vérification d'Ollama"),
            (self.step_5_start_ollama_service, "Démarrage du service Ollama"),
        ]

        if delete_model:
            steps.append((lambda: self.step_delete_model(delete_model), f"Suppression de modèle ({delete_model})"))

        steps.append((lambda: self.step_6_pull_model(target_info), "Téléchargement du modèle"))

        if not skip_model_test:
            steps.append((lambda: self.step_7_test_model(model_name), "Test du modèle"))

        steps.extend([
            (self.step_8_install_cloudflared, "Installation de Cloudflared"),
            (lambda: self.step_9_create_cloudflare_tunnel(), "Création du tunnel Cloudflare"),
            (self.step_10_display_summary, "Résumé final"),
        ])

        for step_func, step_name in steps:
            try:
                if not step_func():
                    print(f"{self.colors['YELLOW']}⚠️  {step_name} - Attention (continuant...):{self.colors['END']}")
            except KeyboardInterrupt:
                print(f"\n{self.colors['RED']}Arrêt utilisateur{self.colors['END']}")
                return False
            except Exception as e:
                print(f"{self.colors['RED']}Erreur dans {step_name}: {str(e)}{self.colors['END']}")

        return True


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                 KAGGLE OLLAMA LLM INSTALLER               ║
║   Explorateur Hugging Face (< 50 Go) + Collage de Liens   ║
╚═══════════════════════════════════════════════════════════╝
    """)
    explorer = HuggingFaceExplorer()
    model_env = os.environ.get("MODEL", "").strip()
    delete_model = os.environ.get("DELETE_MODEL", None)

    if model_env:
        print(f"ℹ️ Variable MODEL détectée : {model_env}")
        target_info = explorer.resolve_target(model_env)
    else:
        target_info = explorer.interactive_menu()

    setup = KaggleLLMSetup()
    success = setup.run_full_setup(target_info=target_info, delete_model=delete_model)

    if success:
        print(f"\n{setup.colors['GREEN']}✓ Installation terminée avec succès!{setup.colors['END']}")
        print(f"{setup.colors['YELLOW']}Le tunnel Cloudflare restera actif (Ctrl+C pour arrêter).\n{setup.colors['END']}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{setup.colors['YELLOW']}Arrêt du script...{setup.colors['END']}")
    else:
        print(f"\n{setup.colors['RED']}✗ Erreur lors de l'installation{setup.colors['END']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
