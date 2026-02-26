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

pilotos = [
    "", "Alex Albon", "Arvid Lindblad", "Carlos Sainz", "Charles Leclerc", 
    "Esteban Ocon", "Fernando Alonso", "Franco Colapinto", "Gabriel Bortoleto", 
    "George Russell", "Isack Hadjar", "Kimi Antonelli", "Lance Stroll", 
    "Lando Norris", "Lewis Hamilton", "Liam Lawson", "Max Verstappen", 
    "Nico Hülkenberg", "Oliver Bearman", "Oscar Piastri", "Pierre Gasly", 
    "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"
]

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
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
    if str(palpite['Pole']).strip() == str(gabarito['Pole']).strip(): pontos += 100
    if str(palpite['P1']).strip() == str(gabarito['P1']).strip(): pontos += 150
    if str(palpite['P2']).strip() == str(gabarito['P2']).strip(): pontos += 125
    if str(palpite['P3']).strip() == str(gabarito['P3']).strip(): pontos += 100
    if str(palpite['P4']).strip() == str(gabarito['P4']).strip(): pontos += 85
    if str(palpite['P5']).strip() == str(gabarito['P5']).strip(): pontos += 70
    if str(palpite['P6']).strip() == str(gabarito['P6']).strip(): pontos += 60
    if str(palpite['P7']).strip() == str(gabarito['P7']).strip(): pontos += 50
    if str(palpite['P8']).strip() == str(gabarito['P8']).strip(): pontos += 40
    if str(palpite['P9']).strip() == str(gabarito['P9']).strip(): pontos += 25
    if str(palpite['P10']).strip() == str(gabarito['P10']).strip(): pontos += 15
    
    if str(palpite['VoltaRapida']).strip() == str(gabarito['VoltaRapida']).strip(): pontos += 75
    if str(palpite['PrimeiroAbandono']).strip() == str(gabarito['PrimeiroAbandono']).strip(): pontos += 200
    if str(palpite['MaisUltrapassagens']).strip() == str(gabarito['MaisUltrapassagens']).strip(): pontos += 75
    
    top10_palpite = [str(palpite[f'P{i}']).strip() for i in range(1, 11)]
    top10_gabarito = [str(gabarito[f'P{i}']).strip() for i in range(1, 11)]
    
    if "" not in top10_palpite:
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
                
                enviado = st.form_submit_button("Guardar Palpites 🏁")
                
                if enviado:
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
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
        
        gabarito_atual = df_gabaritos.iloc[-1]
        
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
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO")
        
        # --- NOVA ÁREA: AUDITORIA DE PALPITES ---
        st.subheader("🕵️‍♂️ Auditoria: Palpites da Turma")
        st.write("Aqui pode conferir todos os palpites enviados para validar os cálculos.")
        if os.path.exists(ARQUIVO_DADOS):
            df_auditoria = pd.read_csv(ARQUIVO_DADOS)
            # Mostra a tabela completa no ecrã
            st.dataframe(df_auditoria, use_container_width=True)
        else:
            st.info("Ainda não foram registados palpites no sistema.")
            
        st.divider()
        
        # --- ÁREA: INSERIR GABARITO ---
        st.header("🇦🇺 Inserir Gabarito Oficial - Austrália")
        
        with st.form("form_gabarito"):
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
