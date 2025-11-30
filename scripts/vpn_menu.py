#!/usr/bin/env python3
"""
Menu simplificado - Monitora e reconecta VPN automaticamente
"""

import sys
import os

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.vpn_monitor import VpnMonitor
from src.ui.terminal import Colors, Spinner, print_header


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
        Spinner.animate("Inicializando sistema", 1.5, 0)
        print()
        
        # Configuração
        GATEWAY = "dtc.sonepar.com.br"
        PORT = 443
        CHECK_INTERVAL = 5  # segundos
        RECONNECT_DELAY = 10  # segundos
        
        # Criar e iniciar monitor
        monitor = VpnMonitor(
            gateway=GATEWAY,
            port=PORT,
            check_interval=CHECK_INTERVAL,
            reconnect_delay=RECONNECT_DELAY
        )
        monitor.monitor()
    except KeyboardInterrupt:
        from src.ui.terminal import clear_screen
        clear_screen()
        print(Colors.BRIGHT_CYAN + "👋 Até logo!" + Colors.RESET)
        sys.exit(0)


if __name__ == "__main__":
    main()
