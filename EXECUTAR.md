# 🚀 Como Executar o Projeto

## 📍 Localização

Todos os scripts estão na pasta `scripts/` e devem ser executados a partir da raiz do projeto.

## 🎯 Opções de Execução

### 1. **Auto-Reconexão (Recomendado)** ⭐

Este é o script principal que monitora e reconecta automaticamente:

```bash
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/vpn_menu.py
```

**O que faz:**
- 🔌 Conecta à VPN automaticamente
- 🔄 Monitora a conexão continuamente
- 🔁 Reconecta automaticamente se desconectar
- 📊 Mostra dashboard com estatísticas em tempo real

### 2. **Conexão Manual**

Para conectar à VPN manualmente:

```bash
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br
```

**Opções:**
- `--gateway`: Gateway da VPN (obrigatório)
- `--port`: Porta (padrão: 443)
- `--username`: Usuário (opcional)

**Exemplo completo:**
```bash
python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br --port 443
```

### 3. **Monitoramento de Tráfego**

Para monitorar o tráfego VPN em tempo real (em terminal separado):

```bash
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/monitor_vpn.py
```

**O que mostra:**
- ⬇️ Tráfego de entrada (download)
- ⬆️ Tráfego de saída (upload)
- 📊 Velocidade de transferência
- 📈 Estatísticas totais

## 📝 Exemplos Práticos

### Cenário 1: Primeira vez usando

```bash
# 1. Navegar até o projeto
cd /Users/igorbrandao/Desktop/development/scripts/vpn

# 2. Executar auto-reconexão (recomendado)
python3 scripts/vpn_menu.py

# 3. Pressionar Enter quando solicitado
# 4. Aguardar conexão automática
```

### Cenário 2: Já tem VPN conectada, só quer monitorar

```bash
# Terminal 1: Deixar VPN rodando (se já estiver conectada)

# Terminal 2: Monitorar tráfego
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/monitor_vpn.py
```

### Cenário 3: Conectar manualmente e depois monitorar

```bash
# Terminal 1: Conectar
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/connect_vpn.py --gateway dtc.sonepar.com.br

# Terminal 2: Monitorar (após conectar)
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/monitor_vpn.py
```

## ⚠️ Requisitos Antes de Executar

1. **Azure CLI autenticado:**
   ```bash
   az login
   az account show  # Verificar se está autenticado
   ```

2. **openfortivpn instalado:**
   ```bash
   brew install openfortivpn
   which openfortivpn  # Verificar instalação
   ```

3. **Python 3.6+:**
   ```bash
   python3 --version  # Deve ser 3.6 ou superior
   ```

## 🛑 Como Parar

- **Pressione `Ctrl+C`** em qualquer script para parar
- O script desconectará a VPN automaticamente ao sair

## 🔍 Troubleshooting

### Erro: "ModuleNotFoundError"
```bash
# Certifique-se de estar na raiz do projeto
cd /Users/igorbrandao/Desktop/development/scripts/vpn
python3 scripts/vpn_menu.py
```

### Erro: "openfortivpn não encontrado"
```bash
brew install openfortivpn
```

### Erro: "Azure CLI não está autenticado"
```bash
az login
```

### Erro: "Interface VPN não encontrada"
- Aguarde alguns segundos após conectar
- Verifique se a VPN está realmente conectada
- Execute `ifconfig` para ver interfaces disponíveis

## 📊 Estrutura de Execução

```
Projeto (raiz)
  └── scripts/
       ├── vpn_menu.py      ← Execute este para auto-reconexão
       ├── connect_vpn.py   ← Execute este para conectar manualmente
       └── monitor_vpn.py   ← Execute este para monitorar tráfego
```

## 💡 Dicas

1. **Use `vpn_menu.py`** para uso diário - é o mais completo
2. **Use `monitor_vpn.py`** em terminal separado para ver estatísticas detalhadas
3. **Mantenha o terminal aberto** - os scripts precisam ficar rodando
4. **Use `tmux` ou `screen`** se quiser rodar em background

## 🎯 Comando Rápido (Copy & Paste)

```bash
cd /Users/igorbrandao/Desktop/development/scripts/vpn && python3 scripts/vpn_menu.py
```

