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

# --- 4. SISTEMA DE LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {
        'name': str(r['nome']),
        'password': str(r['senha']),
        'email': '' 
    }

authenticator = stauth.Authenticate(credentials, 'estoque_pacaembu_cookie', 'auth_pacaembu_key', 30)

# CABEÇALHO
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/931/931949.png"
st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: -30px; margin-bottom: 20px;">
        <img src="{URL_LOGO}" style="width: 100px; filter: drop-shadow(0px 4px 10px rgba(255,75,75,0.4));">
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
    menu_opcoes = ["🏗️ Mapa", "📦 Romarinho", "🔄 Vendas/Cargas", "🍶 Cascos"]
    if sou_admin: menu_opcoes += ["📜 Histórico (Adm)", "👥 Equipe", "📊 Financeiro", "⚙️ Configs"]
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair do Sistema', 'sidebar')

    # --- ABA: HISTÓRICO DE MOVIMENTAÇÃO (SÓ ADMIN) ---
    if menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico Geral de Atividades")
        st.markdown("Veja abaixo quem tirou ou adicionou produtos no estoque:")
        
        df_log = pd.read_csv(LOG_FILE)
        if df_log.empty:
            st.info("Nenhuma movimentação registrada ainda.")
        else:
            # Mostra do mais novo para o mais antigo
            st.dataframe(df_log.iloc[::-1], use_container_width=True)
            
            if st.button("Limpar Histórico (Cuidado!)"):
                pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
                st.success("Histórico limpo!")
                st.rerun()

    # --- ABA: ROMARINHO ---
    elif menu == "📦 Romarinho":
        st.title("📦 Estoque de Romarinhos")
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
                        <p style="font-size: 18px;">Total: <b>{int(row['Qtd'])} un</b></p>
                        <p style="color: #ff4b4b; font-weight: bold;">Engradados (24un): {int(row['Qtd']//row['Fardo'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # --- ABA: VENDAS/CARGAS ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Operação de Estoque")
        df_estoque = pd.read_csv(DB_FILE)
        if not df_estoque.empty:
            with st.form("form_mov"):
                item = st.selectbox("Escolha o Produto", df_estoque['Bebida'].unique())
                op = st.radio("O que deseja fazer?", ["Venda", "Carga (Entrada)", "Quebra/Perda"], horizontal=True)
                quantidade = st.number_input("Quantidade em Unidades", min_value=1, step=1)
                
                if st.form_submit_button("Confirmar Movimentação"):
                    idx = df_estoque[df_estoque['Bebida'] == item].index
                    if op == "Venda":
                        if df_estoque.loc[idx, 'Qtd'].values[0] >= quantidade:
                            df_estoque.loc[idx, 'Qtd'] -= quantidade
                            registrar_log(nome_logado, f"VENDA: Tirou {quantidade} un de {item}")
                        else: st.error("Estoque insuficiente!")
                    elif op == "Carga (Entrada)":
                        df_estoque.loc[idx, 'Qtd'] += quantidade
                        registrar_log(nome_logado, f"CARGA: Adicionou {quantidade} un de {item}")
                    else:
                        df_estoque.loc[idx, 'Qtd'] -= quantidade
                        registrar_log(nome_logado, f"QUEBRA: Removeu {quantidade} un de {item}")
                    
                    df_estoque.to_csv(DB_FILE, index=False)
                    st.success("Movimentação registrada!")
                    st.rerun()

    # --- ABA: CASCOS (COM ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        with st.form("f_casco"):
            cli = st.text_input("Nome do Cliente")
            q = st.number_input("Quantidade", min_value=1)
            if st.form_submit_button("Registrar Empréstimo"):
                pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), cli, q, "", 'PENDENTE']], 
                            columns=['Data', 'Nome', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, mode='a', header=False, index=False)
                registrar_log(nome_logado, f"CASCO: Emprestou {q} para {cli}")
                st.rerun()

        df_c = pd.read_csv(CASCOS_FILE)
        st.subheader("🚩 Pendentes")
        for i, r in df_c[df_c['Status'] == 'PENDENTE'].iterrows():
            c1, c2 = st.columns([3, 1])
            c1.warning(f"⚠️ {r['Nome']} deve {int(r['Quantidade'])} cascos")
            if c2.button("Dar Baixa ✅", key=f"bx_{i}"):
                df_c.at[i, 'Status'] = 'DEVOLVIDO'
                df_c.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Baixa de {r['Nome']}")
                st.rerun()

        with st.expander("🕒 Corrigir Erros / Estornar"):
            for i, r in df_c[df_c['Status'] == 'DEVOLVIDO'].iterrows():
                if st.button(f"Estornar {r['Nome']}", key=f"est_{i}"):
                    df_c.at[i, 'Status'] = 'PENDENTE'
                    df_c.to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"ESTORNO: Voltou cobrança de {r['Nome']}")
                    st.rerun()

    # --- ABA: CONFIGS ---
    elif menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Cadastrar Novo Produto")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Romarinho", "Cerveja", "Refrigerante"])
            nome = st.text_input("Nome do Produto").upper()
            fardo = st.number_input("Unidades por Engradado/Fardo", value=24 if cat == "Romarinho" else 12)
            custo = st.number_input("Custo Unitário", format="%.2f")
            venda = st.number_input("Venda Unitária", format="%.2f")
            if st.form_submit_button("Salvar"):
                df_e = pd.read_csv(DB_FILE)
                novo = pd.DataFrame([[cat, "GERAL", nome, 0, fardo, 1, 12, custo, venda]], columns=df_e.columns)
                pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                registrar_log(nome_logado, f"CADASTRO: Criou o produto {nome}")
                st.success("Cadastrado!")

    # --- DEMAIS ABAS ---
    elif menu == "🏗️ Mapa":
        st.title("🏗️ Mapa de Estoque")
        df_m = pd.read_csv(DB_FILE)
        for _, r in df_m.iterrows():
            st.write(f"📍 {r['Bebida']}: {int(r['Qtd'])} unidades")

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_f = pd.read_csv(DB_FILE)
        st.metric("💰 Total em Custo", f"R$ {(df_f['Qtd'] * df_f['Custo']).sum():,.2f}")
        st.metric("📈 Total em Venda", f"R$ {(df_f['Qtd'] * df_f['Venda']).sum():,.2f}")

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão da Equipe")
        with st.form("add"):
            u = st.text_input("Login").lower()
            n = st.text_input("Nome")
            s = st.text_input("Senha")
            a = st.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Usuário"):
                pd.DataFrame([[u, n, s, a]], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, mode='a', header=False, index=False)
                registrar_log(nome_logado, f"EQUIPE: Criou usuário {u}")
                st.success("Criado!")

elif st.session_state["authentication_status"] is False:
    st.error('Login ou Senha incorretos.')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, faça o login.')
