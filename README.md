# Cotação de Moedas - Automação de Coleta, Processamento e Visualização

Este projeto é um script em Python que automatiza o processo de coleta, processamento e visualização de cotações de moedas fornecidas pelo Banco Central do Brasil. Ele também realiza o armazenamento dos dados no Hadoop e faz o upload dos resultados no Google Drive, além de enviar notificações por e-mail sobre o status das operações.

## Funcionalidades

- Coleta de dados de cotações diárias de moedas de um endpoint do Banco Central do Brasil.
- Processamento e cálculo de valores em R$ e US$ para diferentes tipos de moedas.
- Armazenamento dos dados processados em formato Parquet no Hadoop.
- Upload automático dos dados para o Google Drive.
- Notificação por e-mail em caso de sucesso ou falha na execução do script.
- Visualização interativa dos dados de cotações usando um dashboard em Dash.

## Requisitos

- Python 3.7+
- Pacotes Python: `requests`, `pandas`, `dash`, `plotly`, `hdfs`, `pyarrow`, `pydrive`, `smtplib`, `email`.
- Servidor Hadoop configurado.
- Conta do Google configurada para autenticação com `pydrive`.
- Servidor SMTP configurado para envio de e-mails.

## Instalação

Clone este repositório e instale os requisitos listados no arquivo `requirements.txt`:

```bash
git clone https://github.com/Magalhaes-vitor/Monitoramento-Dados-Financeiros.git
cd repositorio
pip install -r requirements.txt
```

Certifique-se de configurar as variáveis de ambiente necessárias, como informações de autenticação do Google Drive e servidor de e-mail.

## Uso

Para executar o script e visualizar o dashboard, siga os seguintes passos:

1. Certifique-se de que o Hadoop e o serviço Google Drive estejam configurados corretamente.
2. Altere as configurações de e-mail e Hadoop no script conforme necessário.
3. Execute o script:

```bash
python script_cotacoes.py
```

O dashboard estará disponível em `http://127.0.0.1:8050/` e mostrará as cotações das moedas coletadas.

## Estrutura do Código

### Configurações

- Configuração do cliente Hadoop para armazenamento e leitura de dados.
- Autenticação do Google Drive para upload dos arquivos de cotações.
- Configurações de e-mail para envio de notificações.

### Funções Principais

- **`send_email(subject, body, high_priority=False)`**: Envia e-mails de notificação com o status do script.
- **`generate_url(date)`**: Gera a URL do Banco Central para o download de cotações em CSV.
- **`download_csv(date)`**: Faz o download do CSV de cotações e retorna um DataFrame.
- **`calculate_values(df)`**: Calcula os valores em R$ e US$ para os tipos de moedas "A" e "B".
- **`save_to_hadoop(df, file_name)`**: Salva o DataFrame no Hadoop em formato Parquet.
- **`load_from_hadoop(file_name)`**: Carrega um DataFrame do Hadoop.
- **`upload_to_drive(file_path, file_name)`**: Faz upload de um arquivo local para o Google Drive.
- **`save_and_upload_to_drive(df)`**: Salva um DataFrame localmente e realiza o upload para o Google Drive.
- **`fetch_data_save_and_upload()`**: Função principal que gerencia a coleta, processamento, salvamento e upload dos dados.

### Dashboard

- A interface de usuário foi construída usando `Dash` e `Plotly` para visualização interativa das cotações das moedas.

## Testes

### Testes Unitários

Abaixo estão exemplos de testes unitários para garantir o funcionamento correto das principais funções do script.

#### Arquivo `test_script.py`

```python
import pytest
import pandas as pd
from script_cotacoes import (
    send_email, 
    download_csv, 
    calculate_values, 
    save_to_hadoop, 
    load_from_hadoop,
    generate_url
)
from unittest.mock import patch

# Teste para a função de envio de e-mail
def test_send_email():
    with patch('smtplib.SMTP') as mock_smtp:
        send_email('Teste', 'Corpo do e-mail de teste', high_priority=True)
        instance = mock_smtp.return_value
        assert instance.sendmail.called

# Teste para a função de geração de URL
def test_generate_url():
    date = "20240101"
    url = generate_url(date)
    assert url == "https://www4.bcb.gov.br/Download/fechamento/20240101.csv"

# Teste para a função de download de CSV
def test_download_csv():
    df = download_csv("20240101")  # Data fictícia para teste
    assert df is not None
    assert isinstance(df, pd.DataFrame)

# Teste para a função de cálculo de valores
def test_calculate_values():
    data = {
        'Tipo': ['A', 'B'],
        'Taxa Compra': [5.0, 3.0],
        'Taxa Venda': [5.1, 3.1],
        'Paridade Compra': [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    result_df = calculate_values(df)
    assert 'Valor em US$' in result_df.columns
    assert 'Valor em R$' in result_df.columns
    assert result_df['Valor em US$'].iloc[0] == 5.0  # Para Tipo A
    assert result_df['Valor em US$'].iloc[1] == 6.0  # Para Tipo B

# Teste para salvar e carregar dados no Hadoop
def test_hadoop_operations():
    data = {
        'Data': ['20240101'],
        'Moeda': ['USD'],
        'Tipo': ['A'],
        'Valor em R$': [5.0],
        'Valor em US$': [1.0]
    }
    df = pd.DataFrame(data)
    
    # Salvando no Hadoop
    save_to_hadoop(df, 'test_file')
    
    # Carregando do Hadoop
    loaded_df = load_from_hadoop('test_file')
    assert not loaded_df.empty
    assert loaded_df.equals(df)
```

### Testes de Integração

Os testes de integração verificam a funcionalidade completa do sistema, garantindo que todas as partes trabalham juntas como esperado.

#### Arquivo `test_integration.py`

```python
import pytest
from script_cotacoes import fetch_data_save_and_upload

def test_fetch_data_save_and_upload():
    try:
        # Executa a função principal e verifica se ela retorna um DataFrame não vazio.
        df = fetch_data_save_and_upload()
        assert not df.empty
    except Exception as e:
        pytest.fail(f"Falha no teste de integração: {e}")
```

### Executando os Testes

Para rodar todos os testes unitários e de integração, execute o seguinte comando:

```bash
pytest
```

## Validação

Valide se o script está funcionando corretamente com um conjunto de dados menor (ex: 7 dias). Verifique se os arquivos Parquet estão sendo gerados corretamente no Hadoop e se o arquivo de cotações é carregado corretamente no Google Drive.

## Licença

Este projeto está licenciado sob os termos da licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
