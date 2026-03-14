import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v36) ---
DB_PRODUTOS = "produtos_v36.csv"
DB_ESTOQUE = "estoque_v36.csv"
PILAR_ESTRUTURA = "pilares_v36.csv"
USERS_FILE = "usuarios_v36.csv"
LOG_FILE = "historico_v36.csv"
CASCOS_FILE = "cascos_v36.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- FUNÇÃO DE AUTOMAÇÃO DE UNIDADES ---
def obter_unidades_por_categoria(nome_produto, df_produtos):
    if df_produtos.empty:
        return 12
    # Busca a categoria do produto selecionado
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24
        if cat == "Long Neck": return 24
        if cat == "Cerveja Lata": return 12
        if cat == "Refrigerante": return 6
    return 12 # Padrão para outros

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
        opcoes_menu += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        
        with st.expander("➕ Montar Nova Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Lógica de Inversão (3/2 ou 2/3)
                inverter = (cam_atual % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                escolhas, av_in = {}, {}
                
                c_atras, c_frente = st.columns(2)
                with c_atras:
                    st.write("--- ATRÁS ---")
                    for i in range(n_atras):
                        pos = i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")
                with c_frente:
                    st.write("--- FRENTE ---")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, beb, av_in[p]] for p, beb in escolhas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"Montou Camada {cam_atual} no {nome_p}")
                        st.rerun()

        # Visualização e Baixa
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><small>{row["Bebida"]}</small><br><b style="color:#FFD700;">+{row["Avulsos"]} Av</b></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                st.session_state[f"ask_{row['ID']}"] = True
                            
                            if st.session_state.get(f"ask_{row['ID']}", False):
                                with st.form(f"f{row['ID']}"):
                                    # AUTOMAÇÃO NA SAÍDA
                                    qtd_auto = obter_unidades_por_categoria(row['Bebida'], df_prod)
                                    q_f = st.number_input("Unidades no fardo?", value=qtd_auto)
                                    if st.form_submit_button("Confirmar"):
                                        total = q_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        registrar_log(nome_logado, f"Retirou {row['Bebida']} ({total}un)")
                                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (COM AUTOMAÇÃO) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            with st.form("ent_v36"):
                p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
                # AUTOMAÇÃO NA ENTRADA
                un_auto = obter_unidades_por_categoria(p_sel, df_prod)
                
                c1, c2 = st.columns(2)
                u_f = c1.number_input("Unidades por fardo", value=un_auto)
                n_f = c1.number_input("Quantidade de Fardos", 0)
                n_s = c2.number_input("Unidades Soltas (Avulsas)", 0)
                
                if st.form_submit_button("Confirmar Entrada"):
                    total = (n_f * u_f) + n_s
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Entrada: {total}un de {p_sel}")
                    st.success(f"Estoque de {p_sel} atualizado!")
                    st.rerun()
        else:
            st.warning("Cadastre produtos primeiro.")
        st.subheader("Estoque Geral")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad_p"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco = c3.number_input("Preço Unitário (R$)", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome and nome not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Cadastrou: {nome}")
                    st.rerun()
        
        st.subheader("Lista de Produtos")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1
