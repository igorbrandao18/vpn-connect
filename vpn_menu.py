#!/usr/bin/env python3
"""
Menu interativo para gerenciar VPN
"""

import subprocess
import sys
import os
import time
import threading
from datetime import datetime

def clear_screen():
    """Limpa a tela"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    """Imprime cabeçalho do menu"""
    clear_screen()
    print("=" * 70)
    print(" " * 25 + "🔐 VPN MANAGER")
    print("=" * 70)
    print()

def check_vpn_connected():
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
    except:
        return False

def get_vpn_status():
    """Obtém status detalhado da VPN"""
    try:
        # Verificar processos
        result = subprocess.run(['pgrep', '-f', 'openfortivpn'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return f"🟢 Conectada (PID: {', '.join(pids)})"
        
        # Verificar scutil
        result = subprocess.run(['scutil', '--nc', 'list'], capture_output=True, text=True)
        if 'Connected' in result.stdout:
            return "🟢 Conectada"
        
        return "🔴 Desconectada"
    except:
        return "❓ Desconhecido"

def connect_vpn():
    """Conecta à VPN"""
    print_header()
    print("🔌 Conectando à VPN...")
    print()
    
    gateway = "dtc.sonepar.com.br"
    port = 443
    
    print(f"Gateway: {gateway}:{port}")
    print()
    
    # Verificar se já está conectada
    if check_vpn_connected():
        print("⚠️  VPN já está conectada!")
        input("\nPressione Enter para voltar ao menu...")
        return
    
    # Executar script de conexão em background
    script_path = os.path.join(os.path.dirname(__file__), 'connect_vpn.py')
    
    print("💡 Executando conexão...")
    print("💡 O processo será executado em background")
    print("💡 Use o monitor para acompanhar o status")
    print()
    
    try:
        # Executar em background
        process = subprocess.Popen(
            [sys.executable, script_path, '--gateway', gateway, '--port', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ Processo iniciado (PID: {process.pid})")
        print("💡 A conexão está sendo estabelecida...")
        print("💡 Aguarde alguns segundos e verifique o status")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
    
    input("\nPressione Enter para voltar ao menu...")

def disconnect_vpn():
    """Desconecta a VPN"""
    print_header()
    print("🛑 Desconectando VPN...")
    print()
    
    if not check_vpn_connected():
        print("⚠️  VPN não está conectada!")
        input("\nPressione Enter para voltar ao menu...")
        return
    
    try:
        # Matar processos openfortivpn
        result = subprocess.run(['pkill', '-f', 'openfortivpn'], capture_output=True)
        
        if result.returncode == 0:
            print("✅ Processos openfortivpn finalizados")
        else:
            print("⚠️  Nenhum processo openfortivpn encontrado")
        
        # Tentar desconectar via scutil
        result = subprocess.run(['scutil', '--nc', 'list'], capture_output=True, text=True)
        if 'Connected' in result.stdout:
            # Extrair nome da VPN e desconectar
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Connected' in line:
                    # Tentar extrair nome
                    parts = line.split()
                    if parts:
                        vpn_name = parts[0].strip('*').strip()
                        subprocess.run(['scutil', '--nc', 'stop', vpn_name], capture_output=True)
                        print(f"✅ VPN '{vpn_name}' desconectada")
        
        time.sleep(1)
        
        if check_vpn_connected():
            print("⚠️  Ainda há processos VPN ativos")
        else:
            print("✅ VPN desconectada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao desconectar: {e}")
    
    input("\nPressione Enter para voltar ao menu...")

def monitor_vpn():
    """Abre o monitor de tráfego"""
    print_header()
    print("📊 Abrindo monitor de tráfego...")
    print()
    
    script_path = os.path.join(os.path.dirname(__file__), 'monitor_vpn.py')
    
    try:
        # Executar monitor
        subprocess.run([sys.executable, script_path])
    except KeyboardInterrupt:
        print("\n🛑 Monitor encerrado")
    except Exception as e:
        print(f"❌ Erro ao abrir monitor: {e}")
        input("\nPressione Enter para voltar ao menu...")

def show_status():
    """Mostra status detalhado da VPN"""
    print_header()
    print("📊 Status da VPN")
    print("-" * 70)
    print()
    
    status = get_vpn_status()
    print(f"Status: {status}")
    print()
    
    # Verificar processos
    try:
        result = subprocess.run(['pgrep', '-fl', 'openfortivpn'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Processos ativos:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"  • {line}")
        else:
            print("Nenhum processo openfortivpn encontrado")
    except:
        pass
    
    print()
    
    # Verificar interfaces de rede
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        vpn_interfaces = []
        for line in result.stdout.split('\n'):
            if 'ppp' in line.lower() or 'utun' in line.lower():
                match = line.split(':')
                if match:
                    interface = match[0]
                    if interface not in vpn_interfaces:
                        vpn_interfaces.append(interface)
        
        if vpn_interfaces:
            print("Interfaces VPN:")
            for interface in vpn_interfaces:
                print(f"  • {interface}")
        else:
            print("Nenhuma interface VPN encontrada")
    except:
        pass
    
    print()
    
    # Verificar conexões de rede
    try:
        result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True)
        if 'ppp' in result.stdout or 'utun' in result.stdout:
            print("Rotas VPN ativas: Sim")
        else:
            print("Rotas VPN ativas: Não")
    except:
        pass
    
    print()
    input("Pressione Enter para voltar ao menu...")

def show_menu():
    """Mostra o menu principal"""
    print_header()
    
    status = get_vpn_status()
    print(f"Status atual: {status}")
    print()
    print("-" * 70)
    print()
    print("Opções disponíveis:")
    print()
    print("  1. 🔌 Conectar à VPN")
    print("  2. 🛑 Desconectar VPN")
    print("  3. 📊 Monitorar Tráfego")
    print("  4. 📈 Ver Status Detalhado")
    print("  5. ❌ Sair")
    print()
    print("-" * 70)
    print()

def main():
    """Função principal"""
    while True:
        show_menu()
        
        try:
            choice = input("Escolha uma opção (1-5): ").strip()
            
            if choice == '1':
                connect_vpn()
            elif choice == '2':
                disconnect_vpn()
            elif choice == '3':
                monitor_vpn()
            elif choice == '4':
                show_status()
            elif choice == '5':
                clear_screen()
                print("👋 Até logo!")
                sys.exit(0)
            else:
                print("\n❌ Opção inválida! Tente novamente.")
                time.sleep(1)
        
        except KeyboardInterrupt:
            clear_screen()
            print("\n👋 Até logo!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            input("Pressione Enter para continuar...")

if __name__ == "__main__":
    main()

