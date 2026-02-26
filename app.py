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

# NOVA LISTA DE PILOTOS (Organizada por Equipes conforme sua lista)
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
        with col_tipo:
            tipo_sessao = st.radio("Tipo de Sessão:", ["Corrida Principal", "Corrida Sprint"], horizontal=True)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        if tipo_sessao == "Corrida Principal":
            with st.form("form_palpite_corrida"):
                col1, col2 = st.columns(2)
                with col1:
                    pole = st.selectbox("Pole Position:", pilotos)
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox
