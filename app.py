import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_v17.csv"
DB_ESTOQUE = "estoque_v17.csv"
PILAR_ESTRUTURA = "pilares_v17.csv"
USERS_FILE = "usuarios_v17.csv"
LOG_FILE = "historico_v17.csv"
CASCOS_FILE = "cascos_v17.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        # Usuário mestre inicial
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos']).to_csv(PILAR_ESTRUTURA, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Tipo', 'Qtd', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 3. AUTENTICAÇÃO ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials, 'pacaembu_cookie', 'auth_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_logado = st.session_state["username"]
    sou_admin = df_users[df_users['user'] == user_logado]['is_admin'].values[0] == 'SIM'

    st.sidebar.title(f"👤 {nome_logado}")
    
    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Produto", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    # --- CARREGAR DADOS ---
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- 1. GESTÃO DE PILARES (Código Anterior Preservado) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares e Vendas")
        with st.expander("➕ Nova Camada / Novo Pilar"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                if cam_atual == 1:
                    st.session_state[f"layout_{nome_p}"] = st.radio("Início:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)
                
                st.subheader(f"Camada {cam_atual}")
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                n_atras = 3 if not inverter else 2
                n_frente = 2 if not inverter else 3
                
                escolhas, av_in = {}, {}
                st.write("**ATRÁS**")
                cols_a = st.columns(n_atras)
                for i in range(n_atras):
                    pos = i + 1
                    escolhas[pos] = cols_a[i].selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}")
                    av_in[pos] = cols_a[i].number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")
                st.write("**FRENTE**")
                cols_f = st.columns(n_frente)
                for i in range(n_frente):
                    pos = n_atras + i + 1
                    escolhas[pos] = cols_f[i].selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}")
                    av_in[pos] = cols_f[i].number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            f_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            novos.append([f_id, nome_p, cam_atual, pos, beb, av_in[pos]])
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        # Visualização de Pilares
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        p = int(row['Posicao'])
                        with cols[p-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:8px; text-align:center;"><small>{row["Bebida"]}</small><br><b>{row["Avulsos"]} Av</b></div>', unsafe_allow_html=True)
                            if st.button("Fardo", key=f"r{row['ID']}"):
                                vol = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                st.rerun()

    # --- 2. ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        with st.form("entrada"):
            bebida_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            v_un = df_prod[df_prod['Nome'] == bebida_sel]['Un_por_Volume'].values[0]
            f, s = st.columns(2)
            q_f = f.number_input("Fardos", 0)
            q_s = s.number_input("Soltas", 0)
            if st.form_submit_button("Confirmar"):
                total = (q_f * v_un) + q_s
                df_e.loc[df_e['Nome'] == bebida_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque Atualizado!")

    # --- 3. CADASTRAR PRODUTO ---
    elif menu == "✨ Cadastrar Produto":
        st.title("✨ Cadastro")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            if st.form_submit_button("Gravar"):
                vol = 24 if cat == "Romarinho" else (12 if cat == "Cerveja Lata" else 6)
                pd.concat([df_prod, pd.DataFrame([[cat, nome, vol, 0, 0]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.success("Criado!")

    # --- 7. EQUIPE (CADASTRO DE NOVOS LOGINS) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        
        st.subheader("➕ Cadastrar Novo Funcionário")
        with st.form("novo_usuario"):
            new_nome = st.text_input("Nome Completo")
            new_user = st.text_input("Usuário (Login)")
            new_pass = st.text_input("Senha", type="password")
            new_admin = st.selectbox("É Administrador?", ["NÃO", "SIM"])
            
            if st.form_submit_button("Criar Acesso"):
                if new_user in df_users['user'].values:
                    st.error("Este login já existe!")
                elif new_user == "" or new_pass == "":
                    st.error("Preencha login e senha!")
                else:
                    novo_u = pd.DataFrame([[new_user, new_nome, new_pass, new_admin]], columns=df_users.columns)
                    pd.concat([df_users, novo_u]).to_csv(USERS_FILE, index=False)
                    st.success(f"Usuário {new_user} criado com sucesso!")
                    st.rerun()

        st.divider()
        st.subheader("Colaboradores Atuais")
        st.dataframe(df_users[['nome', 'user', 'is_admin']], use_container_width=True)

    # --- HISTÓRICO E FINANCEIRO (Preservados) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Financeiro")
        st.metric("Total em Estoque", f"R$ { (pd.merge(df_e, df_prod, on='Nome')['Estoque_Total_Un'] * pd.merge(df_e, df_prod, on='Nome')['Custo']).sum() :.2f}")

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
