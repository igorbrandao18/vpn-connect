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
                # Procurar linha da interface que começa com o nome (primeira linha, não a segunda com IP)
                if re.match(rf'^{re.escape(interface)}\s+', line) and '<Link#' in line:
                    # Dividir por espaços múltiplos para pegar os campos corretos
                    parts = re.split(r'\s+', line.strip())
                    if len(parts) >= 10:
                        try:
                            # Obter MTU da interface (segundo campo)
                            mtu = int(parts[1]) if len(parts) > 1 else 1500
                            
                            # Encontrar Ipkts e Opkts - podem estar em posições diferentes
                            # Formato: Interface MTU Network Ipkts Ierrs Opkts Oerrs Coll
                            # Mas pode ter campos vazios, então vamos procurar pelos números
                            
                            # Procurar por padrão: após Network (<Link#XX>), vem Ipkts
                            # Vamos procurar pelos campos numéricos na ordem correta
                            ipkts = 0
                            opkts = 0
                            
                            # Formato real do netstat -ibn:
                            # Name Mtu Network Address Ipkts Ierrs Ibytes Opkts Oerrs Obytes Coll
                            # ppp0 1354 <Link#24> 3021 0 4008237 1606 0 90405 0
                            # [0]  [1]  [2]       [3]  [4][5]    [6]  [7][8]   [9]
                            # Interface MTU Network Address Ipkts Ierrs Ibytes Opkts Oerrs Obytes Coll
                            # IMPORTANTE: O netstat mostra BYTES diretamente!
                            # Ibytes (bytes recebidos) está em parts[5]
                            # Obytes (bytes enviados) está em parts[8]
                            rx_bytes = int(parts[5]) if len(parts) > 5 else 0  # Ibytes (BYTES recebidos)
                            tx_bytes = int(parts[8]) if len(parts) > 8 else 0  # Obytes (BYTES enviados)
                            
                            # Retornar mesmo se um for 0 (pode ser que realmente não tenha recebido nada ainda)
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
    
    # Contador de linhas para controle de atualização
    lines_written = 0
    
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
                        
                        # Obter largura do terminal (padrão 70 se não conseguir)
                        try:
                            terminal_width = os.get_terminal_size().columns - 2
                        except:
                            terminal_width = 68
                        
                        # Barra de progresso animada que "percorre"
                        def get_animated_bar(frame, width):
                            """Cria uma barra animada que percorre"""
                            bar_width = width - 20  # Deixar espaço para texto
                            pos = frame % (bar_width * 2)
                            
                            if pos < bar_width:
                                # Barra crescendo da esquerda
                                filled = pos
                                empty = bar_width - pos
                            else:
                                # Barra diminuindo pela direita
                                filled = (bar_width * 2) - pos
                                empty = bar_width - filled
                            
                            # Criar barra com gradiente
                            bar = ""
                            for i in range(bar_width):
                                if i < filled:
                                    # Gradiente de cores
                                    if i < filled * 0.3:
                                        bar += Colors.BRIGHT_GREEN + "█"
                                    elif i < filled * 0.6:
                                        bar += Colors.GREEN + "█"
                                    else:
                                        bar += Colors.BRIGHT_CYAN + "█"
                                else:
                                    bar += Colors.DIM + "░"
                            
                            return bar + Colors.RESET
                        
                        # Frame para animação (baseado no tempo)
                        animation_frame = int(time.time() * 10) % (terminal_width * 2)
                        
                        # Calcular velocidade (comparar com última leitura)
                        if not hasattr(monitor_and_reconnect, 'last_rx_bytes'):
                            monitor_and_reconnect.last_rx_bytes = rx_bytes
                            monitor_and_reconnect.last_tx_bytes = tx_bytes
                            monitor_and_reconnect.last_time = time.time()
                            monitor_and_reconnect.connection_start_time = time.time()
                        
                        current_time_sec = time.time()
                        time_diff = current_time_sec - monitor_and_reconnect.last_time
                        
                        if time_diff > 0:
                            rx_speed = (rx_bytes - monitor_and_reconnect.last_rx_bytes) / time_diff
                            tx_speed = (tx_bytes - monitor_and_reconnect.last_tx_bytes) / time_diff
                        else:
                            rx_speed = 0
                            tx_speed = 0
                        
                        monitor_and_reconnect.last_rx_bytes = rx_bytes
                        monitor_and_reconnect.last_tx_bytes = tx_bytes
                        monitor_and_reconnect.last_time = current_time_sec
                        
                        def format_speed(bps):
                            return format_bytes(bps) + "/s"
                        
                        # Obter IP da VPN
                        try:
                            result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
                            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                            vpn_ip = ip_match.group(1) if ip_match else "N/A"
                        except:
                            vpn_ip = "N/A"
                        
                        # Obter MTU e outros dados do netstat
                        try:
                            result = subprocess.run(['netstat', '-ibn'], capture_output=True, text=True)
                            for line in result.stdout.split('\n'):
                                if re.match(rf'^{re.escape(interface)}\s+', line) and '<Link#' in line:
                                    parts = re.split(r'\s+', line.strip())
                                    mtu = parts[1] if len(parts) > 1 else "N/A"
                                    ipkts = int(parts[4]) if len(parts) > 4 else 0
                                    opkts = int(parts[6]) if len(parts) > 6 else 0
                                    break
                            else:
                                mtu = "N/A"
                                ipkts = 0
                                opkts = 0
                        except:
                            mtu = "N/A"
                            ipkts = 0
                            opkts = 0
                        
                        # Calcular tempo de conexão
                        uptime_seconds = int(current_time_sec - monitor_and_reconnect.connection_start_time)
                        uptime_hours = uptime_seconds // 3600
                        uptime_minutes = (uptime_seconds % 3600) // 60
                        uptime_secs = uptime_seconds % 60
                        
                        # Calcular porcentagens e estatísticas
                        total_bytes = rx_bytes + tx_bytes
                        rx_percent = (rx_bytes / total_bytes * 100) if total_bytes > 0 else 0
                        tx_percent = (tx_bytes / total_bytes * 100) if total_bytes > 0 else 0
                        avg_speed = (rx_speed + tx_speed) / 2 if (rx_speed + tx_speed) > 0 else 0
                        
                        # Barra melhorada que combina animação com valor real
                        def get_enhanced_bar(frame, width, value=0, max_value=1000000000):
                            """Barra que combina animação com valor real"""
                            bar_width = min(width, 50)
                            pos = frame % (bar_width * 2)
                            
                            # Preenchimento baseado no valor
                            if max_value > 0 and value > 0:
                                filled_by_value = min(int((value / max_value) * bar_width), bar_width)
                            else:
                                filled_by_value = 0
                            
                            # Combinar animação com valor
                            if pos < bar_width:
                                filled = max(pos, filled_by_value)
                            else:
                                filled = max((bar_width * 2) - pos, filled_by_value)
                            
                            filled = min(filled, bar_width)
                            
                            # Criar barra com gradiente
                            bar = ""
                            for i in range(bar_width):
                                if i < filled:
                                    ratio = i / bar_width if bar_width > 0 else 0
                                    if ratio < 0.3:
                                        bar += Colors.BRIGHT_GREEN + "█"
                                    elif ratio < 0.6:
                                        bar += Colors.GREEN + "█"
                                    elif ratio < 0.8:
                                        bar += Colors.BRIGHT_CYAN + "█"
                                    else:
                                        bar += Colors.BRIGHT_BLUE + "█"
                                else:
                                    bar += Colors.DIM + "░"
                            
                            return bar + Colors.RESET
                        
                        # Exibir dashboard completo (criando linhas novas)
                        print()
                        print(Colors.BRIGHT_CYAN + "╔" + "═" * (terminal_width - 2) + "╗" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f" {Colors.BRIGHT_GREEN}{spinner} VPN Status{Colors.RESET} " + 
                              f"{Colors.DIM}|{Colors.RESET} {Colors.CYAN}{current_time}{Colors.RESET} " +
                              f"{Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_YELLOW}Uptime: {uptime_hours:02d}:{uptime_minutes:02d}:{uptime_secs:02d}{Colors.RESET}" +
                              " " * (terminal_width - 50) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "╠" + "═" * (terminal_width - 2) + "╣" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f" {Colors.BOLD}Interface:{Colors.RESET} {Colors.CYAN}{interface:<15}{Colors.RESET} " +
                              f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}IP:{Colors.RESET} {Colors.CYAN}{vpn_ip:<15}{Colors.RESET} " +
                              f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}MTU:{Colors.RESET} {Colors.CYAN}{mtu}{Colors.RESET}" +
                              " " * (terminal_width - 60) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "╠" + "─" * (terminal_width - 2) + "╣" + Colors.RESET)
                        print()
                        
                        # Estatísticas de entrada
                        print(f"  {Colors.BRIGHT_BLUE}⬇️  ENTRADA (Download){Colors.RESET}")
                        print(f"     {Colors.BOLD}Total:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(rx_bytes):>15}{Colors.RESET} " +
                              f"{Colors.DIM}({rx_percent:.1f}% do total){Colors.RESET}")
                        print(f"     {Colors.BOLD}Velocidade:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_speed(rx_speed):>15}{Colors.RESET}")
                        print(f"     {Colors.BOLD}Packets:{Colors.RESET} {Colors.CYAN}{ipkts:,}{Colors.RESET}")
                        rx_bar = get_enhanced_bar(animation_frame, terminal_width - 10, rx_bytes, max(rx_bytes, tx_bytes, 1))
                        print(f"     {rx_bar}")
                        print()
                        
                        # Estatísticas de saída
                        print(f"  {Colors.BRIGHT_MAGENTA}⬆️  SAÍDA (Upload){Colors.RESET}")
                        print(f"     {Colors.BOLD}Total:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(tx_bytes):>15}{Colors.RESET} " +
                              f"{Colors.DIM}({tx_percent:.1f}% do total){Colors.RESET}")
                        print(f"     {Colors.BOLD}Velocidade:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_speed(tx_speed):>15}{Colors.RESET}")
                        print(f"     {Colors.BOLD}Packets:{Colors.RESET} {Colors.CYAN}{opkts:,}{Colors.RESET}")
                        tx_bar = get_enhanced_bar(animation_frame + terminal_width, terminal_width - 10, tx_bytes, max(rx_bytes, tx_bytes, 1))
                        print(f"     {tx_bar}")
                        print()
                        
                        # Estatísticas gerais
                        print(Colors.BRIGHT_CYAN + "╠" + "─" * (terminal_width - 2) + "╣" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f" {Colors.BOLD}📊 Estatísticas Gerais:{Colors.RESET}" +
                              " " * (terminal_width - 25) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f"     {Colors.BOLD}Total Transferido:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(total_bytes):>15}{Colors.RESET}" +
                              " " * (terminal_width - 45) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f"     {Colors.BOLD}Velocidade Média:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_speed(avg_speed):>15}{Colors.RESET}" +
                              " " * (terminal_width - 45) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                        print(Colors.BRIGHT_CYAN + "╚" + "═" * (terminal_width - 2) + "╝" + Colors.RESET)
                        
                        lines_written = 0  # Deixar criar linhas novas
                    else:
                        spinner = get_spinner_char(int(time.time() * 5) % 8, 0)
                        sys.stdout.write('\r' + ' ' * 70 + '\r')
                        sys.stdout.write(f"{Colors.BRIGHT_GREEN}[{current_time}] {spinner} VPN Conectada{Colors.RESET} | {Colors.CYAN}Interface: {interface}{Colors.RESET}\n")
                        sys.stdout.write(f"   {Colors.BRIGHT_YELLOW}⚠️  Estatísticas não disponíveis{Colors.RESET}\r")
                        sys.stdout.flush()
                else:
                    spinner = get_spinner_char(int(time.time() * 5) % 8, 0)
                    sys.stdout.write('\r' + ' ' * 70 + '\r')
                    sys.stdout.write(f"{Colors.BRIGHT_GREEN}[{current_time}] {spinner} VPN Conectada{Colors.RESET}\r")
                    sys.stdout.flush()
            
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
