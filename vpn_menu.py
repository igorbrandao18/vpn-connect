#!/usr/bin/env python3
"""
Menu simplificado - Monitora e reconecta VPN automaticamente
"""

import subprocess
import sys
import os
import time
import threading
import re
from datetime import datetime

def clear_screen():
    """Limpa a tela"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    """Imprime cabeçalho"""
    clear_screen()
    print("=" * 70)
    print(" " * 20 + "🔐 VPN AUTO-RECONNECT")
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

def get_vpn_interface():
    """Identifica a interface VPN"""
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        current_interface = None
        for i, line in enumerate(lines):
            match = re.search(r'^([a-z0-9]+):', line)
            if match:
                current_interface = match.group(1)
            
            if current_interface and ('ppp' in current_interface.lower() or 'utun' in current_interface.lower()):
                if i + 1 < len(lines):
                    next_lines = '\n'.join(lines[i:i+5])
                    if 'inet ' in next_lines and '127.0.0.1' not in next_lines:
                        return current_interface
        return None
    except:
        return None

def connect_vpn_process():
    """Conecta à VPN em processo separado"""
    gateway = "dtc.sonepar.com.br"
    port = 443
    script_path = os.path.join(os.path.dirname(__file__), 'connect_vpn.py')
    
    try:
        process = subprocess.Popen(
            [sys.executable, script_path, '--gateway', gateway, '--port', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        return None

def monitor_and_reconnect():
    """Monitora VPN e reconecta automaticamente"""
    print_header()
    print("🔄 Modo Auto-Reconexão Ativado")
    print()
    print("💡 O sistema irá:")
    print("   • Conectar à VPN automaticamente")
    print("   • Monitorar a conexão continuamente")
    print("   • Reconectar se desconectar")
    print()
    print("=" * 70)
    print()
    
    connection_process = None
    last_check = time.time()
    check_interval = 5  # Verificar a cada 5 segundos
    reconnect_delay = 10  # Aguardar 10 segundos antes de reconectar
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            is_connected = check_vpn_connected()
            
            # Verificar se processo de conexão ainda está rodando
            if connection_process:
                if connection_process.poll() is not None:
                    # Processo terminou
                    connection_process = None
            
            # Se não está conectado e não há processo de conexão
            if not is_connected and connection_process is None:
                print(f"[{current_time}] ⚠️  VPN desconectada - Reconectando em {reconnect_delay}s...")
                time.sleep(reconnect_delay)
                
                print(f"[{current_time}] 🔌 Tentando conectar...")
                connection_process = connect_vpn_process()
                
                if connection_process:
                    print(f"[{current_time}] ✅ Processo de conexão iniciado (PID: {connection_process.pid})")
                else:
                    print(f"[{current_time}] ❌ Erro ao iniciar conexão")
            
            # Se está conectado
            elif is_connected:
                # Verificar interface para obter estatísticas
                interface = get_vpn_interface()
                if interface:
                    # Obter estatísticas básicas
                    try:
                        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
                        import re
                        rx_match = re.search(r'RX.*?bytes\s+(\d+)', result.stdout, re.IGNORECASE)
                        tx_match = re.search(r'TX.*?bytes\s+(\d+)', result.stdout, re.IGNORECASE)
                        
                        rx_bytes = int(rx_match.group(1)) if rx_match else 0
                        tx_bytes = int(tx_match.group(1)) if tx_match else 0
                        
                        # Formatar bytes
                        def format_bytes(b):
                            for unit in ['B', 'KB', 'MB', 'GB']:
                                if b < 1024.0:
                                    return f"{b:.2f} {unit}"
                                b /= 1024.0
                            return f"{b:.2f} TB"
                        
                        print(f"[{current_time}] 🟢 VPN Conectada | Interface: {interface}")
                        print(f"   ⬇️  Entrada: {format_bytes(rx_bytes)} | ⬆️  Saída: {format_bytes(tx_bytes)}")
                    except:
                        print(f"[{current_time}] 🟢 VPN Conectada | Interface: {interface}")
                else:
                    print(f"[{current_time}] 🟢 VPN Conectada")
            
            # Aguardar antes da próxima verificação
            time.sleep(check_interval)
            
            # Limpar linha anterior (opcional, para não poluir muito)
            if time.time() - last_check > 30:  # A cada 30 segundos, limpar tela
                print_header()
                print("🔄 Modo Auto-Reconexão Ativado")
                print("=" * 70)
                print()
                last_check = time.time()
    
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("🛑 Encerrando monitoramento...")
        
        # Matar processos de conexão
        if connection_process:
            connection_process.terminate()
        
        # Desconectar VPN
        try:
            subprocess.run(['pkill', '-f', 'openfortivpn'], capture_output=True)
        except:
            pass
        
        print("✅ Encerrado")
        sys.exit(0)

def main():
    """Função principal"""
    print_header()
    print("🔐 VPN Auto-Reconnect")
    print()
    print("Este script irá:")
    print("  • Conectar à VPN automaticamente")
    print("  • Monitorar a conexão continuamente")
    print("  • Reconectar automaticamente se desconectar")
    print()
    print("=" * 70)
    print()
    
    try:
        input("Pressione Enter para iniciar (ou Ctrl+C para sair)...")
        monitor_and_reconnect()
    except KeyboardInterrupt:
        clear_screen()
        print("👋 Até logo!")
        sys.exit(0)

if __name__ == "__main__":
    main()
