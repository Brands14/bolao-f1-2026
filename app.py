import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import urllib.request
import urllib.error
import json
import base64
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")

# 🚨 MUDE AQUI: Coloque exatamente o seu nome de usuário do GitHub dentro das aspas!
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.png", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

participantes = [
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", 
    "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", 
    "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", 
    "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", 
    "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"
]

# DICIONÁRIO DE SEGURANÇA
emails_autorizados = {
    "Alaerte Fleury": "alaertefleury@hotmail.com",
    "César Gaudie": "c3sargaudie@gmail.com",
    "Delvânia Belo": "del.gomes04@gmail.com",
    "Emilio Jacinto": "emiliopaja@gmail.com",
    "Fabrício Abe": "fabricio.fleury84@gmail.com",
    "Fausto Fleury": "faustofleury.perito@gmail.com",
    "Fernanda Fleury": "fefleury17@gmail.com",
    "Flávio Soares": "flaviosoaresparente@gmail.com",
    "Frederico Gaudie": "fredericofleury@gmail.com",
    "George Fleury": "gfleury@gmail.com",
    "Henrique Junqueira": "amtelegas@gmail.com",
    "Hilton Jacinto": "hiltonlpj2@hotmail.com",
    "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com",
    "Luciano (Medalha)": "luciano.pallada@terra.com.br",
    "Maikon Miranda": "maikonmiranda@gmail.com",
    "Myke Ribeiro": "mribeiro3088@gmail.com",
    "Rodolfo Brandão": "rodolfo.fleury@gmail.com",
    "Ronaldo Fleury": "ronaldofleury18@gmail.com",
    "Syllas Araújo": "sylaopoim@gmail.com",
    "Valério Bimbato": "bimbatovalerio2@gmail.com"
}

equipes = {
    "Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"],
    "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"],
    "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"],
    "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"],
    "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"],
    "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"],
    "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"],
    "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"],
    "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"],
    "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]
}

pilotos = [
    "", 
    "Max Verstappen", "Isack Hadjar",
    "Lewis Hamilton", "Charles Leclerc",
    "George Russell", "Kimi Antonelli",
    "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Lance Stroll",
    "Gabriel Bortoleto", "Nico Hülkenberg",
    "Alex Albon", "Carlos Sainz",
    "Pierre Gasly", "Franco Colapinto",
    "Oliver Bearman", "Esteban Ocon",
    "Liam Lawson", "Arvid Lindblad",
    "Sergio Pérez", "Valtteri Bottas",
    "Nenhum / Outro"
]

lista_gps = [
    "Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", 
    "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", 
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", 
    "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# 2. Motor de Banco de Dados Permanente (GitHub API)
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content)), data['sha']
    except urllib.error.HTTPError:
        return pd.DataFrame(), None

def guardar_dados(dados, arquivo):
    df_atual, sha = ler_dados(arquivo)
    df_novo = pd.DataFrame([dados])

    if not df_atual.empty:
        if 'Usuario' in dados:
            mascara = ~((df_atual['GP'] == dados['GP']) & 
                        (df_atual['Tipo'] == dados['Tipo']) & 
                        (df_atual['Usuario'] == dados['Usuario']))
        else:
            mascara = ~((df_atual['GP'] == dados['GP']) & 
                        (df_atual['Tipo'] == dados['Tipo']))
            
        df_atual = df_atual[mascara]
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    csv_content = df_final.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    payload = {
        "message": f"Atualizando registro no banco: {arquivo}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    }, method="PUT")

    try:
        with urllib.request.urlopen(req) as response:
            return response.status in [200, 201]
    except urllib.error.HTTPError as e:
        st.error(f"Erro na nuvem: {e}")
        return False

# Função auxiliar para deletar registro completo (reescrever arquivo sem a linha)
def deletar_registro_github(arquivo, mascara_filtro):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        df_final = df_atual[mascara_filtro]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {
            "message": f"Removendo registro no banco: {arquivo}",
            "content": encoded_content,
            "sha": sha
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }, method="PUT")
        try:
            with urllib.request.urlopen(req) as response:
                return response.status in [200, 201]
        except:
            return False
    return False

