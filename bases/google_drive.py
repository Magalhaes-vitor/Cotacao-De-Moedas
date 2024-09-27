from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Autenticação do Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Função para upload de um arquivo ao Google Drive
def upload_to_drive(file_path, file_name):
    file_drive = drive.CreateFile({'title': file_name})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"Upload completo: {file_name}")

# Salvando o DataFrame em CSV e enviando para o Google Drive
def save_and_upload_to_drive(df):
    file_path = '/tmp/cotacoes_diarias.csv'  # Caminho local temporário
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    upload_to_drive(file_path, 'cotacoes_diarias.csv')

# Modificando a função fetch_data para incluir o upload
def fetch_data_save_and_upload():
    df = fetch_data_and_save()
    save_and_upload_to_drive(df)
    return df

# Obtendo os dados e realizando o upload
df = fetch_data_save_and_upload()
