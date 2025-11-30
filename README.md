# VPN Connection Script

Script para conectar à VPN usando `openfortivpn` com autenticação Azure CLI.

## Requisitos

- macOS
- Python 3.6+
- `openfortivpn` instalado (`brew install openfortivpn`)
- Azure CLI instalado e autenticado (`az login`)

## Instalação

```bash
# Instalar openfortivpn
brew install openfortivpn

# Autenticar no Azure CLI
az login
```

## Uso

### Menu Interativo (Recomendado)

```bash
python3 vpn_menu.py
```

O menu oferece todas as funcionalidades em uma interface simples:
- 🔌 Conectar à VPN
- 🛑 Desconectar VPN
- 📊 Monitorar Tráfego
- 📈 Ver Status Detalhado

### Uso Direto dos Scripts

#### Conectar à VPN

```bash
python3 connect_vpn.py --gateway dtc.sonepar.com.br
```

**Importante:** O script precisa ficar rodando para manter a VPN conectada. Após conectar, o script continuará monitorando a conexão. Para desconectar, pressione `Ctrl+C`.

#### Monitorar Tráfego VPN

Em outro terminal, execute o painel de monitoramento:

```bash
python3 monitor_vpn.py
```

O painel mostra em tempo real:
- ⬇️ Tráfego de entrada (download)
- ⬆️ Tráfego de saída (upload)
- 📊 Velocidade de transferência
- 📈 Estatísticas totais
- 🟢 Status da conexão

## Funcionalidades

### Menu Interativo (`vpn_menu.py`)
- 🎯 Interface simples e intuitiva
- 🔌 Conectar/Desconectar VPN com um clique
- 📊 Acesso rápido ao monitor de tráfego
- 📈 Status detalhado da conexão
- 🔄 Atualização automática do status

### Script de Conexão (`connect_vpn.py`)
- ✅ Verifica autenticação Azure CLI automaticamente
- ✅ Obtém token do Azure CLI
- ✅ Abre navegador automaticamente para autenticação SAML
- ✅ Conecta à VPN usando openfortivpn
- ✅ Mantém conexão ativa e monitora status
- ✅ Desconecta automaticamente ao pressionar Ctrl+C

### Painel de Monitoramento (`monitor_vpn.py`)
- 📊 Monitora tráfego de entrada e saída em tempo real
- 📈 Mostra velocidade de transferência
- 📉 Gráficos visuais de uso
- 🟢 Status da conexão VPN
- 💾 Estatísticas totais de transferência

## Opções

- `--gateway`: Gateway da VPN (obrigatório)
- `--port`: Porta do gateway (padrão: 443)
- `--username`: Nome de usuário (opcional)

## Exemplo

```bash
python3 connect_vpn.py --gateway dtc.sonepar.com.br --port 443
```
