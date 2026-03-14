import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v42) ---
DB_PRODUTOS = "produtos_v42.csv"
DB_ESTOQUE = "estoque_v42.csv"
PILAR_ESTRUTURA = "pilares_v42.csv"
USERS_FILE = "usuarios_v42.csv"
LOG_FILE = "historico_v42.csv"
CASCOS_FILE = "cascos_v42.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        # Usuário padrão: admin | senha: 123
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, cols in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_files()

# --- FUNÇÃO DE AUTOMAÇÃO ---
def obter_dados_categoria(nome_produto, df_produtos):
    if df_produtos.empty: return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# --- 3. SISTEMA DE LOGIN CORRIGIDO ---
df_users = pd.read_csv(USERS_FILE)

# Criamos um formulário de login manual para evitar erros de criptografia com a equipe
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            # Verifica se o usuário e senha batem com o CSV (texto simples)
            user_check = df_users[(df_users['user'] == usuario_input) & (df_users['senha'].astype(str) == senha_input)]
            if not user_check.empty:
                st.session_state['autenticado'] = True
                st.session_state['username'] = usuario_input
                st.session_state['name'] = user_check['nome'].values[0]
                st.session_state['is_admin'] = user_check['is_admin'].values[0] == 'SIM'
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
else:
    # --- SISTEMA APÓS LOGIN ---
    nome_logado = st.session_state['name']
    user_logado = st.session_state['username']
    sou_admin = st.session_state['is_admin']

    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        # (Lógica de pilares mantida igual à v41...)
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.button(f"{row['Bebida']}\n+{row['Avulsos']} Av", key=f"btn_{row['ID']}")
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                st.session_state[f"ask_{row['ID']}"] = True
                            
                            if st.session_state.get(f"ask_{row['ID']}", False):
                                q_auto, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                with st.form(f"baixa_{row['ID']}"):
                                    q_f = st.number_input(f"Unidades no {termo.lower()}?", value=q_auto)
                                    if st.form_submit_button("Confirmar Baixa"):
                                        total = q_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        st.rerun()

    # --- ABA: EQUIPE (ADM) - ONDE VOCÊ CRIA OS ACESSOS ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Usuários")
        st.info("As senhas criadas aqui agora permitem o acesso imediato da equipe.")
        with st.form("add_user"):
            c1, c2, c3, c4 = st.columns(4)
            new_u = c1.text_input("Login (ex: joao)")
            new_n = c2.text_input("Nome (ex: João Silva)")
            new_s = c3.text_input("Senha")
            new_a = c4.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Usuário"):
                if new_u and new_s:
                    new_row = pd.DataFrame([[new_u, new_n, new_s, new_a]], columns=df_users.columns)
                    pd.concat([df_users, new_row]).to_csv(USERS_FILE, index=False)
                    st.success(f"Usuário {new_u} criado!")
                    st.rerun()

        st.subheader("Usuários Atuais")
        st.dataframe(df_users)

    # --- (As outras abas Entrada, Cadastro, Financeiro seguem a lógica da v41) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            un_auto, termo = obter_dados_categoria(p_sel, df_prod)
            with st.form("ent"):
                u_f = st.number_input(f"Unidades por {termo.lower()}", value=un_auto)
                n_f = st.number_input(f"Qtd de {termo}s", 0)
                if st.form_submit_button("Confirmar"):
                    total = n_f * u_f
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.dataframe(df_e)

    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad"):
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome").upper()
            prec = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                pd.concat([df_prod, pd.DataFrame([[cat, nome, prec]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        st.write(df_prod)
