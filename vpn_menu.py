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
        # Verificar processos openfortivpn primeiro
        result = subprocess.run(['pgrep', '-f', 'openfortivpn'], capture_output=True, text=True)
        if result.returncode == 0:
            # openfortivpn está rodando, procurar interface
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            # Procurar por interfaces ppp ou utun
            current_interface = None
            for i, line in enumerate(lines):
                # Detectar início de interface
                match = re.search(r'^([a-z0-9]+):', line)
                if match:
                    current_interface = match.group(1)
                
                # Verificar se é interface VPN e tem IP
                if current_interface and ('ppp' in current_interface.lower() or 'utun' in current_interface.lower()):
                    # Verificar se tem IP atribuído
                    if i + 1 < len(lines):
                        next_lines = '\n'.join(lines[i:i+5])
                        if 'inet ' in next_lines:
                            # Verificar se não é loopback
                            if '127.0.0.1' not in next_lines:
                                return current_interface
        
        # Tentar encontrar por IP específico da VPN (192.168.50.x ou 10.x.x.x)
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        current_interface = None
        
        for i, line in enumerate(lines):
            match = re.search(r'^([a-z0-9]+):', line)
            if match:
                current_interface = match.group(1)
            
            if current_interface:
                # Verificar se tem IP da VPN
                if i + 1 < len(lines):
                    next_lines = '\n'.join(lines[i:i+5])
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', next_lines)
                    if ip_match:
                        ip = ip_match.group(1)
                        # Verificar se é IP da VPN (192.168.50.x ou 10.x.x.x)
                        if ip.startswith('192.168.50.') or ip.startswith('10.'):
                            if 'ppp' in current_interface.lower() or 'utun' in current_interface.lower():
                                return current_interface
        
        # Última tentativa: procurar qualquer interface ppp/utun com IP
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if re.match(r'^(ppp\d+|utun\d+):', line):
                interface = re.match(r'^(ppp\d+|utun\d+):', line).group(1)
                # Verificar se tem IP
                ifconfig_result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
                if 'inet ' in ifconfig_result.stdout and '127.0.0.1' not in ifconfig_result.stdout:
                    return interface
        
        return None
    except Exception as e:
        return None

def get_interface_stats(interface):
    """Obtém estatísticas de tráfego de uma interface"""
    try:
        # Primeiro tentar ifconfig (funciona para a maioria das interfaces)
        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
        if result.returncode == 0:
            # Extrair bytes recebidos e enviados
            rx_bytes = 0
            tx_bytes = 0
            
            # Padrão macOS: "RX packets 1234 bytes 567890"
            rx_match = re.search(r'RX.*?bytes\s+(\d+)', result.stdout, re.IGNORECASE)
            tx_match = re.search(r'TX.*?bytes\s+(\d+)', result.stdout, re.IGNORECASE)
            
            if rx_match:
                rx_bytes = int(rx_match.group(1))
            if tx_match:
                tx_bytes = int(tx_match.group(1))
            
            # Tentar formato alternativo (linhas separadas)
            if rx_bytes == 0 or tx_bytes == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'RX' in line.upper() and 'bytes' in line.lower():
                        match = re.search(r'(\d+)\s+bytes', line)
                        if match:
                            rx_bytes = int(match.group(1))
                    if 'TX' in line.upper() and 'bytes' in line.lower():
                        match = re.search(r'(\d+)\s+bytes', line)
                        if match:
                            tx_bytes = int(match.group(1))
            
            # Se encontrou estatísticas no ifconfig, retornar
            if rx_bytes > 0 or tx_bytes > 0:
                return {'rx': rx_bytes, 'tx': tx_bytes}
        
        # Para interfaces PPP, ifconfig não mostra bytes, usar netstat
        # Formato netstat -ibn: Interface MTU Network Address Ipkts Ierrs Opkts Oerrs Coll
        result = subprocess.run(['netstat', '-ibn'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                # Procurar linha da interface (pode ter espaços antes)
                if re.match(rf'^\s*{re.escape(interface)}\s+', line):
                    parts = line.split()
                    if len(parts) >= 7:
                        try:
                            # Obter MTU da interface
                            mtu = int(parts[1]) if len(parts) > 1 else 1500
                            # Ipkts (packets recebidos - índice 4) e Opkts (packets enviados - índice 6)
                            ipkts = int(parts[4]) if len(parts) > 4 else 0
                            opkts = int(parts[6]) if len(parts) > 6 else 0
                            
                            # Estimar bytes usando MTU da interface (mais preciso)
                            # Usar 80% do MTU como média (considerando overhead)
                            avg_packet_size = int(mtu * 0.8)
                            rx_bytes = ipkts * avg_packet_size
                            tx_bytes = opkts * avg_packet_size
                            
                            return {'rx': rx_bytes, 'tx': tx_bytes}
                        except (ValueError, IndexError) as e:
                            continue
        
        return None
    except Exception as e:
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
                    stats = get_interface_stats(interface)
                    if stats:
                        rx_bytes = stats['rx']
                        tx_bytes = stats['tx']
                        
                        # Formatar bytes
                        def format_bytes(b):
                            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                                if b < 1024.0:
                                    return f"{b:.2f} {unit}"
                                b /= 1024.0
                            return f"{b:.2f} PB"
                        
                        print(f"[{current_time}] 🟢 VPN Conectada | Interface: {interface}")
                        print(f"   ⬇️  Entrada: {format_bytes(rx_bytes)} | ⬆️  Saída: {format_bytes(tx_bytes)}")
                    else:
                        print(f"[{current_time}] 🟢 VPN Conectada | Interface: {interface}")
                        print(f"   ⚠️  Estatísticas não disponíveis")
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
