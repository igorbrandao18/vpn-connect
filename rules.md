---
alwaysApply: true
---

# 📋 Regras e Estrutura do Projeto VPN

## 🏗️ Estrutura do Projeto

```
vpn/
├── src/                    # Código fonte organizado
│   ├── core/               # Funcionalidades principais
│   │   ├── __init__.py
│   │   ├── vpn_connection.py    # Lógica de conexão VPN
│   │   ├── vpn_monitor.py      # Monitoramento de VPN
│   │   └── network_stats.py    # Estatísticas de rede
│   ├── ui/                 # Interface do usuário
│   │   ├── __init__.py
│   │   ├── terminal.py         # Funções de terminal (cores, spinners)
│   │   └── dashboard.py         # Dashboard principal
│   └── utils/              # Utilitários
│       ├── __init__.py
│       ├── formatters.py       # Formatação de dados
│       └── validators.py        # Validações
├── scripts/                # Scripts executáveis
│   ├── connect_vpn.py      # Script de conexão
│   ├── monitor_vpn.py      # Script de monitoramento
│   └── vpn_menu.py         # Menu principal (auto-reconnect)
├── docs/                   # Documentação
│   ├── README.md           # Documentação principal
│   └── EVIDENCIA_VPN.md    # Evidências
├── tests/                  # Testes (opcional)
├── rules.md                # Este arquivo
└── requirements.txt        # Dependências Python
```

## 📝 Convenções de Código

### 1. **Nomenclatura**

- **Arquivos**: `snake_case.py` (ex: `vpn_connection.py`)
- **Classes**: `PascalCase` (ex: `VpnConnection`)
- **Funções/Variáveis**: `snake_case` (ex: `connect_vpn()`)
- **Constantes**: `UPPER_SNAKE_CASE` (ex: `MAX_RETRIES`)

### 2. **Organização de Módulos**

#### `src/core/` - Lógica de Negócio
- **vpn_connection.py**: Toda lógica relacionada à conexão VPN
  - Funções: `connect_vpn()`, `disconnect_vpn()`, `check_vpn_status()`
  - Classes: `VpnConnection`, `AzureAuth`
  
- **vpn_monitor.py**: Monitoramento e auto-reconexão
  - Funções: `monitor_connection()`, `auto_reconnect()`
  - Classes: `VpnMonitor`
  
- **network_stats.py**: Estatísticas de rede
  - Funções: `get_interface_stats()`, `get_vpn_interface()`, `get_vpn_ip()`
  - Classes: `NetworkStats`

#### `src/ui/` - Interface do Usuário
- **terminal.py**: Funções de terminal
  - Classes: `Colors`, `Spinner`
  - Funções: `clear_screen()`, `move_cursor()`, `print_animated()`
  
- **dashboard.py**: Dashboard principal
  - Funções: `render_dashboard()`, `update_header()`
  - Classes: `Dashboard`

#### `src/utils/` - Utilitários
- **formatters.py**: Formatação de dados
  - Funções: `format_bytes()`, `format_speed()`, `format_time()`
  
- **validators.py**: Validações
  - Funções: `validate_gateway()`, `validate_port()`

### 3. **Imports**

```python
# Ordem de imports:
# 1. Standard library
import os
import sys
import time

# 2. Third-party
import subprocess

# 3. Local imports
from src.core.vpn_connection import connect_vpn
from src.ui.terminal import Colors, clear_screen
from src.utils.formatters import format_bytes
```

### 4. **Documentação**

- **Docstrings**: Todas as funções e classes devem ter docstrings
- **Type Hints**: Usar type hints quando possível
- **Comentários**: Comentar código complexo ou não óbvio

```python
def connect_vpn(gateway: str, port: int = 443) -> bool:
    """
    Conecta à VPN usando openfortivpn.
    
    Args:
        gateway: Endereço do gateway VPN
        port: Porta do gateway (padrão: 443)
    
    Returns:
        True se conectou com sucesso, False caso contrário
    """
    pass
```

### 5. **Tratamento de Erros**

- Sempre usar try/except para operações que podem falhar
- Logar erros de forma clara
- Retornar valores padrão quando apropriado

