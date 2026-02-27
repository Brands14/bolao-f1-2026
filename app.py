import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")
ARQUIVO_DADOS = "palpites_db.csv"
ARQUIVO_GABARITOS = "gabaritos_db.csv"

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.jpeg", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

participantes = [
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", 
    "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", 
    "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", 
    "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", 
    "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"
]

# DICIONÁRIO DE SEGURANÇA: Substitua pelos e-mails reais de cada um antes de salvar!
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

# Equipes formatadas com o número e os primeiros nomes
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

# 2. Funções do Banco de Dados e Matemática
def guardar_dados(dados, arquivo):
    df = pd.DataFrame([dados])
    if not os.path.exists(arquivo):
        df.to_csv(arquivo, index=False)
    else:
        df.to_csv(arquivo, mode='a', header=False, index=False)

def calcular_pontos_corrida(palpite, gabarito):
    pontos = 0
    if str(palpite.get('Pole', '')).strip() == str(gabarito.get('Pole', '')).strip(): pontos += 100
    if str(palpite.get('P1', '')).strip() == str(gabarito.get('P1', '')).strip(): pontos += 150
    if str(palpite.get('P2', '')).strip() == str(gabarito.get('P2', '')).strip(): pontos += 125
    if str(palpite.get('P3', '')).strip() == str(gabarito.get('P3', '')).strip(): pontos += 100
    if str(palpite.get('P4', '')).strip() == str(gabarito.get('P4', '')).strip(): pontos += 85
    if str(palpite.get('P5', '')).strip() == str(gabarito.get('P5', '')).strip(): pontos += 70
    if str(palpite.get('P6', '')).strip() == str(gabarito.get('P6', '')).strip(): pontos += 60
    if str(palpite.get('P7', '')).strip() == str(gabarito.get('P7', '')).strip(): pontos += 50
    if str(palpite.get('P8', '')).strip() == str(gabarito.get('P8', '')).strip(): pontos += 40
    if str(palpite.get('P9', '')).strip() == str(gabarito.get('P9', '')).strip(): pontos += 25
    if str(palpite.get('P10', '')).strip() == str(gabarito.get('P10', '')).strip(): pontos += 15
    
    if str(palpite.get('VoltaRapida', '')).strip() == str(gabarito.get('VoltaRapida', '')).strip(): pontos += 75
    if str(palpite.get('PrimeiroAbandono', '')).strip() == str(gabarito.get('PrimeiroAbandono', '')).strip(): pontos += 200
    if str(palpite.get('MaisUltrapassagens', '')).strip() == str(gabarito.get('MaisUltrapassagens', '')).strip(): pontos += 75
    
    top10_palpite = [str(palpite.get(f'P{i}', '')).strip() for i in range(1, 11)]
    top10_gabarito = [str(gabarito.get(f'P{i}', '')).strip() for i in range(1, 11)]
    
    if "" not in top10_palpite:
        if top10_palpite == top10_gabarito:
            pontos += 600
        elif top10_palpite[:5] == top10_gabarito[:5]:
            pontos += 450
        elif top10_palpite[:3] == top10_gabarito[:3]:
            pontos += 300
    return pontos

def calcular_pontos_sprint(palpite, gabarito):
    pontos = 0
    if str(palpite.get('Pole', '')).strip() == str(gabarito.get('Pole', '')).strip(): pontos += 100
    if str(palpite.get('P1', '')).strip() == str(gabarito.get('P1', '')).strip(): pontos += 80
    if str(palpite.get('P2', '')).strip() == str(gabarito.get('P2', '')).strip(): pontos += 70
    if str(palpite.get('P3', '')).strip() == str(gabarito.get('P3', '')).strip(): pontos += 60
    if str(palpite.get('P4', '')).strip() == str(gabarito.get('P4', '')).strip(): pontos += 50
    if str(palpite.get('P5', '')).strip() == str(gabarito.get('P5', '')).strip(): pontos += 40
    if str(palpite.get('P6', '')).strip() == str(gabarito.get('P6', '')).strip(): pontos += 30
    if str(palpite.get('P7', '')).strip() == str(gabarito.get('P7', '')).strip(): pontos += 20
    if str(palpite.get('P8', '')).strip() == str(gabarito.get('P8', '')).strip(): pontos += 10
    return pontos

