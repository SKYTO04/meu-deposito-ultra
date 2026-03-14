import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v28) ---
DB_PRODUTOS = "produtos_v28.csv"
DB_ESTOQUE = "estoque_v28.csv"
PILAR_ESTRUTURA = "pilares_v28.csv"
USERS_FILE = "usuarios_v28.csv"
LOG_FILE = "historico_v28.csv"
CASCOS_FILE = "cascos_v28.csv"
CASCOS_HISTORICO = "cascos_historico_v28.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
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

    # --- ABA: CADASTRO DE PRODUTOS (SIMPLIFICADO) ---
    if menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        with st.form("form_cadastro_v28"):
            st.subheader("Novo Cadastro")
            c1, c2, c3 = st.columns([2, 2, 1])
            nova_cat = c1.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck", "Outros"])
            novo_nome = c2.text_input("Nome do Produto").upper()
            novo_preco_uni = c3.number_input("Preço Unitário (R$)", value=0.0, min_value=0.0, step=0.50)
            
            btn_salvar = st.form_submit_button("Salvar Produto")
            
            if btn_salvar:
                if novo_nome and novo_nome not in df_prod['Nome'].values:
                    nova_linha = pd.DataFrame([[nova_cat, novo_nome, novo_preco_uni]], columns=df_prod.columns)
                    pd.concat([df_prod, nova_linha]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[novo_nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success(f"{novo_nome} cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Nome inválido ou já existente.")

        st.divider()
        st.subheader("📋 Produtos Cadastrados")
        if not df_prod.empty:
            for i, row in df_prod.iterrows():
                cc1, cc2, cc3 = st.columns([4, 3, 1])
                cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
                cc2.write(f"Preço Unitário: **R$ {row['Preco_Unitario']:.2f}**")
                if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                    df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                    df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Excluiu: {row['Nome']}")
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    # --- ABA: ENTRADA DE ESTOQUE (ONDE VOCÊ DEFINE A QUANTIDADE) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            with st.form("form_entrada_estoque"):
                p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
                st.info("Dica: Se estiver entrando um fardo, coloque a quantidade total de unidades que vem nele.")
                qtd_entrada = st.number_input("Quantidade Total de Unidades que está entrando", value=0, min_value=0)
                
                if st.form_submit_button("Confirmar Entrada"):
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += qtd_entrada
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Entrada: {qtd_entrada} unidades de {p_sel}")
                    st.success(f"Estoque de {p_sel} atualizado!")
                    st.rerun()
        else:
            st.warning("Cadastre um produto primeiro!")
            
        st.subheader("Saldo Atual")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        # Visualização e Retirada
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                dados_p = df_pilar[df_pilar['NomePilar'] == np]
                for cam in sorted(dados_p['Camada'].unique(), reverse=True):
                    st.write(f"Camada {cam}")
                    itens = dados_p[dados_p['Camada'] == cam]
                    cols = st.columns(5)
                    for _, row in itens.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="text-align:center; border:1px solid #4CAF50; padding:5px; border-radius:5px;">{row["Bebida"]}<br><small>{row["Avulsos"]} Av</small></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"bx_{row['ID']}"):
                                # Aqui a baixa é de 1 fardo (considerando que o fardo sai inteiro do pilar)
                                # Se você não tem a "qtd no fardo" salva, o sistema vai perguntar ou usar um padrão
                                st.warning("Defina quantas unidades tem esse fardo para baixar:")
                                fardo_valor = st.number_input("Unidades no Fardo", value=12, key=f"val_{row['ID']}")
                                if st.button("Confirmar Baixa", key=f"conf_{row['ID']}"):
                                    total_sair = fardo_valor + row['Avulsos']
                                    df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_sair
                                    df_e.to_csv(DB_ESTOQUE, index=False)
                                    df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                    st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        df_hist_cascos = pd.read_csv(CASCOS_HISTORICO)
        tab1, tab2 = st.tabs(["🔴 Pendências", "📜 Histórico"])
        with tab1:
            with st.form("form_cascos_v28"):
                cli = st.text_input("Cliente").upper()
                vas = st.selectbox("Vasilhame", ["Coca-Cola 1L", "Coca-Cola 2L", "Engradado", "Litrinho"])
                qtd = st.number_input("Quantidade", 1)
                if st.form_submit_button("Lançar"):
                    nid = f"C{datetime.now().strftime('%M%S')}"
                    pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                    st.rerun()
            for _, row in df_cascos.iterrows():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"👤 {row['Cliente']}")
                c2.write(f"{row['Quantidade']}x {row['Vasilhame']}")
                if c3.button("Devolveu", key=f"dev_{row['ID']}"):
                    row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                    row_h['QuemBaixou'] = nome_logado
                    pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                    df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: HISTÓRICO ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Logs")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
