import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v25) ---
DB_PRODUTOS = "produtos_v25.csv"
DB_ESTOQUE = "estoque_v25.csv"
PILAR_ESTRUTURA = "pilares_v25.csv"
USERS_FILE = "usuarios_v25.csv"
LOG_FILE = "historico_v25.csv"
CASCOS_FILE = "cascos_v25.csv"
CASCOS_HISTORICO = "cascos_historico_v25.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        CASCOS_HISTORICO: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

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
    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("➕ Montar Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)
                
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                escolhas, av_in = {}, {}
                cols = st.columns(max(n_atras, n_frente))
                st.write(f"**Camada {cam_atual}**")
                for i in range(n_atras + n_frente):
                    pos = i + 1
                    with cols[i % 5]:
                        escolhas[pos] = st.selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}{nome_p}")
                        av_in[pos] = st.number_input(f"Avulsos {pos}", 0, key=f"a{pos}{cam_atual}{nome_p}")

                if st.button("💾 Salvar Camada"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, b, av_in[p]] for p, b in escolhas.items() if b != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;">{row["Bebida"]}<br>{row["Avulsos"]} Av</div>', unsafe_allow_html=True)
                            if st.button("Fardo", key=f"r{row['ID']}"):
                                vol = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Baixa: {row['Bebida']}")
                                st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        df_hist_cascos = pd.read_csv(CASCOS_HISTORICO)
        tab1, tab2 = st.tabs(["🔴 Pendências", "📜 Histórico"])
        with tab1:
            with st.form("fc"):
                cli = st.text_input("NOME DO CLIENTE").upper()
                tipo = st.selectbox("VASILHAME", ["Coca-Cola 1L Retornável", "Coca-Cola 2L Retornável", "Engradado Completo", "Litrinho (Romarinho) Avulso"])
                qtd = st.number_input("QTD", 1)
                if st.form_submit_button("Lançar"):
                    nid = f"C{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y %H:%M"), cli, tipo, qtd, "DEVE CASCO", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                    st.rerun()
            for _, row in df_cascos.iterrows():
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                c2.write(f"**{row['Cliente']}**")
                c3.write(f"{row['Quantidade']}x {row['Vasilhame']}")
                if c4.button("Devolveu", key=f"d{row['ID']}"):
                    row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                    row_h['QuemBaixou'] = nome_logado
                    pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                    df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: CADASTRO DE PRODUTOS (COM OPÇÃO DE REMOVER) ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        with st.form("cad_p"):
            st.subheader("Novo Cadastro")
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = c2.text_input("Nome do Produto").upper()
            v_un = c3.number_input("Un/Fardo", 6)
            if st.form_submit_button("Cadastrar"):
                if nome and nome not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, v_un, 0, 0]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success("Cadastrado!")
                    st.rerun()

        st.divider()
        st.subheader("🗑️ Remover ou Editar Produtos")
        if not df_prod.empty:
            for i, row in df_prod.iterrows():
                cc1, cc2, cc3, cc4 = st.columns([2, 3, 1, 1])
                cc1.write(f"[{row['Categoria']}]")
                cc2.write(f"**{row['Nome']}**")
                cc3.write(f"{row['Un_por_Volume']} un")
                if cc4.button("Excluir", key=f"del_p_{row['Nome']}"):
                    # Remove do cadastro e do estoque
                    df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                    df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Removeu produto: {row['Nome']}")
                    st.warning(f"Produto {row['Nome']} removido!")
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        with st.form("ent"):
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            f, s = st.columns(2)
            qf = f.number_input("Fardos", 0); qs = s.number_input("Soltas", 0)
            if st.form_submit_button("Lançar"):
                vol = df_prod[df_prod['Nome'] == p_sel]['Un_por_Volume'].values[0]
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += (qf * vol) + qs
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        st.dataframe(df_e)

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        with st.form("eq"):
            u, n, s = st.columns(3)
            user_n = u.text_input("User"); nome_n = n.text_input("Nome"); pass_n = s.text_input("Senha")
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[user_n, nome_n, pass_n, "NÃO"]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
