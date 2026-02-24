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

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
# Simulação do tempo limite para testes
limite_qualy_aus = fuso_br.localize(datetime(2026, 3, 15, 1, 59)) 

# 2. Funções do Banco de Dados e Matemática
def guardar_dados(dados, arquivo):
    df = pd.DataFrame([dados])
    if not os.path.exists(arquivo):
        df.to_csv(arquivo, index=False)
    else:
        df.to_csv(arquivo, mode='a', header=False, index=False)

def calcular_pontos(palpite, gabarito):
    pontos = 0
    # Pontos de Posição
    if str(palpite['Pole']).strip().lower() == str(gabarito['Pole']).strip().lower(): pontos += 100
    if str(palpite['P1']).strip().lower() == str(gabarito['P1']).strip().lower(): pontos += 150
    if str(palpite['P2']).strip().lower() == str(gabarito['P2']).strip().lower(): pontos += 125
    if str(palpite['P3']).strip().lower() == str(gabarito['P3']).strip().lower(): pontos += 100
    if str(palpite['P4']).strip().lower() == str(gabarito['P4']).strip().lower(): pontos += 85
    if str(palpite['P5']).strip().lower() == str(gabarito['P5']).strip().lower(): pontos += 70
    if str(palpite['P6']).strip().lower() == str(gabarito['P6']).strip().lower(): pontos += 60
    if str(palpite['P7']).strip().lower() == str(gabarito['P7']).strip().lower(): pontos += 50
    if str(palpite['P8']).strip().lower() == str(gabarito['P8']).strip().lower(): pontos += 40
    if str(palpite['P9']).strip().lower() == str(gabarito['P9']).strip().lower(): pontos += 25
    if str(palpite['P10']).strip().lower() == str(gabarito['P10']).strip().lower(): pontos += 15
    
    # Extras
    if str(palpite['VoltaRapida']).strip().lower() == str(gabarito['VoltaRapida']).strip().lower(): pontos += 75
    if str(palpite['PrimeiroAbandono']).strip().lower() == str(gabarito['PrimeiroAbandono']).strip().lower(): pontos += 200
    if str(palpite['MaisUltrapassagens']).strip().lower() == str(gabarito['MaisUltrapassagens']).strip().lower(): pontos += 75
    
    # Bónus de Exatidão
    top10_palpite = [str(palpite[f'P{i}']).strip().lower() for i in range(1, 11)]
    top10_gabarito = [str(gabarito[f'P{i}']).strip().lower() for i in range(1, 11)]
    
    if top10_palpite == top10_gabarito:
        pontos += 600
    elif top10_palpite[:5] == top10_gabarito[:5]:
        pontos += 450
    elif top10_palpite[:3] == top10_gabarito[:3]:
        pontos += 300
        
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
        st.header("🇦🇺 GP da Austrália - Corrida")
        
        if agora > limite_qualy_aus:
            st.error("⚠️ Tempo esgotado! O sistema bloqueou novos palpites para este GP.")
        else:
            with st.form("form_palpite_corrida"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.text_input("Pole:")
                    p1 = st.text_input("1º Colocado:")
                    p2 = st.text_input("2º Colocado:")
                    p3 = st.text_input("3º Colocado:")
                    p4 = st.text_input("4º Colocado:")
                    p5 = st.text_input("5º Colocado:")
                with col2:
                    p6 = st.text_input("6º Colocado:")
                    p7 = st.text_input("7º Colocado:")
                    p8 = st.text_input("8º Colocado:")
                    p9 = st.text_input("9º Colocado:")
                    p10 = st.text_input("10º Colocado:")
                    volta_rapida = st.text_input("Melhor Volta:")
                    primeiro_abandono = st.text_input("1º Abandono:")
                    mais_ultrapassagens = st.text_input("Mais Ultrapassagens:")
                
                enviado = st.form_submit_button("Guardar Palpites 🏁")
                
                if enviado:
                    dados = {
                        "GP": "Austrália", "Usuario": usuario_logado, "Equipa": equipa_utilizador,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono,
                        "MaisUltrapassagens": mais_ultrapassagens
                    }
                    guardar_dados(dados, ARQUIVO_DADOS)
                    st.success("Palpite registado com sucesso!")
    else:
        st.info("Selecione o seu nome no menu lateral para começar.")

# --- ÁREA: CLASSIFICAÇÕES ---
elif menu == "Classificações":
    st.header("🏆 Classificações do Campeonato")
    
    if os.path.exists(ARQUIVO_DADOS) and os.path.exists(ARQUIVO_GABARITOS):
        df_palpites = pd.read_csv(ARQUIVO_DADOS)
        df_gabaritos = pd.read_csv(ARQUIVO_GABARITOS)
        
        # Pegar o último gabarito inserido
        gabarito_atual = df_gabaritos.iloc[-1]
        
        # Calcular pontuações
        resultados = []
        for index, row in df_palpites.iterrows():
            if row['GP'] == gabarito_atual['GP']:
                pontos = calcular_pontos(row, gabarito_atual)
                resultados.append({"Usuario": row['Usuario'], "Equipa": row['Equipa'], "Pontos": pontos})
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Geral (Pilotos)")
                ranking_geral = df_resultados.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_geral.index = range(1, len(ranking_geral) + 1)
                st.dataframe(ranking_geral, use_container_width=True)
                
            with col2:
                st.subheader("🏎️ Construtores (Equipas)")
                ranking_equipas = df_resultados.groupby('Equipa')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                st.dataframe(ranking_equipas, use_container_width=True)
        else:
            st.warning("Ainda não existem palpites calculados para o último Gabarito Oficial.")
    else:
        st.warning("Aguardando inserção de palpites e do Gabarito Oficial para gerar a classificação.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Palavra-passe:", type="password")
    
    if senha == "admin123":
        st.warning("⚠️ MODO ADMINISTRADOR - Inserir Resultado Oficial")
        st.header("🇦🇺 Gabarito Oficial - Austrália")
        
        with st.form("form_gabarito"):
            col1, col2 = st.columns(2)
            with col1:
                pole = st.text_input("Pole:")
                p1 = st.text_input("1º Colocado:")
                p2 = st.text_input("2º Colocado:")
                p3 = st.text_input("3º Colocado:")
                p4 = st.text_input("4º Colocado:")
                p5 = st.text_input("5º Colocado:")
            with col2:
                p6 = st.text_input("6º Colocado:")
                p7 = st.text_input("7º Colocado:")
                p8 = st.text_input("8º Colocado:")
                p9 = st.text_input("9º Colocado:")
                p10 = st.text_input("10º Colocado:")
                volta_rapida = st.text_input("Melhor Volta:")
                primeiro_abandono = st.text_input("1º Abandono:")
                mais_ultrapassagens = st.text_input("Mais Ultrapassagens:")
                
            enviar_gabarito = st.form_submit_button("Submeter Gabarito 🏆")
            
            if enviar_gabarito:
                dados_gabarito = {
                    "GP": "Austrália", "Pole": pole, "P1": p1, "P2": p2, "P3": p3, 
                    "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                    "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono,
                    "MaisUltrapassagens": mais_ultrapassagens
                }
                guardar_dados(dados_gabarito, ARQUIVO_GABARITOS)
                st.success("Gabarito guardado com sucesso! As classificações foram atualizadas.")
    elif senha != "":
        st.error("Palavra-passe incorreta.")