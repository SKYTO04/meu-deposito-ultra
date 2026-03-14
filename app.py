import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v20) ---
DB_PRODUTOS = "produtos_v20.csv"
DB_ESTOQUE = "estoque_v20.csv"
PILAR_ESTRUTURA = "pilares_v20.csv"
USERS_FILE = "usuarios_v20.csv"
LOG_FILE = "historico_v20.csv"
CASCOS_FILE = "cascos_v20.csv"
CASCOS_BACKUP = "cascos_backup_v20.csv" # Arquivo para o "Desfazer"

def init_files():
    for f in [USERS_FILE, DB_PRODUTOS, DB_ESTOQUE, PILAR_ESTRUTURA, LOG_FILE, CASCOS_FILE, CASCOS_BACKUP]:
        if not os.path.exists(f):
            if f == USERS_FILE:
                pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(f, index=False)
            elif f == CASCOS_FILE or f == CASCOS_BACKUP:
                pd.DataFrame(columns=['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status']).to_csv(f, index=False)
            elif f == DB_PRODUTOS:
                pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(f, index=False)
            elif f == DB_ESTOQUE:
                pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(f, index=False)
            elif f == PILAR_ESTRUTURA:
                pd.DataFrame(columns=['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos']).to_csv(f, index=False)
            elif f == LOG_FILE:
                pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(f, index=False)

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
    sou_admin = df_users[df_users['user'] == st.session_state["username"]]['is_admin'].values[0] == 'SIM'

    st.sidebar.title(f"👤 {nome_logado}")
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Produto", "🍶 Cascos", "📜 Histórico (Adm)", "👥 Equipe"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CASCOS (COM FUNÇÃO REMOVER E DESFAZER) ---
    if menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        
        col_f1, col_f2 = st.columns([2, 1])
        
        with col_f1:
            with st.form("form_cascos", clear_on_submit=True):
                st.subheader("Registrar Movimentação")
                c1, c2, c3 = st.columns([2, 2, 1])
                cliente = c1.text_input("Nome do Cliente").upper()
                tipo_v = c2.selectbox("Vasilhame", ["Coca-Cola 1L Retornável", "Coca-Cola 2L Retornável", "Engradado Completo", "Litrinho (Romarinho) Avulso"])
                qtd_v = c3.number_input("Qtd", 1, step=1)
                status_v = st.radio("Situação:", ["Cliente DEVE", "Cliente DEIXOU / PAGO"], horizontal=True)
                
                if st.form_submit_button("Lançar"):
                    c_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    nova_linha = pd.DataFrame([[c_id, datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, tipo_v, qtd_v, status_v]], columns=df_cascos.columns)
                    pd.concat([df_cascos, nova_linha]).to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"Casco: {status_v} {qtd_v}x {tipo_v} ({cliente})")
                    st.rerun()

        with col_f2:
            st.subheader("Recuperação")
            if st.button("⏪ Desfazer Última Exclusão"):
                df_bkp = pd.read_csv(CASCOS_BACKUP)
                if not df_bkp.empty:
                    pd.concat([df_cascos, df_bkp]).drop_duplicates(subset=['ID']).to_csv(CASCOS_FILE, index=False)
                    pd.DataFrame(columns=df_cascos.columns).to_csv(CASCOS_BACKUP, index=False)
                    st.success("Registro recuperado!")
                    st.rerun()
                else:
                    st.warning("Nada para desfazer.")

        st.divider()
        st.subheader("📋 Pendências Atuais")
        if not df_cascos.empty:
            for i, row in df_cascos.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 1])
                c1.text(row['Data'])
                c2.warning(f"👤 {row['Cliente']}")
                c3.info(f"{row['Quantidade']}x {row['Vasilhame']}")
                c4.write(f"**{row['Status']}**")
                if c5.button("Baixar", key=f"del_c_{row['ID']}"):
                    # Salva no backup antes de deletar
                    df_cascos[df_cascos['ID'] == row['ID']].to_csv(CASCOS_BACKUP, index=False)
                    # Deleta
                    df_novo = df_cascos[df_cascos['ID'] != row['ID']]
                    df_novo.to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"Removeu registro de casco: {row['Cliente']}")
                    st.rerun()
        else:
            st.info("Nenhuma pendência.")

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        with st.expander("➕ Montar Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                if cam_atual == 1:
                    st.session_state[f"layout_{nome_p}"] = st.radio("Início:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)
                
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

                if st.button("💾 Salvar"):
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            f_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%M%S')}"
                            novos.append([f_id, nome_p, cam_atual, pos, beb, av_in[pos]])
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

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
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><b>{row["Bebida"]}</b><br>{row["Avulsos"]} Av</div>', unsafe_allow_html=True)
                            if st.button("Fardo", key=f"r{row['ID']}"):
                                vol = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        with st.form("ent"):
            b = st.selectbox("Produto", df_prod['Nome'].unique())
            v_un = df_prod[df_prod['Nome'] == b]['Un_por_Volume'].values[0]
            f, s = st.columns(2)
            q_f = f.number_input("Adicionar Fardos", 0)
            q_s = s.number_input("Adicionar Soltas", 0)
            if st.form_submit_button("Lançar"):
                total = (q_f * v_un) + q_s
                df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque Atualizado!")
        st.dataframe(df_e)

    # --- ABA: CADASTRAR PRODUTO ---
    elif menu == "✨ Cadastrar Produto":
        st.title("✨ Cadastro")
        df_prod = pd.read_csv(DB_PRODUTOS)
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            if st.form_submit_button("Salvar"):
                if nome in df_prod['Nome'].values:
                    st.warning("Já existe!")
                else:
                    vol = 24 if cat == "Romarinho" else (12 if cat == "Cerveja Lata" else 6)
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, vol, 0, 0]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    df_e_temp = pd.read_csv(DB_ESTOQUE)
                    pd.concat([df_e_temp, pd.DataFrame([[nome, 0]], columns=['Nome', 'Estoque_Total_Un'])]).to_csv(DB_ESTOQUE, index=False)
                    st.success("Criado!")

    # --- ABA: EQUIPE ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Login")
        with st.form("equipe"):
            n_u = st.text_input("Novo Usuário")
            n_s = st.text_input("Senha")
            n_a = st.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                novo = pd.DataFrame([[n_u, n_u, n_s, n_a]], columns=df_users.columns)
                pd.concat([df_users, novo]).to_csv(USERS_FILE, index=False)
                st.success("Acesso criado!")

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
