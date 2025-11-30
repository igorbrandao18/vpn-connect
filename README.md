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

```bash
python3 connect_vpn.py --gateway dtc.sonepar.com.br
```

**Importante:** O script precisa ficar rodando para manter a VPN conectada. Após conectar, o script continuará monitorando a conexão. Para desconectar, pressione `Ctrl+C`.

## Funcionalidades

- ✅ Verifica autenticação Azure CLI automaticamente
- ✅ Obtém token do Azure CLI
- ✅ Abre navegador automaticamente para autenticação SAML
- ✅ Conecta à VPN usando openfortivpn
- ✅ Mantém conexão ativa e monitora status
- ✅ Desconecta automaticamente ao pressionar Ctrl+C

## Opções

- `--gateway`: Gateway da VPN (obrigatório)
- `--port`: Porta do gateway (padrão: 443)
- `--username`: Nome de usuário (opcional)

## Exemplo

```bash
python3 connect_vpn.py --gateway dtc.sonepar.com.br --port 443
```