# 3. Disparador de E-mails
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    
    corpo = f"""
    Olá {dados['Usuario']},
    
    Seu palpite foi registrado com sucesso pelo VAR do nosso sistema!
    Abaixo está a cópia oficial do seu envio.
    
    --- DETALHES DO REGISTRO ---
    Grande Prêmio: {dados['GP']}
    Sessão: {dados['Tipo']}
    Data e Hora Exata do Envio: {dados['Data_Envio']}
    
    --- SEU PALPITE ---
    """
    
    if "Pole" in dados['Tipo']:
        corpo += f"Pole Position: {dados.get('Pole', '')}\n"
    elif "Corrida Principal" == dados['Tipo']:
        corpo += f"1º Colocado: {dados.get('P1', '')}\n2º Colocado: {dados.get('P2', '')}\n3º Colocado: {dados.get('P3', '')}\n"
        corpo += f"4º Colocado: {dados.get('P4', '')}\n5º Colocado: {dados.get('P5', '')}\n6º Colocado: {dados.get('P6', '')}\n"
        corpo += f"7º Colocado: {dados.get('P7', '')}\n8º Colocado: {dados.get('P8', '')}\n9º Colocado: {dados.get('P9', '')}\n10º Colocado: {dados.get('P10', '')}\n"
        corpo += f"\nMelhor Volta: {dados.get('VoltaRapida', '')}\n1º Abandono: {dados.get('PrimeiroAbandono', '')}\nMais Ultrapassagens: {dados.get('MaisUltrapassagens', '')}\n"
    elif "Corrida Sprint" == dados['Tipo']:
        corpo += f"1º Colocado: {dados.get('P1', '')}\n2º Colocado: {dados.get('P2', '')}\n3º Colocado: {dados.get('P3', '')}\n4º Colocado: {dados.get('P4', '')}\n"
        corpo += f"5º Colocado: {dados.get('P5', '')}\n6º Colocado: {dados.get('P6', '')}\n7º Colocado: {dados.get('P7', '')}\n8º Colocado: {dados.get('P8', '')}\n"
        
    corpo += "\n\nEste é um e-mail automático. Em caso de dúvidas, procure a Direção de Prova (Fabrício ou Rodolfo)."
    
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# 4. Matemática das Sessões
def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    if val_p and val_p == val_g:
        return valor_pontos
    return 0

def calcular_pontos_sessao(palpite, gabarito):
    pontos = 0
    tipo = palpite.get('Tipo', '')
    
    if "Classificação" in tipo or "Qualy Sprint" in tipo:
        pontos += check_ponto(palpite, gabarito, 'Pole', 100)
        
    elif tipo == "Corrida Principal":
        pontos += check_ponto(palpite, gabarito, 'P1', 150)
        pontos += check_ponto(palpite, gabarito, 'P2', 125)
        pontos += check_ponto(palpite, gabarito, 'P3', 100)
        pontos += check_ponto(palpite, gabarito, 'P4', 85)
        pontos += check_ponto(palpite, gabarito, 'P5', 70)
        pontos += check_ponto(palpite, gabarito, 'P6', 60)
        pontos += check_ponto(palpite, gabarito, 'P7', 50)
        pontos += check_ponto(palpite, gabarito, 'P8', 40)
        pontos += check_ponto(palpite, gabarito, 'P9', 25)
        pontos += check_ponto(palpite, gabarito, 'P10', 15)
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
        
        top10_p = [str(palpite.get(f'P{i}', '')).strip() for i in range(1, 11)]
        top10_g = [str(gabarito.get(f'P{i}', '')).strip() for i in range(1, 11)]
        
        if all(top10_p) and all(top10_g):
            if top10_p == top10_g: pontos += 600
            elif top10_p[:5] == top10_g[:5]: pontos += 450
            elif top10_p[:3] == top10_g[:3]: pontos += 300
            
    elif tipo == "Corrida Sprint":
        pontos += check_ponto(palpite, gabarito, 'P1', 80)
        pontos += check_ponto(palpite, gabarito, 'P2', 70)
        pontos += check_ponto(palpite, gabarito, 'P3', 60)
        pontos += check_ponto(palpite, gabarito, 'P4', 50)
        pontos += check_ponto(palpite, gabarito, 'P5', 40)
        pontos += check_ponto(palpite, gabarito, 'P6', 30)
        pontos += check_ponto(palpite, gabarito, 'P7', 20)
        pontos += check_ponto(palpite, gabarito, 'P8', 10)
        
    return pontos

