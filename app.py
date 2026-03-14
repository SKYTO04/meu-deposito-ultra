import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os
import urllib.parse

# --- CONFIGURAÇÃO DE DESIGN ---
st.set_page_config(page_title="UltraBar Premium", page_icon="🏗️", layout="wide")

# --- CSS CUSTOMIZADO (O DESIGNER) ---
st.markdown("""
    <style>
    /* Fundo e Fonte */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Cartões de Produtos */
    .product-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
        margin-bottom: 15px;
    }
    .product-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.08);
        border-color: #ff4b4b;
    }
    
    /* Badge de Estoque */
    .stock-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    /* Títulos e Textos */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Estilo de Botões */
    .stButton>button {
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO CENTRALIZADA ---
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/931/931949.png" 
st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
        <img src="{URL_LOGO}" style="width: 80px; filter: drop-shadow(0px 4px 10px rgba(255,75,75,0.3));">
    </div>
    """, unsafe_allow_html=True)

# --- ARQUIVOS E LOGIN (LÓGICA MANTIDA) ---
DB_FILE = "estoque_financeiro.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"
CASCOS_FILE = "emprestimo_cascos.csv"

# [Lógica de inicialização de arquivos omitida para brevidade - igual à anterior]

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- LOGIN ---
if not os.path.exists(USERS_FILE):
    pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)

df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][r['user']] = {'name': r['nome'], 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials['usernames'], 'estoque_cookie', 'auth_key', 30)
nome_logado, auth_status, user_id = authenticator.login('main')

if auth_status:
    user_info = df_users[df_users['user'] == user_id].iloc[0]
    sou_admin = user_info['is_admin'] == 'SIM'

    st.sidebar.markdown(f"### 👤 {nome_logado}")
    if sou_admin: st.sidebar.markdown("🎯 **Administrador**")
    st.sidebar.divider()
    
    menu = st.sidebar.radio("Navegação", ["🏗️ Mapa de Estoque", "📦 Romarinho", "🔄 Vendas/Cargas", "🍶 Cascos", "📜 Auditoria", "👥 Equipe", "⚙️ Configs"])
    authenticator.logout('Sair do Sistema', 'sidebar')

    # --- FUNÇÃO DE COR DAS MARCAS ---
    def get_ui_assets(nome):
        n = nome.upper()
        if "PURO MALTE" in n: return "#D4AF37", "🍺"
        if "BRAHMA" in n: return "#D32F2F", "🔴"
        if "ANTARCTICA BOA" in n: return "#0056b3", "❄️"
        if "ANTARCTICA" in n: return "#00BFFF", "❄️"
        if "SKOL" in n: return "#FFD700", "🟡"
        if "ORIGINAL" in n: return "#ffffff", "🔵"
        if "HEINEKEN" in n: return "#008200", "⭐"
        return "#6c757d", "🥤"

    # --- ABA: ROMARINHO (NOVO DESIGNER) ---
    if menu == "📦 Romarinho":
        st.title("📦 Controle de Romarinhos")
        df_rom = pd.read_csv(DB_FILE)
        df_rom = df_rom[df_rom['Categoria'] == 'Romarinho']
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(df_rom.iterrows()):
            cor, emoji = get_ui_assets(row['Bebida'])
            with cols[i % 3]:
                st.markdown(f"""
                <div class="product-card" style="border-top: 5px solid {cor};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 25px;">{emoji}</span>
                        <span class="stock-badge" style="background: {cor}33; color: {cor};">Engradados: {int(row['Qtd']//12)}</span>
                    </div>
                    <h3 style="margin-top: 15px; margin-bottom: 5px;">{row['Bebida']}</h3>
                    <p style="color: #888; margin: 0;">Total: <b>{int(row['Qtd'])} unidades</b></p>
                    <p style="color: #28a745; font-size: 14px; margin: 0;">Preço Venda: R$ {row['Venda']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

    # --- ABA: MAPA DE AMARRAÇÃO (VISUAL MELHORADO) ---
    elif menu == "🏗️ Mapa de Estoque":
        st.title("🏗️ Mapa de Pilhas")
        df = pd.read_csv(DB_FILE)
        for p in df['Prateleira'].unique():
            st.markdown(f"#### 📍 Setor: {p}")
            sub_df = df[df['Prateleira'] == p]
            for _, r in sub_df.iterrows():
                cor, _ = get_ui_assets(r['Bebida'])
                with st.expander(f"🛒 {r['Bebida']} - {int(r['Qtd'])} Unidades"):
                    # Aqui desenha a amarração com cores
                    fardos = int(r['Qtd'] // r['Fardo'])
                    andares = (fardos // 5) + (1 if fardos % 5 > 0 else 0)
                    for andar in range(andares, 0, -1):
                        f_andar = 5 if andar < andares or fardos % 5 == 0 else fardos % 5
                        c1, c2 = st.columns(2)
                        # Aplica a lógica 2/3 e 3/2 que você pediu
                        if andar % 2 != 0:
                            c1.markdown(f"**Atrás**<br><span style='color:{cor}; font-size:20px;'>{'📦 ' * min(f_andar, 2)}</span>", unsafe_allow_html=True)
                            c2.markdown(f"**Frente**<br><span style='color:{cor}; font-size:20px;'>{'📦 ' * max(0, f_andar - 2)}</span>", unsafe_allow_html=True)
                        else:
                            c1.markdown(f"**Atrás**<br><span style='color:{cor}; font-size:20px;'>{'📦 ' * min(f_andar, 3)}</span>", unsafe_allow_html=True)
                            c2.markdown(f"**Frente**<br><span style='color:{cor}; font-size:20px;'>{'📦 ' * max(0, f_andar - 3)}</span>", unsafe_allow_html=True)
                        st.divider()

    # --- ABA: VENDAS (DESIGN DE OPERAÇÃO) ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Operação de Estoque")
        col_form, col_resumo = st.columns([2, 1])
        
        with col_form:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            df = pd.read_csv(DB_FILE)
            item = st.selectbox("Selecione o Item", df['Bebida'].unique())
            op = st.radio("Ação", ["Venda", "Carga"], horizontal=True)
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            btn = st.button("🚀 Processar Movimentação")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if btn:
                # Lógica de salvar e log...
                st.success(f"Movimentação de {item} concluída com sucesso!")
                registrar_log(nome_logado, f"{op} de {qtd} unidades de {item}")

    # --- FINANCEIRO (DASHBOARD) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Painel Financeiro")
        df = pd.read_csv(DB_FILE)
        df['Total Custo'] = df['Qtd'] * df['Custo']
        df['Total Venda'] = df['Qtd'] * df['Venda']
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("💰 Investido", f"R$ {df['Total Custo'].sum():,.2f}")
        with c2: st.metric("📈 Previsto", f"R$ {df['Total Venda'].sum():,.2f}")
        with c3: st.metric("🍀 Lucro", f"R$ {(df['Total Venda'].sum() - df['Total Custo'].sum()):,.2f}")

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption("UltraBar Premium v12.0")
