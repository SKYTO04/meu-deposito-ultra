import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v40) ---
DB_PRODUTOS = "produtos_v40.csv"
DB_ESTOQUE = "estoque_v40.csv"
PILAR_ESTRUTURA = "pilares_v40.csv"
USERS_FILE = "usuarios_v40.csv"
LOG_FILE = "historico_v40.csv"
CASCOS_FILE = "cascos_v40.csv"

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

# --- FUNÇÃO DE INTELIGÊNCIA (FORA DO FORMULÁRIO PARA SER DINÂMICA) ---
def obter_dados_categoria(nome_produto, df_produtos):
    if df_produtos.empty:
        return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

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

    # --- ABA: ENTRADA DE ESTOQUE (DINÂMICA) ---
    if menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        
        if not df_prod.empty:
            # SELETOR FORA DO FORMULÁRIO PARA ATUALIZAR NA HORA
            p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
            
            # Obtém os dados assim que o produto muda
            un_auto, termo = obter_dados_categoria(p_sel, df_prod)
            
            # Mostra a categoria atual apenas para conferência
            cat_atual = df_prod[df_prod['Nome'] == p_sel]['Categoria'].values[0]
            st.info(f"Categoria: **{cat_atual}** | Unidades padrão: **{un_auto}**")

            with st.form("form_entrada"):
                c1, c2 = st.columns(2)
                u_f = c1.number_input(f"Unidades por {termo.lower()}", value=un_auto)
                n_f = c1.number_input(f"Quantidade de {termo}s", 0)
                n_s = c2.number_input("Unidades Soltas (Avulsas)", 0)
                
                if st.form_submit_button("Confirmar Entrada"):
                    total = (n_f * u_f) + n_s
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success(f"Entrada de {total} unidades realizada!")
                    st.rerun()
        else:
            st.warning("Cadastre produtos primeiro.")
        st.dataframe(df_e)

    # --- ABA: GESTÃO DE PILARES (DINÂMICA) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;">{row["Bebida"]}</div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                st.session_state[f"ask_{row['ID']}"] = True
                            
                            if st.session_state.get(f"ask_{row['ID']}", False):
                                # Identifica os dados da categoria do produto do pilar
                                q_auto, termo_pilar = obter_dados_categoria(row['Bebida'], df_prod)
                                with st.form(f"baixa_{row['ID']}"):
                                    q_f = st.number_input(f"Unidades no {termo_pilar.lower()}?", value=q_auto)
                                    if st.form_submit_button("Confirmar"):
                                        total = q_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        st.session_state[f"ask_{row['ID']}"] = False
                                        st.rerun()

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad_p"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco = c3.number_input("Preço Unitário", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.rerun()

    # ... (Demais abas Financeiro, Equipe, etc, mantidas)

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