# 5. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        if gp_selecionado in sprint_gps:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"]
        else:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal"]
            
        with col_tipo:
            tipo_sessao = st.selectbox("Tipo de Sessão (Selecione a fase atual):", opcoes_sessao)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            volta_rapida = primeiro_abandono = mais_ultrapassagens = ""
            
            if "Pole" in tipo_sessao:
                st.info("📌 Palpite apenas para a Pole Position desta sessão.")
                pole = st.selectbox("Pole Position:", pilotos)
                
            elif tipo_sessao == "Corrida Principal":
                st.info("📌 Palpite para a Corrida de Domingo.")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    p9 = st.selectbox("9º Colocado:", pilotos)
                    p10 = st.selectbox("10º Colocado:", pilotos)
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos)
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos)
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos)
                    
            elif tipo_sessao == "Corrida Sprint":
                st.info("📌 Palpite para a Corrida Sprint (Top 8).")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)

            st.divider()
            st.markdown("🔒 **Assinatura de Segurança**")
            email_confirmacao = st.text_input("Digite o seu E-mail cadastrado para validar o palpite:", type="password")
            
            enviado = st.form_submit_button(f"Salvar Palpite - {tipo_sessao} 🏁")
            
            if enviado:
                email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                email_digitado = email_confirmacao.strip().lower()
                
                if email_digitado == email_correto and email_correto != "":
                    st.info("Gravando permanentemente no cofre do GitHub e gerando recibos... Aguarde!")
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        email_enviado = enviar_recibo_email(dados, email_correto)
                        if email_enviado:
                            st.success(f"Palpite de {tipo_sessao} salvo! Recibo enviado para o seu e-mail e para a Direção de Prova.")
                        else:
                            st.warning(f"Palpite salvo no banco com sucesso, mas houve uma falha ao enviar o recibo por e-mail.")
                    else:
                        st.error("Falha ao salvar no banco permanente. Fale com a Direção de Prova.")
                else:
                    st.error("🚫 Acesso Negado: E-mail incorreto.")

    else:
        st.info("Selecione o seu nome no menu lateral para começar.")

# --- ÁREA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.header("🕵️ Meu Histórico de Palpites")
    st.write("Consulte aqui todos os palpites que você já enviou. Os dados agora são permanentes!")
    
    usuario_consulta = st.selectbox("Selecione o seu nome:", [""] + participantes)
    
    if usuario_consulta:
        email_consulta = st.text_input("Digite o seu E-mail cadastrado para abrir o cofre:", type="password")
        
        if st.button("Buscar Meus Palpites 🔍"):
            email_correto = emails_autorizados.get(usuario_consulta, "").strip().lower()
            email_digitado = email_consulta.strip().lower()
            
            if email_digitado == email_correto and email_correto != "":
                df_todos, _ = ler_dados(ARQUIVO_DADOS)
                if not df_todos.empty:
                    meus_dados = df_todos[df_todos['Usuario'] == usuario_consulta]
                    if not meus_dados.empty:
                        st.success("Cofre aberto com sucesso!")
                        meus_dados_view = meus_dados.drop(columns=['Usuario', 'Equipe'])
                        st.dataframe(meus_dados_view, use_container_width=True)
                    else:
                        st.warning("Você ainda não enviou nenhum palpite.")
                else:
                    st.info("Nenhum palpite registrado no banco permanente ainda.")
            else:
                st.error("🚫 Acesso Negado: O e-mail não confere.")

