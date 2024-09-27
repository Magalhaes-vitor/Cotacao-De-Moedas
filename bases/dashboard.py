import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

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

# Função principal para obter os dados
def fetch_data():
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

    return pd.concat(dataframes.values())

# Inicializando o Dash
app = Dash(__name__)

# Obtendo os dados
df = fetch_data()

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
