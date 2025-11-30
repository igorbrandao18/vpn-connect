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

### Auto-Reconexão (Recomendado)

```bash
python3 vpn_menu.py
```

O script monitora e reconecta automaticamente:
- 🔌 Conecta à VPN automaticamente
- 🔄 Monitora a conexão continuamente
- 🔁 Reconecta automaticamente se desconectar
- 📊 Mostra estatísticas de tráfego em tempo real

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

### Auto-Reconexão (`vpn_menu.py`)
- 🔄 Monitora conexão VPN continuamente
- 🔁 Reconecta automaticamente se desconectar
- 📊 Mostra estatísticas de tráfego em tempo real
- 🟢 Status visual da conexão
- ⚡ Verificação a cada 5 segundos

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
