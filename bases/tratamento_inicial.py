import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import logging

# Configuração de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para gerar a URL com a data
def generate_url(date):
    base_url = "https://www4.bcb.gov.br/Download/fechamento/"
    return f"{base_url}{date}.csv"

# Função para fazer o download e retornar um dataframe a partir do CSV
def download_csv(date):
    url = generate_url(date)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.content.decode('latin1')
        df = pd.read_csv(StringIO(data), sep=';', decimal=',')
        return df
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logging.warning(f"Dados não encontrados para a data {date} (Erro 404).")
        else:
            logging.error(f"Erro HTTP ao baixar dados para a data {date}: {http_err}")
        return None
    except Exception as e:
        logging.error(f"Erro ao processar dados para a data {date}: {e}")
        return None

# Função para calcular os valores em US$ e R$
def calculate_values(df):
    df['Valor em US$'] = 0
    df['Valor em R$'] = 0

    # Para Moedas do Tipo A
    df_a = df[df['Tipo'] == 'A'].copy()
    df.loc[df['Tipo'] == 'A', 'Valor em US$'] = df_a['Taxa Compra'] / df_a['Paridade Compra']
    df.loc[df['Tipo'] == 'A', 'Valor em R$'] = df_a['Taxa Compra'] * df_a['Taxa Venda']

    # Para Moedas do Tipo B
    df_b = df[df['Tipo'] == 'B'].copy()
    df.loc[df['Tipo'] == 'B', 'Valor em US$'] = df_b['Taxa Compra'] * df_b['Paridade Compra']
    df.loc[df['Tipo'] == 'B', 'Valor em R$'] = df_b['Taxa Compra'] * df_b['Taxa Venda']

    return df

# Função para salvar os dados em um único arquivo Excel
def save_to_excel(dataframes, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        workbook = writer.book
        format_header = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3'})
        format_row1 = workbook.add_format({'bg_color': '#FFEB9C'})
        format_row2 = workbook.add_format({'bg_color': '#CCCCCC'})

        for date, df in dataframes.items():
            if df is not None and not df.empty:
                expected_columns = ['Data', 'Cod Moeda', 'Tipo', 'Moeda', 'Taxa Compra', 'Taxa Venda', 'Paridade Compra', 'Paridade Venda']
                if len(df.columns) == len(expected_columns):
                    df.columns = expected_columns
                else:
                    logging.warning(f"Número de colunas não corresponde para a data {date}. Esperado: {len(expected_columns)}, encontrado: {len(df.columns)}.")
                    continue  # Ignora esta data

                df = calculate_values(df)

                # Ordena pelo código da moeda
                df = df.sort_values(by='Cod Moeda')

                # Escreve o DataFrame na planilha
                df.to_excel(writer, sheet_name=date.replace('-', ''), index=False, header=False)

                # Adiciona cabeçalho
                worksheet = writer.sheets[date.replace('-', '')]
                worksheet.write_row(0, 0, df.columns, format_header)

                # Aplica a formatação nas linhas
                num_rows = df.shape[0]
                for i in range(num_rows):
                    row_format = format_row1 if i % 2 == 0 else format_row2
                    for col in range(len(df.columns)):
                        worksheet.write(i + 1, col, df.iloc[i, col], row_format)

                logging.info(f"Dados salvos para a data: {date}")

# Função principal
def fetch_and_save_last_365_days():
    today = datetime.now()
    dataframes = {}
    weekdays_count = 0
    days_checked = 0

    while weekdays_count < 365:
        date = (today - timedelta(days=days_checked)).strftime('%Y%m%d')
        day_of_week = (today - timedelta(days=days_checked)).weekday()

        if day_of_week < 5:  # Dias úteis
            df = download_csv(date)
            if df is not None:
                dataframes[date] = df
                weekdays_count += 1
        else:
            logging.info(f"Data {date} ignorada (Fim de semana).")

        days_checked += 1

    save_to_excel(dataframes, 'cotacoes_ultimos_365_dias_uteis.xlsx')
    logging.info("Dados salvos com sucesso no arquivo 'cotacoes_ultimos_365_dias_uteis.xlsx'.")

# Executar o script
if __name__ == "__main__":
    fetch_and_save_last_365_days()