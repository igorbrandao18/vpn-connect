#!/usr/bin/env python3
"""
Módulo de conexão VPN - Azure CLI, openfortivpn
"""

import subprocess
import sys
import json
import ssl
import urllib.request
import urllib.error
from typing import Optional, Tuple, Dict


class AzureAuth:
    """Classe para autenticação Azure CLI"""
    
    @staticmethod
    def run_command(command: list, timeout: int = 10) -> Tuple[bool, str]:
        """Executa comando e retorna sucesso e output"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def check_authenticated() -> Tuple[bool, Optional[Dict]]:
        """Verifica se Azure CLI está autenticado"""
        success, output = AzureAuth.run_command(["az", "account", "show"])
        if success:
            try:
                account_info = json.loads(output)
                return True, account_info
            except Exception:
                return False, None
        return False, None
    
    @staticmethod
    def login() -> bool:
        """Faz login no Azure CLI"""
        success, _ = AzureAuth.run_command(["az", "login"])
        return success
    
    @staticmethod
    def get_token() -> Optional[str]:
        """Obtém token de acesso do Azure CLI"""
        success, output = AzureAuth.run_command(["az", "account", "get-access-token", "--output", "json"])
        if success:
            try:
                token_info = json.loads(output)
                return token_info.get("accessToken")
            except Exception:
                pass
        return None
    
    @staticmethod
    def authenticate_with_token(gateway: str, port: int, access_token: str) -> bool:
        """Tenta autenticar no gateway VPN usando token Azure CLI"""
        saml_url = f"https://{gateway}:{port}/remote/saml/start?redirect=1"
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'VPN-Client/1.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            req = urllib.request.Request(saml_url, headers=headers)
            
            try:
                with urllib.request.urlopen(req, timeout=10, context=context) as response:
                    return True
            except urllib.error.HTTPError as e:
                return e.code in [200, 302, 401, 403]
        except Exception:
            return False


class VpnConnection:
    """Classe para gerenciar conexão VPN"""
    
    # Digest conhecido do certificado (em minúsculas como openfortivpn espera)
    CERT_DIGEST = "2285b102c6bcbfef350f48611daba7de94325d8e482f901aa0c813cdbbfb064e"
    
    @staticmethod
    def check_openfortivpn() -> bool:
        """Verifica se openfortivpn está instalado"""
        success, _ = AzureAuth.run_command(["which", "openfortivpn"])
        return success
    
    @staticmethod
    def check_vpn_connected() -> bool:
        """Verifica se VPN está conectada"""
        try:
            # Verificar processos openfortivpn
            result = subprocess.run(['pgrep', '-f', 'openfortivpn'], capture_output=True)
            if result.returncode == 0:
                return True
            
            # Verificar scutil
            result = subprocess.run(['scutil', '--nc', 'list'], capture_output=True, text=True)
            if 'Connected' in result.stdout:
                return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def connect(gateway: str, port: int = 443, username: Optional[str] = None) -> bool:
        """
        Conecta à VPN usando openfortivpn com Azure CLI.
        
        Args:
            gateway: Endereço do gateway VPN
            port: Porta do gateway (padrão: 443)
            username: Nome de usuário (opcional)
        
        Returns:
            True se conectou com sucesso, False caso contrário
        """
        # Verificar Azure CLI
        azure_authenticated, account_info = AzureAuth.check_authenticated()
        
        if not azure_authenticated:
            if not AzureAuth.login():
                return False
            azure_authenticated, account_info = AzureAuth.check_authenticated()
        
        # Obter token
        access_token = AzureAuth.get_token()
        
        if not VpnConnection.check_openfortivpn():
            return False
        
        # Tentar autenticar com token Azure CLI antes
        if access_token:
            AzureAuth.authenticate_with_token(gateway, port, access_token)
        
        # Construir comando
        cmd = ["openfortivpn", f"{gateway}:{port}", "--saml-login"]
        
        # Adicionar certificado confiável
        if VpnConnection.CERT_DIGEST:
            cmd.extend(["--trusted-cert", VpnConnection.CERT_DIGEST])
        
        if username:
            cmd.extend(["--username", username])
        
        try:
            # Executar openfortivpn com sudo
            sudo_cmd = ["sudo"] + cmd
            process = subprocess.Popen(
                sudo_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            saml_url = None
            browser_opened = False
            
            # Ler output em tempo real
            for line in iter(process.stdout.readline, ''):
                if line:
                    line_stripped = line.rstrip()
                    
                    # Detectar URL SAML
                    if "Authenticate at" in line_stripped or "saml" in line_stripped.lower():
                        if "http" in line_stripped:
                            import re
                            urls = re.findall(r'https?://[^\s\']+', line_stripped)
                            if urls and not browser_opened:
                                saml_url = urls[0]
                                try:
                                    subprocess.run(["open", saml_url], check=False)
                                    browser_opened = True
                                except Exception:
                                    pass
                    
                    # Verificar se conectou
                    if "connected" in line.lower() or "tunnel is up" in line.lower():
                        # Manter processo rodando
                        try:
                            for line in iter(process.stdout.readline, ''):
                                if line:
                                    line_stripped = line.rstrip()
                                    if "disconnected" in line.lower() or "connection closed" in line.lower():
                                        return False
                        except KeyboardInterrupt:
                            process.terminate()
                            process.wait()
                            return True
                        
                        return True
                    
                    # Verificar erros
                    if "error" in line.lower() and "failed" in line.lower() and "certificate" not in line.lower():
                        return False
            
            process.wait()
            return process.returncode == 0
            
        except KeyboardInterrupt:
            if 'process' in locals():
                process.terminate()
                process.wait()
            return True
        except Exception:
            if 'process' in locals():
                process.terminate()
                process.wait()
            return False
    
    @staticmethod
    def disconnect():
        """Desconecta a VPN"""
        try:
            subprocess.run(['pkill', '-f', 'openfortivpn'], capture_output=True)
        except Exception:
            pass

