#!/usr/bin/env python3
"""
Script d'installation et configuration d'Ollama + LLM sur Kaggle Notebooks
Installe toutes les dépendances, configure Ollama, gère l'espace disque / suppression de modèles, et crée un tunnel Cloudflare

⚡ Commande 1-Clic pour Kaggle Notebook :
!curl -fsSL https://raw.githubusercontent.com/yomix90/free-kaggle-llm/main/setup_kaggle.sh | bash
"""

import subprocess
import time
import os
import sys

DEFAULT_MODEL = os.environ.get(
    "MODEL",
    "hf.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF:Q4_K_M"
)

class KaggleLLMSetup:
    def __init__(self):
        self.colors = {
            'GREEN': '\033[92m',
            'BLUE': '\033[94m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'END': '\033[0m'
        }
    
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
                result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=300)
            else:
                result = subprocess.run(command, shell=False, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_success(description)
                return True, result.stdout
            else:
                self.log_error(f"{description} - Erreur: {result.stderr}")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            self.log_error(f"{description} - Timeout après 5 minutes")
            return False, "Timeout"
        except Exception as e:
            self.log_error(f"{description} - Exception: {str(e)}")
            return False, str(e)
    
    def step_1_update_system(self):
        """Étape 1: Mettre à jour le système"""
        self.log_step(1, "Mise à jour du système")
        success, _ = self.run_command(
            "apt-get update -qq && apt-get upgrade -y -qq",
            "Mise à jour des paquets"
        )
        return success
    
    def step_2_install_zstandard(self):
        """Étape 2: Installer Zstandard et Aria2"""
        self.log_step(2, "Installation des dépendances (Zstandard, Aria2)")
        success, _ = self.run_command(
            "apt-get install -y -qq zstd aria2 || apt-get install -y -qq zstd",
            "Installation des prérequis"
        )
        return success
    
    def step_3_install_ollama(self):
        """Étape 3: Installer Ollama"""
        self.log_step(3, "Installation d'Ollama")
        success, output = self.run_command(
            "curl -fsSL https://ollama.com/install.sh | sh",
            "Téléchargement et installation d'Ollama"
        )
        return success
    
    def step_4_verify_ollama(self):
        """Étape 4: Vérifier l'installation d'Ollama"""
        self.log_step(4, "Vérification d'Ollama")
        success, _ = self.run_command(
            "ollama --version",
            "Vérification de la version d'Ollama"
        )
        return success
    
    def step_5_start_ollama_service(self):
        """Étape 5: Démarrer le service Ollama"""
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
            self.log_success("Ollama démarré (PID: {})".format(self.ollama_process.pid))
            return True
        except Exception as e:
            self.log_error(f"Erreur au démarrage d'Ollama: {str(e)}")
            return False

    def step_delete_model(self, model_to_delete):
        """Supprime un ancien modèle pour libérer l'espace disque"""
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
    
    def step_6_pull_model(self, model=DEFAULT_MODEL):
        """Étape 6: Télécharger un modèle LLM"""
        self.log_step(6, f"Téléchargement et préparation du modèle: {model}")
        print(f"{self.colors['YELLOW']}→ Espace disque disponible : {self.get_free_disk()}{self.colors['END']}")
        
        # Contournement de la limite Ollama de 80 caractères pour le repo HF
        if "DavidAU" in model and "Qwen3.8-27B-TURBO" in model:
            self.active_model = "qwen3.8-27b-turbo"
            gguf_url = "https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF/resolve/main/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf"
            work_dir = "/kaggle/working" if os.path.exists("/kaggle/working") else "/tmp"
            gguf_file = os.path.join(work_dir, "qwen3.8-27b.gguf")
            modelfile = os.path.join(work_dir, "Modelfile")

            print(f"{self.colors['BLUE']}ℹ️ Nom HF > 80 car. : Téléchargement direct accéléré du GGUF Q4_K_M (~17 Go)...{self.colors['END']}")
            download_cmd = f"aria2c -x 16 -s 16 -k 1M -c '{gguf_url}' -d '{work_dir}' -o 'qwen3.8-27b.gguf' || wget -c --progress=bar:force '{gguf_url}' -O '{gguf_file}'"
            self.run_command(download_cmd, "Téléchargement du GGUF")

            print(f"{self.colors['BLUE']}⚙️ Création du modèle Ollama '{self.active_model}'...{self.colors['END']}")
            with open(modelfile, "w") as f:
                f.write(f"FROM {gguf_file}\nPARAMETER temperature 0.7\nPARAMETER top_p 0.9\n")
            
            success, _ = self.run_command(f"ollama create {self.active_model} -f {modelfile}", f"Création du modèle {self.active_model}")
            
            print(f"{self.colors['YELLOW']}🧹 Nettoyage du fichier temporaire...{self.colors['END']}")
            if os.path.exists(gguf_file):
                os.remove(gguf_file)
            if os.path.exists(modelfile):
                os.remove(modelfile)
            
            print(f"{self.colors['GREEN']}✓ Espace disque restant : {self.get_free_disk()}{self.colors['END']}")
            return success
        else:
            self.active_model = model
            print(f"{self.colors['YELLOW']}→ Téléchargement via Ollama pull ({self.active_model})...{self.colors['END']}")
            success, output = self.run_command(
                f"ollama pull {self.active_model}",
                f"Téléchargement du modèle {self.active_model}",
                shell=True
            )
            if success:
                print(f"{self.colors['YELLOW']}→ Sortie:\n{output}{self.colors['END']}")
                print(f"{self.colors['GREEN']}✓ Espace disque restant : {self.get_free_disk()}{self.colors['END']}")
            return success
    
    def step_7_test_model(self, model=None):
        """Étape 7: Tester le modèle"""
        target = getattr(self, 'active_model', model or DEFAULT_MODEL)
        self.log_step(7, f"Test du modèle {target}")
        
        print(f"{self.colors['YELLOW']}→ Envoi d'une requête de test...{self.colors['END']}")
        
        try:
            result = subprocess.run(
                f'echo "Dis-moi comment tu t\'appelles" | ollama run {target}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                self.log_success("Modèle fonctionne correctement")
                print(f"{self.colors['YELLOW']}Réponse du modèle:\n{result.stdout}{self.colors['END']}")
                return True
            else:
                self.log_error(f"Erreur du modèle: {result.stderr}")
                return False
        except Exception as e:
            self.log_error(f"Erreur au test: {str(e)}")
            return False
    
    def step_8_install_cloudflared(self):
        """Étape 8: Installer Cloudflared"""
        self.log_step(8, "Installation de Cloudflared")
        
        # Télécharger Cloudflared
        success, _ = self.run_command(
            "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
            "Téléchargement de Cloudflared"
        )
        
        if not success:
            return False
        
        # Installer le paquet deb
        success, _ = self.run_command(
            "dpkg -i cloudflared-linux-amd64.deb",
            "Installation du paquet Cloudflared"
        )
        
        if success:
            self.run_command(
                "rm -f cloudflared-linux-amd64.deb",
                "Nettoyage du fichier d'installation"
            )
        
        return success
    
    def step_9_create_cloudflare_tunnel(self, port=11434):
        """Étape 9: Créer un tunnel Cloudflare"""
        self.log_step(9, "Création du tunnel Cloudflare")
        
        print(f"{self.colors['YELLOW']}→ Le tunnel sera accessible publiquement...{self.colors['END']}")
        
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
            
            print(f"{self.colors['YELLOW']}Sortie du tunnel Cloudflare:{self.colors['END']}")
            
            tunnel_url = None
            for i in range(30):
                line = self.cloudflared_process.stdout.readline()
                if line:
                    print(line.rstrip())
                    if "cloudflared.com" in line or "trycloudflare.com" in line:
                        tunnel_url = line.strip()
            
            self.log_success(f"Tunnel Cloudflare créé (PID: {self.cloudflared_process.pid})")
            
            if tunnel_url:
                print(f"\n{self.colors['GREEN']}=== URL D'ACCÈS PUBLIC ==={self.colors['END']}")
                print(f"{tunnel_url}")
                print(f"{self.colors['GREEN']}=======================\n{self.colors['END']}")
            
            return True
        except Exception as e:
            self.log_error(f"Erreur création tunnel: {str(e)}")
            return False
    
    def step_10_display_summary(self, model=None):
        """Étape 10: Afficher le résumé final"""
        target = getattr(self, 'active_model', model or DEFAULT_MODEL)
        self.log_step(10, "Résumé de l'installation")
        
        summary = f"""
{self.colors['GREEN']}╔════════════════════════════════════════════════════╗
║          INSTALLATION COMPLÉTÉE AVEC SUCCÈS           ║
╚════════════════════════════════════════════════════════╝{self.colors['END']}

{self.colors['BLUE']}📋 INFORMATIONS DE CONNEXION:{self.colors['END']}

  🖥️  Ollama (Local):
     • URL: http://localhost:11434
     • Modèle: {target}
     • Disque libre: {self.get_free_disk()}

  🌐 Tunnel Cloudflare (Public):
     • Vérifié dans la sortie ci-dessus
     • Format: https://xxxx.trycloudflare.com

{self.colors['BLUE']}📝 COMMANDES UTILES:{self.colors['END']}

  # Lister les modèles disponibles et leur taille
  ollama list

  # Supprimer un modèle pour libérer du stockage
  ollama rm <nom_du_modele>

  # Exécuter un modèle
  ollama run {model}

  # Appeler l'API
  curl http://localhost:11434/api/generate -d '{{"model": "{model}", "prompt": "Bonjour", "stream": false}}'

  # Arrêter Ollama
  pkill -f "ollama serve"

{self.colors['BLUE']}📚 DOCUMENTATION:{self.colors['END']}

  • Ollama: https://ollama.com
  • Hugging Face: https://huggingface.co
  • Modèle: {model}

{self.colors['YELLOW']}Nota: Le tunnel Cloudflare restera actif tant que ce script s'exécute.{self.colors['END']}
        """
        print(summary)
    
    def run_full_setup(self, model=DEFAULT_MODEL, delete_model=None, skip_model_test=False):
        """Exécute l'installation complète"""
        print(f"{self.colors['BLUE']}{'='*60}")
        print("  SETUP COMPLET OLLAMA + LLM POUR KAGGLE NOTEBOOKS")
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
        
        steps.append((lambda: self.step_6_pull_model(model), "Téléchargement du modèle"))
        
        if not skip_model_test:
            steps.append((lambda: self.step_7_test_model(model), "Test du modèle"))
        
        steps.extend([
            (self.step_8_install_cloudflared, "Installation de Cloudflared"),
            (lambda: self.step_9_create_cloudflare_tunnel(), "Création du tunnel Cloudflare"),
            (lambda: self.step_10_display_summary(model), "Résumé final"),
        ])
        
        completed = 0
        for step_func, step_name in steps:
            try:
                if step_func():
                    completed += 1
                else:
                    print(f"{self.colors['YELLOW']}⚠️  {step_name} - Attention (continuant...):{self.colors['END']}")
            except KeyboardInterrupt:
                print(f"\n{self.colors['RED']}Installation interrompue par l'utilisateur{self.colors['END']}")
                return False
            except Exception as e:
                print(f"{self.colors['RED']}Erreur dans {step_name}: {str(e)}{self.colors['END']}")
        
        return completed == len(steps)


def main():
    """Fonction principale"""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                 KAGGLE OLLAMA LLM INSTALLER              ║
║              Script de Configuration Automatique           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Paramètres du script
    model = os.environ.get("MODEL", DEFAULT_MODEL)
    delete_model = os.environ.get("DELETE_MODEL", None)
    
    print(f"Modèle LLM cible: {model}")
    if delete_model:
        print(f"Suppression demandée pour: {delete_model}")
    print("Démarrage de l'installation...\n")
    
    setup = KaggleLLMSetup()
    success = setup.run_full_setup(model=model, delete_model=delete_model)
    
    if success:
        print(f"\n{setup.colors['GREEN']}✓ Installation terminée avec succès!{setup.colors['END']}")
        print(f"\n{setup.colors['YELLOW']}Le tunnel Cloudflare restera actif.{setup.colors['END']}")
        print(f"{setup.colors['YELLOW']}Utilisez Ctrl+C pour arrêter.\n{setup.colors['END']}")
        
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
