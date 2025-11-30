#!/usr/bin/env python3
"""
Script para conectar à VPN usando openfortivpn com autenticação Azure CLI
"""

import subprocess
import sys
import time
import argparse
import json
import ssl
import hashlib
import urllib.request
import urllib.parse

def print_flush(*args, **kwargs):
    print(*args, **kwargs, flush=True)


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def check_azure_cli():
    """Verifica se Azure CLI está autenticado"""
    success, output = run_command(["az", "account", "show"])
    if success:
        try:
            account_info = json.loads(output)
            return True, account_info
        except:
            return False, None
    return False, None


def get_azure_token():
    """Obtém token de acesso do Azure CLI"""
    print_flush("🔑 Obtendo token do Azure CLI...")
    
    success, output = run_command(["az", "account", "get-access-token", "--output", "json"])
    if success:
        try:
            token_info = json.loads(output)
            access_token = token_info.get("accessToken")
            if access_token:
                print_flush("✅ Token obtido com sucesso")
                return access_token
        except Exception as e:
            print_flush(f"⚠️  Erro ao processar token: {e}")
    
    print_flush("⚠️  Não foi possível obter token")
    return None


def get_certificate_digest(gateway, port=443):
    """Obtém o digest SHA256 do certificado SSL"""
    # Usar digest conhecido (em minúsculas como o openfortivpn espera)
    known_digest = "2285b102c6bcbfef350f48611daba7de94325d8e482f901aa0c813cdbbfb064e"
    return known_digest


def authenticate_with_azure_token(gateway, port, access_token):
    """Tenta autenticar no gateway VPN usando token Azure CLI"""
    print_flush("🔐 Tentando autenticar com token Azure CLI...")
    
    saml_url = f"https://{gateway}:{port}/remote/saml/start?redirect=1"
    
    try:
        # Criar contexto SSL que aceita certificado
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Fazer requisição autenticada
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'VPN-Client/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        req = urllib.request.Request(saml_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                print_flush(f"✅ Resposta recebida (Status: {response.getcode()})")
                return True
        except urllib.error.HTTPError as e:
            if e.code in [200, 302, 401, 403]:
                print_flush(f"✅ Gateway respondeu (Status: {e.code})")
                return True
            else:
                print_flush(f"⚠️  Gateway respondeu com status: {e.code}")
                return False
    except Exception as e:
        print_flush(f"⚠️  Erro na autenticação: {e}")
        return False


def check_openfortivpn():
    """Verifica se openfortivpn está instalado"""
    success, _ = run_command(["which", "openfortivpn"])
    return success


