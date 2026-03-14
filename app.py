import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v26) ---
DB_PRODUTOS = "produtos_v26.csv"
DB_ESTOQUE = "estoque_v26.csv"
PILAR_ESTRUTURA = "pilares_v26.csv"
USERS_FILE = "usuarios_v26.csv"
LOG_FILE = "historico_v26.csv"
CASCOS_FILE = "cascos_v26.csv"
CASCOS_HISTORICO = "cascos_historico_v26.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Un_por_Volume', 'Preco_Unitario'],
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
        opcoes_menu += ["📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: CADASTRO DE PRODUTOS (COM PREÇO UNITÁRIO E REMOVER) ---
    if menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        with st.form("cad_p"):
            st.subheader("Novo Cadastro")
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            cat = c1.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = c2.text_input("Nome do Produto").upper()
            v_un = c3.number_input("Qtd no Fardo", 6, min_value=1)
            preco = c4.number_input("Preço Unitário (R$)", 0.0, format="%.2f")
            
            if st.form_submit_button("Cadastrar Produto"):
                if nome and nome not in df_prod['Nome'].values:
                    nova_linha = pd.DataFrame([[cat, nome, v_un, preco]], columns=df_prod.columns)
                    pd.concat([df_prod, nova_linha]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success(f"{nome} cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Nome inválido ou já existente.")

        st.divider()
        st.subheader("📋 Produtos Cadastrados")
        if not df_prod.empty:
            for i, row in df_prod.iterrows():
                cc1, cc2, cc3, cc4, cc5 = st.columns([2, 2, 1, 1, 1])
                cc1.write(f"**{row['Nome']}**")
                cc2.write(f"Unitário: R$ {row['Preco_Unitario']:.2f}")
                valor_fardo = row['Preco_Unitario'] * row['Un_por_Volume']
                cc3.write(f"Fardo ({row['Un_por_Volume']}un):")
                cc4.write(f"R$ {valor_fardo:.2f}")
                if cc5.button("Excluir", key=f"del_p_{row['Nome']}"):
                    df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                    df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Removeu produto: {row['Nome']}")
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    # --- ABA: GESTÃO DE PILARES (COM PREÇOS) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        # Visualização simplificada para focar na lógica de pilar solicitada
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            info_p = df_prod[df_prod['Nome'] == row['Bebida']]
                            preco_exibir = f"R$ {info_p['Preco_Unitario'].values[0]:.2f}" if not info_p.empty else "S/P"
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><b>{row["Bebida"]}</b><br>{preco_exibir}<br><small>{row["Avulsos"]} Av</small></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                vol = info_p['Un_por_Volume'].values[0]
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Venda: {row['Bebida']}")
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
                r1, r2, r3, r4 = st.columns([1, 2, 2, 1])
                r2.write(f"👤 **{row['Cliente']}**")
                r3.write(f"{row['Quantidade']}x {row['Vasilhame']}")
                if r4.button("Devolveu", key=f"d{row['ID']}"):
                    row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                    row_h['QuemBaixou'] = nome_logado
                    pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                    df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        with st.form("ent"):
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            f, s = st.columns(2)
            qf = f.number_input("Fardos", 0); qs = s.number_input("Soltas", 0)
            if st.form_submit_button("Lançar Entrada"):
                vol = df_prod[df_prod['Nome'] == p_sel]['Un_por_Volume'].values[0]
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += (qf * vol) + qs
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque atualizado!")
        st.dataframe(df_e, use_container_width=True)

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
