#!/usr/bin/env python3
"""
Módulo de estatísticas de rede - interface VPN, IP, tráfego
"""

import subprocess
import re
from typing import Optional, Dict


class NetworkStats:
    """Classe para obter estatísticas de rede da VPN"""
    
    @staticmethod
    def get_vpn_interface() -> Optional[str]:
        """
        Identifica a interface VPN.
        
        Returns:
            Nome da interface VPN ou None se não encontrada
        """
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
        except Exception:
            return None
    
    @staticmethod
    def get_interface_stats(interface: str) -> Optional[Dict[str, int]]:
        """
        Obtém estatísticas de tráfego de uma interface.
        
        Args:
            interface: Nome da interface de rede
        
        Returns:
            Dicionário com 'rx' (recebido) e 'tx' (enviado) em bytes, ou None
        """
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
            # Formato netstat -ibn: Interface MTU Network Address Ipkts Ierrs Ibytes Opkts Oerrs Obytes Coll
            result = subprocess.run(['netstat', '-ibn'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    # Procurar linha da interface que começa com o nome
                    if re.match(rf'^{re.escape(interface)}\s+', line) and '<Link#' in line:
                        # Dividir por espaços múltiplos para pegar os campos corretos
                        parts = re.split(r'\s+', line.strip())
                        if len(parts) >= 10:
                            try:
                                # Ibytes (bytes recebidos) está em parts[5]
                                # Obytes (bytes enviados) está em parts[8]
                                rx_bytes = int(parts[5]) if len(parts) > 5 else 0
                                tx_bytes = int(parts[8]) if len(parts) > 8 else 0
                                
                                # Retornar mesmo se um for 0
                                return {'rx': rx_bytes, 'tx': tx_bytes}
                            except (ValueError, IndexError):
                                continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_vpn_ip(interface: str) -> str:
        """
        Obtém IP da VPN a partir da interface.
        
        Args:
            interface: Nome da interface de rede
        
        Returns:
            IP da VPN ou "N/A" se não encontrado
        """
        try:
            result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            return ip_match.group(1) if ip_match else "N/A"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_interface_details(interface: str) -> Dict[str, any]:
        """
        Obtém detalhes completos da interface (MTU, packets, etc).
        
        Args:
            interface: Nome da interface de rede
        
        Returns:
            Dicionário com detalhes da interface
        """
        details = {
            'mtu': 'N/A',
            'ipkts': 0,
            'opkts': 0
        }
        
        try:
            result = subprocess.run(['netstat', '-ibn'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if re.match(rf'^{re.escape(interface)}\s+', line) and '<Link#' in line:
                    parts = re.split(r'\s+', line.strip())
                    if len(parts) > 1:
                        details['mtu'] = parts[1]
                    if len(parts) > 4:
                        details['ipkts'] = int(parts[4])
                    if len(parts) > 6:
                        details['opkts'] = int(parts[6])
                    break
        except Exception:
            pass
        
        return details

