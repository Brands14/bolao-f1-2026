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


# ── Identidade visual: fotos públicas já usadas no site de referência ──
FOTOS_PARTICIPANTES = {
    'Valério Bimbato': 'https://i.ibb.co/DDCBrrrS/20180428-15.jpg',
    'Rodolfo Brandão': 'https://i.ibb.co/WpM5VMgq/Sem-t-tulo.jpg',
    'Maikon Miranda': 'https://i.ibb.co/WWH5RYfs/129159798-205592931152894-3590323114454579446-n.jpg',
    'Flávio Soares': 'https://i.ibb.co/TMXDpwK0/IMG-20240908-WA0070.jpg',
    'Fausto Fleury': 'https://i.ibb.co/mCR7RBxs/fausto.jpg',
    'Alaerte Fleury': 'https://i.ibb.co/B2vRBVB6/Sem-t-tulo.png',
    'Delvânia Belo': 'https://i.ibb.co/0jkhb8JJ/IMG-20260608-WA0025.jpg',
    'Fabrício Abe': 'https://i.ibb.co/h1dvSHZn/Sem-t-tulo.png',
    'George Fleury': 'https://i.ibb.co/35pS08d4/Sem-t-tulo-2.jpg',
    'Henrique Junqueira': 'https://i.ibb.co/gFrVwNPZ/653007390-18416258482123519-4856301629390269506-n.jpg',
    'Jaime Gabriel': 'https://i.ibb.co/8gXzwZh2/20241130-190400.jpg',
    'Hilton Jacinto': 'https://i.ibb.co/0yQttFsS/20180428-154832.jpg',
    'Myke Ribeiro': 'https://i.ibb.co/JwQ34Z0Q/myk.jpg',
    'Emilio Jacinto': 'https://i.ibb.co/XZ9QqCCs/Sem-t-tulo.jpg',
    'Fernanda Fleury': 'https://i.ibb.co/PG2kD09h/20241102-180321.jpg',
    'César Gaudie': 'https://i.ibb.co/VW3y4t9M/IMG-20240908-WA0070.jpg',
    'Frederico Gaudie': 'https://i.ibb.co/qMfLfk9M/fred.jpg',
    'Syllas Araújo': 'https://i.ibb.co/DgMCn3bn/Sem-t-tulo.jpg',
}
MAX_PONTOS_SESSAO = {
    'Classificação Principal (Pole)': 100, 'Qualy Sprint (Pole)': 100,
    'Corrida Principal': sum(PONTOS_PRINCIPAL.values()) + 600,
    'Corrida Sprint': sum(PONTOS_SPRINT.values()),
}


def numero_br(valor, casas=0):
    return f'{valor:,.{casas}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def _svg_uri(svg):
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()


def arte_f1(tipo='carro'):
    """Ilustrações vetoriais incorporadas: não dependem de downloads ou novos arquivos."""
    desenhos = {
        'carro': '<path d="M140 30h40l10 48 28 21v32l-27-9-1 66 25 21v24l-31-5-8 33h-32l-8-33-31 5v-24l25-21-1-66-27 9V99l28-21z" fill="#ff463e"/><path d="M141 95h38v80h-38z" fill="#f8a39d"/><ellipse cx="160" cy="156" rx="14" ry="25" fill="#0a101c"/><path d="M106 78h108v16H106zm8 155h92v17h-92z" fill="#dce5f3"/><g fill="#05090f" stroke="#51617b" stroke-width="3"><rect x="88" y="95" width="27" height="55" rx="7"/><rect x="205" y="95" width="27" height="55" rx="7"/><rect x="98" y="197" width="29" height="53" rx="7"/><rect x="193" y="197" width="29" height="53" rx="7"/></g>',
        'bandeira': '<path d="M88 255V48" stroke="#a7b6cd" stroke-width="9"/><path d="M94 51c53-30 83 31 140 0v122c-57 31-87-30-140 0z" fill="#f3f6ff"/>' + ''.join(f'<rect x="{94+x*28}" y="{52+y*30}" width="28" height="30" fill="#101a2a"/>' for y in range(4) for x in range(5) if (x+y)%2==0),
        'trofeu': '<path d="M115 54h90v77a45 45 0 0 1-90 0z" fill="#ffcc76"/><path d="M115 70H87v40q0 41 43 41m75-81h28v40q0 41-43 41" fill="none" stroke="#f2aa4d" stroke-width="13"/><path d="M160 177v48m-35 14h70" stroke="#ffcc76" stroke-width="16" stroke-linecap="round"/><path d="m160 79 8 16 18 3-13 13 3 18-16-9-16 9 3-18-13-13 18-3z" fill="#9b5f22"/>',
        'capacete': '<path d="M78 187v-43a82 82 0 0 1 164 0v72H105z" fill="#ff463e"/><path d="M120 115h115v54H120q-30-27 0-54" fill="#091523"/><path d="M129 125h100v15H121z" fill="#76e0ee"/><path d="M82 187h157v30H103z" fill="#f7f9ff"/><path d="M150 63q30 0 53 20" fill="none" stroke="#fff" stroke-width="9"/>',
    }
    return _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 300">' + desenhos.get(tipo, desenhos['carro']) + '</svg>')


def _arquivo_imagem_uri(caminho):
    from mimetypes import guess_type
    return 'data:' + (guess_type(str(caminho))[0] or 'image/png') + ';base64,' + base64.b64encode(caminho.read_bytes()).decode()


def foto_participante(nome):
    from pathlib import Path
    # Fotos próprias no repositório têm prioridade sobre os links da referência.
    raiz = Path(__file__).resolve().parent / 'assets' / 'palpiteiros'
    for extensao in ('.jpg', '.png', '.webp', '.jpeg'):
        caminho = raiz / (nome + extensao)
        if caminho.is_file():
            return _arquivo_imagem_uri(caminho)
    return FOTOS_PARTICIPANTES.get(nome, '')


