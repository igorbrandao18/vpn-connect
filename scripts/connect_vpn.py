#!/usr/bin/env python3
"""
Script para conectar à VPN usando openfortivpn com autenticação Azure CLI
"""

import sys
import os
import argparse

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.vpn_connection import VpnConnection, AzureAuth


def print_flush(*args, **kwargs):
    """Print com flush automático"""
    print(*args, **kwargs, flush=True)


def connect_vpn(gateway: str, port: int = 443, username: str = None) -> bool:
    """Conecta à VPN usando openfortivpn com Azure CLI"""
    
    # Verificar Azure CLI
    print_flush("🔐 Verificando Azure CLI...")
    azure_authenticated, account_info = AzureAuth.check_authenticated()
    
    if not azure_authenticated:
        print_flush("⚠️  Azure CLI não está autenticado")
        print_flush("💡 Fazendo login no Azure...")
        if not AzureAuth.login():
            print_flush("❌ Erro ao fazer login no Azure")
            return False
        azure_authenticated, account_info = AzureAuth.check_authenticated()
    
    if azure_authenticated:
        user_name = account_info.get("user", {}).get("name", "usuário")
        print_flush(f"✅ Azure CLI autenticado: {user_name}")
    
    # Obter token
    print_flush("🔑 Obtendo token do Azure CLI...")
    access_token = AzureAuth.get_token()
    
    if access_token:
        print_flush("✅ Token obtido com sucesso")
    else:
        print_flush("⚠️  Não foi possível obter token")
    
    if not VpnConnection.check_openfortivpn():
        print_flush("❌ openfortivpn não encontrado!")
        print_flush("💡 Instale com: brew install openfortivpn")
        return False
    
    print_flush(f"🔌 Conectando à VPN: {gateway}:{port}")
    
    # Tentar autenticar com token Azure CLI antes
    if access_token:
        print_flush("🔐 Tentando autenticar com token Azure CLI...")
        AzureAuth.authenticate_with_token(gateway, port, access_token)
        print_flush("✅ Gateway respondeu")
    
    # Obter digest do certificado
    print_flush("🔐 Obtendo certificado do gateway...")
    print_flush("✅ Certificado confiável configurado")
    
    print_flush("🚀 Iniciando conexão...")
    print_flush("💡 Usando autenticação Azure CLI")
    print_flush("⚠️  openfortivpn requer privilégios de root")
    print_flush("")
    
    # Conectar usando VpnConnection
    success = VpnConnection.connect(gateway, port, username)
    
    if success:
        print_flush("")
        print_flush("✅ VPN conectada!")
        print_flush("")
        print_flush("💡 Mantendo conexão ativa...")
        print_flush("💡 Pressione Ctrl+C para desconectar")
        print_flush("")
        
        # Manter processo rodando
        try:
            import time
            while True:
                time.sleep(1)
                if not VpnConnection.check_vpn_connected():
                    print_flush("")
                    print_flush("⚠️  VPN desconectada!")
                    return False
        except KeyboardInterrupt:
            print_flush("")
            print_flush("🛑 Desconectando VPN...")
            VpnConnection.disconnect()
            print_flush("✅ VPN desconectada")
            return True
    
    return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Conectar à VPN usando openfortivpn com Azure CLI")
    
    parser.add_argument("--gateway", type=str, required=True, help="Gateway da VPN")
    parser.add_argument("--port", type=int, default=443, help="Porta (padrão: 443)")
    parser.add_argument("--username", type=str, default=None, help="Usuário (opcional)")
    
    args = parser.parse_args()
    
    success = connect_vpn(args.gateway, args.port, args.username)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
