from hdfs import InsecureClient
import pyarrow as pa
import pyarrow.parquet as pq

# Configuração do Hadoop
HADOOP_HOST = 'http://localhost:50070'  # Alterar para o endereço do seu cluster Hadoop
HADOOP_USER = 'user'
HADOOP_PATH = '/user/data/cotacoes/'

# Conectando ao cliente Hadoop
client = InsecureClient(HADOOP_HOST, user=HADOOP_USER)

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

# Modificando a função fetch_data para salvar os dados no Hadoop
def fetch_data_and_save():
    df = fetch_data()
    # Salvando os dados no Hadoop
    save_to_hadoop(df, 'cotacoes_diarias')
    return df

# Obtendo os dados a partir do Hadoop (se necessário)
# df = load_from_hadoop('cotacoes_diarias')
