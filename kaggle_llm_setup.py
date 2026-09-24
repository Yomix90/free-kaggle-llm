#!/usr/bin/env python3
"""
Script d'installation et configuration d'Ollama + LLM sur Kaggle Notebooks
Installe toutes les dépendances, configure Ollama, et crée un tunnel Cloudflare
"""

import subprocess
import time
import os
import sys

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
            "apt-get update && apt-get upgrade -y",
            "Mise à jour des paquets"
        )
        return success
    
    def step_2_install_zstandard(self):
        """Étape 2: Installer Zstandard"""
        self.log_step(2, "Installation de Zstandard")
        success, _ = self.run_command(
            "apt-get install -y zstd",
            "Installation de zstd"
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
    
    def step_6_pull_model(self, model="qwen:7b"):
        """Étape 6: Télécharger un modèle LLM"""
        self.log_step(6, f"Téléchargement du modèle: {model}")
        
        print(f"{self.colors['YELLOW']}→ Cela peut prendre plusieurs minutes...{self.colors['END']}")
        
        success, output = self.run_command(
            f"ollama pull {model}",
            f"Téléchargement du modèle {model}",
            shell=True
        )
        
        if success:
            print(f"{self.colors['YELLOW']}→ Sortie:\n{output}{self.colors['END']}")
        
        return success
    
    def step_7_test_model(self, model="qwen:7b"):
        """Étape 7: Tester le modèle"""
        self.log_step(7, f"Test du modèle {model}")
        
        print(f"{self.colors['YELLOW']}→ Envoi d'une requête de test...{self.colors['END']}")
        
        try:
            result = subprocess.run(
                f'echo "Dis-moi comment tu t\'appelles" | ollama run {model}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
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
                "rm cloudflared-linux-amd64.deb",
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
            
            # Lire les premières lignes de sortie
            tunnel_url = None
            for i in range(30):
                line = self.cloudflared_process.stdout.readline()
                if line:
                    print(line.rstrip())
                    
                    # Chercher l'URL publique
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
    
    def step_10_display_summary(self, model="qwen:7b"):
        """Étape 10: Afficher le résumé final"""
        self.log_step(10, "Résumé de l'installation")
        
        summary = f"""
{self.colors['GREEN']}╔════════════════════════════════════════════════════╗
║          INSTALLATION COMPLÉTÉE AVEC SUCCÈS           ║
╚════════════════════════════════════════════════════════╝{self.colors['END']}

{self.colors['BLUE']}📋 INFORMATIONS DE CONNEXION:{self.colors['END']}

  🖥️  Ollama (Local):
     • URL: http://localhost:11434
     • Modèle: {model}

  🌐 Tunnel Cloudflare (Public):
     • Vérifié dans la sortie ci-dessus
     • Format: https://xxxx.trycloudflare.com

{self.colors['BLUE']}📝 COMMANDES UTILES:{self.colors['END']}

  # Lister les modèles disponibles
  ollama list

  # Exécuter un modèle
  ollama run {model}

  # Appeler l'API
  curl http://localhost:11434/api/generate -d '{{"model": "{model}", "prompt": "Bonjour"}}'

  # Arrêter Ollama
  kill {self.ollama_process.pid if hasattr(self, 'ollama_process') else 'PID_OLLAMA'}

{self.colors['BLUE']}🔧 MODÈLES ALTERNATIFS:{self.colors['END']}

  - qwen:7b         (7B - Recommandé)
  - mistral:7b      (7B - Rapide)
  - llama2:7b       (7B - Populaire)
  - neural-chat:7b  (7B - Chat optimisé)

{self.colors['BLUE']}📚 DOCUMENTATION:{self.colors['END']}

  • Ollama: https://ollama.com
  • Hugging Face: https://huggingface.co
  • Kaggle: https://kaggle.com

{self.colors['YELLOW']}Nota: Le tunnel Cloudflare restera actif tant que ce script s'exécute.{self.colors['END']}
        """
        print(summary)
    
    def run_full_setup(self, model="qwen:7b", skip_model_test=False):
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
            (lambda: self.step_6_pull_model(model), "Téléchargement du modèle"),
        ]
        
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
    model = "qwen:7b"  # Modèle par défaut
    
    print(f"Modèle LLM à installer: {model}")
    print("Démarrage de l'installation...\n")
    
    setup = KaggleLLMSetup()
    success = setup.run_full_setup(model=model)
    
    if success:
        print(f"\n{setup.colors['GREEN']}✓ Installation terminée avec succès!{setup.colors['END']}")
        print(f"\n{setup.colors['YELLOW']}Le tunnel Cloudflare restera actif.{setup.colors['END']}")
        print(f"{setup.colors['YELLOW']}Utilisez Ctrl+C pour arrêter.\n{setup.colors['END']}")
        
        # Garder le script actif
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
