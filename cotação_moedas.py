import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from hdfs import InsecureClient
import pyarrow as pa
import pyarrow.parquet as pq
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração do Hadoop
HADOOP_HOST = 'http://localhost:50070'  # Alterar para o endereço do seu cluster Hadoop
HADOOP_USER = 'user'
HADOOP_PATH = '/user/data/cotacoes/'

# Configurando cliente Hadoop
client = InsecureClient(HADOOP_HOST, user=HADOOP_USER)

# Autenticação do Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Configurações de e-mail
EMAIL_USER = 'seu_email@gmail.com'  # Seu e-mail de envio
EMAIL_PASSWORD = 'sua_senha'  # Senha do seu e-mail de envio
EMAIL_RECIPIENT = 'destinatario@gmail.com'  # E-mail para notificação

# Função para enviar e-mail
def send_email(subject, body, high_priority=False):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = subject
    if high_priority:
        msg['X-Priority'] = '1'
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, EMAIL_RECIPIENT, msg.as_string())
        server.quit()
        print(f'E-mail enviado com sucesso para {EMAIL_RECIPIENT}')
    except Exception as e:
        print(f'Erro ao enviar e-mail: {e}')

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
    except requests.exceptions.HTTPError:
        return None
    except Exception:
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

# Função para salvar dataframe como Parquet no Hadoop
def save_to_hadoop(df, file_name):
    table = pa.Table.from_pandas(df)
    with client.write(f"{HADOOP_PATH}{file_name}.parquet", overwrite=True) as writer:
        pq.write_table(table, writer)

# Função para carregar dataframe do Hadoop
def load_from_hadoop(file_name):
    with client.read(f"{HADOOP_PATH}{file_name}.parquet") as reader:
        table = pq.read_table(reader)
    return table.to_pandas()

# Função para upload de um arquivo ao Google Drive
def upload_to_drive(file_path, file_name):
    file_drive = drive.CreateFile({'title': file_name})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"Upload completo: {file_name}")

# Função para salvar e enviar para o Google Drive
def save_and_upload_to_drive(df):
    file_path = '/tmp/cotacoes_diarias.csv'  # Caminho local temporário
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    upload_to_drive(file_path, 'cotacoes_diarias.csv')

# Função principal para obter os dados e salvar no Hadoop e Google Drive
def fetch_data_save_and_upload():
    try:
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
                    expected_columns = ['Data', 'Cod Moeda', 'Tipo', 'Moeda', 'Taxa Compra', 'Taxa Venda', 'Paridade Compra', 'Paridade Venda']
                    if len(df.columns) == len(expected_columns):
                        df.columns = expected_columns
                        df = calculate_values(df)
                        dataframes[date] = df
                        weekdays_count += 1
            days_checked += 1

        # Concatenando todos os DataFrames em um único DataFrame
        final_df = pd.concat(dataframes.values())
        
        # Salvando no Hadoop
        save_to_hadoop(final_df, 'cotacoes_diarias')
        
        # Salvando e subindo para o Google Drive
        save_and_upload_to_drive(final_df)
        
        # Envio de e-mail de sucesso
        send_email(
            subject='Upload de Cotações - Sucesso',
            body='O arquivo de cotações foi enviado com sucesso para o Google Drive.'
        )
        
        return final_df

    except Exception as e:
        # Envio de e-mail de erro com log
        send_email(
            subject='Erro no Script de Cotações - ALTA PRIORIDADE',
            body=f'Ocorreu um erro durante a execução do script de cotações. Log do erro:\n\n{str(e)}',
            high_priority=True
        )
        raise e

# Inicializando o Dash
app = Dash(__name__)

# Obtendo os dados e realizando o upload
df = fetch_data_save_and_upload()

# Layout da aplicação
app.layout = html.Div([
    html.H1("Visualização de Cotações de Moedas"),
    dcc.Dropdown(
        id='moeda-dropdown',
        options=[{'label': moeda, 'value': moeda} for moeda in df['Moeda'].unique()],
        value=df['Moeda'].unique()[0]  # Valor padrão
    ),
    dcc.RadioItems(
        id='valor-radio',
        options=[
            {'label': 'Valor em R$', 'value': 'Valor em R$'},
            {'label': 'Valor em US$', 'value': 'Valor em US$'}
        ],
        value='Valor em R$',  # Valor padrão
        labelStyle={'display': 'block'}
    ),
    dcc.Graph(id='grafico-moeda')
])

# Callback para atualizar o gráfico
@app.callback(
    Output('grafico-moeda', 'figure'),
    Input('moeda-dropdown', 'value'),
    Input('valor-radio', 'value')
)
def update_graph(moeda_selecionada, valor_tipo):
    filtered_df = df[df['Moeda'] == moeda_selecionada]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_df['Data'],
        y=filtered_df[valor_tipo],
        mode='lines+markers',
        name=moeda_selecionada
    ))

    fig.update_layout(
        title=f'Valor da {moeda_selecionada} ao longo do tempo',
        xaxis_title='Data',
        yaxis_title=valor_tipo,
        xaxis_tickformat='%Y-%m-%d',
        template='plotly_white'
    )

    return fig

# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True)
