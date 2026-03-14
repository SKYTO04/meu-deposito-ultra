import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v38) ---
DB_PRODUTOS = "produtos_v38.csv"
DB_ESTOQUE = "estoque_v38.csv"
PILAR_ESTRUTURA = "pilares_v38.csv"
USERS_FILE = "usuarios_v38.csv"
LOG_FILE = "historico_v38.csv"
CASCOS_FILE = "cascos_v38.csv"

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

# --- FUNÇÃO DE INTELIGÊNCIA POR CATEGORIA ---
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

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        # (Lógica de montagem mantida...)
        
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
                                    # MUDANÇA AQUI: NOME DINÂMICO (ENGRADADO OU FARDO)
                                    q_auto, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                    q_f = st.number_input(f"Unidades no {termo.lower()}?", value=q_auto)
                                    if st.form_submit_button("Confirmar Baixa"):
                                        total = q_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        registrar_log(nome_logado, f"Retirou {row['Bebida']} ({total}un)")
                                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (COM TERMO DINÂMICO) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            with st.form("ent_v38"):
                p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
                # BUSCA SE É ENGRADADO OU FARDO
                un_auto, termo = obter_dados_categoria(p_sel, df_prod)
                
                c1, c2 = st.columns(2)
                u_f = c1.number_input(f"Unidades por {termo.lower()}", value=un_auto)
                n_f = c1.number_input(f"Qtd de {termo}s", 0)
                n_s = c2.number_input("Unidades Soltas", 0)
                
                if st.form_submit_button("Confirmar Entrada"):
                    total = (n_f * u_f) + n_s
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Entrada: {total}un de {p_sel}")
                    st.success("Estoque Atualizado!")
                    st.rerun()
        st.dataframe(df_e)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad_p"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco = c3.number_input("Preço Unitário (R$)", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        
        st.subheader("Lista de Produtos")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1]) # LINHA CORRIGIDA
            cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
            cc2.write(f"R$ {row['Preco_Unitario']:.2f}")
            if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ABAS ADM (Financeiro, Histórico, Equipe, Cascos) ---
    # (Mantidas conforme as versões anteriores...)

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
