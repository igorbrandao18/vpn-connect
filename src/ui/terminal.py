#!/usr/bin/env python3
"""
Módulo de funções de terminal - cores, spinners, manipulação de cursor
"""

import os
import sys
import time
import re


class Colors:
    """Cores ANSI para terminal"""
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


class Spinner:
    """Gerenciador de spinners animados"""
    
    SPINNERS = [
        ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        ['◐', '◓', '◑', '◒'],
        ['◴', '◷', '◶', '◵'],
        ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
        ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    ]
    
    @staticmethod
    def get_char(frame: int, spinner_type: int = 0) -> str:
        """Retorna caractere do spinner baseado no frame"""
        spinner = Spinner.SPINNERS[spinner_type % len(Spinner.SPINNERS)]
        return spinner[frame % len(spinner)]
    
    @staticmethod
    def animate(text: str, duration: float = 2, spinner_type: int = 0):
        """Anima um spinner por um tempo"""
        start_time = time.time()
        frame = 0
        while time.time() - start_time < duration:
            spinner_char = Spinner.get_char(frame, spinner_type)
            sys.stdout.write(f'\r{spinner_char} {text}')
            sys.stdout.flush()
            time.sleep(0.1)
            frame += 1
        sys.stdout.write('\r' + ' ' * (len(text) + 3) + '\r')
        sys.stdout.flush()


def clear_screen():
    """Limpa a tela"""
    os.system('clear' if os.name != 'nt' else 'cls')


def move_cursor_to_line(line: int):
    """Move o cursor para uma linha específica"""
    sys.stdout.write(f'\033[{line};1H')
    sys.stdout.flush()


def clear_from_cursor():
    """Limpa da posição do cursor até o fim da tela"""
    sys.stdout.write('\033[J')
    sys.stdout.flush()


def strip_ansi(text: str) -> str:
    """Remove códigos ANSI de uma string"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def print_animated(text: str, color: str = Colors.RESET, end: str = '\n'):
    """Imprime texto com animação"""
    sys.stdout.write(f"{color}{text}{Colors.RESET}{end}")
    sys.stdout.flush()


def print_header():
    """Imprime cabeçalho com animação"""
    clear_screen()
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
    title = "🔐 VPN AUTO-RECONNECT"
    padding = (70 - len(title)) // 2
    print(" " * padding + Colors.BOLD + Colors.BRIGHT_GREEN + title + Colors.RESET)
    print(Colors.BRIGHT_CYAN + "=" * 70 + Colors.RESET)
    print()

