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

GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# --- NOVO: FUNÇÃO PARA MOSTRAR FOTO DO PILOTO ---
def mostrar_foto_piloto(nome_piloto):
    if nome_piloto and nome_piloto != "Nenhum / Outro":
        # Formata o nome para bater com o arquivo (ex: "Max Verstappen" -> "Max Verstappen.png")
        # Se os arquivos não tiverem .png, ajuste aqui.
        img_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_piloto}.png"
        
        # Usamos uma coluna pequena para a foto não ficar gigante
        st.image(img_url, width=120, caption=nome_piloto)

# [MANTENHA O RESTANTE DO SEU CÓDIGO ATÉ A LINHA DO MENU...]

# ... (Funções ler_dados, guardar_dados, enviar_recibo_email, calcular_pontos permanecem iguais)

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
                col_sel, col_img = st.columns([2, 1])
                with col_sel:
                    pole = st.selectbox("Pole Position:", pilotos)
                with col_img:
                    mostrar_foto_piloto(pole)
                
            elif tipo_sessao == "Corrida Principal":
                st.info("📌 Palpite para a Corrida de Domingo.")
                
                # Exemplo para P1, P2 e P3 com fotos (os demais mantivemos padrão para não ocupar muito espaço)
                c1, c2, c3 = st.columns(3)
                with c1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    mostrar_foto_piloto(p1)
                with c2:
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    mostrar_foto_piloto(p2)
                with c3:
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    mostrar_foto_piloto(p3)

                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                with col2:
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    p9 = st.selectbox("9º Colocado:", pilotos)
                    p10 = st.selectbox("10º Colocado:", pilotos)
                
                st.divider()
                col_extra1, col_extra2, col_extra3 = st.columns(3)
                with col_extra1:
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos)
                    mostrar_foto_piloto(volta_rapida)
                with col_extra2:
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos)
                    mostrar_foto_piloto(primeiro_abandono)
                with col_extra3:
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos)
                    mostrar_foto_piloto(mais_ultrapassagens)
                    
            elif tipo_sessao == "Corrida Sprint":
                st.info("📌 Palpite para a Corrida Sprint (Top 8).")
                # Grid de fotos para o Top 3 da Sprint
                s1, s2, s3 = st.columns(3)
                with s1:
                    p1 = st.selectbox("1º Colocado:", pilotos, key="s1")
                    mostrar_foto_piloto(p1)
                with s2:
                    p2 = st.selectbox("2º Colocado:", pilotos, key="s2")
                    mostrar_foto_piloto(p2)
                with s3:
                    p3 = st.selectbox("3º Colocado:", pilotos, key="s3")
                    mostrar_foto_piloto(p3)

                col1, col2 = st.columns(2)
                with col1:
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)

            # ... (Restante do formulário e lógica de envio permanecem iguais)
