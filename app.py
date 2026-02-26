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
    "Rodolfo Brandão", "Valério Bimbato", "Jaime Gabriel", "Myke Ribeiro", 
    "George Fleury", "Fausto Fleury", "Flávio Soares", "Fernanda Fleury",
    "Henrique Junqueira", "Frederico Gaudie", "Hilton Jacinto", "Fabrício Abe",
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Maikon Miranda",
    "Ronaldo Fleury", "Emilio Jacinto", "Syllas Araújo", "Luciano (Medalha)"
]

equipas = {
    "Equipa 1º": ["Fabrício Abe", "Fausto Fleury"],
    "Equipa 2º": ["Myke Ribeiro", "Luciano (Medalha)"],
    "Equipa 3º": ["César Gaudie", "Ronaldo Fleury"],
    "Equipa 4º": ["Valério Bimbato", "Syllas Araújo"],
    "Equipa 5º": ["Frederico Gaudie", "Emilio Jacinto"],
    "Equipa 6º": ["Fernanda Fleury", "Henrique Junqueira"],
    "Equipa 7º": ["Jaime Gabriel", "Hilton Jacinto"],
    "Equipa 8º": ["Delvânia Belo", "Maikon Miranda"],
    "Equipa 9º": ["Alaerte Fleury", "Flávio Soares"],
    "Equipa 10º": ["Rodolfo Brandão", "George Fleury"]
}

# Pilotos (Organizados por Equipes)
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

# Calendário 2026
lista_gps = [
    "Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", 
    "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", 
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", 
    "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

# GPs que têm Corrida Sprint (Atualizado 2026)
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

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
        equipa_utilizador = next((equipa for equipa, membros in equipas.items() if usuario_logado in membros), "Sem Equipa")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipa_utilizador}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        # A MÁGICA ACONTECE AQUI: Define as opções baseado no GP selecionado
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
                
                enviado = st.form_submit_button("Guardar Palpite da Corrida 🏁")
                if enviado:
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipa": equipa_utilizador,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                    }
                    guardar_dados(dados, ARQUIVO_DADOS)
                    st.success(f"Palpite para a {tipo_sessao} do GP {gp_selecionado} registado com sucesso!")
                    
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
                    
                enviado_sprint = st.form_submit_button("Guardar Palpite da Sprint ⏱️")
                if enviado_sprint:
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipa": equipa_utilizador,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": "", "P10": "",
                        "VoltaRapida": "", "PrimeiroAbandono": "", "MaisUltrapassagens": ""
                    }
                    guardar_dados(dados, ARQUIVO_DADOS)
                    st.success(f"Palpite para a {tipo_sessao} do GP {gp_selecionado} registado com sucesso!")

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
                    
                resultados.append({"Usuario": row_p['Usuario'], "Equipa": row_p['Equipa'], "Pontos": pontos})
        
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
                ranking_equipas = df_resultados.groupby('Equipa')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                st.dataframe(ranking_equipas, use_container_width=True)
        else:
            st.warning("Ainda não existem Gabaritos Oficiais para calcular as pontuações dos palpites inseridos.")
    else:
        st.warning("Aguardando inserção de palpites e Gabaritos Oficiais para gerar a classificação.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Palavra-passe:", type="password")
    
    if senha == "admin123":
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO")
        
        st.subheader("🕵️‍♂️ Auditoria: Palpites da Turma")
        if os.path.exists(ARQUIVO_DADOS):
            df_auditoria = pd.read_csv(ARQUIVO_DADOS)
            st.dataframe(df_auditoria, use_container_width=True)
        else:
            st.info("Ainda não foram registados palpites no sistema.")
            
        st.divider()
        st.header("🏆 Inserir Gabarito Oficial")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_admin = st.selectbox("GP do Gabarito:", lista_gps)
            
        # O Admin também só vê Sprint se o GP tiver Sprint
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
                    st.success("Gabarito da Corrida guardado! As classificações foram atualizadas.")
                    
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
                    st.success("Gabarito da Sprint guardado! As classificações foram atualizadas.")
                    
    elif senha != "":
        st.error("Palavra-passe incorreta.")