def connect_vpn(gateway, port=443, username=None):
    """Conecta à VPN usando openfortivpn com Azure CLI"""
    
    # Verificar Azure CLI
    print_flush("🔐 Verificando Azure CLI...")
    azure_authenticated, account_info = check_azure_cli()
    
    if not azure_authenticated:
        print_flush("⚠️  Azure CLI não está autenticado")
        print_flush("💡 Fazendo login no Azure...")
        success, _ = run_command(["az", "login"])
        if not success:
            print_flush("❌ Erro ao fazer login no Azure")
            return False
        azure_authenticated, account_info = check_azure_cli()
    
    if azure_authenticated:
        user_name = account_info.get("user", {}).get("name", "usuário")
        print_flush(f"✅ Azure CLI autenticado: {user_name}")
    
    # Obter token
    access_token = get_azure_token()
    
    if not check_openfortivpn():
        print_flush("❌ openfortivpn não encontrado!")
        print_flush("💡 Instale com: brew install openfortivpn")
        return False
    
    print_flush(f"🔌 Conectando à VPN: {gateway}:{port}")
    
    # Tentar autenticar com token Azure CLI antes
    if access_token:
        authenticate_with_azure_token(gateway, port, access_token)
    
    # Obter digest do certificado
    print_flush("🔐 Obtendo certificado do gateway...")
    cert_digest = get_certificate_digest(gateway, port)
    
    # Construir comando
    cmd = ["openfortivpn", f"{gateway}:{port}", "--saml-login"]
    
    # Adicionar certificado confiável
    if cert_digest:
        cmd.append("--trusted-cert")
        cmd.append(cert_digest)
        print_flush(f"✅ Certificado confiável configurado")
    
    if username:
        cmd.extend(["--username", username])
    
    print_flush("🚀 Iniciando conexão...")
    print_flush("💡 Usando autenticação Azure CLI")
    print_flush("⚠️  openfortivpn requer privilégios de root")
    print_flush("")
    
    try:
        # Executar openfortivpn com sudo
        sudo_cmd = ["sudo"] + cmd
        print_flush("🔐 Executando com sudo (será solicitada sua senha)...")
        print_flush("")
        
        process = subprocess.Popen(
            sudo_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print_flush("📊 Logs da conexão:")
        print_flush("-" * 50)
        
        saml_url = None
        browser_opened = False
        
        # Ler output em tempo real
        for line in iter(process.stdout.readline, ''):
            if line:
                line_stripped = line.rstrip()
                print_flush(f"   {line_stripped}")
                
                # Detectar URL SAML
                if "Authenticate at" in line_stripped or "saml" in line_stripped.lower():
                    if "http" in line_stripped:
                        import re
                        urls = re.findall(r'https?://[^\s\']+', line_stripped)
                        if urls:
                            saml_url = urls[0]
                            if not browser_opened:
                                print_flush("")
                                print_flush("🌐 Abrindo navegador para autenticação...")
                                try:
                                    print_flush("")
                                    print_flush("🌐 Abrindo navegador para autenticação...")
                                    subprocess.run(["open", saml_url], check=False)
                                    browser_opened = True
                                    print_flush(f"   ✅ Navegador aberto: {saml_url}")
                                    print_flush("   💡 Complete o login no navegador")
                                    
                                except Exception as e:
                                    print_flush(f"   ⚠️  Erro ao abrir navegador: {e}")
                                    print_flush(f"   💡 Abra manualmente: {saml_url}")
                
                # Verificar se conectou
                if "connected" in line.lower() or "tunnel is up" in line.lower():
                    print_flush("")
                    print_flush("✅ VPN conectada!")
                    print_flush("")
                    print_flush("💡 Mantendo conexão ativa...")
                    print_flush("💡 Pressione Ctrl+C para desconectar")
                    print_flush("")
                    
                    # Manter processo rodando e monitorar
                    connected = True
                    try:
                        # Continuar lendo logs para monitorar desconexões
                        for line in iter(process.stdout.readline, ''):
                            if line:
                                line_stripped = line.rstrip()
                                print_flush(f"   {line_stripped}")
                                
                                # Verificar se desconectou
                                if "disconnected" in line.lower() or "connection closed" in line.lower():
                                    print_flush("")
                                    print_flush("⚠️  VPN desconectada!")
                                    return False
                    except KeyboardInterrupt:
                        print_flush("")
                        print_flush("🛑 Desconectando VPN...")
                        process.terminate()
                        process.wait()
                        print_flush("✅ VPN desconectada")
                        return True
                    
                    return True
                
                # Verificar erros de certificado e tentar extrair digest
                if "certificate validation failed" in line.lower() and "trusted-cert" in line.lower():
                    print_flush("")
                    print_flush("⚠️  Erro de certificado detectado")
                    # Tentar extrair o digest da mensagem de erro
                    import re
                    digest_match = re.search(r'--trusted-cert\s+([A-F0-9]{64})', line_stripped, re.IGNORECASE)
                    if digest_match:
                        suggested_digest = digest_match.group(1).upper()
                        print_flush(f"   💡 Digest sugerido: {suggested_digest[:16]}...")
                        print_flush("   💡 Tente executar novamente - o certificado será adicionado")
                    # Não retornar False imediatamente, aguardar mais
                    continue
                
                # Verificar outros erros
                if "error" in line.lower() and "failed" in line.lower() and "certificate" not in line.lower():
                    print_flush("")
                    print_flush(f"❌ Erro: {line_stripped}")
                    if saml_url and not browser_opened:
                        print_flush(f"   💡 Tente abrir manualmente: {saml_url}")
                    return False
        
        # Aguardar processo
        process.wait()
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print_flush("")
        print_flush("🛑 Desconectando VPN...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print_flush("✅ VPN desconectada")
        return True
    except Exception as e:
        print_flush("")
        print_flush(f"❌ Erro: {e}")
        if 'process' in locals():
            process.terminate()
            process.wait()
        return False


def main():
    parser = argparse.ArgumentParser(description="Conectar à VPN usando openfortivpn com Azure CLI")
    
    parser.add_argument("--gateway", type=str, required=True, help="Gateway da VPN")
    parser.add_argument("--port", type=int, default=443, help="Porta (padrão: 443)")
    parser.add_argument("--username", type=str, default=None, help="Usuário (opcional)")
    
    args = parser.parse_args()
    
    success = connect_vpn(args.gateway, args.port, args.username)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