# 3. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        opcoes_sessao = ["Corrida Principal", "Corrida Sprint"] if gp_selecionado in sprint_gps else ["Corrida Principal"]
        
        with col_tipo:
            tipo_sessao = st.radio("Tipo de Sessão:", opcoes_sessao, horizontal=True)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        if tipo_sessao == "Corrida Principal":
            with st.form("form_palpite_corrida"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.selectbox("Pole Position:", pilotos)
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
                
                st.divider()
                st.markdown("🔒 **Assinatura de Segurança**")
                email_confirmacao = st.text_input("Digite seu E-mail cadastrado para validar o palpite:", type="password")
                
                enviado = st.form_submit_button("Salvar Palpite da Corrida 🏁")
                
                if enviado:
                    email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                    email_digitado = email_confirmacao.strip().lower()
                    
                    if email_digitado == email_correto and email_correto != "":
                        dados = {
                            "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                            "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                            "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                            "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                            "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                        }
                        guardar_dados(dados, ARQUIVO_DADOS)
                        st.success(f"Autenticação confirmada! Palpite para a {tipo_sessao} do GP {gp_selecionado} registrado com sucesso!")
                    else:
                        st.error("🚫 Acesso Negado: O e-mail informado não corresponde ao usuário selecionado. O palpite NÃO foi salvo.")
                    
        elif tipo_sessao == "Corrida Sprint":
            with st.form("form_palpite_sprint"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.selectbox("Pole Sprint:", pilotos)
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
                email_confirmacao = st.text_input("Digite seu E-mail cadastrado para validar o palpite:", type="password")
                
                enviado_sprint = st.form_submit_button("Salvar Palpite da Sprint ⏱️")
                
                if enviado_sprint:
                    email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                    email_digitado = email_confirmacao.strip().lower()
                    
                    if email_digitado == email_correto and email_correto != "":
                        dados = {
                            "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                            "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                            "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                            "P6": p6, "P7": p7, "P8": p8, "P9": "", "P10": "",
                            "VoltaRapida": "", "PrimeiroAbandono": "", "MaisUltrapassagens": ""
                        }
                        guardar_dados(dados, ARQUIVO_DADOS)
                        st.success(f"Autenticação confirmada! Palpite para a {tipo_sessao} do GP {gp_selecionado} registrado com sucesso!")
                    else:
                        st.error("🚫 Acesso Negado: O e-mail informado não corresponde ao usuário selecionado. O palpite NÃO foi salvo.")

    else:
        st.info("Selecione o seu nome no menu lateral para começar.")

# --- ÁREA: CLASSIFICAÇÕES ---
elif menu == "Classificações":
    st.header("🏆 Classificações do Campeonato F1 2026")
    
    if os.path.exists(ARQUIVO_DADOS) and os.path.exists(ARQUIVO_GABARITOS):
        df_palpites = pd.read_csv(ARQUIVO_DADOS)
        df_gabaritos = pd.read_csv(ARQUIVO_GABARITOS)
        
        resultados = []
        
        for index_p, row_p in df_palpites.iterrows():
            gp = row_p.get('GP', '')
            tipo = row_p.get('Tipo', 'Corrida Principal')
            
            gabarito_match = df_gabaritos[(df_gabaritos['GP'] == gp) & (df_gabaritos['Tipo'] == tipo)]
            
            if not gabarito_match.empty:
                gabarito_oficial = gabarito_match.iloc[-1]
                
                if tipo == "Corrida Principal":
                    pontos = calcular_pontos_corrida(row_p, gabarito_oficial)
                else:
                    pontos = calcular_pontos_sprint(row_p, gabarito_oficial)
                    
                resultados.append({"Usuario": row_p['Usuario'], "Equipe": row_p.get('Equipe', 'Sem Equipe'), "Pontos": pontos})
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Mundial de Pilotos (Geral)")
                ranking_geral = df_resultados.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_geral.index = range(1, len(ranking_geral) + 1)
                st.dataframe(ranking_geral, use_container_width=True)
                
            with col2:
                st.subheader("🏎️ Mundial de Construtores (Equipes)")
                ranking_equipas = df_resultados.groupby('Equipe')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                st.dataframe(ranking_equipas, use_container_width=True)
        else:
            st.warning("Ainda não existem Gabaritos Oficiais para calcular as pontuações dos palpites inseridos.")
    else:
        st.warning("Aguardando inserção de palpites e Gabaritos Oficiais para gerar a classificação.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha de Diretor de Prova:", type="password")
    
    if senha == "fleury1475":
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO")
        
        st.subheader("🕵️‍♂️ Auditoria: Palpites da Turma")
        if os.path.exists(ARQUIVO_DADOS):
            df_auditoria = pd.read_csv(ARQUIVO_DADOS)
            st.dataframe(df_auditoria, use_container_width=True)
        else:
            st.info("Ainda não foram registrados palpites no sistema.")
            
        st.divider()
        st.header("🏆 Inserir Gabarito Oficial")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_admin = st.selectbox("GP do Gabarito:", lista_gps)
            
        opcoes_admin = ["Corrida Principal", "Corrida Sprint"] if gp_admin in sprint_gps else ["Corrida Principal"]
        
        with col_tipo:
            tipo_admin = st.radio("Sessão do Gabarito:", opcoes_admin, horizontal=True)
        
        if tipo_admin == "Corrida Principal":
            with st.form("form_gabarito_corrida"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.selectbox("Pole Position:", pilotos)
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
                    
                enviar_gabarito = st.form_submit_button("Submeter Gabarito da Corrida 🏆")
                if enviar_gabarito:
                    dados_gabarito = {
                        "GP": gp_admin, "Tipo": tipo_admin, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, 
                        "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                    }
                    guardar_dados(dados_gabarito, ARQUIVO_GABARITOS)
                    st.success("Gabarito da Corrida salvo! As classificações foram atualizadas.")
                    
        elif tipo_admin == "Corrida Sprint":
             with st.form("form_gabarito_sprint"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.selectbox("Pole Sprint:", pilotos)
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    
                enviar_gabarito = st.form_submit_button("Submeter Gabarito da Sprint 🏆")
                if enviar_gabarito:
                    dados_gabarito = {
                        "GP": gp_admin, "Tipo": tipo_admin, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, 
                        "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": "", "P10": "",
                        "VoltaRapida": "", "PrimeiroAbandono": "", "MaisUltrapassagens": ""
                    }
                    guardar_dados(dados_gabarito, ARQUIVO_GABARITOS)
                    st.success("Gabarito da Sprint salvo! As classificações foram atualizadas.")
                    
    elif senha != "":
        st.error("Senha incorreta.")
