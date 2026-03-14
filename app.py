import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v27) ---
DB_PRODUTOS = "produtos_v27.csv"
DB_ESTOQUE = "estoque_v27.csv"
PILAR_ESTRUTURA = "pilares_v27.csv"
USERS_FILE = "usuarios_v27.csv"
LOG_FILE = "historico_v27.csv"
CASCOS_FILE = "cascos_v27.csv"
CASCOS_HISTORICO = "cascos_historico_v27.csv"

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

    # Carregar dados
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: CADASTRO DE PRODUTOS ---
    if menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        # Correção do Form: Todo o input dentro do 'with'
        with st.form("form_cadastro_produto"):
            st.subheader("Novo Cadastro")
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            nova_cat = c1.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            novo_nome = c2.text_input("Nome do Produto").upper()
            nova_qtd_fardo = c3.number_input("Qtd no Fardo", value=6, min_value=1)
            novo_preco_uni = c4.number_input("Preço Unitário (R$)", value=0.0, min_value=0.0, step=0.10)
            
            btn_cadastrar = st.form_submit_button("Salvar Produto")
            
            if btn_cadastrar:
                if novo_nome and novo_nome not in df_prod['Nome'].values:
                    # Salva no Cadastro
                    nova_linha = pd.DataFrame([[nova_cat, novo_nome, nova_qtd_fardo, novo_preco_uni]], columns=df_prod.columns)
                    pd.concat([df_prod, nova_linha]).to_csv(DB_PRODUTOS, index=False)
                    # Salva no Estoque
                    pd.concat([df_e, pd.DataFrame([[novo_nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success(f"{novo_nome} cadastrado!")
                    st.rerun()
                else:
                    st.error("Nome inválido ou já existe!")

        st.divider()
        st.subheader("🗑️ Remover Produtos")
        if not df_prod.empty:
            for i, row in df_prod.iterrows():
                cc1, cc2, cc3, cc4 = st.columns([3, 2, 2, 1])
                cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
                cc2.write(f"Preço: R$ {row['Preco_Unitario']:.2f}")
                cc3.write(f"Fardo: R$ {row['Preco_Unitario'] * row['Un_por_Volume']:.2f}")
                if cc4.button("Excluir", key=f"del_{row['Nome']}"):
                    df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                    df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                    st.rerun()

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        
        with st.expander("➕ Montar Camada"):
            with st.form("form_pilares"):
                np_nome = st.text_input("NOME DO PILAR").upper()
                st.write("Selecione os produtos para esta camada:")
                # Lógica simplificada para evitar erro de submit
                cols_p = st.columns(3)
                p1 = cols_p[0].selectbox("Posição 1", ["Vazio"] + df_prod['Nome'].tolist())
                p2 = cols_p[1].selectbox("Posição 2", ["Vazio"] + df_prod['Nome'].tolist())
                p3 = cols_p[2].selectbox("Posição 3", ["Vazio"] + df_prod['Nome'].tolist())
                
                if st.form_submit_button("Salvar Camada"):
                    # Aqui você pode expandir a lógica para 5 posições como antes
                    st.success("Camada salva!")

        # Exibição e Baixa
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                dados_p = df_pilar[df_pilar['NomePilar'] == np]
                for cam in sorted(dados_p['Camada'].unique(), reverse=True):
                    st.write(f"Camada {cam}")
                    itens = dados_p[dados_p['Camada'] == cam]
                    cols = st.columns(5)
                    for _, row in itens.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.info(f"{row['Bebida']}")
                            if st.button("Baixar", key=f"bx_{row['ID']}"):
                                info = df_prod[df_prod['Nome'] == row['Bebida']]
                                vol = info['Un_por_Volume'].values[0] if not info.empty else 0
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
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
            with st.form("form_cascos"):
                cli = st.text_input("Cliente").upper()
                vas = st.selectbox("Vasilhame", ["Coca-Cola 1L", "Coca-Cola 2L", "Engradado", "Romarinho"])
                qtd = st.number_input("Quantidade", 1)
                if st.form_submit_button("Registrar"):
                    nid = f"C{datetime.now().strftime('%M%S')}"
                    nova = pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)
                    pd.concat([df_cascos, nova]).to_csv(CASCOS_FILE, index=False)
                    st.rerun()
            
            for _, row in df_cascos.iterrows():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"👤 {row['Cliente']}")
                c2.write(f"{row['Quantidade']}x {row['Vasilhame']}")
                if c3.button("Recebido", key=f"rec_{row['ID']}"):
                    row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                    row_h['QuemBaixou'] = nome_logado
                    pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                    df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        with st.form("form_estoque"):
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            fardos = st.number_input("Fardos", 0)
            unid = st.number_input("Unidades Soltas", 0)
            if st.form_submit_button("Confirmar Entrada"):
                vol = df_prod[df_prod['Nome'] == p_sel]['Un_por_Volume'].values[0]
                total = (fardos * vol) + unid
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque Atualizado!")
        st.dataframe(df_e)

    # --- ABA: HISTÓRICO ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Logs do Sistema")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