# --- ÁREA: CLASSIFICAÇÕES E RAIO-X ---
elif menu == "Classificações":
    st.header("🏆 Classificações do Campeonato F1 2026")
    
    df_palpites, _ = ler_dados(ARQUIVO_DADOS)
    df_gabaritos, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if not df_palpites.empty and not df_gabaritos.empty:
        resultados = []
        for index_p, row_p in df_palpites.iterrows():
            gp = row_p.get('GP', '')
            tipo = row_p.get('Tipo', '')
            
            gabarito_match = df_gabaritos[(df_gabaritos['GP'] == gp) & (df_gabaritos['Tipo'] == tipo)]
            
            if not gabarito_match.empty:
                gabarito_oficial = gabarito_match.iloc[-1]
                pontos = calcular_pontos_sessao(row_p, gabarito_oficial)
                resultados.append({"Usuario": row_p['Usuario'], "Equipe": row_p.get('Equipe', 'Sem Equipe'), "Pontos": pontos, "GP": gp})
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            st.markdown("### 🔍 Filtro de Resultados")
            filtro_classificacao = st.selectbox("Selecione a visualização desejada:", ["Geral (Campeonato Completo)"] + lista_gps)
            
            if filtro_classificacao != "Geral (Campeonato Completo)":
                df_resultados = df_resultados[df_resultados["GP"] == filtro_classificacao]
                st.subheader(f"📊 Resultado Específico: GP de {filtro_classificacao}")
            else:
                st.subheader("📊 Classificação Geral do Campeonato")
            
            if not df_resultados.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**👤 Mundial de Pilotos**")
                    ranking_geral = df_resultados.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    ranking_geral.index = range(1, len(ranking_geral) + 1)
                    st.dataframe(ranking_geral, use_container_width=True)
                    
                with col2:
                    st.markdown("**🏎️ Mundial de Construtores**")
                    ranking_equipas = df_resultados.groupby('Equipe')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                    st.dataframe(ranking_equipas, use_container_width=True)
            else:
                st.warning(f"Ainda não há pontuações calculadas para o GP de {filtro_classificacao}.")
                
            st.divider()
            st.subheader("🕵️‍♂️ Raio-X dos Palpites (Auditoria Pública)")
            col_rx1, col_rx2 = st.columns(2)
            with col_rx1:
                rx_gp = st.selectbox("Selecione o GP para o Raio-X:", lista_gps)
            with col_rx2:
                rx_opcoes = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if rx_gp in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
                rx_tipo = st.selectbox("Sessão do Raio-X:", rx_opcoes)
                
            gabarito_rx = df_gabaritos[(df_gabaritos['GP'] == rx_gp) & (df_gabaritos['Tipo'] == rx_tipo)]
            
            if not gabarito_rx.empty:
                gabarito_oficial_rx = gabarito_rx.iloc[-1]
                palpites_rx = df_palpites[(df_palpites['GP'] == rx_gp) & (df_palpites['Tipo'] == rx_tipo)]
                
                if not palpites_rx.empty:
                    usuarios_que_palpitaram = sorted(palpites_rx['Usuario'].unique())
                    rx_usuario = st.selectbox("Selecione o Palpiteiro para abrir o Raio-X:", [""] + usuarios_que_palpitaram)
                    
                    if rx_usuario:
                        palpite_usuario = palpites_rx[palpites_rx['Usuario'] == rx_usuario].iloc[-1]
                        st.markdown(f"**Comparativo: Palpite de {rx_usuario} vs Gabarito Oficial**")
                        
                        chaves_comparacao = []
                        if "Pole" in rx_tipo: chaves_comparacao = ['Pole']
                        elif "Corrida Principal" == rx_tipo: chaves_comparacao = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'VoltaRapida', 'PrimeiroAbandono', 'MaisUltrapassagens']
                        elif "Corrida Sprint" == rx_tipo: chaves_comparacao = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']
                            
                        for chave in chaves_comparacao:
                            val_p = str(palpite_usuario.get(chave, '')).strip()
                            val_g = str(gabarito_oficial_rx.get(chave, '')).strip()
                            nome_chave = chave.replace('P', 'º Colocado').replace('VoltaRapida', 'Melhor Volta').replace('PrimeiroAbandono', '1º Abandono').replace('MaisUltrapassagens', 'Mais Ultrapassagens')
                            
                            if val_p == val_g and val_p != "" and val_p != "nan":
                                st.success(f"✅ **{nome_chave}:** {val_p}")
                            else:
                                if val_p == "" or val_p == "nan": val_p = "Em branco"
                                st.error(f"❌ **{nome_chave}:** Apostou em *{val_p}* | Oficial: **{val_g}**")
                else:
                    st.info("Ninguém enviou palpite para esta sessão.")
            else:
                st.warning("🔒 O Raio-X ainda está bloqueado (Sem Gabarito).")
    else:
        st.warning("Banco de dados permanente está vazio.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha de Diretor de Prova:", type="password")
    
    if senha == "fleury1475":
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO (DADOS PERMANENTES)")
        
        tab1, tab2, tab3 = st.tabs(["Auditoria de Palpites", "Gabaritos Oficiais", "Limpeza de Dados"])
        
        with tab1:
            st.subheader("🕵️‍♂️ Auditoria: Palpites da Turma")
            filtro_gp_auditoria = st.selectbox("Filtrar Auditoria por GP:", ["Todos os GPs"] + lista_gps)
            df_auditoria, _ = ler_dados(ARQUIVO_DADOS)
            if not df_auditoria.empty:
                if filtro_gp_auditoria != "Todos os GPs":
                    df_auditoria = df_auditoria[df_auditoria["GP"] == filtro_gp_auditoria]
                st.dataframe(df_auditoria, use_container_width=True)
            else:
                st.info("Sem palpites.")

        with tab2:
            st.header("🏆 Inserir Gabarito Oficial")
            col_gp_a, col_tipo_a = st.columns(2)
            with col_gp_a: gp_admin = st.selectbox("GP do Gabarito:", lista_gps, key="gp_adm")
            opcoes_admin = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_admin in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
            with col_tipo_a: tipo_admin = st.selectbox("Sessão do Gabarito:", opcoes_admin, key="tipo_adm")
            
            with st.form("form_gabarito"):
                pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
                volta_rapida = primeiro_abandono = mais_ultrapassagens = ""
                if "Pole" in tipo_admin: pole = st.selectbox("Pole Position Oficial:", pilotos)
                elif "Corrida Principal" in tipo_admin:
                    c1, c2 = st.columns(2)
                    with c1:
                        p1, p2, p3, p4, p5 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(1, 6)]
                    with c2:
                        p6, p7, p8, p9, p10 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(6, 11)]
                        volta_rapida = st.selectbox("Melhor Volta:", pilotos)
                        primeiro_abandono = st.selectbox("1º Abandono:", pilotos)
                        mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos)
                elif "Corrida Sprint" in tipo_admin:
                    c1, c2 = st.columns(2)
                    with c1: p1, p2, p3, p4 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(1, 5)]
                    with c2: p5, p6, p7, p8 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(5, 9)]
                
                if st.form_submit_button("Salvar Gabarito Oficial 🏆"):
                    dados_g = {"GP": gp_admin, "Tipo": tipo_admin, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens}
                    if guardar_dados(dados_g, ARQUIVO_GABARITOS): st.success("Gabarito Salvo!")

        with tab3:
            st.header("🗑️ Apagar Registros")
            df_limpeza, _ = ler_dados(ARQUIVO_DADOS)
            if not df_limpeza.empty:
                col_del_gp, col_del_sessao = st.columns(2)
                with col_del_gp: gp_del = st.selectbox("GP para excluir:", lista_gps, key="del_gp")
                with col_del_sessao: sessao_del = st.selectbox("Sessão para excluir:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="del_sessao")
                
                palpites_filtrados = df_limpeza[(df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del)]
                
                if not palpites_filtrados.empty:
                    user_del = st.selectbox("Selecione o usuário para APAGAR o palpite:", [""] + sorted(palpites_filtrados['Usuario'].tolist()), key="del_user")
                    if user_del != "":
                        if st.button(f"CONFIRMAR EXCLUSÃO DE {user_del}", type="primary"):
                            mascara = ~((df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del) & (df_limpeza['Usuario'] == user_del))
                            if deletar_registro_github(ARQUIVO_DADOS, mascara):
                                st.success("Palpite removido com sucesso!")
                                st.rerun()
                else:
                    st.info("Nenhum palpite encontrado para este GP/Sessão.")

    elif senha != "":
        st.error("Senha incorreta.")
