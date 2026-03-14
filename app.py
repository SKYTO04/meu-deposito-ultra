import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os
import urllib.parse

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. DESIGN PREMIUM ---
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

# --- 3. BANCO DE DADOS ---
DB_FILE = "estoque_financeiro.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"
CASCOS_FILE = "emprestimo_cascos_v2.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['Categoria', 'Prateleira', 'Bebida', 'Qtd', 'Fardo', 'Posição', 'Minimo', 'Custo', 'Venda']).to_csv(DB_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Tipo', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 4. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha']), 'email': ''}

authenticator = stauth.Authenticate(credentials, 'estoque_pacaembu_cookie', 'auth_pacaembu_key', 30)

# CABEÇALHO
st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: -30px; margin-bottom: 20px;">
        <img src="https://cdn-icons-png.flaticon.com/512/931/931949.png" style="width: 100px;">
        <h1 style="text-align: center;">Conveniência Pacaembu</h1>
    </div>
    """, unsafe_allow_html=True)

authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_id = st.session_state["username"]
    user_info = df_users[df_users['user'] == user_id].iloc[0]
    sou_admin = user_info['is_admin'] == 'SIM'

    st.sidebar.markdown(f"### 👤 {nome_logado}")
    menu_opcoes = ["🏗️ Mapa", "📦 Romarinho", "🍾 Long Neck", "🔄 Vendas/Cargas", "🍶 Cascos"]
    if sou_admin: menu_opcoes += ["📜 Histórico (Adm)", "👥 Equipe", "📊 Financeiro", "⚙️ Configs"]
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: ROMARINHO ---
    if menu == "📦 Romarinho":
        st.title("📦 Estoque Romarinhos")
        df_estoque = pd.read_csv(DB_FILE)
        df_rom = df_estoque[df_estoque['Categoria'] == 'Romarinho']
        if df_rom.empty:
            st.info("Nenhum romarinho cadastrado.")
        else:
            cols = st.columns(3)
            for i, (_, row) in enumerate(df_rom.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""<div class="product-card"><h3>{row['Bebida']}</h3>
                    <p>Total: {int(row['Qtd'])} un</p>
                    <p style="color:#ff4b4b; font-weight:bold;">Engradados (24un): {int(row['Qtd']//row['Fardo'])}</p></div>""", unsafe_allow_html=True)

    # --- ABA: LONG NECK ---
    elif menu == "🍾 Long Neck":
        st.title("🍾 Estoque Long Necks")
        df_estoque = pd.read_csv(DB_FILE)
        df_ln = df_estoque[df_estoque['Categoria'] == 'Long Neck']
        if df_ln.empty:
            st.info("Nenhuma Long Neck cadastrada.")
        else:
            cols = st.columns(3)
            for i, (_, row) in enumerate(df_ln.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""<div class="product-card"><h3>{row['Bebida']}</h3>
                    <p>Total: {int(row['Qtd'])} un</p>
                    <p style="color:#ff4b4b; font-weight:bold;">Caixas (24un): {int(row['Qtd']//row['Fardo'])}</p></div>""", unsafe_allow_html=True)

    # --- ABA: CONFIGS (LÓGICA AUTOMÁTICA) ---
    elif menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Cadastro de Bebidas")
        with st.form("cad_smart"):
            cat = st.selectbox("Categoria", ["Romarinho", "Cerveja Garrafa", "Cerveja Lata", "Long Neck", "Refrigerante"])
            nome = st.text_input("Nome da Bebida").upper()
            
            if cat == "Romarinho" or cat == "Cerveja Garrafa":
                label_un = "Unidades por Engradado"
                val_padrao = 24
            elif cat == "Cerveja Lata":
                label_un = "Unidades por Fardo"
                val_padrao = 12
            elif cat == "Refrigerante":
                label_un = "Unidades por Fardo"
                val_padrao = 6
            elif cat == "Long Neck":
                label_un = "Unidades por Caixa (4x6)"
                val_padrao = 24
            
            fardo = st.number_input(label_un, value=val_padrao, step=1)
            custo = st.number_input("Custo Unitário", format="%.2f")
            venda = st.number_input("Venda Unitária", format="%.2f")
            prat = st.text_input("Localização").upper()
            
            if st.form_submit_button("Salvar Produto"):
                df_e = pd.read_csv(DB_FILE)
                novo = pd.DataFrame([[cat, prat, nome, 0, fardo, 1, 12, custo, venda]], columns=df_e.columns)
                pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                registrar_log(nome_logado, f"CADASTRO: {nome} ({cat})")
                st.success("Produto Salvo!")
                st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        with st.form("f_casco"):
            cli = st.text_input("Nome do Cliente")
            tipo_c = st.selectbox("O que ele levou?", ["Romarinho", "Coca-Cola 1L", "Coca-Cola 2L", "Cerveja 600ml"])
            qtd_c = st.number_input("Quantidade", min_value=1, step=1)
            if st.form_submit_button("Registrar"):
                pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), cli, tipo_c, qtd_c, "", 'PENDENTE']], 
                            columns=['Data', 'Nome', 'Tipo', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, mode='a', header=False, index=False)
                registrar_log(nome_logado, f"CASCO: Emprestou {qtd_c} un de {tipo_c} para {cli}")
                st.rerun()

        df_c = pd.read_csv(CASCOS_FILE)
        st.subheader("🚩 Pendentes")
        pendentes = df_c[df_c['Status'] == 'PENDENTE']
        for i, r in pendentes.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.warning(f"⚠️ **{r['Nome']}** deve {int(r['Quantidade'])} un de **{r['Tipo']}**")
            if c2.button("Baixa ✅", key=f"bx_{i}"):
                df_c.at[i, 'Status'] = 'DEVOLVIDO'
                df_c.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Baixa de {r['Nome']}")
                st.rerun()

        with st.expander("🕒 Corrigir Erros"):
            for i, r in df_c[df_c['Status'] == 'DEVOLVIDO'].iterrows():
                if st.button(f"Estornar {r['Nome']}", key=f"est_{i}"):
                    df_c.at[i, 'Status'] = 'PENDENTE'
                    df_c.to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: VENDAS/CARGAS ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Operação")
        df_e = pd.read_csv(DB_FILE)
        if not df_e.empty:
            with st.form("mov"):
                item = st.selectbox("Produto", df_e['Bebida'].unique())
                op = st.radio("Ação", ["Venda", "Carga", "Quebra"], horizontal=True)
                qtd = st.number_input("Quantidade (Unidades)", min_value=1)
                if st.form_submit_button("Confirmar"):
                    idx = df_e[df_e['Bebida'] == item].index
                    if op == "Venda": 
                        df_e.loc[idx, 'Qtd'] -= qtd
                        registrar_log(nome_logado, f"VENDA: {qtd} un de {item}")
                    elif op == "Carga": 
                        df_e.loc[idx, 'Qtd'] += qtd
                        registrar_log(nome_logado, f"CARGA: {qtd} un de {item}")
                    else: 
                        df_e.loc[idx, 'Qtd'] -= qtd
                        registrar_log(nome_logado, f"QUEBRA: {qtd} un de {item}")
                    df_e.to_csv(DB_FILE, index=False)
                    st.rerun()

    # --- ABA: HISTÓRICO (ADM) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- DEMAIS ABAS ---
    elif menu == "🏗️ Mapa":
        st.title("🏗️ Mapa")
        df_m = pd.read_csv(DB_FILE)
        for _, r in df_m.iterrows(): st.write(f"📍 {r['Bebida']}: {int(r['Qtd'])} un")

    elif menu == "📊 Financeiro" and sou_admin:
        df_f = pd.read_csv(DB_FILE)
        st.metric("💰 Custo", f"R$ {(df_f['Qtd']*df_f['Custo']).sum():,.2f}")
        st.metric("📈 Venda", f"R$ {(df_f['Qtd']*df_f['Venda']).sum():,.2f}")

    elif menu == "👥 Equipe" and sou_admin:
        with st.form("eq"):
            u, n, s = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha")
            a = st.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.DataFrame([[u, n, s, a]], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, mode='a', header=False, index=False)
                st.success("Criado!")

elif st.session_state["authentication_status"] is False:
    st.error('Login ou Senha incorretos.')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, faça o login.')