def logo_grupo():
    from pathlib import Path
    raiz = Path(__file__).resolve().parent / 'assets'
    for nome in ('logo_grupo.png', 'logo_grupo.webp', 'logo_grupo.jpg'):
        caminho = raiz / nome
        if caminho.is_file():
            return _arquivo_imagem_uri(caminho)
    url = str(configuracao('LOGO_GRUPO_URL', '') or '')
    return url if url.startswith(('https://', 'http://')) else ''


def avatar_html(nome, tamanho='normal'):
    iniciais = ''.join(p[0] for p in nome.split()[:2]) or 'F1'
    fundo = _svg_uri(f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" rx="48" fill="#293b58"/><text x="48" y="59" text-anchor="middle" fill="#f3f6ff" font-family="sans-serif" font-size="30" font-weight="700">{escape(iniciais)}</text></svg>')
    foto = foto_participante(nome)
    imagens = (f'url(&quot;{escape(foto, quote=True)}&quot;), ' if foto else '') + f'url(&quot;{fundo}&quot;)'
    return f'<span class="avatar avatar-{tamanho}" role="img" aria-label="{escape(nome, quote=True)}" style="background-image:{imagens}"></span>'


def calendario_temporada(gabaritos):
    realizados = set() if gabaritos.empty else set(zip(gabaritos['GP'],gabaritos['Tipo']))
    registros = []
    for gp in lista_gps:
        sessoes = sessoes_disponiveis(gp)
        pendentes = [tipo for tipo in sessoes if (gp,tipo) not in realizados]
        registros.append({'GP':gp, 'Status':'Concluído' if not pendentes else ('Parcial' if len(pendentes)<len(sessoes) else 'Não apurado'),
                          'Sessões pendentes':len(pendentes), 'Pontos disponíveis':sum(MAX_PONTOS_SESSAO[t] for t in pendentes),
                          'Pendentes':tuple(pendentes), 'Sprint':gp in sprint_gps})
    return pd.DataFrame(registros)


def _posicoes(totais):
    return totais.rank(method='min',ascending=False).astype(int)


def _contar_acertos(palpites,gabaritos,nomes):
    campos_totais = ['Acertos','Campos avaliados','Poles certas','Especiais certos','Sessões enviadas']
    contadores = {nome:dict.fromkeys(campos_totais,0) for nome in nomes}
    indice = {(r['GP'],r['Tipo']):r for r in gabaritos.to_dict('records')} if not gabaritos.empty else {}
    registros = palpites.drop_duplicates(['Usuario','GP','Tipo'],keep='last').to_dict('records') if not palpites.empty else []
    for p in registros:
        g = indice.get((p['GP'],p['Tipo']))
        if g is None or p['Usuario'] not in contadores:
            continue
        contador = contadores[p['Usuario']]
        contador['Sessões enviadas'] += 1
        for campo in campos_sessao(p['Tipo']):
            real,valor = g.get(campo,''),p.get(campo,'')
            if pd.isna(real) or not str(real).strip():
                continue
            contador['Campos avaliados'] += 1
            if pd.notna(valor) and str(valor).strip()==str(real).strip():
                contador['Acertos'] += 1
                contador['Poles certas'] += int(campo=='Pole')
                contador['Especiais certos'] += int(campo in ('VoltaRapida','PrimeiroAbandono','MaisUltrapassagens'))
    metricas = pd.DataFrame.from_dict(contadores,orient='index',columns=campos_totais)
    metricas['Precisão (%)'] = (100*metricas['Acertos']/metricas['Campos avaliados'].replace(0,float('nan'))).fillna(0)
    return metricas


def _detalhar_sessoes(palpites,gabaritos):
    colunas = ['Usuario','GP','Tipo','Pontos']
    if palpites.empty or gabaritos.empty:
        return pd.DataFrame(columns=colunas)
    indice = {(r['GP'],r['Tipo']):r for r in gabaritos.to_dict('records')}
    registros = []
    for p in palpites.drop_duplicates(['Usuario','GP','Tipo'],keep='last').to_dict('records'):
        g = indice.get((p['GP'],p['Tipo']))
        if g is not None:
            registros.append({'Usuario':p['Usuario'],'GP':p['GP'],'Tipo':p['Tipo'],'Pontos':calcular_pontos_sessao(p,g)})
    return pd.DataFrame(registros,columns=colunas)


@st.cache_data(max_entries=4, ttl=300, show_spinner=False)
def analisar_temporada(palpites,gabaritos):
    # Dados novos alteram a chave do cache imediatamente; não são feitas outras requisições.
    g = gabaritos.drop_duplicates(['GP','Tipo'],keep='last') if not gabaritos.empty else gabaritos
    nomes = list(dict.fromkeys(participantes + (palpites['Usuario'].dropna().tolist() if not palpites.empty else [])))
    calendario = calendario_temporada(g)
    sessoes = _detalhar_sessoes(palpites,g)
    gps_apurados = set(g['GP']) if not g.empty else set()
    ordem = [gp for gp in lista_gps if gp in gps_apurados] + sorted(gps_apurados-set(lista_gps))
    matriz = pd.DataFrame(0,index=ordem,columns=nomes,dtype=float)
    if not sessoes.empty:
        matriz = sessoes.pivot_table(index='GP',columns='Usuario',values='Pontos',aggfunc='sum',fill_value=0).reindex(index=ordem,columns=nomes,fill_value=0).fillna(0)
    totais = matriz.sum()
    completos = calendario.loc[calendario['Status']=='Concluído','GP'].tolist()
    recentes = completos[-3:]
    historico = matriz.reindex(completos,fill_value=0)
    media = historico.mean().fillna(0) if completos else totais*0
    forma = matriz.reindex(recentes,fill_value=0).mean().fillna(0) if recentes else totais*0
    melhor = historico.max().fillna(0) if completos else totais*0
    vitorias = ((historico.eq(historico.max(axis=1),axis=0)) & historico.gt(0)).sum() if completos else totais*0
    anteriores = matriz.iloc[:-1].sum() if len(matriz) else totais*0
    pos = _posicoes(totais)
    acertos = _contar_acertos(palpites,g,nomes)
    tabela = pd.DataFrame({'Usuario':nomes,'Pontos':totais.reindex(nomes).values})
    tabela['Posição'] = tabela['Usuario'].map(pos)
    tabela['Equipe'] = tabela['Usuario'].map(EQUIPE_POR_USUARIO).fillna('Sem Equipe')
    tabela['Distância do líder'] = totais.max()-tabela['Pontos']
    tabela['Média / GP completo'] = tabela['Usuario'].map(media)
    tabela['Últimos 3 / GP'] = tabela['Usuario'].map(forma)
    tabela['Melhor GP'] = tabela['Usuario'].map(melhor)
    tabela['Vitórias em GPs'] = tabela['Usuario'].map(vitorias)
    tabela['Variação na última etapa'] = tabela['Usuario'].map(_posicoes(anteriores))-tabela['Posição'] if len(matriz)>1 else 0
    for campo in acertos.columns:
        tabela[campo] = tabela['Usuario'].map(acertos[campo])
    tabela = tabela.sort_values(['Pontos','Usuario'],ascending=[False,True],kind='stable').reset_index(drop=True)
    pontuacao_apurada = sum(MAX_PONTOS_SESSAO.get(r['Tipo'],0) for r in g.to_dict('records')) if not g.empty else 0
    return {'tabela':tabela, 'matriz':matriz, 'sessoes':sessoes, 'calendario':calendario,
            'gabaritos':g, 'completos':completos, 'recentes':recentes,
            'pontos_restantes':int(calendario['Pontos disponíveis'].sum()), 'maximo_apurado':pontuacao_apurada}


@st.cache_data(max_entries=4, ttl=300, show_spinner=False)
def simular_reta_final(sessoes,gabaritos,calendario,nomes,totais,simulacoes=4000):
    """Bootstrap conjunto por tipo de sessão; empates dividem o crédito de liderança."""
    import numpy as np
    rng = np.random.default_rng(2026)
    finais = np.tile(np.asarray(totais,dtype=float),(simulacoes,1))
    pendencias = [t for valores in calendario['Pendentes'] for t in valores]
    tipos = sorted(set(pendencias))
    for tipo in tipos:
        gps = gabaritos.loc[gabaritos['Tipo']==tipo,'GP'].drop_duplicates().tolist() if not gabaritos.empty else []
        if not gps:
            return None
        registros = sessoes.loc[sessoes['Tipo']==tipo]
        if registros.empty:
            return None
        amostras = registros.pivot_table(index='GP',columns='Usuario',values='Pontos',aggfunc='sum',fill_value=0).reindex(index=gps,columns=nomes,fill_value=0).fillna(0).to_numpy(dtype=float)
        # A mesma sessão sorteada serve para todos: preserva a correlação observada.
        sorteios = rng.integers(0,len(amostras),size=(simulacoes,pendencias.count(tipo)))
        finais += amostras[sorteios].sum(axis=1)
    maximos = finais.max(axis=1,keepdims=True)
    empatados = finais==maximos
    chances = (empatados/empatados.sum(axis=1,keepdims=True)).mean(axis=0)*100
    return pd.DataFrame({'Usuario':nomes,'Liderança simulada (%)':chances,
                         'Projeção mediana':np.median(finais,axis=0),
                         'Faixa inferior (P10)':np.percentile(finais,10,axis=0),
                         'Faixa superior (P90)':np.percentile(finais,90,axis=0)})


def tabela_chances(analise):
    tabela = analise['tabela']
    return simular_reta_final(analise['sessoes'],analise['gabaritos'],analise['calendario'],
                             tabela['Usuario'].tolist(),tabela['Pontos'].tolist())


def situacao_titulo(pontos,pontos_lider,restantes):
    diferenca = pontos_lider-pontos
    if diferenca==0:
        return 'Na liderança'
    if diferenca>restantes:
        return 'Sem alcance matemático'
    if diferenca==restantes:
        return 'Pode alcançar empate'
    return 'Pode alcançar a liderança'


def manual_pontuacao():
    st.markdown('### 🏁 Manual do palpiteiro')
    st.caption('Pontos por acerto exato · mesmas regras do seu bolão')
    with st.expander('⏱️ Pole position',expanded=True):
        st.markdown('**Classificação principal: 100 pontos**\n\n**Qualy Sprint: 100 pontos**')
    with st.expander('🏎️ Corrida principal · posição por posição'):
        st.table(pd.DataFrame({'Posição':[f'{i}º' for i in range(1,11)],'Pontos':list(PONTOS_PRINCIPAL.values())[:10]}).set_index('Posição'))
    with st.expander('⚡ Apostas especiais'):
        st.markdown('**Melhor volta:** 75 pontos\n\n**Primeiro abandono:** 200 pontos\n\n**Mais ultrapassagens:** 75 pontos')
        st.caption('Especiais válidos para a corrida principal. “Nenhum / Outro” segue a opção do gabarito.')
    with st.expander('🎯 Bônus por sequência exata'):
        st.markdown('**Top 3 na ordem:** +300 pontos\n\n**Top 5 na ordem:** +450 pontos\n\n**Top 10 na ordem:** +600 pontos')
        st.caption('Os bônus não se somam: vale somente o maior. Pela regra atual, os dez campos do palpite e do gabarito precisam estar preenchidos para avaliar o bônus.')
    with st.expander('🚀 Corrida Sprint'):
        st.table(pd.DataFrame({'Posição':[f'{i}º' for i in range(1,9)],'Pontos':list(PONTOS_SPRINT.values())}).set_index('Posição'))
        st.caption('Sem especiais e sem bônus de sequência na Sprint.')
    with st.expander('🏆 Quanto vale um fim de semana?'):
        st.markdown(f'**Corrida principal perfeita:** {numero_br(MAX_PONTOS_SESSAO["Corrida Principal"])} pontos\n\n**GP comum com pole:** 1.770 pontos\n\n**GP com Sprint e duas poles:** 2.230 pontos')
        st.caption('Conta somente o último palpite por participante, GP e sessão. A pontuação entra após o gabarito ser homologado.')



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


def estilo_paddock():
    bandeira,carro,trofeu = arte_f1('bandeira'),arte_f1('carro'),arte_f1('trofeu')
    return '''<style>
.hero {border-color:#354461; box-shadow:0 18px 45px #0002;}
.hero-body {padding-right:28%;}
.hero-art {position:absolute; width:250px; right:20px; top:10px; height:92%; object-fit:contain; opacity:.8; transform:rotate(18deg); pointer-events:none;}
.brand-logo {width:58px; height:58px; object-fit:contain; border-radius:12px;}
.group-watermark {position:absolute; right:24px; bottom:16px; width:80px; max-height:70px; object-fit:contain; opacity:.8;}
[data-testid="stMetric"] {position:relative; overflow:hidden; min-height:112px; padding-right:72px;}
[data-testid="stMetric"]::after {content:""; position:absolute; right:-4px; top:10px; width:95px; height:95px; background:url("''' + carro + '''") center/contain no-repeat; opacity:.2; pointer-events:none;}
[data-testid="stHorizontalBlock"]>div:nth-child(1) [data-testid="stMetric"]::after {background-image:url("''' + bandeira + '''");}
[data-testid="stHorizontalBlock"]>div:nth-child(3) [data-testid="stMetric"]::after {background-image:url("''' + trofeu + '''");}
[data-testid="stMetricValue"] {position:relative; z-index:1; font-variant-numeric:tabular-nums;}
[data-testid="stRadio"] label[data-baseweb="radio"]::before {content:""; display:inline-block; width:22px; height:25px; background:url("''' + bandeira + '''") center/cover no-repeat; flex-shrink:0; margin-right:6px;}
[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(2)::before {background-image:url("''' + carro + '''");}
[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(3)::before {background-image:url("''' + trofeu + '''");}
.avatar {display:inline-block; width:48px; height:48px; border-radius:50%; background-color:#293b58; background-size:cover; background-position:center 28%; flex-shrink:0; border:2px solid #566982; box-shadow:0 4px 14px #0004;}
.avatar-large {width:86px; height:86px; margin:18px 0 5px; border:3px solid #e6b564;}
.avatar-mini {width:40px; height:40px;}
.podium {position:relative; min-height:310px; padding:24px; border-radius:18px; background:radial-gradient(ellipse at top right,#273c5c 0,transparent 65%),linear-gradient(145deg,#182438,#101827);}
.podium-1 {border-color:#bb914d; background:radial-gradient(ellipse at top right,#74532b66 0,transparent 70%),linear-gradient(145deg,#192437,#101827);}
.podium-top {display:flex; justify-content:space-between; gap:10px; align-items:center;}
.movement {color:#9ac9be; font-size:12px; background:#1a2a39; padding:4px 7px; border-radius:7px;}
.podium .team-name {color:#9caec9; font-size:12px; min-height:32px;}
.podium .score {margin-top:16px; font-size:32px;}
.podium .gap {font-size:12px; color:#c3cedf; margin-top:8px;}
.season-strip {display:flex; flex-wrap:wrap; gap:10px 22px; border:1px solid #30405a; background:#101c2e; border-radius:12px; padding:13px 17px; margin:18px 0 25px; font-size:12px; color:#bdcce1;}
.editorial {position:relative; overflow:hidden; border:1px solid #30405a; border-radius:16px; padding:20px; background:linear-gradient(135deg,#18263a,#101a2a); min-height:206px; margin-bottom:16px;}
.editorial .tag {color:#ffb672; font-size:10px; font-weight:850; letter-spacing:.13em; text-transform:uppercase; padding-right:25px;}
.editorial-person {display:flex; align-items:center; gap:10px; margin:17px 0 12px; position:relative; z-index:1;}
.editorial h3 {font-size:17px; margin:0; padding:0; line-height:1.3;}
.editorial p {font-size:12px; line-height:1.7; color:#b5c4da; position:relative; z-index:1; margin:0;}
.editorial-art {position:absolute; width:130px; right:-30px; top:-17px; opacity:.12; pointer-events:none;}
.ranking-list {background:#111c2c; border:1px solid #2f3d53; border-radius:16px; overflow:hidden; margin-bottom:20px;}
.ranking-row {display:flex; align-items:center; gap:14px; padding:15px 20px; border-bottom:1px solid #263449; transition:background .15s;}
.ranking-row:last-child {border-bottom:0;}
.ranking-row:hover {background:#1b2b42;}
.row-pos {font-size:18px; font-weight:850; color:#f0b96e; width:30px; flex-shrink:0;}
.row-name {min-width:0; flex:1;}
.row-name strong {display:block; font-size:14px;}
.row-name small {display:block; color:#92a6c4; font-size:11px; margin-top:4px;}
.row-pace {width:18%; background:#233149; height:6px; border-radius:8px; overflow:hidden;}
.row-pace span {display:block; height:100%; background:linear-gradient(90deg,#ff453e,#ff9a62); border-radius:8px;}
.row-points {width:80px; text-align:right; font-size:19px; font-weight:800; font-variant-numeric:tabular-nums;}
.row-points small {display:block; font-size:10px; font-weight:400; color:#9bacc5;}
.profile {display:flex; align-items:center; gap:22px; padding:15px 22px; background:#152238; border:1px solid #344765; border-radius:18px; margin:18px 0;}
.profile .avatar {margin:0;}
.profile h2 {padding:0; margin:0; font-size:26px;}
.profile p {color:#9fb1ce; margin:8px 0 0; font-size:12px;}
@media(max-width:640px) {.hero-body {padding-right:23px;} .hero-art {opacity:.13; right:-20px; width:210px;} .hero-body h1,.hero-body p {position:relative; z-index:1;} .podium {min-height:280px;} .ranking-row {padding:12px 10px; gap:9px;} .row-pace {display:none;} .row-name strong {font-size:12px;} .row-name small {font-size:10px;} .row-points {font-size:16px; width:65px;} .profile {gap:14px; padding:15px;} .profile h2 {font-size:21px;} [data-testid="stMetric"] {padding-right:52px;} [data-testid="stMetric"]::after {width:75px; opacity:.13;} }
</style>'''


def cabecalho():
    st.markdown(CSS + estilo_paddock(), unsafe_allow_html=True)
    logo = logo_grupo()
    marca = f'<img class="brand-logo" src="{escape(logo, quote=True)}" alt="Logo do grupo"/>' if logo else '<div class="brand-mark">F1</div>'
    st.markdown(f'<div class="brand">{marca}<div class="brand-name">BOLÃO 2026<small>SEU PALPITE. SUA DISPUTA.</small></div></div>', unsafe_allow_html=True)
    return st.radio('Navegação', ['Enviar Palpite','Meus Palpites','Classificações','Administrador'],
                    horizontal=True, label_visibility='collapsed', key='navegacao')


def hero(titulo, descricao, etiqueta='TEMPORADA 2026'):
    arte = 'trofeu' if 'PALPITEIROS' in etiqueta else 'bandeira' if 'PARTICIPANTE' in etiqueta else 'carro'
    st.markdown(f'''<div class="hero"><video autoplay loop muted playsinline aria-hidden="true"><source src="{URL_VIDEO_GITHUB}" type="video/mp4"></video>
    <div class="hero-body"><div class="eyebrow">{escape(etiqueta)}</div><h1>{escape(titulo)}</h1>
    <p>{escape(descricao)}</p><span class="pill">20 PARTICIPANTES</span><span class="pill">10 EQUIPES</span><span class="pill">UMA DISPUTA</span></div><img class="hero-art" src="{arte_f1(arte)}" alt="Ilustração de automobilismo"/></div>''', unsafe_allow_html=True)


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


def cartao_editorial(titulo,nome,descricao,tipo='capacete'):
    foto = avatar_html(nome,'mini') if nome else ''
    st.markdown(f'<div class="editorial"><img class="editorial-art" src="{arte_f1(tipo)}" alt=""/><div class="tag">{escape(titulo)}</div><div class="editorial-person">{foto}<h3>{escape(nome or "Aguardando resultados")}</h3></div><p>{escape(descricao)}</p></div>',unsafe_allow_html=True)


def quadro_destaques(analise,chances):
    tabela = analise['tabela']
    secao('PADDOCK / QUEM ESTÁ FAZENDO A DIFERENÇA','Os nomes da disputa')
    c1,c2,c3 = st.columns(3)
    lider = tabela.iloc[0]
    with c1:
        if chances is not None:
            maior = chances.sort_values(['Liderança simulada (%)','Usuario'],ascending=[False,True]).iloc[0]
            qtd_empates = int((chances['Liderança simulada (%)']==maior['Liderança simulada (%)']).sum())
            detalhe = f'{numero_br(maior["Liderança simulada (%)"],1)}% de liderança no modelo histórico.'
            if qtd_empates>1:
                detalhe += f' Empatado com outros {qtd_empates-1} no modelo.'
            cartao_editorial('Favorito da simulação',maior['Usuario'],detalhe,'trofeu')
        else:
            cartao_editorial('Referência a ser batida',lider['Usuario'],f'{numero_br(lider["Pontos"])} pontos no campeonato. As chances aguardam histórico suficiente.','trofeu')
    quantidade = len(analise['gabaritos'])
    elegiveis = tabela.loc[(tabela['Sessões enviadas']>=max(1,(quantidade+1)//2)) & (tabela['Campos avaliados']>0)]
    with c2:
        if not elegiveis.empty:
            cabeca = elegiveis.sort_values(['Precisão (%)','Acertos'],ascending=False).iloc[0]
            cartao_editorial('Cabeça de gasolina',cabeca['Usuario'],f'{numero_br(cabeca["Precisão (%)"],1)}% de acertos: {int(cabeca["Acertos"])} em {int(cabeca["Campos avaliados"])} campos. Participação em pelo menos metade das sessões apuradas.')
        else:
            cartao_editorial('Cabeça de gasolina','', 'O destaque de precisão aparece quando há campos oficiais válidos para comparar.')
    fora_podio = tabela.loc[(tabela['Posição']>3)&(tabela['Distância do líder']<=analise['pontos_restantes'])&(tabela['Sessões enviadas']>0)]
    with c3:
        if not fora_podio.empty and analise['pontos_restantes']>0:
            if chances is not None:
                disputa = fora_podio.merge(chances[['Usuario','Liderança simulada (%)']],on='Usuario').sort_values(['Liderança simulada (%)','Últimos 3 / GP','Pontos'],ascending=False)
            else:
                disputa = fora_podio.sort_values(['Últimos 3 / GP','Pontos'],ascending=False)
            surpresa = disputa.iloc[0]
            cartao_editorial('Azarão na pista',surpresa['Usuario'],f'Fora do pódio e a {numero_br(surpresa["Distância do líder"])} pontos do líder. É o melhor colocado no modelo entre os candidatos fora do top 3.' if chances is not None else 'Fora do pódio, mas com o melhor ritmo recente entre os que ainda podem alcançar o líder.','carro')
        else:
            cartao_editorial('Azarão na pista','', 'Ainda não há candidato fora do top 3 com participação e alcance matemático nesta apuração.','carro')
    c4,c5,c6 = st.columns(3)
    with c4:
        if analise['recentes']:
            quente = tabela.sort_values(['Últimos 3 / GP','Pontos'],ascending=False).iloc[0]
            cartao_editorial('Pé embaixo',quente['Usuario'],f'Média de {numero_br(quente["Últimos 3 / GP"],1)} pontos nos {len(analise["recentes"])} últimos GPs completos. Empates são possíveis.','carro')
        else:
            cartao_editorial('Pé embaixo','','Aguardando o primeiro GP com todas as sessões homologadas.','carro')
    with c5:
        pole = tabela.sort_values(['Poles certas','Pontos'],ascending=False).iloc[0]
        cartao_editorial('Mestre da pole',pole['Usuario'] if pole['Poles certas']>0 else '',f'{int(pole["Poles certas"])} poles acertadas entre classificações principais e Sprint. Empates são possíveis.','bandeira')
    with c6:
        especial = tabela.sort_values(['Especiais certos','Pontos'],ascending=False).iloc[0]
        cartao_editorial('Faro para os especiais',especial['Usuario'] if especial['Especiais certos']>0 else '',f'{int(especial["Especiais certos"])} acertos em melhor volta, primeiro abandono e mais ultrapassagens. Empates são possíveis.','capacete')


def podio_palpiteiros(tabela):
    secao('NA FRENTE / CAMPEONATO COMPLETO','A disputa pelo topo')
    ativos = tabela.loc[tabela['Sessões enviadas']>0]
    for coluna,registro in zip(st.columns(3),ativos.head(3).to_dict('records')):
        with coluna:
            gap = 'Na liderança' if registro['Distância do líder']==0 else f'{numero_br(registro["Distância do líder"])} pontos para o líder'
            variacao = int(registro['Variação na última etapa'])
            movimento = f'↑ {variacao}' if variacao>0 else (f'↓ {abs(variacao)}' if variacao<0 else '—')
            st.markdown(f'<div class="podium podium-{int(registro["Posição"])}"><div class="podium-top"><div class="rank">{int(registro["Posição"]):02d} / CLASSIFICAÇÃO</div><span class="movement">{movimento}</span></div>{avatar_html(registro["Usuario"],"large")}<h3>{escape(registro["Usuario"])}</h3><div class="team-name">{escape(registro["Equipe"])}</div><div class="score">{numero_br(registro["Pontos"])} <small>pontos</small></div><div class="gap">{escape(gap)}</div></div>',unsafe_allow_html=True)
    st.caption('Posições empatadas compartilham a colocação. A seta compara com o campeonato sem o último GP apurado; dentro do empate, a ordem visual é alfabética.')


def _grafico_barras(tabela,chave):
    opcoes = {'color':'#ff463e','horizontal':True}
    parametros = inspect.signature(st.bar_chart).parameters
    st.bar_chart(tabela.set_index(chave)['Pontos'],**{k:v for k,v in opcoes.items() if k in parametros})


def visao_tabelas(analise,filtro):
    tabela = analise['tabela']
    tab1,tab2 = st.tabs(['🏁 Palpiteiros','🏎️ Equipes'])
    with tab1:
        if filtro=='Geral (Campeonato Completo)':
            mostrar = tabela.copy()
        else:
            mostrar = tabela.copy()
            mostrar['Pontos'] = mostrar['Usuario'].map(analise['matriz'].loc[filtro])
            mostrar['Posição'] = _posicoes(mostrar.set_index('Usuario')['Pontos']).reindex(mostrar['Usuario']).values
            mostrar['Distância do líder'] = mostrar['Pontos'].max()-mostrar['Pontos']
            mostrar = mostrar.sort_values(['Pontos','Usuario'],ascending=[False,True])
        st.markdown('#### Grid dos palpiteiros')
        maior = max(1,mostrar['Pontos'].max())
        linhas = []
        for r in mostrar.to_dict('records'):
            largura = min(100,100*r['Pontos']/maior)
            linhas.append(f'<div class="ranking-row"><span class="row-pos">{int(r["Posição"]):02d}</span>{avatar_html(r["Usuario"],"mini")}<div class="row-name"><strong>{escape(r["Usuario"])}</strong><small>{escape(r["Equipe"])}</small></div><div class="row-pace"><span style="width:{largura:.1f}%"></span></div><div class="row-points">{numero_br(r["Pontos"])}<small>pontos</small></div></div>')
        st.markdown('<div class="ranking-list">'+''.join(linhas)+'</div>',unsafe_allow_html=True)
        with st.expander('Ver os números em detalhe'):
            campos = ['Posição','Usuario','Pontos','Distância do líder','Média / GP completo','Últimos 3 / GP','Melhor GP','Vitórias em GPs','Precisão (%)']
            st.dataframe(mostrar[campos].round(1),use_container_width=True,hide_index=True)
            if filtro!='Geral (Campeonato Completo)':
                st.caption('Pontos, posição e distância são da etapa selecionada; as demais estatísticas resumem a temporada.')
            st.caption('Médias e vitórias usam GPs completos; ausências contam como zero. Vitórias empatadas contam para todos os primeiros com pontuação positiva.')
    with tab2:
        if filtro=='Geral (Campeonato Completo)':
            base = tabela
        else:
            base = tabela.copy()
            base['Pontos'] = base['Usuario'].map(analise['matriz'].loc[filtro])
        equipes_df = ranking(base,'Equipe')
        equipes_df['Posição'] = equipes_df['Pontos'].rank(method='min',ascending=False).astype(int)
        st.dataframe(equipes_df[['Posição','Equipe','Pontos']],use_container_width=True,hide_index=True)
        _grafico_barras(equipes_df,'Equipe')
        st.caption('As equipes somam os pontos dos seus integrantes, conforme o cadastro atual.')


def raio_x_palpiteiro(analise):
    tabela = analise['tabela']
    nome = st.selectbox('Quem você quer acompanhar?',tabela['Usuario'].tolist(),key='raiox_usuario')
    r = tabela.loc[tabela['Usuario']==nome].iloc[0]
    restantes = analise['pontos_restantes']
    lider = tabela.iloc[0]['Pontos']
    st.markdown(f'<div class="profile">{avatar_html(nome,"large")}<div><div class="eyebrow">RAIO-X DO PALPITEIRO</div><h2>{escape(nome)}</h2><p>{escape(r["Equipe"])}</p></div></div>',unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('Posição por pontos',f'{int(r["Posição"])}º')
    c2.metric('Distância do líder',numero_br(r['Distância do líder']))
    c3.metric('Precisão nos campos válidos',numero_br(r['Precisão (%)'],1)+'%')
    c4,c5,c6 = st.columns(3)
    c4.metric('Média por GP completo',numero_br(r['Média / GP completo'],1))
    c5.metric('Forma recente / GP',numero_br(r['Últimos 3 / GP'],1))
    c6.metric('Melhor GP completo',numero_br(r['Melhor GP']))
    st.info(f'{situacao_titulo(r["Pontos"],lider,restantes)} · Teto individual: {numero_br(r["Pontos"]+restantes)} pontos se acertar tudo o que falta apurar.')
    if r['Distância do líder']>0 and restantes>0:
        st.caption(f'Precisa descontar {numero_br(r["Distância do líder"])} pontos para empatar com a pontuação atual do líder. Os adversários também continuarão pontuando.')
    matriz = analise['matriz']
    if not matriz.empty:
        st.markdown('#### Seu campeonato, etapa a etapa')
        evolucao = matriz[[nome]].cumsum()
        evolucao.index.name = 'GP'
        st.line_chart(evolucao)
        detalhes = pd.DataFrame({'GP':matriz.index,'Pontos no GP':matriz[nome].values,'Total acumulado':evolucao[nome].values})
        detalhes['Apuração'] = detalhes['GP'].map(analise['calendario'].set_index('GP')['Status']).fillna('Fora do calendário')
        st.dataframe(detalhes,use_container_width=True,hide_index=True)
    st.caption(f'{int(r["Acertos"])} acertos em {int(r["Campos avaliados"])} campos oficiais válidos nas sessões enviadas; campos em branco no palpite contam como erro. A precisão é informativa e não substitui os pontos ponderados do regulamento.')


def visao_titulo(analise,chances):
    tabela = analise['tabela']
    restantes = analise['pontos_restantes']
    lider = tabela.iloc[0]['Pontos']
    pendentes = analise['calendario'].loc[analise['calendario']['Sessões pendentes']>0]
    secao('RETA FINAL / CENÁRIOS','O campeonato ainda pode virar?')
    c1,c2,c3 = st.columns(3)
    c1.metric('GPs com sessões pendentes',len(pendentes))
    c2.metric('Pontos ainda em jogo por pessoa',numero_br(restantes))
    c3.metric('Sessões a apurar',int(pendentes['Sessões pendentes'].sum()))
    base = tabela[['Posição','Usuario','Pontos','Distância do líder']].copy()
    base['Teto individual'] = base['Pontos']+restantes
    base['Situação matemática'] = base['Pontos'].map(lambda p:situacao_titulo(p,lider,restantes))
    st.markdown('#### Termômetro do título')
    if chances is not None:
        base = base.merge(chances,on='Usuario')
        st.dataframe(base.round(1),use_container_width=True,hide_index=True)
        if restantes==0:
            st.success('Todas as sessões do calendário estão homologadas. A tabela já mostra o resultado final por pontos, preservando empates.')
        else:
            st.caption('Liderança simulada: crédito dividido entre os empatados na primeira posição. As porcentagens somam 100% antes do arredondamento. “0,0%” pode representar um valor pequeno ou nenhum caso nas 4.000 simulações; não significa eliminação matemática.')
    else:
        st.dataframe(base,use_container_width=True,hide_index=True)
        st.info('As chances aparecem quando existe histórico de pontuação para cada tipo de sessão ainda pendente. O alcance matemático já pode ser consultado acima.')
    with st.expander('Entenda o modelo e seus limites'):
        st.write('O modelo faz 4.000 reamostragens das pontuações já obtidas em cada tipo de sessão. Em cada sorteio, usa a mesma sessão histórica para todos os participantes, preservando diferenças observadas e ausências. A semente é fixa: mexer na página não muda os sorteios.')
        st.write('Parte da pontuação atual e adiciona as sessões ainda sem gabarito. Trata os tipos de sessão separadamente e pressupõe desempenho e participação semelhantes ao histórico. Não usa cotações, dados dos treinos nem resultados futuros da F1.')
        st.write('É uma estimativa condicionada ao histórico, não uma probabilidade calibrada ou garantia. P10 e P90 delimitam os 80% centrais das simulações, não um intervalo de confiança. Amostras pequenas ou mudanças de participação reduzem a utilidade do modelo.')
        st.caption('O calendário é o cadastrado no aplicativo. Sessão sem gabarito conta como pendente, inclusive de GP passado. Homologue resultados atrasados para atualizar os cenários. Não se aplica desempate extra, porque ele não existe no código atual.')
    if restantes<=0:
        return
    st.markdown('#### E se eu acelerar na reta final?')
    st.caption('Cenário hipotético: escolha o aproveitamento dos pontos restantes de dois concorrentes. Os demais mantêm o aproveitamento total observado até agora.')
    nomes = tabela['Usuario'].tolist()
    c1,c2 = st.columns(2)
    with c1:
        voce = st.selectbox('Seu palpiteiro',nomes,index=min(1,len(nomes)-1),key='sim_usuario')
    with c2:
        rivais = [n for n in nomes if n!=voce]
        rival = st.selectbox('Comparar com',rivais,key='sim_rival')
    eficiencia = (tabela.set_index('Usuario')['Pontos']/max(1,analise['maximo_apurado'])).clip(0,1)
    c1,c2 = st.columns(2)
    with c1:
        sua_pct = st.slider('Seu aproveitamento daqui para frente (%)',0,100,value=int(round(100*eficiencia[voce])),key=f'cenario_{voce}')
    with c2:
        rival_pct = st.slider('Aproveitamento do concorrente (%)',0,100,value=int(round(100*eficiencia[rival])),key=f'rival_{rival}')
    cenario = tabela[['Usuario','Pontos']].copy()
    cenario['Aproveitamento futuro (%)'] = cenario['Usuario'].map(eficiencia)*100
    cenario.loc[cenario['Usuario']==voce,'Aproveitamento futuro (%)'] = sua_pct
    cenario.loc[cenario['Usuario']==rival,'Aproveitamento futuro (%)'] = rival_pct
    cenario['Total no cenário'] = cenario['Pontos']+restantes*cenario['Aproveitamento futuro (%)']/100
    cenario['Posição no cenário'] = cenario['Total no cenário'].rank(method='min',ascending=False).astype(int)
    cenario = cenario.sort_values(['Total no cenário','Usuario'],ascending=[False,True])
    seus = cenario.loc[cenario['Usuario']==voce].iloc[0]
    dele = cenario.loc[cenario['Usuario']==rival].iloc[0]
    diferenca = seus['Total no cenário']-dele['Total no cenário']
    st.info(f'{voce}: {numero_br(seus["Total no cenário"],1)} pontos e {int(seus["Posição no cenário"])}º lugar neste cenário. Diferença para {rival}: {numero_br(diferenca,1)} pontos.')
    st.dataframe(cenario.round(1),use_container_width=True,hide_index=True)
    st.caption('Percentuais geram valores médios, que podem não corresponder a uma combinação exata de acertos. Este simulador não altera palpites, gabaritos ou pontos reais.')


def visao_evolucao(analise):
    st.markdown('#### A corrida pela liderança')
    nomes = analise['tabela']['Usuario'].tolist()
    escolhidos = st.multiselect('Comparar palpiteiros',nomes,default=nomes[:5],key='evolucao_usuarios')
    modo = st.radio('Gráfico',['Acumulado','Por GP'],horizontal=True)
    matriz = analise['matriz']
    if escolhidos and not matriz.empty:
        grafico = matriz[escolhidos].cumsum() if modo=='Acumulado' else matriz[escolhidos]
        grafico.index.name = 'GP'
        st.line_chart(grafico)
    st.caption('O gráfico segue a ordem de GPs cadastrada e inclui etapas parciais. Ausência de palpite apurado aparece como zero.')
    st.markdown('#### Calendário e pontos disponíveis')
    cal = analise['calendario'].copy()
    cal['Sessões sem gabarito'] = cal['Pendentes'].map(lambda valores:' · '.join(valores) or 'Todas homologadas')
    st.dataframe(cal[['GP','Sprint','Status','Pontos disponíveis','Sessões sem gabarito']],use_container_width=True,hide_index=True)
    st.caption('GP normal vale até 1.770 pontos; com Sprint, até 2.230. Os pontos disponíveis descontam somente as sessões já homologadas.')


def tela_classificacoes():
    hero('O grid muda. A disputa também.', 'Seu lugar no campeonato, quem vem acelerando e os caminhos até a última bandeirada.', 'CENTRAL DOS PALPITEIROS')
    palpites,_ = ler_dados(ARQUIVO_DADOS)
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    analise = analisar_temporada(palpites,gabaritos)
    tabela = analise['tabela']
    filtro = st.selectbox('Etapa',['Geral (Campeonato Completo)']+lista_gps,key='filtro_classificacao')
    if analise['sessoes'].empty:
        st.info('Ainda não há palpites com resultado homologado. O manual de pontuação está disponível na lateral.')
        return
    pontos = tabela['Pontos'] if filtro=='Geral (Campeonato Completo)' else analise['matriz'].loc[filtro] if filtro in analise['matriz'].index else pd.Series(dtype=float)
    if pontos.empty:
        st.info('Ainda não há pontuação apurada para esta etapa. Selecione outra etapa ou a classificação geral.')
        return
    c1,c2,c3 = st.columns(3)
    if filtro=='Geral (Campeonato Completo)':
        c1.metric('Palpiteiros com resultado',int((tabela['Sessões enviadas']>0).sum()))
        c2.metric('GPs completos',len(analise['completos']))
    else:
        c1.metric('Palpiteiros com resultado no GP',analise['sessoes'].loc[analise['sessoes']['GP']==filtro,'Usuario'].nunique())
        c2.metric('Sessões homologadas no GP',int((analise['gabaritos']['GP']==filtro).sum()))
    c3.metric('Pontos do líder' if filtro=='Geral (Campeonato Completo)' else 'Melhor pontuação no GP',numero_br(pontos.max()))
    if filtro!='Geral (Campeonato Completo)':
        st.caption(f'Grid filtrado por GP de {filtro}. Os destaques, o raio-X e as projeções usam o campeonato completo.')
    st.markdown(f'<div class="season-strip"><span>🏁 {len(analise["completos"])} GPs completos</span><span>⏳ {int((analise["calendario"]["Sessões pendentes"]>0).sum())} com sessões pendentes</span><span>⚡ {numero_br(analise["pontos_restantes"])} pontos ainda disponíveis por pessoa</span></div>',unsafe_allow_html=True)
    podio_palpiteiros(tabela)
    chances = tabela_chances(analise)
    quadro_destaques(analise,chances)
    st.markdown('### Explore a disputa')
    painel = st.radio('Central de classificação',['Tabela e equipes','Raio-X do palpiteiro','Corrida pelo título','Evolução e calendário'],horizontal=True,key='painel_classificacao')
    if painel=='Tabela e equipes':
        visao_tabelas(analise,filtro)
    elif painel=='Raio-X do palpiteiro':
        raio_x_palpiteiro(analise)
    elif painel=='Corrida pelo título':
        visao_titulo(analise,chances)
    else:
        visao_evolucao(analise)


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
    st.caption('🏁 Abra a lateral no canto superior esquerdo para consultar o manual de pontuação.')
    if not GITHUB_TOKEN:
        st.error('A variável GITHUB_TOKEN não foi encontrada nas configurações de ambiente.')
        return
    if st.session_state.get('mensagem_sucesso'):
        st.success(st.session_state.pop('mensagem_sucesso'))
    with st.sidebar:
        st.markdown('### Central do campeonato')
        st.caption('Atualize para conferir os últimos palpites e resultados homologados.')
        if st.button('Atualizar dados agora',use_container_width=True):
            _ler_dados_cache.clear()
            st.rerun()
        manual_pontuacao()
    try:
        {'Enviar Palpite':tela_enviar,'Meus Palpites':tela_meus_palpites,
         'Classificações':tela_classificacoes,'Administrador':tela_admin}[menu]()
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        logger.exception('Falha ao carregar tela')
        st.error('Não foi possível carregar os dados. Verifique a conexão, a configuração de acesso e as colunas dos CSVs e tente atualizar.')
    st.markdown('<div class="footer">BOLÃO F1 2026 · A EMOÇÃO DA CORRIDA CONTINUA NO SEU PALPITE.</div>',unsafe_allow_html=True)


if __name__ == '__main__':
    main()
