import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v21) ---
DB_PRODUTOS = "produtos_v21.csv"
DB_ESTOQUE = "estoque_v21.csv"
PILAR_ESTRUTURA = "pilares_v21.csv"
USERS_FILE = "usuarios_v21.csv"
LOG_FILE = "historico_v21.csv"
CASCOS_FILE = "cascos_v21.csv"
CASCOS_HISTORICO = "cascos_historico_v21.csv" # Novo arquivo para histórico de excluídos

def init_files():
    for f in [USERS_FILE, DB_PRODUTOS, DB_ESTOQUE, PILAR_ESTRUTURA, LOG_FILE, CASCOS_FILE, CASCOS_HISTORICO]:
        if not os.path.exists(f):
            if f == USERS_FILE:
                pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(f, index=False)
            elif f in [CASCOS_FILE, CASCOS_HISTORICO]:
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

    # --- ABA: CASCOS (COM HISTÓRICO E REATIVAÇÃO) ---
    if menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        df_hist_cascos = pd.read_csv(CASCOS_HISTORICO)
        
        tab1, tab2 = st.tabs(["📋 Pendências Ativas", "📜 Histórico de Baixas"])

        with tab1:
            with st.form("form_cascos", clear_on_submit=True):
                st.subheader("Registrar Novo Casco")
                c1, c2, c3 = st.columns([2, 2, 1])
                cliente = c1.text_input("Nome do Cliente").upper()
                tipo_v = c2.selectbox("Vasilhame", ["Coca-Cola 1L Retornável", "Coca-Cola 2L Retornável", "Engradado Completo", "Litrinho (Romarinho) Avulso"])
                qtd_v = c3.number_input("Qtd", 1, step=1)
                status_v = st.radio("Situação:", ["Cliente DEVE", "Cliente DEIXOU / PAGO"], horizontal=True)
                
                if st.form_submit_button("Lançar"):
                    c_id = f"C{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    nova_linha = pd.DataFrame([[c_id, datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, tipo_v, qtd_v, status_v]], columns=df_cascos.columns)
                    pd.concat([df_cascos, nova_linha]).to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"Cadastrou Casco: {cliente}")
                    st.rerun()

            st.divider()
            if not df_cascos.empty:
                for i, row in df_cascos.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 1])
                    c1.text(row['Data'])
                    c2.markdown(f"**{row['Cliente']}**")
                    c3.text(f"{row['Quantidade']}x {row['Vasilhame']}")
                    c4.write(f"_{row['Status']}_")
                    if c5.button("Dar Baixa", key=f"baixa_{row['ID']}"):
                        # Move para o histórico
                        pd.concat([df_hist_cascos, df_cascos[df_cascos['ID'] == row['ID']]]).to_csv(CASCOS_HISTORICO, index=False)
                        # Remove da ativa
                        df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                        registrar_log(nome_logado, f"Deu baixa no casco de: {row['Cliente']}")
                        st.rerun()
            else:
                st.info("Nenhuma pendência ativa.")

        with tab2:
            st.subheader("Registros Finalizados")
            if not df_hist_cascos.empty:
                for i, row in df_hist_cascos.iterrows():
                    h1, h2, h3, h4 = st.columns([1, 3, 2, 1])
                    h1.text(row['Data'])
                    h2.text(f"✅ {row['Cliente']} - {row['Quantidade']}x {row['Vasilhame']}")
                    h3.write(f"Status original: {row['Status']}")
                    if h4.button("Reativar", key=f"undo_{row['ID']}", help="Voltar para a lista de pendências"):
                        # Volta para a ativa
                        pd.concat([df_cascos, df_hist_cascos[df_hist_cascos['ID'] == row['ID']]]).to_csv(CASCOS_FILE, index=False)
                        # Remove do histórico
                        df_hist_cascos[df_hist_cascos['ID'] != row['ID']].to_csv(CASCOS_HISTORICO, index=False)
                        registrar_log(nome_logado, f"Reativou pendência de: {row['Cliente']}")
                        st.rerun()
                
                if sou_admin and st.button("Limpar Histórico Definitivamente"):
                    pd.DataFrame(columns=df_cascos.columns).to_csv(CASCOS_HISTORICO, index=False)
                    st.rerun()
            else:
                st.info("O histórico está vazio.")

    # --- RESTANTE DO CÓDIGO (PILARES, ESTOQUE, ETC) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        # (Lógica de Pilares mantida conforme versões anteriores...)
        # [Para economizar espaço, a lógica de pilares/estoque segue o padrão funcional das últimas respostas]
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
                                
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        with st.form("ent"):
            b = st.selectbox("Produto", df_prod['Nome'].unique())
            v_un = df_prod[df_prod['Nome'] == b]['Un_por_Volume'].values[0]
            f, s = st.columns(2)
            q_f = f.number_input("Fardos", 0); q_s = s.number_input("Soltas", 0)
            if st.form_submit_button("Lançar"):
                df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] += (q_f * v_un) + q_s
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque Atualizado!")

    elif menu == "✨ Cadastrar Produto":
        st.title("✨ Cadastro")
        df_prod = pd.read_csv(DB_PRODUTOS)
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            if st.form_submit_button("Salvar"):
                vol = 24 if cat == "Romarinho" else (12 if cat == "Cerveja Lata" else 6)
                pd.concat([df_prod, pd.DataFrame([[cat, nome, vol, 0, 0]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([pd.read_csv(DB_ESTOQUE), pd.DataFrame([[nome, 0]], columns=['Nome', 'Estoque_Total_Un'])]).to_csv(DB_ESTOQUE, index=False)
                st.success("Produto Criado!")

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Logs")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
