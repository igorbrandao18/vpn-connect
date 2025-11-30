#!/usr/bin/env python3
"""
Módulo de formatação de dados - bytes, velocidade, tempo
"""


def format_bytes(bytes_value: float) -> str:
    """
    Formata bytes em formato legível (B, KB, MB, GB, TB).
    
    Args:
        bytes_value: Valor em bytes
    
    Returns:
        String formatada (ex: "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """
    Formata velocidade em formato legível.
    
    Args:
        bytes_per_sec: Bytes por segundo
    
    Returns:
        String formatada (ex: "1.23 MB/s")
    """
    return format_bytes(bytes_per_sec) + "/s"


def format_time(seconds: int) -> str:
    """
    Formata tempo em formato HH:MM:SS.
    
    Args:
        seconds: Tempo em segundos
    
    Returns:
        String formatada (ex: "01:23:45")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

