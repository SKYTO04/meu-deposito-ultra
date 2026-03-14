import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os
import urllib.parse

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. PERSONALIZAÇÃO DE DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .product-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
    }
    h1, h2, h3 { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .stButton>button { border-radius: 8px; width: 100%; font-weight: bold; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ARQUIVOS DE DADOS ---
DB_FILE = "estoque_financeiro.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"
CASCOS_FILE = "emprestimo_cascos.csv"

# Inicialização de arquivos automática
def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], 
                    columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['Categoria', 'Prateleira', 'Bebida', 'Qtd', 'Fardo', 'Posição', 'Minimo', 'Custo', 'Venda']).to_csv(DB_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 4. SISTEMA DE LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][r['user']] = {'name': r['nome'], 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials['usernames'], 'estoque_cookie', 'auth_key', 30)

# LOGO E TÍTULO NO LOGIN
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/931/931949.png" # Substitua por "logo.png" se subir a imagem
st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: -30px; margin-bottom: 20px;">
        <img src="{URL_LOGO}" style="width: 100px; filter: drop-shadow(0px 4px 10px rgba(255,75,75,0.3));">
        <h1 style="text-align: center;">Conveniência Pacaembu</h1>
    </div>
    """, unsafe_allow_html=True)

nome_logado, auth_status, user_id = authenticator.login('main')

if auth_status:
    user_info = df_users[df_users['user'] == user_id].iloc[0]
    sou_admin = user_info['is_admin'] == 'SIM'

    st.sidebar.markdown(f"### 👤 {nome_logado}")
    if sou_admin: st.sidebar.info("Acesso: ADMINISTRADOR")
    
    menu_opcoes = ["🏗️ Mapa de Estoque", "📦 Romarinho", "🔄 Vendas/Cargas", "🍶 Cascos"]
    if sou_admin: menu_opcoes += ["📜 Histórico (Auditoria)", "👥 Gestão de Equipe", "📊 Financeiro", "⚙️ Configurações"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair do Sistema', 'sidebar')

    # --- FUNÇÕES AUXILIARES ---
    def get_cor_marca(nome):
        n = nome.upper()
        if "PURO MALTE" in n: return "#D4AF37"
        if "BRAHMA" in n: return "#D32F2F"
        if "BOA" in n: return "#0056b3"
        if "SKOL" in n: return "#FFD700"
        return "#6c757d"

    # --- ABA: ROMARINHO ---
    if menu == "📦 Romarinho":
        st.title("📦 Stock de Romarinhos")
        df_estoque = pd.read_csv(DB_FILE)
        df_rom = df_estoque[df_estoque['Categoria'] == 'Romarinho']
        
        if df_rom.empty: st.info("Nenhum romarinho cadastrado em Configurações.")
        else:
            cols = st.columns(3)
            for i, (_, row) in enumerate(df_rom.iterrows()):
                cor = get_cor_marca(row['Bebida'])
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="product-card" style="border-top: 5px solid {cor};">
                        <h3>{row['Bebida']}</h3>
                        <p>Total: <b>{int(row['Qtd'])} un</b></p>
                        <p>Engradados (12un): <b>{int(row['Qtd']//12)}</b></p>
                        <small style="color: {cor};">Preço Venda: R$ {row['Venda']:.2f}</small>
                    </div>
                    """, unsafe_allow_html=True)

    # --- ABA: VENDAS/CARGAS ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Movimentação de Estoque")
        df_estoque = pd.read_csv(DB_FILE)
        if not df_estoque.empty:
            with st.form("mov_form"):
                escolha = st.selectbox("Selecione o Produto", df_estoque['Bebida'].unique())
                tipo = st.radio("Tipo de Operação", ["Venda", "Entrada (Carga)", "Quebra/Perda"], horizontal=True)
                qtd_mov = st.number_input("Quantidade de Unidades", min_value=1, step=1)
                
                if st.form_submit_button("Confirmar Movimentação"):
                    idx = df_estoque[df_estoque['Bebida'] == escolha].index
                    row = df_estoque.loc[idx].iloc[0]
                    
                    if tipo == "Venda":
                        if df_estoque.loc[idx, 'Qtd'].values[0] >= qtd_mov:
                            df_estoque.loc[idx, 'Qtd'] -= qtd_mov
                            total_venda = qtd_mov * row['Venda']
                            msg = f"🧾 *RECIBO - PACAEMBU*\nItem: {escolha}\nQtd: {qtd_mov}\n
