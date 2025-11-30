# 🔐 VPN Auto-Reconnect

Script para conectar à VPN usando `openfortivpn` com autenticação Azure CLI, com monitoramento automático e reconexão.

## 📋 Estrutura do Projeto

```
vpn/
├── src/                    # Código fonte organizado
│   ├── core/               # Funcionalidades principais
│   │   ├── vpn_connection.py    # Lógica de conexão VPN
│   │   ├── vpn_monitor.py      # Monitoramento e auto-reconexão
│   │   └── network_stats.py    # Estatísticas de rede
│   ├── ui/                 # Interface do usuário
│   │   └── terminal.py         # Funções de terminal (cores, spinners)
│   └── utils/              # Utilitários
│       └── formatters.py       # Formatação de dados
├── scripts/                # Scripts executáveis
│   ├── connect_vpn.py      # Script de conexão
│   ├── monitor_vpn.py      # Script de monitoramento
│   └── vpn_menu.py         # Menu principal (auto-reconnect)
├── docs/                   # Documentação
│   └── EVIDENCIA_VPN.md    # Evidências
├── rules.md                # Regras e convenções do projeto
└── requirements.txt        # Dependências Python
```

## 📦 Requisitos

### Sistema
- macOS (testado em macOS 12+)
- Python 3.6+
- `openfortivpn` instalado (`brew install openfortivpn`)
- Azure CLI instalado e autenticado (`az login`)

### Python
- Apenas biblioteca padrão (sem dependências externas)

## 🚀 Instalação

```bash
# Instalar openfortivpn
brew install openfortivpn

# Autenticar no Azure CLI
az login

# Clonar ou baixar o projeto
cd vpn/
```

## 💻 Uso

### Auto-Reconexão (Recomendado)

```bash
python3 scripts/vpn_menu.py
```

O script monitora e reconecta automaticamente:
- 🔌 Conecta à VPN automaticamente
- 🔄 Monitora a conexão continuamente
- 🔁 Reconecta automaticamente se desconectar
- 📊 Mostra estatísticas de tráfego em tempo real
- 📈 Dashboard visual com informações detalhadas

### Conexão Manual

```bash
python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br
```

**Importante:** O script precisa ficar rodando para manter a VPN conectada. Após conectar, o script continuará monitorando a conexão. Para desconectar, pressione `Ctrl+C`.

### Monitoramento de Tráfego

Em outro terminal, execute o painel de monitoramento:

```bash
python3 scripts/monitor_vpn.py
```

O painel mostra em tempo real:
- ⬇️ Tráfego de entrada (download)
- ⬆️ Tráfego de saída (upload)
- 📊 Velocidade de transferência
- 📈 Estatísticas totais
- 🟢 Status da conexão

## 🎯 Funcionalidades

### Auto-Reconexão (`scripts/vpn_menu.py`)
- 🔄 Monitora conexão VPN continuamente
- 🔁 Reconecta automaticamente se desconectar
- 📊 Mostra estatísticas de tráfego em tempo real
- 🟢 Status visual da conexão
- ⚡ Verificação a cada 5 segundos
- 📈 Dashboard com informações detalhadas
- 🎨 Interface colorida e animada

### Script de Conexão (`scripts/connect_vpn.py`)
- ✅ Verifica autenticação Azure CLI automaticamente
- ✅ Obtém token do Azure CLI
- ✅ Abre navegador automaticamente para autenticação SAML
- ✅ Conecta à VPN usando openfortivpn
- ✅ Mantém conexão ativa e monitora status
- ✅ Desconecta automaticamente ao pressionar Ctrl+C

### Painel de Monitoramento (`scripts/monitor_vpn.py`)
- 📊 Monitora tráfego de entrada e saída em tempo real
- 📈 Mostra velocidade de transferência
- 📉 Gráficos visuais de uso
- 🟢 Status da conexão VPN
- 💾 Estatísticas totais de transferência

## ⚙️ Opções

### `connect_vpn.py`
- `--gateway`: Gateway da VPN (obrigatório)
- `--port`: Porta do gateway (padrão: 443)
- `--username`: Nome de usuário (opcional)

## 📝 Exemplos

### Conectar à VPN
```bash
python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br --port 443
```

### Auto-reconexão com monitoramento
```bash
python3 scripts/vpn_menu.py
```

### Monitorar tráfego (em terminal separado)
```bash
python3 scripts/monitor_vpn.py
```

## 🏗️ Arquitetura

O projeto está organizado em módulos:

- **`src/core/`**: Lógica de negócio
  - `vpn_connection.py`: Conexão VPN e autenticação Azure
  - `vpn_monitor.py`: Monitoramento e auto-reconexão
  - `network_stats.py`: Estatísticas de rede

- **`src/ui/`**: Interface do usuário
  - `terminal.py`: Cores, spinners, manipulação de terminal

- **`src/utils/`**: Utilitários
  - `formatters.py`: Formatação de bytes, velocidade, tempo

- **`scripts/`**: Scripts executáveis que usam os módulos

## 📚 Documentação

- **`rules.md`**: Regras e convenções do projeto
- **`README.md`**: Este arquivo
- **`docs/EVIDENCIA_VPN.md`**: Evidências e testes

## 🔧 Desenvolvimento

### Estrutura de Módulos

Cada módulo tem responsabilidades claras:

1. **Core**: Lógica de negócio isolada
2. **UI**: Interface separada da lógica
3. **Utils**: Funções reutilizáveis

### Convenções

- Nomenclatura: `snake_case` para funções, `PascalCase` para classes
- Docstrings: Todas as funções públicas documentadas
- Type hints: Usados quando possível
- Tratamento de erros: Try/except com mensagens claras

Veja `rules.md` para mais detalhes.

## 🐛 Troubleshooting

### VPN não conecta
1. Verifique se Azure CLI está autenticado: `az account show`
2. Verifique se openfortivpn está instalado: `which openfortivpn`
3. Tente fazer login novamente: `az login`

### Estatísticas não aparecem
1. Verifique se a VPN está conectada
2. Verifique se a interface VPN foi detectada
3. Execute `ifconfig` para ver interfaces disponíveis

### Erro de permissão
- O `openfortivpn` requer privilégios de root (sudo)
- O script solicitará senha automaticamente

## 📄 Licença

Este projeto é para uso interno.

## 🤝 Contribuindo

1. Siga a estrutura de diretórios
2. Mantenha código limpo e documentado
3. Teste antes de commitar
4. Siga convenções de nomenclatura
5. Atualize documentação quando necessário

Veja `rules.md` para mais detalhes sobre contribuição.