```python
try:
    result = subprocess.run(['command'], capture_output=True)
    return result.returncode == 0
except Exception as e:
    print(f"⚠️  Erro: {e}")
    return False
```

### 6. **Cores e Formatação**

- Usar a classe `Colors` de `src.ui.terminal`
- Sempre resetar cores após uso: `Colors.RESET`
- Usar cores consistentes:
  - 🟢 Verde: Sucesso/Conectado
  - 🔴 Vermelho: Erro/Desconectado
  - 🟡 Amarelo: Aviso/Processando
  - 🔵 Azul: Informação

## 🔄 Fluxo de Trabalho

### 1. **Desenvolvimento**
- Criar branch para features: `git checkout -b feature/nome-da-feature`
- Commits descritivos: `git commit -m "feat: adiciona funcionalidade X"`
- Seguir padrão de commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### 2. **Testes**
- Testar localmente antes de commitar
- Verificar se não quebrou funcionalidades existentes
- Testar em diferentes cenários (conectado, desconectado, erro)

### 3. **Commits**
- Commits pequenos e focados
- Mensagens claras e descritivas
- Evitar commits com múltiplas mudanças não relacionadas

## 📦 Dependências

### Requisitos do Sistema
- macOS (testado em macOS 12+)
- Python 3.6+
- `openfortivpn` (`brew install openfortivpn`)
- Azure CLI (`az login`)

### Dependências Python
- Apenas biblioteca padrão (sem dependências externas)

## 🚀 Scripts Principais

### `vpn_menu.py` - Menu Principal
- **Função**: Auto-reconexão e dashboard
- **Uso**: `python3 scripts/vpn_menu.py`
- **Dependências**: Todos os módulos

### `connect_vpn.py` - Conexão VPN
- **Função**: Conectar à VPN
- **Uso**: `python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br`
- **Dependências**: `src/core/vpn_connection.py`

### `monitor_vpn.py` - Monitoramento
- **Função**: Monitorar tráfego VPN
- **Uso**: `python3 scripts/monitor_vpn.py`
- **Dependências**: `src/core/network_stats.py`, `src/ui/dashboard.py`

## 🔍 Padrões de Código

### 1. **Funções Puras**
- Preferir funções puras quando possível
- Evitar efeitos colaterais
- Retornar valores ao invés de modificar estado global

### 2. **Separação de Responsabilidades**
- Cada módulo tem uma responsabilidade clara
- UI separada da lógica de negócio
- Utilitários reutilizáveis

### 3. **Configuração**
- Valores configuráveis devem estar no topo do arquivo
- Usar constantes para valores mágicos

```python
# Configuração no topo do arquivo
GATEWAY = "dtc.sonepar.com.br"
PORT = 443
CHECK_INTERVAL = 5  # segundos
RECONNECT_DELAY = 10  # segundos
```

## 📚 Documentação

### README.md
- Instruções de instalação
- Guia de uso
- Exemplos

### Docstrings
- Todas as funções públicas
- Explicar parâmetros e retornos
- Exemplos quando apropriado

## 🐛 Debugging

### Logs
- Usar `print()` com cores para feedback visual
- Logs de erro devem ser claros e informativos
- Não logar informações sensíveis

### Testes Manuais
- Testar conexão/desconexão
- Testar reconexão automática
- Testar com VPN desconectada
- Testar com erros de rede

## 🔒 Segurança

- Não commitar credenciais
- Usar variáveis de ambiente para dados sensíveis
- Validar inputs do usuário
- Sanitizar comandos shell

## 📈 Melhorias Futuras

- [ ] Adicionar testes unitários
- [ ] Suporte para múltiplas VPNs
- [ ] Configuração via arquivo YAML/JSON
- [ ] Logging estruturado
- [ ] Notificações do sistema
- [ ] Métricas e alertas

## 🤝 Contribuindo

1. Seguir a estrutura de diretórios
2. Manter código limpo e documentado
3. Testar antes de commitar
4. Seguir convenções de nomenclatura
5. Atualizar documentação quando necessário

