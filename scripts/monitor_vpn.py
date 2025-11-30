#!/usr/bin/env python3
"""
Painel de monitoramento de tráfego VPN
Mostra estatísticas de entrada e saída em tempo real
"""

import sys
import os
import time
from datetime import datetime

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.network_stats import NetworkStats
from src.core.vpn_connection import VpnConnection
from src.ui.terminal import Colors, clear_screen
from src.utils.formatters import format_bytes, format_speed


def get_vpn_status() -> str:
    """Verifica status da VPN"""
    if VpnConnection.check_vpn_connected():
        return "🟢 Conectada"
    return "🔴 Desconectada"


def draw_bar(value: float, max_value: float, width: int = 30) -> str:
    """Desenha uma barra de progresso"""
    if max_value == 0:
        return "█" * width
    
    filled = int((value / max_value) * width)
    filled = min(filled, width)
    return "█" * filled + "░" * (width - filled)


def main():
    """Função principal"""
    print("🔍 Procurando interface VPN...")
    
    interface = None
    retry_count = 0
    max_retries = 5
    
    # Tentar encontrar interface com retry
    while not interface and retry_count < max_retries:
        interface = NetworkStats.get_vpn_interface()
        if not interface:
            retry_count += 1
            if retry_count < max_retries:
                print(f"   Tentativa {retry_count}/{max_retries}...")
                time.sleep(1)
    
    if not interface:
        print("❌ Interface VPN não encontrada!")
        print("💡 Certifique-se de que a VPN está conectada")
        print("💡 Execute: python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br")
        print()
        print("🔄 Tentando novamente a cada 5 segundos...")
        print("   Pressione Ctrl+C para sair")
        print()
        
        # Tentar novamente periodicamente
        while True:
            time.sleep(5)
            interface = NetworkStats.get_vpn_interface()
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
            vpn_ip = NetworkStats.get_vpn_ip(interface) if interface else "N/A"
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"Status: {status} | IP VPN: {vpn_ip} | Interface: {interface}")
            print(f"Horário: {current_time}")
            print("-" * 70)
            print()
            
            # Obter estatísticas atuais
            stats = NetworkStats.get_interface_stats(interface) if interface else None
            
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
