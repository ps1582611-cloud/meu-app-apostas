import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BetaAnalyst Pro + AI", layout="wide", initial_sidebar_state="collapsed")

# --- CSS CUSTOMIZADO PARA INTERFACE DARK MODE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4255; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; border-radius: 8px; height: 3em; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #ff3333; color: white; }
    .stTextInput>div>div>input { background-color: #1e2130; color: white; border: 1px solid #3e4255; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e2130; border: 1px solid #3e4255; border-radius: 5px 5px 0px 0px; padding: 10px 20px; color: #8a8d9a; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES DAS APIs ---
API_FOOTBALL_KEY = "d379541faa02a4cd2b5b13ba86c23955"
GOOGLE_AI_KEY = st.secrets.get("GOOGLE_AI_KEY")

# --- CONFIGURAÇÃO DO GOOGLE GEMINI (FORÇANDO V1 ESTÁVEL) ---
if GOOGLE_AI_KEY:
    try:
        # Forçamos o uso da versão v1 para evitar o erro 404 da v1beta
        genai.configure(api_key=GOOGLE_AI_KEY, transport='rest') 
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro ao configurar o Gemini: {e}")
        model = None
else:
    st.warning("⚠️ Chave do Google Gemini não encontrada nos Secrets.")
    model = None

HEADERS = {'x-apisports-key': API_FOOTBALL_KEY}

# --- FUNÇÕES DE BUSCA E PROCESSAMENTO ---

@st.cache_data(ttl=3600)
def buscar_id_por_nome(nome_time):
    if not API_FOOTBALL_KEY:
        return None, None, None
    url = f"https://v3.football.api-sports.io/teams?search={nome_time}"
    try:
        response = requests.get(url, headers=HEADERS)
        dados = response.json().get('response', [])
        if dados:
            return dados[0]['team']['id'], dados[0]['team']['name'], dados[0]['team']['logo']
        return None, None, None
    except:
        return None, None, None

@st.cache_data(ttl=3600)
def buscar_stats(team_id):
    if not API_FOOTBALL_KEY:
        return None
    # Liga 71 = Brasileirão | Temporada 2024
    url = f"https://v3.football.api-sports.io/teams/statistics?league=71&season=2024&team={team_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.json().get('response')
    except:
        return None

def calcular_peso_forma(string_forma):
    if not string_forma: 
        return 0.0
    ultimos_5 = string_forma[-5:]
    peso = 0.0
    for jogo in ultimos_5:
        if jogo == 'W': peso += 0.25
        if jogo == 'L': peso -= 0.20
        if jogo == 'D': peso += 0.05
    return peso

def gerar_analise_ia(casa, fora, p_c, p_e, p_f, gols, esc, cart_c, cart_f):
    if not model:
        return "⚠️ IA não configurada corretamente nos Secrets."
    
    prompt = f"""
    Aja como um analista de apostas desportivas profissional.
    Analise o confronto: {casa} vs {fora}
    Probabilidades: {casa} ({p_c:.1f}%), Empate ({p_e:.1f}%), {fora} ({p_f:.1f}%)
    Gols Previstos: {gols:.2f} | Escanteios: {esc:.1f}
    Cartões: {casa} ({cart_c}), {fora} ({cart_f})
    
    Escreva uma análise técnica curta. Recomende um mercado de valor (Ex: Over/Under, Match Odds).
    """
    try:
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro na análise da IA: {str(e)}"

# --- INTERFACE PRINCIPAL ---
st.title("⚽ BetaAnalyst Pro + 🤖 IA")
st.markdown("Painel de Inteligência Preditiva com **Gemini 1.5 Flash**.")

col1, col2 = st.columns(2)

with col1:
    nome_casa = st.text_input("Time Mandante", "Flamengo")
    id_casa, real_nome_casa, logo_casa = buscar_id_por_nome(nome_casa)

with col2:
    nome_fora = st.text_input("Time Visitante", "Palmeiras")
    id_fora, real_nome_fora, logo_fora = buscar_id_por_nome(nome_fora)

if st.button("🚀 REALIZAR ANÁLISE COMPLETA"):
    if id_casa and id_fora:
        with st.spinner('Processando estatísticas...'):
            s_casa = buscar_stats(id_casa)
            s_fora = buscar_stats(id_fora)

            if s_casa and s_fora:
                # PROCESSAMENTO
                p_casa = calcular_peso_forma(s_casa.get('form', ''))
                p_fora = calcular_peso_forma(s_fora.get('form', ''))

                g_casa_base = float(s_casa.get('goals', {}).get('for', {}).get('average', {}).get('home', 0.1) or 0.1)
                g_fora_base = float(s_fora.get('goals', {}).get('for', {}).get('average', {}).get('away', 0.1) or 0.1)
                mg_casa = max(0.1, g_casa_base + p_casa)
                mg_fora = max(0.1, g_fora_base + p_fora)
                total_gols = mg_casa + mg_fora

                total_escanteios = float(s_casa.get('corner_kicks', {}).get('for', {}).get('average', 5.0) or 5.0) + \
                                 float(s_fora.get('corner_kicks', {}).get('for', {}).get('average', 4.5) or 4.5)
                
                cartoes_casa = s_casa.get('cards', {}).get('yellow', {}).get('average', '2.3')
                cartoes_fora = s_fora.get('cards', {}).get('yellow', {}).get('average', '2.6')

                soma_forcas = mg_casa + mg_fora
                prob_casa = (mg_casa / soma_forcas) * 70
                prob_fora = (mg_fora / soma_forcas) * 70
                prob_empate = 100 - (prob_casa + prob_fora)

                # VISUALIZAÇÃO
                st.divider()
                c_l1, c_vs, c_l2 = st.columns([2, 1, 2])
                with c_l1:
                    if logo_casa: st.image(logo_casa, width=100)
                    st.subheader(real_nome_casa)
                with c_vs:
                    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>VS</h1>", unsafe_allow_html=True)
                with c_l2:
                    if logo_fora: st.image(logo_fora, width=100)
                    st.subheader(real_nome_fora)

                tab1, tab2, tab3 = st.tabs(["📊 Probabilidades", "⚽ Stats Projetadas", "🤖 Análise IA"])
                
                with tab1:
                    st.progress(int(prob_casa), text=f"{real_nome_casa}: {prob_casa:.1f}%")
                    st.progress(int(prob_empate), text=f"Empate: {prob_empate:.1f}%")
                    st.progress(int(prob_fora), text=f"{real_nome_fora}: {prob_fora:.1f}%")

                with tab2:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Gols Totais", f"{total_gols:.2f}")
                    m2.metric("Escanteios", f"{total_escanteios:.1f}")
                    m3.metric("Cartões", f"{cartoes_casa} / {cartoes_fora}")

                with tab3:
                    st.write(gerar_analise_ia(real_nome_casa, real_nome_fora, prob_casa, prob_empate, prob_fora, total_gols, total_escanteios, cartoes_casa, cartoes_fora))
            else:
                st.error("Dados não encontrados para esta liga/temporada.")
    else:
        st.warning("Times não encontrados. Verifique a ortografia.")