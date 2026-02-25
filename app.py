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

# NOVA LISTA DE PILOTOS (Grid Atualizado - Ordem Alfabética)
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
# Simulação de tempo para testes
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
menu = st.sidebar.radio("Ir para:", ["Enviar