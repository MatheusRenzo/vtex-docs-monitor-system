
# 📦 VTEX Dock Monitoring System
![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![Interface](https://img.shields.io/badge/GUI-Tkinter-informational)
![Sistema](https://img.shields.io/badge/Sistema-Desktop-lightgrey)
![Entrada](https://img.shields.io/badge/Suporte-CSV%20%7C%20XLSX-orange)
![API](https://img.shields.io/badge/API-VTEX-red)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)
![Licença](https://img.shields.io/badge/Licença-MIT-green)
## 📝 Descrição
Aplicação de desktop para coletar informações sobre **docks (anexos)** de múltiplas lojas VTEX via API de logística. Permite gerar relatórios em XLSX ou CSV e mantém **logs detalhados**.

## 🔧 Funcionalidades
- 🔄 Coleta de dados de múltiplas lojas VTEX simultaneamente.
- 🖥️ Interface gráfica amigável com barra de progresso e logs em tempo real.
- 📤 Exportação dos dados em formato Excel (.xlsx) ou CSV.
- 🗂️ Registro de logs detalhados (timestamp, ID da loja, status, detalhes).
- 📁 Exportação dos logs para análise posterior.
- ⚙️ Operação assíncrona que evita travamentos da interface.

## 📋 Pré-requisitos
- Python 3.7 ou superior
- Bibliotecas:
  - `requests`
  - `pandas`
  - `openpyxl`
  - `tkinter` (nativo na maioria dos sistemas)

## 🚀 Instalação
```bash
git clone https://github.com/seuusuario/vtex-dock-monitor.git
cd vtex-dock-monitor
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
pip install requests pandas openpyxl
```

## ▶️ Uso
```bash
python dock_monitor.py
```

### 🖱️ Passos na interface gráfica:
1. Insira as **App Key** e **App Token**.
2. Adicione os **IDs das lojas** (um por linha).
3. Escolha o formato de saída: Excel ou CSV.
4. (Opcional) Escolha o local de salvamento.
5. Clique em **Start Collection**.
6. Acompanhe o progresso pela barra e área de logs.
7. Verifique o arquivo gerado na pasta `Documents` ou no local escolhido.

### 🔘 Botões Extras
- 🧹 **Clear Logs**: Limpa os logs da interface.
- 📁 **Export Logs**: Exporta os logs em CSV.

## 📁 Estrutura do Projeto
```
├── dock_monitor.py       # Script principal
├── api_logs.csv          # Logs gerados (em ~/Documents)
```

## 🔐 Configuração
- **Credenciais VTEX** com permissão para `GET /api/logistics/pvt/configuration/docks`.
- **Lista de lojas**: IDs separados por linha (ex: loja1, loja2).

## 📊 Logs
Salvos em `~/Documents/api_logs.csv` com:
- `timestamp`: Data e hora
- `store_id`: ID da loja
- `status`: SUCCESS ou ERROR
- `details`: Número de docks ou erro

## 🚫 Limitações Atuais
- ❌ Não é possível cancelar a coleta em andamento.
- ❌ Não há retentativas automáticas.
- 🔧 Melhorias futuras:
  - Botão para cancelar operação
  - Retentativas com backoff exponencial
  - Leitura de lojas via arquivo externo
  - Suporte a proxy
  - Melhor tratamento de exceções

## 🤝 Contribuição
Contribuições são bem-vindas! Abra uma issue ou envie um pull request.

## 📄 Licença
Distribuído sob a [MIT License](LICENSE).
