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

# Cores ANSI para terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Cores básicas
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Cores brilhantes
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

# Spinners animados
SPINNERS = [
    ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
    ['◐', '◓', '◑', '◒'],
    ['◴', '◷', '◶', '◵'],
    ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
    ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
]

def get_spinner_char(frame, spinner_type=0):
    """Retorna caractere do spinner baseado no frame"""
    spinner = SPINNERS[spinner_type % len(SPINNERS)]
    return spinner[frame % len(spinner)]

def print_animated(text, color=Colors.RESET, end='\n'):
    """Imprime texto com animação"""
    sys.stdout.write(f"{color}{text}{Colors.RESET}{end}")
    sys.stdout.flush()

def animate_spinner(text, duration=2, spinner_type=0):
    """Anima um spinner por um tempo"""
    start_time = time.time()
    frame = 0
    while time.time() - start_time < duration:
        spinner_char = get_spinner_char(frame, spinner_type)
        sys.stdout.write(f'\r{spinner_char} {text}')
        sys.stdout.flush()
        time.sleep(0.1)
        frame += 1
    sys.stdout.write('\r' + ' ' * (len(text) + 3) + '\r')
    sys.stdout.flush()

def clear_screen():
    """Limpa a tela"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    """Imprime cabeçalho com animação"""
    clear_screen()
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
    title = "🔐 VPN AUTO-RECONNECT"
    padding = (70 - len(title)) // 2
    print(" " * padding + Colors.BOLD + Colors.BRIGHT_GREEN + title + Colors.RESET)
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
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
    print(Colors.BRIGHT_YELLOW + "🔄 Modo Auto-Reconexão Ativado" + Colors.RESET)
    print()
    print(Colors.BRIGHT_BLUE + "💡 O sistema irá:" + Colors.RESET)
    print(Colors.CYAN + "   • Conectar à VPN automaticamente" + Colors.RESET)
    print(Colors.CYAN + "   • Monitorar a conexão continuamente" + Colors.RESET)
    print(Colors.CYAN + "   • Reconectar se desconectar" + Colors.RESET)
    print()
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
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
                print(Colors.BRIGHT_RED + f"[{current_time}] ⚠️  VPN desconectada" + Colors.RESET)
                
                # Animação de contagem regressiva
                for remaining in range(reconnect_delay, 0, -1):
                    spinner = get_spinner_char(int(time.time() * 10) % 8, 1)
                    sys.stdout.write(f'\r{Colors.BRIGHT_YELLOW}{spinner} Reconectando em {remaining}s...{Colors.RESET}')
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write('\r' + ' ' * 50 + '\r')
                sys.stdout.flush()
                
                print(Colors.BRIGHT_BLUE + f"[{current_time}] 🔌 Tentando conectar..." + Colors.RESET)
                animate_spinner("Iniciando conexão", 1, 2)
                
                connection_process = connect_vpn_process()
                
                if connection_process:
                    print(Colors.BRIGHT_GREEN + f"[{current_time}] ✅ Processo de conexão iniciado (PID: {connection_process.pid})" + Colors.RESET)
                else:
                    print(Colors.BRIGHT_RED + f"[{current_time}] ❌ Erro ao iniciar conexão" + Colors.RESET)
            
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
                        
                        # Animação de status conectado
                        spinner = get_spinner_char(int(time.time() * 5) % 8, 0)
                        status_indicator = Colors.BRIGHT_GREEN + "🟢" + Colors.RESET
                        
                        # Barra de progresso visual para tráfego
                        def get_traffic_bar(value, max_value=1000000000, width=20):
                            if max_value == 0:
                                return "░" * width
                            filled = min(int((value / max_value) * width), width)
                            bar = Colors.BRIGHT_GREEN + "█" * filled + Colors.DIM + "░" * (width - filled) + Colors.RESET
                            return bar
                        
                        # Calcular porcentagem de uso (estimativa)
                        max_traffic = max(rx_bytes, tx_bytes, 1)
                        rx_bar = get_traffic_bar(rx_bytes, max_traffic * 1.2, 15)
                        tx_bar = get_traffic_bar(tx_bytes, max_traffic * 1.2, 15)
                        
                        print(f"{Colors.BRIGHT_GREEN}[{current_time}] {spinner} VPN Conectada{Colors.RESET} | {Colors.CYAN}Interface: {interface}{Colors.RESET}")
                        print(f"   {Colors.BRIGHT_BLUE}⬇️  Entrada:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(rx_bytes):>12}{Colors.RESET} {rx_bar}")
                        print(f"   {Colors.BRIGHT_MAGENTA}⬆️  Saída:{Colors.RESET}   {Colors.BRIGHT_GREEN}{format_bytes(tx_bytes):>12}{Colors.RESET} {tx_bar}")
                    else:
                        spinner = get_spinner_char(int(time.time() * 5) % 8, 0)
                        print(f"{Colors.BRIGHT_GREEN}[{current_time}] {spinner} VPN Conectada{Colors.RESET} | {Colors.CYAN}Interface: {interface}{Colors.RESET}")
                        print(f"   {Colors.BRIGHT_YELLOW}⚠️  Estatísticas não disponíveis{Colors.RESET}")
                else:
                    spinner = get_spinner_char(int(time.time() * 5) % 8, 0)
                    print(f"{Colors.BRIGHT_GREEN}[{current_time}] {spinner} VPN Conectada{Colors.RESET}")
            
            # Aguardar antes da próxima verificação
            time.sleep(check_interval)
            
            # Limpar linha anterior (opcional, para não poluir muito)
            if time.time() - last_check > 30:  # A cada 30 segundos, limpar tela
                print_header()
                print(Colors.BRIGHT_YELLOW + "🔄 Modo Auto-Reconexão Ativado" + Colors.RESET)
                print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
                print()
                last_check = time.time()
    
    except KeyboardInterrupt:
        print()
        print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
        print(Colors.BRIGHT_YELLOW + "🛑 Encerrando monitoramento..." + Colors.RESET)
        
        # Animação de encerramento
        animate_spinner("Desconectando", 1, 1)
        
        # Matar processos de conexão
        if connection_process:
            connection_process.terminate()
        
        # Desconectar VPN
        try:
            subprocess.run(['pkill', '-f', 'openfortivpn'], capture_output=True)
        except:
            pass
        
        print(Colors.BRIGHT_GREEN + "✅ Encerrado" + Colors.RESET)
        sys.exit(0)

def main():
    """Função principal"""
    print_header()
    print(Colors.BOLD + Colors.BRIGHT_GREEN + "🔐 VPN Auto-Reconnect" + Colors.RESET)
    print()
    print(Colors.BRIGHT_BLUE + "Este script irá:" + Colors.RESET)
    print(Colors.CYAN + "  • Conectar à VPN automaticamente" + Colors.RESET)
    print(Colors.CYAN + "  • Monitorar a conexão continuamente" + Colors.RESET)
    print(Colors.CYAN + "  • Reconectar automaticamente se desconectar" + Colors.RESET)
    print()
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
    print()
    
    try:
        print(Colors.BRIGHT_YELLOW + "💡 Pressione Enter para iniciar (ou Ctrl+C para sair)..." + Colors.RESET)
        input()
        
        # Animação de inicialização
        print()
        animate_spinner("Inicializando sistema", 1.5, 0)
        print()
        
        monitor_and_reconnect()
    except KeyboardInterrupt:
        clear_screen()
        print(Colors.BRIGHT_CYAN + "👋 Até logo!" + Colors.RESET)
        sys.exit(0)

if __name__ == "__main__":
    main()
