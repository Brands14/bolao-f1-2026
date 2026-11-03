import base64
import hmac
import io
import inspect
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from urllib.parse import quote

import pandas as pd
import pytz
import streamlit as st

logger = logging.getLogger(__name__)

GITHUB_USER = "Brands14"

GITHUB_REPO = "bolao-f1-2026"

EMAIL_ADMIN = "palpitesf12026@gmail.com"

ARQUIVO_DADOS = "palpites_permanentes_2026.csv"

ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

ARQUIVO_HISTORICO = "historico_alteracoes_2026.csv"

participantes = [
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", 
    "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", 
    "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", 
    "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", 
    "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"
]

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
    "Equipe 2º Myke e César": ["Myke Ribeiro", "César Gaudie"],
    "Equipe 3º Luciano e Ronaldo": ["Luciano (Medalha)", "Ronaldo Fleury"],
    "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"],
    "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"],
    "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"],
    "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"],
    "Equipe 8º Delvânia Belo e Maikon": ["Delvânia Belo", "Maikon Miranda"],
    "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"],
    "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]
}

pilotos = [
    "", 
    "Max Verstappen", "Yuki Tsunoda", "Isack Hadjar",
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
    "Austrália", "China", "Japão", "Miami", "Canadá", "Mônaco", 
    "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", 
    "Holanda", "Itália", "Madrid", "Azerbaijão", 
    "Bahrein (Malásia / Sepang)", 
    "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]

SENHA_ADMIN_LEGADA = 'fleury1475'
fuso_br = pytz.timezone('America/Sao_Paulo')
URL_VIDEO_GITHUB = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/f1_bg.mp4"
EQUIPE_POR_USUARIO = {membro: equipe for equipe, membros in equipes.items() for membro in membros}
INDICE_PILOTOS = {nome: i for i, nome in enumerate(pilotos)}
CAMPOS_PALPITE = ['Pole'] + [f'P{i}' for i in range(1, 11)] + [
    'VoltaRapida', 'PrimeiroAbandono', 'MaisUltrapassagens']
SESSOES = ['Classificação Principal (Pole)', 'Corrida Principal', 'Qualy Sprint (Pole)', 'Corrida Sprint']
PONTOS_PRINCIPAL = dict(zip([f'P{i}' for i in range(1, 11)], [150,125,100,85,70,60,50,40,25,15]))
PONTOS_PRINCIPAL.update(VoltaRapida=75, PrimeiroAbandono=200, MaisUltrapassagens=75)
PONTOS_SPRINT = dict(zip([f'P{i}' for i in range(1, 9)], [80,70,60,50,40,30,20,10]))
ROTULOS = {'Pole': 'Pole position', 'VoltaRapida': 'Melhor volta',
           'PrimeiroAbandono': '1º abandono', 'MaisUltrapassagens': 'Mais ultrapassagens'}
ROTULOS.update({f'P{i}': f'{i}º colocado' for i in range(1,11)})


def configuracao(nome, padrao=None):
    valor = os.environ.get(nome)
    if valor:
        return valor
    try:
        return st.secrets.get(nome, padrao)
    except (FileNotFoundError, getattr(st.errors, 'StreamlitSecretNotFoundError', FileNotFoundError)):
        return padrao


GITHUB_TOKEN = configuracao('GITHUB_TOKEN')
SENHA_EMAIL = configuracao('SENHA_EMAIL')


def _url_arquivo(arquivo):
    return f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{quote(arquivo, safe="/")}'


def _headers():
    return {'Authorization': f'token {GITHUB_TOKEN}', 'Content-Type': 'application/json',
            'User-Agent': 'BolaoF1-App', 'Accept': 'application/vnd.github+json'}


def _ler_dados_remotos(arquivo):
    """Leitura fresca para escritas: falhas de acesso não são tratadas como CSV vazio."""
    req = urllib.request.Request(_url_arquivo(arquivo), headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return pd.DataFrame(), None
        raise
    conteudo = base64.b64decode(data['content']).decode('utf-8-sig')
    try:
        df = pd.read_csv(io.StringIO(conteudo))
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()
    return df, data['sha']


@st.cache_data(ttl=20, max_entries=8, show_spinner=False)
def _ler_dados_cache(arquivo):
    return _ler_dados_remotos(arquivo)


def ler_dados(arquivo):
    return _ler_dados_cache(arquivo)


def _escrever_csv(arquivo, df, sha, mensagem):
    payload = {'message': mensagem, 'content': base64.b64encode(df.to_csv(index=False).encode()).decode()}
    if sha:
        payload['sha'] = sha
    req = urllib.request.Request(_url_arquivo(arquivo), data=json.dumps(payload).encode(),
                                 headers=_headers(), method='PUT')
    with urllib.request.urlopen(req, timeout=15) as response:
        sucesso = response.status in (200, 201)
    if sucesso:
        _ler_dados_cache.clear()
    return sucesso


def _atualizar_csv(arquivo, transformar, mensagem):
    """Em conflito de SHA, relê e reaplica a operação sobre a versão mais nova."""
    for tentativa in range(3):
        df, sha = _ler_dados_remotos(arquivo)
        novo_df, contexto = transformar(df)
        try:
            return _escrever_csv(arquivo, novo_df, sha, mensagem), contexto
        except urllib.error.HTTPError as exc:
            if exc.code != 409 or tentativa == 2:
                raise
    raise RuntimeError('Não foi possível concluir a atualização concorrente.')


def _mascara_registro(df, dados):
    chaves = ['GP', 'Tipo'] + (['Usuario'] if 'Usuario' in dados else [])
    return df[chaves].eq(pd.Series({chave: dados[chave] for chave in chaves})).all(axis=1)


def registrar_historico(usuario, gp, tipo, acao):
    agora = datetime.now(fuso_br)
    registro = {'Data_Hora': agora.strftime('%d/%m/%Y %H:%M:%S'), 'Usuario': usuario,
                'GP': gp, 'Tipo': tipo,
                'Mensagem': f'O participante {usuario} {acao} seu palpite no GP de {gp} ({tipo}) às {agora:%H:%M:%S} de {agora:%d/%m/%Y}.'}
    def adicionar(df):
        return pd.concat([df, pd.DataFrame([registro])], ignore_index=True), None
    try:
        ok, _ = _atualizar_csv(ARQUIVO_HISTORICO, adicionar, f'Log de histórico: {usuario} - {gp}')
        if not ok:
            st.warning('Palpite salvo, mas o histórico não pôde ser atualizado.')
    except Exception:
        logger.exception('Falha ao registrar histórico')
        st.warning('Palpite salvo, mas o histórico não pôde ser atualizado.')


def guardar_dados(novos_dados, nome_arquivo, eh_edicao_admin=False):
    def substituir(df):
        mascara = _mascara_registro(df, novos_dados) if not df.empty else pd.Series(False, index=df.index)
        alteracao = bool(mascara.any()) and 'Usuario' in novos_dados
        return pd.concat([df.loc[~mascara], pd.DataFrame([novos_dados])], ignore_index=True), alteracao
    mensagem = (f"Atualizado palpite: {novos_dados['Usuario']} - {novos_dados['GP']} ({novos_dados['Tipo']})"
                if 'Usuario' in novos_dados else
                f"Atualizado Gabarito: {novos_dados.get('GP', 'Oficial')} ({novos_dados.get('Tipo', '')})")
    try:
        sucesso, alteracao = _atualizar_csv(nome_arquivo, substituir, mensagem)
    except Exception:
        logger.exception('Falha ao salvar CSV')
        st.error('Não foi possível salvar no GitHub. Confira a conexão e as permissões e tente novamente.')
        return False
    if sucesso and 'Usuario' in novos_dados:
        acao = 'alterou (pelo Admin)' if eh_edicao_admin else ('alterou' if alteracao else 'enviou')
        registrar_historico(novos_dados['Usuario'], novos_dados['GP'], novos_dados['Tipo'], acao)
    return sucesso


def deletar_registro_github(arquivo, mascara_filtro):
    """Mantém a máscara de retenção da API original; recusa máscaras obsoletas."""
    try:
        _, snapshot_sha = ler_dados(arquivo)
        atual, sha = _ler_dados_remotos(arquivo)
        if atual.empty or sha != snapshot_sha or len(mascara_filtro) != len(atual):
            st.warning('Os dados mudaram. Atualize a tela antes de excluir.')
            _ler_dados_cache.clear()
            return False
        if isinstance(mascara_filtro, pd.Series) and not mascara_filtro.index.equals(atual.index):
            return False
        return _escrever_csv(arquivo, atual.loc[mascara_filtro], sha, f'Removendo registro: {arquivo}')
    except Exception:
        logger.exception('Falha ao excluir registro')
        st.error('Não foi possível excluir. Atualize os dados e tente novamente.')
        return False


def campos_sessao(tipo):
    if 'Pole' in tipo:
        return ['Pole']
    if tipo == 'Corrida Principal':
        return list(PONTOS_PRINCIPAL)
    if tipo == 'Corrida Sprint':
        return list(PONTOS_SPRINT)
    return []


def enviar_recibo_email(dados, email_destino):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADMIN
    msg['To'] = ', '.join([EMAIL_ADMIN, email_destino])
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    corpo = (f"Olá {dados['Usuario']},\n\nSeu palpite foi registrado/atualizado com sucesso no Bolão F1 2026!\n\n"
             f"--- REGISTRO OFICIAL ---\nGrande Prêmio: {dados['GP']}\nSessão: {dados['Tipo']}\n"
             f"Data/Hora do Envio: {dados['Data_Envio']}\n\n--- DETALHES DO SEU PALPITE ---\n")
    corpo += '\n'.join(f'{ROTULOS[campo]}: {dados.get(campo, "")}' for campo in campos_sessao(dados['Tipo']))
    msg.attach(MIMEText(corpo + '\n\nDireção de Prova — Bolão F1 2026', 'plain', 'utf-8'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
            server.starttls()
            server.login(EMAIL_ADMIN, SENHA_EMAIL)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception('Falha ao enviar recibo')
        return False


def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    return valor_pontos if (val_p and val_p == val_g) else 0


def _bonus_principal(palpite, gabarito):
    top_p = [str(palpite.get(f'P{i}', '')).strip() for i in range(1,11)]
    top_g = [str(gabarito.get(f'P{i}', '')).strip() for i in range(1,11)]
    if not (all(top_p) and all(top_g)):
        return 0
    return next((bonus for n, bonus in ((10,600),(5,450),(3,300)) if top_p[:n] == top_g[:n]), 0)


def calcular_pontos_sessao(palpite, gabarito):
    tipo = palpite.get('Tipo', '')
    if 'Classificação' in tipo or 'Qualy Sprint' in tipo:
        return check_ponto(palpite, gabarito, 'Pole', 100)
    pesos = {'Corrida Principal': PONTOS_PRINCIPAL, 'Corrida Sprint': PONTOS_SPRINT}.get(tipo, {})
    pontos = sum(check_ponto(palpite, gabarito, chave, valor) for chave, valor in pesos.items())
    return pontos + (_bonus_principal(palpite, gabarito) if tipo == 'Corrida Principal' else 0)


def processar_resultados(df_palpites, df_gabaritos):
    """Índice de gabaritos O(G); consulta O(1) por palpite, sem refiltrar o DataFrame."""
    colunas = ['Usuario','Equipe','Pontos','GP']
    if df_palpites.empty or df_gabaritos.empty:
        return pd.DataFrame(columns=colunas)
    gabaritos = {(r['GP'], r['Tipo']): r for r in
                 df_gabaritos.drop_duplicates(['GP','Tipo'], keep='last').to_dict('records')}
    resultados = []
    for palpite in df_palpites.drop_duplicates(['Usuario','GP','Tipo'], keep='last').to_dict('records'):
        gabarito = gabaritos.get((palpite['GP'], palpite['Tipo']))
        if gabarito is not None:
            resultados.append({'Usuario': palpite['Usuario'],
                               'Equipe': EQUIPE_POR_USUARIO.get(palpite['Usuario'], 'Sem Equipe'),
                               'Pontos': calcular_pontos_sessao(palpite,gabarito), 'GP': palpite['GP']})
    return pd.DataFrame(resultados, columns=colunas)


def index_piloto(val):
    return INDICE_PILOTOS.get(str(val).strip() if pd.notna(val) else '', 0)


def exibir_foto_piloto(nome):
    if nome and nome != 'Nenhum / Outro':
        st.image(f'https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{quote(nome)}.png', width=64)


CSS = '''
<style>
:root {color-scheme:dark; --red:#ff463e; --muted:#a4adbd; --line:#283143;}
.stApp {background:#0a101c; color:#edf2fa;}
header[data-testid="stHeader"] {background:rgba(10,16,28,.9);}
.block-container {max-width:1280px; padding-top:2rem; padding-bottom:3rem;}
h1,h2,h3 {letter-spacing:-.035em; color:#f4f7fd!important;}
p,label {color:inherit;}
[data-testid="stCaptionContainer"] {color:#a4adbd;}
[data-testid="stSidebar"] {background:#101827; border-right:1px solid var(--line);}
.brand {display:flex; align-items:center; gap:12px; margin:0 0 24px;}
.brand-mark {background:#ff463e; border-radius:10px 3px 10px 3px; padding:6px 12px; font-weight:950; font-size:24px; color:white; font-style:italic;}
.brand-name {font-size:14px; font-weight:800; letter-spacing:.13em;}
.brand-name small {display:block; font-size:10px; color:#9aa6bd; letter-spacing:.2em; margin-top:3px;}
.hero {position:relative; overflow:hidden; border:1px solid #303b51; border-radius:24px; background:linear-gradient(110deg,#18253c,#101a2d); margin:18px 0 24px;}
.hero video {position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:.24;}
.hero-body {position:relative; padding:38px 42px; background:linear-gradient(90deg,rgba(12,21,38,.94),rgba(12,21,38,.15));}
.eyebrow {font-size:11px; font-weight:800; letter-spacing:.2em; color:#ff776e; text-transform:uppercase; margin-bottom:12px;}
.hero h1 {font-size:clamp(2rem,4.6vw,3.7rem); font-weight:900; margin:0; padding:0; line-height:1.08; max-width:700px;}
.hero p {color:#c0cadb; margin:16px 0 22px; max-width:570px; font-size:15px;}
.pill {display:inline-block; font-size:11px; letter-spacing:.08em; border:1px solid #4d5668; background:#172339; border-radius:999px; padding:6px 12px; margin-right:6px; color:#e4eaf5;}
.section-kicker {color:#7c90b1; font-size:11px; letter-spacing:.18em; text-transform:uppercase; margin:24px 0 8px; font-weight:800;}
[data-testid="stMetric"] {background:linear-gradient(140deg,#182235,#121b2c); border:1px solid var(--line); border-radius:16px; padding:17px 20px;}
[data-testid="stMetricLabel"] {color:#b7c2d4; font-size:12px;}
[data-testid="stMetricValue"] {font-size:29px; font-weight:800; color:#fff;}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#2b3548!important; border-radius:16px!important;}
div[data-baseweb="select"]>div, [data-testid="stTextInput"] input {background:#111c2d!important; color:#f2f5fb!important; border-color:#344157!important; border-radius:10px!important;}
[data-baseweb="popover"] {color-scheme:dark;}
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {border-radius:10px; min-height:44px; font-weight:700; transition:transform .15s,box-shadow .15s;}
.stButton>button:hover, .stFormSubmitButton>button:hover {transform:translateY(-1px); box-shadow:0 6px 20px #0004; border-color:#ff6860;}
button[kind="primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {background:#ff463e; border:1px solid #ff463e; color:#fff;}
[data-testid="stRadio"]>div[role="radiogroup"] {gap:8px; padding:8px; background:#121c2d; border:1px solid var(--line); border-radius:14px; flex-wrap:wrap;}
[data-testid="stRadio"] label[data-baseweb="radio"] {padding:9px 14px; border-radius:9px; margin:0; background:#182438; cursor:pointer;}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {background:#ff463e; color:#fff;}
.stTabs [data-baseweb="tab-list"] {gap:8px; background:#121c2d; padding:8px; border-radius:12px; overflow-x:auto;}
.stTabs [data-baseweb="tab"] {border-radius:8px; padding:10px 16px; color:#b7c2d4;}
.stTabs [aria-selected="true"] {background:#263650; color:#fff;}
.podium {padding:20px; background:linear-gradient(145deg,#1e2c43,#121b2b); border:1px solid #36465e; border-radius:16px; min-height:150px; margin-bottom:16px;}
.podium .rank {color:#ffad61; font-size:12px; font-weight:800; letter-spacing:.13em;}
.podium h3 {font-size:19px; margin:10px 0 4px;}
.podium .score {font-size:27px; font-weight:900; color:#fff;}
.podium .score small {font-size:12px; color:#a4adbd; font-weight:500;}
.footer {text-align:center; color:#7c8aa2; font-size:11px; letter-spacing:.06em; margin-top:42px; padding-top:20px; border-top:1px solid #243047;}
@media(max-width:640px) {.block-container {padding:1.2rem 1rem 2rem;} .hero-body {padding:28px 23px;} .hero h1 {font-size:2rem;} [data-testid="stRadio"] label[data-baseweb="radio"] {padding:7px 9px;} }
@media(prefers-reduced-motion:reduce) {*,*::before,*::after {transition:none!important; animation:none!important;} .hero video {display:none;}}
</style>
'''


def cabecalho():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="brand"><div class="brand-mark">F1</div><div class="brand-name">BOLÃO 2026<small>SEU PALPITE. SUA DISPUTA.</small></div></div>', unsafe_allow_html=True)
    return st.radio('Navegação', ['Enviar Palpite','Meus Palpites','Classificações','Administrador'],
                    horizontal=True, label_visibility='collapsed', key='navegacao')


def hero(titulo, descricao, etiqueta='TEMPORADA 2026'):
    st.markdown(f'''<div class="hero"><video autoplay loop muted playsinline aria-hidden="true"><source src="{URL_VIDEO_GITHUB}" type="video/mp4"></video>
    <div class="hero-body"><div class="eyebrow">{escape(etiqueta)}</div><h1>{escape(titulo)}</h1>
    <p>{escape(descricao)}</p><span class="pill">20 PARTICIPANTES</span><span class="pill">10 EQUIPES</span><span class="pill">UMA DISPUTA</span></div></div>''', unsafe_allow_html=True)


def secao(numero, titulo):
    st.markdown(f'<div class="section-kicker">{escape(numero)}</div>', unsafe_allow_html=True)
    st.subheader(titulo)


def sessoes_disponiveis(gp):
    return SESSOES if gp in sprint_gps else SESSOES[:2]


def ultimo_registro(df, gp, tipo, usuario=None):
    if df.empty:
        return {}
    dados = {'GP':gp, 'Tipo':tipo}
    if usuario is not None:
        dados['Usuario'] = usuario
    filtrado = df.loc[_mascara_registro(df,dados)]
    return filtrado.iloc[-1].to_dict() if not filtrado.empty else {}


def seletor_etapa(prefixo, gps):
    c1,c2 = st.columns(2)
    with c1:
        gp = st.selectbox('Grande Prêmio', gps, key=f'{prefixo}_gp')
    with c2:
        tipo = st.selectbox('Sessão', sessoes_disponiveis(gp), key=f'{prefixo}_tipo')
    return gp,tipo


def formulario_pilotos(tipo, existente, contexto, fotos=False):
    valores = dict.fromkeys(CAMPOS_PALPITE,'')
    campos = campos_sessao(tipo)
    posicoes = [c for c in campos if c.startswith('P') and c[1:].isdigit()]
    extras = [c for c in campos if c not in posicoes]
    if posicoes:
        colunas = st.columns(2)
        metade = (len(posicoes)+1)//2
        for i,campo in enumerate(posicoes):
            with colunas[i//metade]:
                valores[campo] = st.selectbox(ROTULOS[campo], pilotos,
                    index=index_piloto(existente.get(campo,'')), key=f'{contexto}_{campo}')
                if fotos:
                    exibir_foto_piloto(valores[campo])
    if extras:
        if posicoes:
            st.markdown('#### Apostas extras')
        for coluna,campo in zip(st.columns(len(extras)),extras):
            with coluna:
                valores[campo] = st.selectbox(ROTULOS[campo], pilotos,
                    index=index_piloto(existente.get(campo,'')), key=f'{contexto}_{campo}')
                if fotos:
                    exibir_foto_piloto(valores[campo])
    return valores


def _email_valido(usuario, informado):
    esperado = emails_autorizados.get(usuario,'').strip().lower()
    return bool(esperado) and hmac.compare_digest(informado.strip().lower().encode(), esperado.encode())


def _dados_palpite(usuario,gp,tipo,valores,admin=False):
    return {'Data_Envio':datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S') + (' (Admin)' if admin else ''),
            'GP':gp,'Tipo':tipo,'Usuario':usuario,'Equipe':EQUIPE_POR_USUARIO.get(usuario,'Sem Equipe'), **valores}


def tela_enviar():
    hero('O próximo pódio começa aqui.', 'Escolha sua etapa, monte o grid e coloque seu conhecimento de Fórmula 1 na disputa.')
    usuario = st.selectbox('Quem vai acelerar?', ['']+participantes, key='usuario_enviar')
    if not usuario:
        st.info('Selecione seu nome para preparar o próximo palpite.')
        return
    st.caption(EQUIPE_POR_USUARIO.get(usuario,'Sem Equipe'))
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    realizados = set(gabaritos['GP']) if not gabaritos.empty else set()
    gps = [gp for gp in lista_gps if gp not in realizados]
    if not gps:
        st.info('Todas as etapas já possuem gabarito. Acompanhe a classificação do campeonato.')
        return
    secao('01 / ETAPA','Escolha sua disputa')
    gp,tipo = seletor_etapa('envio',gps)
    df,_ = ler_dados(ARQUIVO_DADOS)
    existente = ultimo_registro(df,gp,tipo,usuario)
    if existente:
        st.info('Seu palpite atual foi carregado. Ao gravar, suas novas escolhas substituem as anteriores.')
    secao('02 / GRID',f'GP de {gp} · {tipo}')
    fotos = getattr(st, 'toggle', st.checkbox)('Mostrar fotos dos pilotos', value=False)
    # Contexto inclui participante, GP e sessão: trocar a seleção nunca carrega o grid de outra pessoa.
    contexto = f'envio_{usuario}_{gp}_{tipo}'
    with st.container(**({'border': True} if 'border' in inspect.signature(st.container).parameters else {})):
        valores = formulario_pilotos(tipo,existente,contexto,fotos)
    preenchidos = sum(bool(valores[c]) for c in campos_sessao(tipo))
    total = len(campos_sessao(tipo))
    st.progress(preenchidos/total if total else 0, text=f'{preenchidos} de {total} escolhas preenchidas')
    secao('03 / CONFIRMAÇÃO','Pronto para entrar na pista?')
    with st.form(f'confirmar_{contexto}'):
        email = st.text_input('Confirme seu e-mail cadastrado', type='password')
        enviar = st.form_submit_button('Gravar meu palpite  →', type='primary', use_container_width=True)
    if enviar:
        if not _email_valido(usuario,email):
            st.error('E-mail não confere com o cadastrado para este participante.')
            return
        dados = _dados_palpite(usuario,gp,tipo,valores)
        with st.spinner('Registrando seu palpite…'):
            salvo = guardar_dados(dados,ARQUIVO_DADOS)
        if salvo:
            st.success(f'Palpite de {usuario} para o GP de {gp} gravado com sucesso!')
            st.toast('Você está na disputa!',icon='🏁')
            if not enviar_recibo_email(dados,email.strip()):
                st.warning('Seu palpite está salvo. Não foi possível enviar o recibo por e-mail.')


def tela_meus_palpites():
    hero('Seu histórico na pista.', 'Consulte as escolhas que você registrou ao longo do campeonato.', 'ÁREA DO PARTICIPANTE')
    with st.form('consulta'):
        usuario = st.selectbox('Participante',['']+participantes)
        email = st.text_input('E-mail cadastrado',type='password')
        buscar = st.form_submit_button('Consultar meus palpites',type='primary')
    if not buscar:
        return
    if not _email_valido(usuario,email):
        st.error('Acesso negado: e-mail incorreto.')
        return
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Banco de dados vazio.')
        return
    meus = df.loc[df['Usuario']==usuario].drop_duplicates(['GP','Tipo'],keep='last')
    if meus.empty:
        st.info('Você ainda não enviou palpites.')
        return
    c1,c2 = st.columns(2)
    c1.metric('Palpites registrados',len(meus))
    c2.metric('Etapas disputadas',meus['GP'].nunique())
    st.dataframe(meus.drop(columns=['Usuario','Equipe']),use_container_width=True,hide_index=True)


def ranking(df,chave):
    return df.groupby(chave)['Pontos'].sum().reset_index().sort_values('Pontos',ascending=False)


def tela_classificacoes():
    hero('Cada ponto muda o jogo.', 'Acompanhe a disputa entre participantes e equipes, no campeonato ou por Grande Prêmio.', 'CLASSIFICAÇÃO OFICIAL DO BOLÃO')
    palpites,_ = ler_dados(ARQUIVO_DADOS)
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    df = processar_resultados(palpites,gabaritos)
    filtro = st.selectbox('Etapa',['Geral (Campeonato Completo)']+lista_gps)
    if filtro != 'Geral (Campeonato Completo)':
        df = df.loc[df['GP']==filtro]
    if df.empty:
        st.info('Ainda não há pontuação apurada para esta seleção.')
        return
    individual = ranking(df,'Usuario')
    por_equipe = ranking(df,'Equipe')
    c1,c2,c3 = st.columns(3)
    c1.metric('Participantes pontuados',df['Usuario'].nunique())
    c2.metric('Etapas apuradas',df['GP'].nunique())
    c3.metric('Pontos do líder',int(individual.iloc[0]['Pontos']))
    secao('NA FRENTE','A disputa pelo topo')
    for coluna,(pos,registro) in zip(st.columns(3),enumerate(individual.head(3).to_dict('records'),1)):
        with coluna:
            st.markdown(f'<div class="podium"><div class="rank">{pos:02d} / CLASSIFICAÇÃO</div><h3>{escape(registro["Usuario"])}</h3><div class="score">{int(registro["Pontos"]):,} <small>pontos</small></div></div>',unsafe_allow_html=True)
    tab1,tab2 = st.tabs(['Participantes','Equipes'])
    for tab,tabela in ((tab1,individual),(tab2,por_equipe)):
        with tab:
            tabela = tabela.copy()
            tabela.index = range(1,len(tabela)+1)
            tabela.index.name = 'Posição'
            st.dataframe(tabela,use_container_width=True)
            grafico = tabela.set_index(tabela.columns[0])['Pontos']
            opcoes_grafico = {'color': '#ff463e', 'horizontal': True}
            parametros = inspect.signature(st.bar_chart).parameters
            st.bar_chart(grafico, **{k: v for k, v in opcoes_grafico.items() if k in parametros})


def admin_auditoria():
    st.subheader('Palpites dos participantes')
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Nenhum palpite cadastrado.')
        return
    df = df.drop_duplicates(['Usuario','GP','Tipo'],keep='last')
    gp_filtro = st.selectbox('Filtrar auditoria por GP',['Todos os GPs']+lista_gps)
    st.dataframe(df if gp_filtro=='Todos os GPs' else df.loc[df['GP']==gp_filtro],use_container_width=True,hide_index=True)
    secao('EDIÇÃO','Ajustar palpite de participante')
    usuario = st.selectbox('Participante',['']+participantes,key='adm_usuario')
    gp,tipo = seletor_etapa('adm',lista_gps)
    if not usuario:
        return
    contexto = f'admin_{usuario}_{gp}_{tipo}'
    with st.form(contexto):
        valores = formulario_pilotos(tipo,ultimo_registro(df,gp,tipo,usuario),contexto)
        salvar = st.form_submit_button('Salvar alteração do administrador',type='primary')
    if salvar and guardar_dados(_dados_palpite(usuario,gp,tipo,valores,admin=True),ARQUIVO_DADOS,eh_edicao_admin=True):
        st.session_state['mensagem_sucesso'] = f'Palpite de {usuario} atualizado.'
        st.rerun()


def admin_historico():
    st.subheader('Histórico de alterações')
    df,_ = ler_dados(ARQUIVO_HISTORICO)
    if df.empty:
        st.info('Histórico de alterações vazio.')
        return
    c1,c2 = st.columns(2)
    with c1:
        usuario = st.selectbox('Participante',['Todos']+participantes,key='log_usuario')
    with c2:
        gp = st.selectbox('Grande Prêmio',['Todos']+lista_gps,key='log_gp')
    if usuario != 'Todos':
        df = df.loc[df['Usuario']==usuario]
    if gp != 'Todos':
        df = df.loc[df['GP']==gp]
    if df.empty:
        st.info('Nenhum evento com esses filtros.')
    else:
        st.dataframe(df.iloc[::-1],use_container_width=True,hide_index=True)


def admin_gabarito():
    st.subheader('Homologar resultado oficial')
    gp,tipo = seletor_etapa('gabarito',lista_gps)
    df,_ = ler_dados(ARQUIVO_GABARITOS)
    contexto = f'gabarito_{gp}_{tipo}'
    with st.form(contexto):
        valores = formulario_pilotos(tipo,ultimo_registro(df,gp,tipo),contexto)
        salvar = st.form_submit_button('Salvar / atualizar gabarito oficial',type='primary')
    if salvar and guardar_dados({'GP':gp,'Tipo':tipo,**valores},ARQUIVO_GABARITOS):
        st.session_state['mensagem_sucesso'] = 'Gabarito oficial homologado!'
        st.rerun()


def admin_gabaritos_salvos():
    st.subheader('Gabaritos homologados')
    df,_ = ler_dados(ARQUIVO_GABARITOS)
    if df.empty:
        st.info('Nenhum gabarito cadastrado.')
    else:
        st.dataframe(df.dropna(how='all',axis=1),use_container_width=True,hide_index=True)


def admin_excluir():
    st.subheader('Exclusão de registros')
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Nenhum palpite cadastrado.')
        return
    gp,tipo = seletor_etapa('excluir',lista_gps)
    filtrado = df.loc[(df['GP']==gp)&(df['Tipo']==tipo)]
    if filtrado.empty:
        st.info('Nenhum registro nesta sessão.')
        return
    usuario = st.selectbox('Participante para excluir',['']+sorted(filtrado['Usuario'].unique()))
    if usuario:
        st.warning(f'A exclusão removerá o palpite de {usuario} desta sessão.')
        if st.button('Confirmar exclusão',type='primary'):
            mascara = ~((df['GP']==gp)&(df['Tipo']==tipo)&(df['Usuario']==usuario))
            if deletar_registro_github(ARQUIVO_DADOS,mascara):
                st.session_state['mensagem_sucesso'] = 'Registro removido com sucesso.'
                st.rerun()


def tela_admin():
    hero('Direção de prova.', 'Gerencie os palpites, homologue os resultados e acompanhe os registros do campeonato.', 'ÁREA ADMINISTRATIVA')
    senha = st.text_input('Senha do diretor de prova',type='password')
    esperada = configuracao('SENHA_ADMIN',SENHA_ADMIN_LEGADA)
    if not senha:
        return
    if not hmac.compare_digest(senha.encode(),esperada.encode()):
        st.error('Senha de administrador incorreta.')
        return
    st.caption('Painel administrativo · acesso autorizado')
    # Radio executa apenas a seção ativa, ao contrário de cinco abas executadas a cada interação.
    painel = st.radio('Painel',['Auditoria e edição','Histórico','Homologar resultado','Gabaritos salvos','Excluir registro'],horizontal=True)
    {'Auditoria e edição':admin_auditoria,'Histórico':admin_historico,
     'Homologar resultado':admin_gabarito,'Gabaritos salvos':admin_gabaritos_salvos,
     'Excluir registro':admin_excluir}[painel]()


def main():
    st.set_page_config(page_title='Bolão F1 2026 · Na disputa',page_icon='🏁',layout='wide',initial_sidebar_state='collapsed')
    menu = cabecalho()
    if not GITHUB_TOKEN:
        st.error('A variável GITHUB_TOKEN não foi encontrada nas configurações de ambiente.')
        return
    if st.session_state.get('mensagem_sucesso'):
        st.success(st.session_state.pop('mensagem_sucesso'))
    with st.sidebar:
        st.markdown('### Central do campeonato')
        st.caption('O cache de leitura expira após 20 segundos; os dados são renovados na próxima interação.')
        if st.button('Atualizar dados agora',use_container_width=True):
            _ler_dados_cache.clear()
            st.rerun()
        with st.expander('Como funciona a pontuação'):
            st.write('Pole: 100 pontos. Principal: pontos por posição e apostas extras; bônus exclusivo de 300, 450 ou 600 pontos por top 3, top 5 ou top 10 na ordem. Sprint: pontuação do 1º ao 8º colocado.')
    try:
        {'Enviar Palpite':tela_enviar,'Meus Palpites':tela_meus_palpites,
         'Classificações':tela_classificacoes,'Administrador':tela_admin}[menu]()
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        logger.exception('Falha ao carregar tela')
        st.error('Não foi possível carregar os dados. Verifique a conexão, a configuração de acesso e as colunas dos CSVs e tente atualizar.')
    st.markdown('<div class="footer">BOLÃO F1 2026 · A EMOÇÃO DA CORRIDA CONTINUA NO SEU PALPITE.</div>',unsafe_allow_html=True)


if __name__ == '__main__':
    main()
