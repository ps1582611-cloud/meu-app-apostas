import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BetaAnalyst Pro + AI", layout="wide", initial_sidebar_state="collapsed")

# --- CSS CUSTOMIZADO PARA INTERFACE DARK MODE PROFISSIONAL ---
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

# --- CONFIGURAÇÕES DAS APIs (CHAVES) ---
# Substitua com as suas chaves reais
API_FOOTBALL_KEY = "d379541faa02a4cd2b5b13ba86c23955"
GOOGLE_AI_KEY = "AIzaSyC5kni7Y6IM0io3w0sO85i37Oc5yViiUDk"

# Configuração do Google Gemini
if GOOGLE_AI_KEY and GOOGLE_AI_KEY != "AIzaSyC5kni7Y6IM0io3w0sO85i37Oc5yViiUDk":
    genai.configure(api_key=GOOGLE_AI_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

HEADERS = {'x-apisports-key': API_FOOTBALL_KEY}

# --- FUNÇÕES COM SISTEMA DE CACHE PARA ECONOMIZAR CRÉDITOS ---

@st.cache_data(ttl=3600)  # Guarda o resultado por 1 hora na memória do computador
def buscar_id_por_nome(nome_time):
    if not API_FOOTBALL_KEY or API_FOOTBALL_KEY == "SUA_CHAVE_API_FOOTBALL":
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

@st.cache_data(ttl=3600)  # Guarda o resultado por 1 hora
def buscar_stats(team_id):
    if not API_FOOTBALL_KEY or API_FOOTBALL_KEY == "SUA_CHAVE_API_FOOTBALL":
        return None
    # Liga 71 = Brasileirão. Pode mudar o ID da liga e temporada se necessário.
    url = f"https://v3.football.api-sports.io/teams/statistics?league=71&season=2024&team={team_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.json().get('response')
    except:
        return None

def calcular_peso_forma(string_forma):
    if not string_forma: 
        return 0.0
    # Analisa os últimos 5 jogos
    ultimos_5 = string_forma[-5:]
    peso = 0.0
    for jogo in ultimos_5:
        if jogo == 'W': peso += 0.25  # Vitória sobe a força
        if jogo == 'L': peso -= 0.20  # Derrota desce a força
        if jogo == 'D': peso += 0.05  # Empate mantém levemente
    return peso

def gerar_analise_ia(casa, fora, p_c, p_e, p_f, gols, esc, cart_c, cart_f):
    if not model:
        return "⚠️ Chave do Google Gemini não configurada. Insira a sua chave para obter a análise da IA."
    
    prompt = f"""
    Aja como um analista de apostas desportivas profissional e especialista em futebol.
    Analise o seguinte confronto com base nos dados fornecidos:
    
    Confronto: {casa} vs {fora}
    Probabilidades de Vitória: {casa} ({p_c:.1f}%), Empate ({p_e:.1f}%), {fora} ({p_f:.1f}%)
    Gols Previstos para o jogo: {gols:.2f}
    Escanteios Projetados: {esc:.1f}
    Média de Cartões: {casa} ({cart_c}), {fora} ({cart_f})
    
    Escreva uma análise técnica curta (máximo de 3 parágrafos). 
    Destaque quem tem o favoritismo real com base no momento das equipas, o nível de risco e recomende um mercado de valor para investir (Ex: Over/Under de gols, Match Odds, Escanteios ou Ambos Marcam).
    """
    try:
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Não foi possível gerar a análise da IA neste momento. (Erro: {str(e)})"

# --- INTERFACE PRINCIPAL ---
st.title("⚽ BetaAnalyst Pro + 🤖 IA")
st.markdown("Painel de Inteligência Preditiva com **Economia de Créditos (Cache)** e **Análise Automática**.")

# Bloco de inputs
col1, col2 = st.columns(2)

with col1:
    nome_casa = st.text_input("Time Mandante", "Flamengo", placeholder="Digite o nome do time da casa...")
    id_casa, real_nome_casa, logo_casa = buscar_id_por_nome(nome_casa)

with col2:
    nome_fora = st.text_input("Time Visitante", "Palmeiras", placeholder="Digite o nome do time visitante...")
    id_fora, real_nome_fora, logo_fora = buscar_id_por_nome(nome_fora)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 REALIZAR ANÁLISE COMPLETA"):
    # Validação inicial das chaves
    if API_FOOTBALL_KEY == "SUA_CHAVE_API_FOOTBALL":
        st.error("Por favor, configure a sua **API_FOOTBALL_KEY** no código para continuar.")
    elif id_casa and id_fora:
        with st.spinner('Acessando bancos de dados e gerando inteligência preditiva...'):
            s_casa = buscar_stats(id_casa)
            s_fora = buscar_stats(id_fora)

            if s_casa and s_fora:
                # 1. PROCESSAMENTO DE PESOS (FORMA RECENTE)
                p_casa = calcular_peso_forma(s_casa.get('form', ''))
                p_fora = calcular_peso_forma(s_fora.get('form', ''))

                # 2. GOLS PREVISTOS (Ajustados pelo peso)
                g_casa_base = float(s_casa.get('goals', {}).get('for', {}).get('average', {}).get('home', 0 or 0.1))
                g_fora_base = float(s_fora.get('goals', {}).get('for', {}).get('average', {}).get('away', 0 or 0.1))
                
                mg_casa = max(0.1, g_casa_base + p_casa)
                mg_fora = max(0.1, g_fora_base + p_fora)
                total_gols_previstos = mg_casa + mg_fora

                # 3. ESCANTEIOS (1T, 2T e Total)
                c_casa = float(s_casa.get('corner_kicks', {}).get('for', {}).get('average', 5.0) or 5.0)
                c_fora = float(s_fora.get('corner_kicks', {}).get('for', {}).get('average', 4.5) or 4.5)
                total_escanteios = c_casa + c_fora
                esc_1t = total_escanteios * 0.45
                esc_2t = total_escanteios * 0.55

                # 4. CARTÕES
                cartoes_casa = s_casa.get('cards', {}).get('yellow', {}).get('average', '2.3')
                cartoes_fora = s_fora.get('cards', {}).get('yellow', {}).get('average', '2.6')

                # 5. PROBABILIDADES DE RESULTADO FINAL (Lógica de Equilíbrio)
                dif = abs(mg_casa - mg_fora)
                if dif < 0.25:
                    prob_empate = 35.0
                elif dif < 0.6:
                    prob_empate = 28.0
                else:
                    prob_empate = 20.0
                
                restante = 100 - prob_empate
                soma_forcas = mg_casa + mg_fora
                prob_casa = (mg_casa / soma_forcas) * restante
                prob_fora = (mg_fora / soma_forcas) * restante

                # --- NOVO CABEÇALHO VISUAL COM LOGOS ---
                st.divider()
                
                col_logo_1, col_vs, col_logo_2 = st.columns([2, 1, 2])
                
                with col_logo_1:
                    if logo_casa:
                        st.markdown(f"<div style='text-align: center;'><img src='{logo_casa}' width='120'></div>", unsafe_allow_html=True)
                        st.markdown(f"<h2 style='text-align: center;'>{real_nome_casa}</h2>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: gray;'>MANDANTE</p>", unsafe_allow_html=True)
                    else:
                        st.subheader(real_nome_casa)

                with col_vs:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown("<h1 style='text-align: center; color: #ff4b4b; font-size: 60px;'>VS</h1>", unsafe_allow_html=True)

                with col_logo_2:
                    if logo_fora:
                        st.markdown(f"<div style='text-align: center;'><img src='{logo_fora}' width='120'></div>", unsafe_allow_html=True)
                        st.markdown(f"<h2 style='text-align: center;'>{real_nome_fora}</h2>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: gray;'>VISITANTE</p>", unsafe_allow_html=True)
                    else:
                        st.subheader(real_nome_fora)
                
                st.markdown("<br>", unsafe_allow_html=True)

                # --- NAVEGAÇÃO POR ABAS ---
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Probabilidades", 
                    "⚽ Gols e Escanteios", 
                    "🛡️ Disciplina", 
                    "🤖 Análise da IA"
                ])

                with tab1:
                    st.write("### Chances de Vitória Calculadas")
                    st.progress(int(prob_casa), text=f"{real_nome_casa}: {prob_casa:.1f}% (Peso: {p_casa:+.2f})")
                    st.progress(int(prob_empate), text=f"Empate: {prob_empate:.1f}%")
                    st.progress(int(prob_fora), text=f"{real_nome_fora}: {prob_fora:.1f}% (Peso: {p_fora:+.2f})")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    # Sugestão de mercado baseada nas probabilidades
                    if prob_casa > 50:
                        st.success(f"💡 **Forte Tendência:** Vitória do Mandante ({real_nome_casa})")
                    elif prob_fora > 50:
                        st.success(f"💡 **Forte Tendência:** Vitória do Visitante ({real_nome_fora})")
                    elif prob_empate > 33:
                        st.info("💡 **Forte Tendência:** Jogo muito equilibrado. 'Dupla Chance' ou 'Empate Anula Aposta' são recomendados.")

                with tab2:
                    st.write("### Gols e Cantos Projetados")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Gols Previstos (Total)", f"{total_gols_previstos:.2f}")
                    m2.metric("Escanteios Totais", f"{total_escanteios:.1f}")
                    m3.metric("Ambos Marcam", "SIM" if (mg_casa > 0.9 and mg_fora > 0.9) else "NÃO")
                    
                    st.divider()
                    st.write("#### 🚩 Distribuição de Escanteios por Tempo")
                    e1, e2 = st.columns(2)
                    e1.metric("1º Tempo (HT - 45%)", f"{esc_1t:.1f}")
                    e2.metric("2º Tempo (FT - 55%)", f"{esc_2t:.1f}")

                with tab3:
                    st.write("### Cartões e Disciplina")
                    c1, c2 = st.columns(2)
                    c1.metric(f"Média de Cartões ({real_nome_casa})", f"{cartoes_casa}")
                    c2.metric(f"Média de Cartões ({real_nome_fora})", f"{cartoes_fora}")

                with tab4:
                    st.write("### 🤖 Sugestão do Especialista Virtual")
                    with st.spinner('A IA está a redigir a análise...'):
                        analise_texto = gerar_analise_ia(
                            real_nome_casa, real_nome_fora, 
                            prob_casa, prob_empate, prob_fora, 
                            total_gols_previstos, total_escanteios, 
                            cartoes_casa, cartoes_fora
                        )
                        st.write(analise_texto)

            else:
                st.error("Não foi possível carregar os dados das equipas para a liga e temporada selecionadas.")
    else:
        st.warning("Certifique-se de que inseriu nomes válidos para ambos os times.")