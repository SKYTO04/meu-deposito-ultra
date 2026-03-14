import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v29) ---
DB_PRODUTOS = "produtos_v29.csv"
DB_ESTOQUE = "estoque_v29.csv"
PILAR_ESTRUTURA = "pilares_v29.csv"
USERS_FILE = "usuarios_v29.csv"
LOG_FILE = "historico_v29.csv"
CASCOS_FILE = "cascos_v29.csv"
CASCOS_HISTORICO = "cascos_historico_v29.csv"

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

    # --- ABA: CADASTRO DE PRODUTOS ---
    if menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        with st.form("form_cad_v29"):
            st.subheader("Novo Cadastro")
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco_un = c3.number_input("Preço Unitário (R$)", value=0.0, step=0.50)
            
            if st.form_submit_button("Salvar Produto"):
                if nome and nome not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco_un]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success(f"{nome} cadastrado!")
                    st.rerun()

        st.divider()
        st.subheader("📋 Produtos Cadastrados")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1])
            cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
            cc2.write(f"Preço Unitário: **R$ {row['Preco_Unitario']:.2f}**")
            if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        
        with st.expander("➕ Montar Nova Camada"):
            with st.form("montar_camada"):
                np_nome = st.text_input("NOME DO PILAR").upper()
                c1, c2, c3, c4, c5 = st.columns(5)
                escolhas = {}
                for i, col in enumerate([c1, c2, c3, c4, c5]):
                    escolhas[i+1] = col.selectbox(f"Pos {i+1}", ["Vazio"] + df_prod['Nome'].tolist(), key=f"p{i}")
                
                if st.form_submit_button("Confirmar Camada"):
                    if np_nome:
                        dados_p = df_pilar[df_pilar['NomePilar'] == np_nome]
                        cam_nova = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                        novos = []
                        for pos, beb in escolhas.items():
                            if beb != "Vazio":
                                nid = f"{np_nome}_{cam_nova}_{pos}_{datetime.now().strftime('%S')}"
                                novos.append([nid, np_nome, cam_nova, pos, beb, 0])
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        # Visualização Profissional
        for np in df_pilar['NomePilar'].unique():
            st.subheader(f"📍 {np}")
            dados_p = df_pilar[df_pilar['NomePilar'] == np]
            for cam in sorted(dados_p['Camada'].unique(), reverse=True):
                st.write(f"**Camada {cam}**")
                cols = st.columns(5)
                itens_cam = dados_p[dados_p['Camada'] == cam]
                for _, row in itens_cam.iterrows():
                    with cols[int(row['Posicao'])-1]:
                        # Pega o preço para exibir no card
                        p_info = df_prod[df_prod['Nome'] == row['Bebida']]
                        preco_card = p_info['Preco_Unitario'].values[0] if not p_info.empty else 0
                        
                        st.markdown(f"""
                        <div style="background-color:#1E1E1E; border:2px solid #4CAF50; padding:10px; border-radius:10px; text-align:center;">
                            <b style="color:white;">{row['Bebida']}</b><br>
                            <span style="color:#4CAF50;">R$ {preco_card:.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botão de baixa
                        if st.button("BAIXAR FARDO", key=f"bx_{row['ID']}"):
                            # Diálogo de confirmação de unidades (já que não salvamos no cadastro)
                            st.session_state[f"confirm_bx_{row['ID']}"] = True
                        
                        if st.session_state.get(f"confirm_bx_{row['ID']}", False):
                            qtd_fardo = st.number_input(f"Unidades no fardo de {row['Bebida']}?", value=12, key=f"q_{row['ID']}")
                            if st.button("Confirmar Saída", key=f"btn_c_{row['ID']}"):
                                total_sair = qtd_fardo + row['Avulsos']
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_sair
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Saída: {row['Bebida']} ({total_sair}un)")
                                st.session_state[f"confirm_bx_{row['ID']}"] = False
                                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("entrada"):
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            qtd = st.number_input("Total de Unidades entrando", min_value=1)
            if st.form_submit_button("Registrar Entrada"):
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success("Estoque Atualizado!")
                st.rerun()
        st.dataframe(df_e)

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        df_hist_cascos = pd.read_csv(CASCOS_HISTORICO)
        
        tab1, tab2 = st.tabs(["🔴 Pendências", "📜 Histórico"])
        with tab1:
            with st.form("casco_f"):
                cli = st.text_input("Cliente").upper()
                vas = st.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
                qtd = st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    nid = f"C{datetime.now().strftime('%M%S')}"
                    pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                    st.rerun()
            
            for _, row in df_cascos.iterrows():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"👤 **{row['Cliente']}**")
                c2.write(f"Deve: {row['Quantidade']}x {row['Vasilhame']}")
                if c3.button("Devolveu", key=f"dv_{row['ID']}"):
                    row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                    row_h['QuemBaixou'] = nome_logado
                    pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                    df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                    st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
