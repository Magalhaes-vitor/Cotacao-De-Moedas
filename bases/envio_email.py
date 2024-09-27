import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurações do e-mail
smtp_server = "smtp.exemplo.com"
smtp_port = 587
smtp_user = "usuario@exemplo.com"
smtp_password = "senha"
to_email = "destinatario@exemplo.com"

# Criar o e-mail
msg = MIMEMultipart()
msg['From'] = smtp_user
msg['To'] = to_email
msg['Subject'] = "Alerta de Dados Financeiros"

body = "Os dados financeiros foram atualizados com sucesso."
msg.attach(MIMEText(body, 'plain'))

# Enviar o e-mail
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.send_message(msg)
