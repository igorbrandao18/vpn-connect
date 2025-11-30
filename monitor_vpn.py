#!/usr/bin/env python3
"""
Painel de monitoramento de tráfego VPN
Mostra estatísticas de entrada e saída em tempo real
"""

import subprocess
import time
import os
import sys
import re
from datetime import datetime

def clear_screen():
    """Limpa a tela"""
    os.system('clear' if os.name != 'nt' else 'cls')

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
        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        
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
        
        return {'rx': rx_bytes, 'tx': tx_bytes}
    except Exception as e:
        return None

def format_bytes(bytes_value):
    """Formata bytes em formato legível"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_speed(bytes_per_sec):
    """Formata velocidade em formato legível"""
    return format_bytes(bytes_per_sec) + "/s"

def get_vpn_status():
    """Verifica status da VPN"""
    try:
        # Verificar processos openfortivpn
        result = subprocess.run(['pgrep', '-f', 'openfortivpn'], capture_output=True)
        if result.returncode == 0:
            return "🟢 Conectada"
        
        # Verificar scutil
        result = subprocess.run(['scutil', '--nc', 'list'], capture_output=True, text=True)
        if 'Connected' in result.stdout:
            return "🟢 Conectada"
        
        return "🔴 Desconectada"
    except:
        return "❓ Desconhecido"

def get_vpn_ip():
    """Obtém IP da VPN"""
    try:
        interface = get_vpn_interface()
        if not interface:
            return "N/A"
        
        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
        match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        if match:
            return match.group(1)
        return "N/A"
    except:
        return "N/A"

def draw_bar(value, max_value, width=30):
    """Desenha uma barra de progresso"""
    if max_value == 0:
        return "█" * width
    
    filled = int((value / max_value) * width)
    filled = min(filled, width)
    return "█" * filled + "░" * (width - filled)

def main():
    print("🔍 Procurando interface VPN...")
    
    interface = None
    retry_count = 0
    max_retries = 5
    
    # Tentar encontrar interface com retry
    while not interface and retry_count < max_retries:
        interface = get_vpn_interface()
        if not interface:
            retry_count += 1
            if retry_count < max_retries:
                print(f"   Tentativa {retry_count}/{max_retries}...")
                time.sleep(1)
    
    if not interface:
        print("❌ Interface VPN não encontrada!")
        print("💡 Certifique-se de que a VPN está conectada")
        print("💡 Execute: python3 connect_vpn.py --gateway dtc.sonepar.com.br")
        print()
        print("🔄 Tentando novamente a cada 5 segundos...")
        print("   Pressione Ctrl+C para sair")
        print()
        
        # Tentar novamente periodicamente
        while True:
            time.sleep(5)
            interface = get_vpn_interface()
            if interface:
                print(f"✅ Interface encontrada: {interface}")
                break
            print("   ⏳ Aguardando conexão VPN...")
    
    if interface:
        print(f"✅ Interface encontrada: {interface}")
        print("📊 Iniciando monitoramento...")
        time.sleep(1)
    
    last_stats = None
    last_time = time.time()
    
    try:
        while True:
            clear_screen()
            
            # Cabeçalho
            print("=" * 70)
            print(" " * 20 + "🔐 PAINEL DE MONITORAMENTO VPN")
            print("=" * 70)
            print()
            
            # Status
            status = get_vpn_status()
            vpn_ip = get_vpn_ip()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"Status: {status} | IP VPN: {vpn_ip} | Interface: {interface}")
            print(f"Horário: {current_time}")
            print("-" * 70)
            print()
            
            # Obter estatísticas atuais
            stats = get_interface_stats(interface)
            
            if stats:
                rx_bytes = stats['rx']
                tx_bytes = stats['tx']
                
                # Calcular velocidade
                current_time_sec = time.time()
                if last_stats:
                    time_diff = current_time_sec - last_time
                    if time_diff > 0:
                        rx_speed = (rx_bytes - last_stats['rx']) / time_diff
                        tx_speed = (tx_bytes - last_stats['tx']) / time_diff
                    else:
                        rx_speed = 0
                        tx_speed = 0
                else:
                    rx_speed = 0
                    tx_speed = 0
                
                # Exibir estatísticas de entrada
                print("⬇️  ENTRADA (Download)")
                print(f"   Total: {format_bytes(rx_bytes)}")
                print(f"   Velocidade: {format_speed(rx_speed)}")
                
                # Barra de velocidade de entrada
                max_speed = max(rx_speed, 1)  # Evitar divisão por zero
                bar_rx = draw_bar(rx_speed, max_speed * 1.2, 50)
                print(f"   [{bar_rx}]")
                print()
                
                # Exibir estatísticas de saída
                print("⬆️  SAÍDA (Upload)")
                print(f"   Total: {format_bytes(tx_bytes)}")
                print(f"   Velocidade: {format_speed(tx_speed)}")
                
                # Barra de velocidade de saída
                max_speed = max(tx_speed, 1)
                bar_tx = draw_bar(tx_speed, max_speed * 1.2, 50)
                print(f"   [{bar_tx}]")
                print()
                
                # Estatísticas combinadas
                total_bytes = rx_bytes + tx_bytes
                total_speed = rx_speed + tx_speed
                
                print("📈 RESUMO")
                print(f"   Total Transferido: {format_bytes(total_bytes)}")
                print(f"   Velocidade Total: {format_speed(total_speed)}")
                print()
                
                # Atualizar para próxima iteração
                last_stats = {'rx': rx_bytes, 'tx': tx_bytes}
                last_time = current_time_sec
            else:
                print("⚠️  Não foi possível obter estatísticas")
                print("💡 Verificando conexão...")
            
            print("-" * 70)
            print("💡 Pressione Ctrl+C para sair")
            
            time.sleep(1)  # Atualizar a cada segundo
            
    except KeyboardInterrupt:
        clear_screen()
        print("🛑 Monitoramento encerrado")
        sys.exit(0)

if __name__ == "__main__":
    main()

