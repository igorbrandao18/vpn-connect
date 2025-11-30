#!/usr/bin/env python3
"""
Módulo de monitoramento VPN - auto-reconexão
"""

import subprocess
import sys
import os
import time
from datetime import datetime
from typing import Optional

from .vpn_connection import VpnConnection
from .network_stats import NetworkStats
from ..ui.terminal import Colors, Spinner, clear_screen, move_cursor_to_line, clear_from_cursor, strip_ansi
from ..utils.formatters import format_bytes, format_speed, format_time


class VpnMonitor:
    """Classe para monitorar e reconectar VPN automaticamente"""
    
    def __init__(self, gateway: str, port: int = 443, check_interval: int = 5, reconnect_delay: int = 10):
        """
        Inicializa monitor de VPN.
        
        Args:
            gateway: Endereço do gateway VPN
            port: Porta do gateway
            check_interval: Intervalo de verificação em segundos
            reconnect_delay: Delay antes de reconectar em segundos
        """
        self.gateway = gateway
        self.port = port
        self.check_interval = check_interval
        self.reconnect_delay = reconnect_delay
        self.reconnect_count = 0
        self.was_connected = False
        self.connection_process = None
        self.connection_start_time = None
        self.last_rx_bytes = 0
        self.last_tx_bytes = 0
        self.last_time = time.time()
    
    def connect_vpn_process(self) -> Optional[subprocess.Popen]:
        """Conecta à VPN em processo separado"""
        script_path = os.path.join(os.path.dirname(__file__), '../../scripts/connect_vpn.py')
        
        try:
            process = subprocess.Popen(
                [sys.executable, script_path, '--gateway', self.gateway, '--port', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return process
        except Exception:
            return None
    
    def get_enhanced_bar(self, frame: int, width: int, value: int = 0, max_value: int = 1000000000) -> str:
        """Cria barra de progresso animada"""
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
    
    def monitor(self):
        """Inicia monitoramento e auto-reconexão"""
        clear_screen()
        
        # Obter largura do terminal
        try:
            terminal_width = os.get_terminal_size().columns - 2
        except Exception:
            terminal_width = 68
        
        # Criar header fixo
        print(Colors.BRIGHT_CYAN + "╔" + "═" * (terminal_width - 2) + "╗" + Colors.RESET)
        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + f" {Colors.BRIGHT_GREEN}🔐 VPN AUTO-RECONNECT{Colors.RESET}" +
              " " * (terminal_width - 22) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
        print(Colors.BRIGHT_CYAN + "╠" + "═" * (terminal_width - 2) + "╣" + Colors.RESET)
        
        header_status_line = 4
        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + " " * (terminal_width - 2) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
        
        header_info_line = 5
        print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + " " * (terminal_width - 2) + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
        
        print(Colors.BRIGHT_CYAN + "╠" + "─" * (terminal_width - 2) + "╣" + Colors.RESET)
        
        content_start_line = 7
        
        try:
            while True:
                current_time = datetime.now().strftime("%H:%M:%S")
                is_connected = VpnConnection.check_vpn_connected()
                
                # Verificar se processo de conexão ainda está rodando
                if self.connection_process:
                    if self.connection_process.poll() is not None:
                        self.connection_process = None
                
                # Se não está conectado e não há processo de conexão
                if not is_connected and self.connection_process is None:
                    # Incrementar contador de reconexões se estava conectado antes
                    if self.was_connected:
                        self.reconnect_count += 1
                    
                    # Atualizar header com status desconectado
                    spinner = Spinner.get_char(int(time.time() * 5) % 8, 0)
                    move_cursor_to_line(header_status_line)
                    status_text = (f" {Colors.BRIGHT_RED}{spinner} VPN Desconectada{Colors.RESET} " + 
                                  f"{Colors.DIM}|{Colors.RESET} {Colors.CYAN}{current_time}{Colors.RESET} " +
                                  f"{Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_MAGENTA}Reconexões: {self.reconnect_count}{Colors.RESET}")
                    status_text_plain = strip_ansi(status_text)
                    padding = max(0, terminal_width - len(status_text_plain) - 3)
                    print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + status_text + " " * padding + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                    sys.stdout.flush()
                    
                    # Mostrar mensagem no conteúdo
                    move_cursor_to_line(content_start_line)
                    clear_from_cursor()
                    print(Colors.BRIGHT_RED + f"⚠️  VPN desconectada" + Colors.RESET)
                    if self.was_connected:
                        print(Colors.BRIGHT_MAGENTA + f"📊 Reconexão #{self.reconnect_count}" + Colors.RESET)
                    sys.stdout.flush()
                    
                    # Animação de contagem regressiva
                    for remaining in range(self.reconnect_delay, 0, -1):
                        spinner = Spinner.get_char(int(time.time() * 10) % 8, 1)
                        move_cursor_to_line(content_start_line + (2 if self.was_connected else 1))
                        sys.stdout.write(f'{Colors.BRIGHT_YELLOW}{spinner} Reconectando em {remaining}s...{Colors.RESET}')
                        sys.stdout.flush()
                        time.sleep(1)
                    move_cursor_to_line(content_start_line + (2 if self.was_connected else 1))
                    sys.stdout.write(' ' * 50)
                    sys.stdout.flush()
                    
                    # Atualizar header com status reconectando
                    spinner = Spinner.get_char(int(time.time() * 10) % 8, 1)
                    move_cursor_to_line(header_status_line)
                    status_text = (f" {Colors.BRIGHT_YELLOW}{spinner} Reconectando...{Colors.RESET} " + 
                                  f"{Colors.DIM}|{Colors.RESET} {Colors.CYAN}{current_time}{Colors.RESET} " +
                                  f"{Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_MAGENTA}Reconexões: {self.reconnect_count}{Colors.RESET}")
                    status_text_plain = strip_ansi(status_text)
                    padding = max(0, terminal_width - len(status_text_plain) - 3)
                    print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + status_text + " " * padding + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                    sys.stdout.flush()
                    
                    # Mostrar no conteúdo
                    move_cursor_to_line(content_start_line)
                    clear_from_cursor()
                    print(Colors.BRIGHT_BLUE + f"🔌 Tentando conectar..." + Colors.RESET)
                    sys.stdout.flush()
                    
                    self.connection_process = self.connect_vpn_process()
                    
                    move_cursor_to_line(content_start_line)
                    clear_from_cursor()
                    if self.connection_process:
                        print(Colors.BRIGHT_GREEN + f"✅ Processo de conexão iniciado (PID: {self.connection_process.pid})" + Colors.RESET)
                    else:
                        print(Colors.BRIGHT_RED + f"❌ Erro ao iniciar conexão" + Colors.RESET)
                    sys.stdout.flush()
                    
                    self.was_connected = False
                
                # Se está conectado
                elif is_connected:
                    # Verificar interface para obter estatísticas
                    interface = NetworkStats.get_vpn_interface()
                    if interface:
                        # Obter estatísticas básicas
                        stats = NetworkStats.get_interface_stats(interface)
                        if stats:
                            rx_bytes = stats['rx']
                            tx_bytes = stats['tx']
                            
                            # Calcular velocidade
                            current_time_sec = time.time()
                            time_diff = current_time_sec - self.last_time
                            
                            if time_diff > 0:
                                rx_speed = (rx_bytes - self.last_rx_bytes) / time_diff
                                tx_speed = (tx_bytes - self.last_tx_bytes) / time_diff
                            else:
                                rx_speed = 0
                                tx_speed = 0
                            
                            self.last_rx_bytes = rx_bytes
                            self.last_tx_bytes = tx_bytes
                            self.last_time = current_time_sec
                            
                            # Obter IP da VPN
                            vpn_ip = NetworkStats.get_vpn_ip(interface)
                            
                            # Obter detalhes da interface
                            details = NetworkStats.get_interface_details(interface)
                            mtu = details['mtu']
                            ipkts = details['ipkts']
                            opkts = details['opkts']
                            
                            # Atualizar status de conexão
                            if not self.was_connected:
                                self.was_connected = True
                                if self.connection_start_time is None:
                                    self.connection_start_time = time.time()
                            
                            # Calcular tempo de conexão
                            uptime_seconds = int(time.time() - self.connection_start_time)
                            
                            # Calcular porcentagens
                            total_bytes = rx_bytes + tx_bytes
                            rx_percent = (rx_bytes / total_bytes * 100) if total_bytes > 0 else 0
                            tx_percent = (tx_bytes / total_bytes * 100) if total_bytes > 0 else 0
                            avg_speed = (rx_speed + tx_speed) / 2 if (rx_speed + tx_speed) > 0 else 0
                            
                            # Atualizar header fixo
                            spinner = Spinner.get_char(int(time.time() * 5) % 8, 0)
                            move_cursor_to_line(header_status_line)
                            status_text = (f" {Colors.BRIGHT_GREEN}{spinner} VPN Status{Colors.RESET} " + 
                                          f"{Colors.DIM}|{Colors.RESET} {Colors.CYAN}{current_time}{Colors.RESET} " +
                                          f"{Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_YELLOW}Uptime: {format_time(uptime_seconds)}{Colors.RESET} " +
                                          f"{Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_MAGENTA}Reconexões: {self.reconnect_count}{Colors.RESET}")
                            status_text_plain = strip_ansi(status_text)
                            padding = max(0, terminal_width - len(status_text_plain) - 3)
                            print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + status_text + " " * padding + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                            
                            # Atualizar linha de informações
                            move_cursor_to_line(header_info_line)
                            info_text = (f" {Colors.BOLD}Interface:{Colors.RESET} {Colors.CYAN}{interface:<15}{Colors.RESET} " +
                                        f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}IP:{Colors.RESET} {Colors.CYAN}{vpn_ip:<15}{Colors.RESET} " +
                                        f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}MTU:{Colors.RESET} {Colors.CYAN}{mtu}{Colors.RESET}")
                            info_text_plain = strip_ansi(info_text)
                            padding = max(0, terminal_width - len(info_text_plain) - 3)
                            print(Colors.BRIGHT_CYAN + "║" + Colors.RESET + info_text + " " * padding + Colors.BRIGHT_CYAN + "║" + Colors.RESET)
                            
                            # Mover para linha de conteúdo e limpar abaixo
                            move_cursor_to_line(content_start_line)
                            clear_from_cursor()
                            
                            # Frame para animação
                            animation_frame = int(time.time() * 10) % (terminal_width * 2)
                            
                            # Exibir dashboard completo
                            # Estatísticas de entrada
                            print(f"  {Colors.BRIGHT_BLUE}⬇️  ENTRADA (Download){Colors.RESET}")
                            print(f"     {Colors.BOLD}Total:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(rx_bytes):>15}{Colors.RESET} " +
                                  f"{Colors.DIM}({rx_percent:.1f}% do total){Colors.RESET}")
                            print(f"     {Colors.BOLD}Velocidade:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_speed(rx_speed):>15}{Colors.RESET}")
                            print(f"     {Colors.BOLD}Packets:{Colors.RESET} {Colors.CYAN}{ipkts:,}{Colors.RESET}")
                            rx_bar = self.get_enhanced_bar(animation_frame, terminal_width - 10, rx_bytes, max(rx_bytes, tx_bytes, 1))
                            print(f"     {rx_bar}")
                            print()
                            
                            # Estatísticas de saída
                            print(f"  {Colors.BRIGHT_MAGENTA}⬆️  SAÍDA (Upload){Colors.RESET}")
                            print(f"     {Colors.BOLD}Total:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_bytes(tx_bytes):>15}{Colors.RESET} " +
                                  f"{Colors.DIM}({tx_percent:.1f}% do total){Colors.RESET}")
                            print(f"     {Colors.BOLD}Velocidade:{Colors.RESET} {Colors.BRIGHT_GREEN}{format_speed(tx_speed):>15}{Colors.RESET}")
                            print(f"     {Colors.BOLD}Packets:{Colors.RESET} {Colors.CYAN}{opkts:,}{Colors.RESET}")
                            tx_bar = self.get_enhanced_bar(animation_frame + terminal_width, terminal_width - 10, tx_bytes, max(rx_bytes, tx_bytes, 1))
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
                            
                            sys.stdout.flush()
                
                # Aguardar antes da próxima verificação
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print()
            print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
            print(Colors.BRIGHT_YELLOW + "🛑 Encerrando monitoramento..." + Colors.RESET)
            
            Spinner.animate("Desconectando", 1, 1)
            
            # Matar processos de conexão
            if self.connection_process:
                self.connection_process.terminate()
            
            # Desconectar VPN
            VpnConnection.disconnect()
            
            print(Colors.BRIGHT_GREEN + "✅ Encerrado" + Colors.RESET)
            sys.exit(0)

