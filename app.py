import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os
import urllib.parse

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. DESIGN PREMIUM (CSS) ---
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
    .stButton>button { border-radius: 8px; width: 100%; font-weight: bold; background-color: #ff4b4b; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS (CSV) ---
DB_FILE = "estoque_financeiro.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"
CASCOS_FILE = "emprestimo_cascos.csv"

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

# --- 4. SISTEMA DE LOGIN (VERSÃO ATUALIZADA) ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}

for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {
        'name': str(r['nome']),
        'password': str(r['senha']),
        'email': '' 
    }

authenticator = stauth.Authenticate(
    credentials,
    'estoque_pacaembu_cookie',
    'auth_pacaembu_key',
    30
)

# LOGO NO TOPO
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/931/931949.png"
st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: -30px; margin-bottom: 20px;">
        <img src="{URL_LOGO}" style="width: 100px; filter: drop-shadow(0px 4px 10px rgba(255,75,75,0.4));">
        <h1 style="text-align: center;">Conveniência Pacaembu</h1>
    </div>
    """, unsafe_allow_html=True)

# Chamada do login (estilo novo)
authenticator.login(location='main')

# Verificação do status
if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_id = st.session_state["username"]
    
    # Identificar Admin
    user_info = df_users[df_users['user'] == user_id].iloc[0]
    sou_admin = user_info['is_admin'] == 'SIM'

    st.sidebar.markdown(f"### 👤 {nome_logado}")
    if sou_admin: st.sidebar.info("Acesso: ADMINISTRADOR")
    
    menu_opcoes = ["🏗️ Mapa", "📦 Romarinho", "🔄 Vendas/Cargas", "🍶 Cascos"]
    if sou_admin:
        menu_opcoes += ["📜 Auditoria", "👥 Equipe", "📊 Financeiro", "⚙️ Configs"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair do Sistema', 'sidebar')

    # --- ABA: ROMARINHO ---
    if menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df_estoque = pd.read_csv(DB_FILE)
        df_rom = df_estoque[df_estoque['Categoria'] == 'Romarinho']
        if df_rom.empty:
            st.info("Nenhum romarinho cadastrado.")
        else:
            cols = st.columns(3)
            for i, (_, row) in enumerate(df_rom.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <h3>{row['Bebida']}</h3>
                        <p style="font-size: 20px;">Total: <b>{int(row['Qtd'])} un</b></p>
                        <p style="color: #ff4b4b;">Engradados: <b>{int(row['Qtd']//12)}</b></p>
                    </div>
                    """, unsafe_allow_html=True)

    # --- ABA: VENDAS/CARGAS ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Operação")
        df_estoque = pd.read_csv(DB_FILE)
        if not df_estoque.empty:
            with st.form("form_mov"):
                item = st.selectbox("Produto", df_estoque['Bebida'].unique())
                op = st.radio("Ação", ["Venda", "Carga", "Quebra"], horizontal=True)
                quantidade = st.number_input("Quantidade", min_value=1, step=1)
                
                if st.form_submit_button("Confirmar"):
                    idx = df_estoque[df_estoque['Bebida'] == item].index
                    if op == "Venda":
                        if df_estoque.loc[idx, 'Qtd'].values[0] >= quantidade:
                            df_estoque.loc[idx, 'Qtd'] -= quantidade
                            total = quantidade * df_estoque.loc[idx, 'Venda'].values[0]
                            msg = f"""*CONVENIÊNCIA PACAEMBU* 🧾
--------------------------
📦 *Item:* {item}
🔢 *Qtd:* {quantidade}
💵 *Total:* R$ {total:.2f}
--------------------------
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
                            st.session_state.link_zap = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                        else: st.error("Sem estoque!")
                    elif op == "Carga":
                        df_estoque.loc[idx, 'Qtd'] += quantidade
                    else:
                        df_estoque.loc[idx, 'Qtd'] -= quantidade
                    
                    df_estoque.to_csv(DB_FILE, index=False)
                    registrar_log(nome_logado, f"{op} de {quantidade} un de {item}")
                    st.success("Atualizado!")
                    st.rerun()
            
            if 'link_zap' in st.session_state:
                st.link_button("📤 Enviar WhatsApp", st.session_state.link_zap)

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        with st.form("f_casco"):
            cli = st.text_input("Cliente")
            q_casco = st.number_input("Qtd", min_value=1)
            tel = st.text_input("Telefone")
            if st.form_submit_button("Gravar"):
                pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), cli, q_casco, tel, 'PENDENTE']], 
                            columns=['Data', 'Nome', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, mode='a', header=False, index=False)
                registrar_log(nome_logado, f"Casco: {cli}")
                st.rerun()

        df_c = pd.read_csv(CASCOS_FILE)
        for i, r in df_c[df_c['Status'] == 'PENDENTE'].iterrows():
            c1, c2 = st.columns([3, 1])
            c1.warning(f"⚠️ {r['Nome']} ({int(r['Quantidade'])} un)")
            if c2.button("Baixa", key=f"c_{i}"):
                df_c.at[i, 'Status'] = 'DEVOLVIDO'
                df_c.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # --- ABA: CONFIGS ---
    elif menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Cadastro")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Romarinho", "Cerveja", "Refrigerante"])
            nome = st.text_input("Bebida").upper()
            custo = st.number_input("Custo", format="%.2f")
            venda = st.number_input("Venda", format="%.2f")
            fardo = st.number_input("Unidades/Fardo", value=12)
            prat = st.text_input("Setor").upper()
            if st.form_submit_button("Salvar"):
                df_e = pd.read_csv(DB_FILE)
                novo = pd.DataFrame([[cat, prat, nome, 0, fardo, 1, 12, custo, venda]], columns=df_e.columns)
                pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                st.success("Salvo!")

    # --- ABA: FINANCEIRO ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Dinheiro")
        df_f = pd.read_csv(DB_FILE)
        if not df_f.empty:
            custo_t = (df_f['Qtd'] * df_f['Custo']).sum()
            venda_t = (df_f['Qtd'] * df_f['Venda']).sum()
            st.metric("📦 Custo Estoque", f"R$ {custo_t:,.2f}")
            st.metric("📈 Retorno Previsto", f"R$ {venda_t:,.2f}")
            st.metric("🍀 Lucro", f"R$ {(venda_t-custo_t):,.2f}")

    # --- ABA: EQUIPE ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Funcionários")
        with st.form("add"):
            u_log = st.text_input("Login").lower()
            u_nom = st.text_input("Nome")
            u_sen = st.text_input("Senha")
            u_adm = st.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.DataFrame([[u_log, u_nom, u_sen, u_adm]], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, mode='a', header=False, index=False)
                st.success("Criado!")

    # --- ABA: MAPA ---
    elif menu == "🏗️ Mapa":
        st.title("🏗️ Mapa")
        df_m = pd.read_csv(DB_FILE)
        for p in df_m['Prateleira'].unique():
            st.subheader(f"📍 {p}")
            for _, r in df_m[df_m['Prateleira'] == p].iterrows():
                with st.expander(f"{r['Bebida']} ({int(r['Qtd'])} un)"):
                    st.text("📦 " * min(20, int(r['Qtd'] // r['Fardo'])))

elif st.session_state["authentication_status"] is False:
    st.error('Login ou Senha incorretos.')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, faça o login.')
