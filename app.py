import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v30) ---
DB_PRODUTOS = "produtos_v30.csv"
DB_ESTOQUE = "estoque_v30.csv"
PILAR_ESTRUTURA = "pilares_v30.csv"
USERS_FILE = "usuarios_v30.csv"
LOG_FILE = "historico_v30.csv"
CASCOS_FILE = "cascos_v30.csv"
CASCOS_HISTORICO = "cascos_historico_v30.csv"

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
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"])
    authenticator.logout('Sair', 'sidebar')

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES (COM AVULSOS) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        
        with st.expander("➕ Montar Nova Camada"):
            with st.form("form_montar"):
                np_nome = st.text_input("NOME DO PILAR").upper()
                st.write("Selecione a Bebida e a Qtd de Avulsos em cada posição:")
                c = st.columns(5)
                escolhas = {}
                for i in range(5):
                    pos = i + 1
                    with c[i]:
                        beb = st.selectbox(f"Pos {pos}", ["Vazio"] + df_prod['Nome'].tolist(), key=f"beb_{pos}")
                        av = st.number_input(f"Avulsos P{pos}", 0, key=f"av_{pos}")
                        escolhas[pos] = {"beb": beb, "av": av}
                
                if st.form_submit_button("Salvar Camada"):
                    if np_nome:
                        dados_p = df_pilar[df_pilar['NomePilar'] == np_nome]
                        cam_nova = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                        novos = []
                        for p, dados in escolhas.items():
                            if dados['beb'] != "Vazio":
                                nid = f"{np_nome}_{cam_nova}_{p}_{datetime.now().strftime('%S')}"
                                novos.append([nid, np_nome, cam_nova, p, dados['beb'], dados['av']])
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        # Visualização e Baixa
        for np in df_pilar['NomePilar'].unique():
            st.subheader(f"📍 {np}")
            dados_p = df_pilar[df_pilar['NomePilar'] == np]
            for cam in sorted(dados_p['Camada'].unique(), reverse=True):
                st.write(f"**Camada {cam}**")
                cols = st.columns(5)
                itens_cam = dados_p[dados_p['Camada'] == cam]
                for _, row in itens_cam.iterrows():
                    with cols[int(row['Posicao'])-1]:
                        st.markdown(f"""
                        <div style="background-color:#1E1E1E; border:2px solid #4CAF50; padding:8px; border-radius:10px; text-align:center;">
                            <b style="color:white; font-size:14px;">{row['Bebida']}</b><br>
                            <span style="color:#FFD700; font-size:12px;">+{row['Avulsos']} Avulsos</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("BAIXAR", key=f"bx_{row['ID']}"):
                            st.session_state[f"pop_{row['ID']}"] = True

                        if st.session_state.get(f"pop_{row['ID']}", False):
                            with st.form(f"f_bx_{row['ID']}"):
                                q_fardo = st.number_input("Unidades no fardo?", 12)
                                if st.form_submit_button("Confirmar Saída"):
                                    total_sair = q_fardo + row['Avulsos']
                                    df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_sair
                                    df_e.to_csv(DB_ESTOQUE, index=False)
                                    df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                    st.session_state[f"pop_{row['ID']}"] = False
                                    st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (COM FARDOS E SOLTAS) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("entrada_avulso"):
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            c1, c2 = st.columns(2)
            qtd_fardo_un = c1.number_input("Quantas un. vem no fardo?", 12)
            num_fardos = c1.number_input("Quantos Fardos?", 0)
            soltas = c2.number_input("Quantas Unidades Soltas?", 0)
            
            if st.form_submit_button("Confirmar Entrada"):
                total = (num_fardos * qtd_fardo_un) + soltas
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success(f"Adicionado {total} unidades ao estoque!")
                st.rerun()
        st.subheader("Estoque Atual")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad"):
            c1, c2, c3 = st.columns([2,2,1])
            cat = c1.selectbox("Categoria", ["Refrigerante", "Cerveja", "Outros"])
            nome = c2.text_input("Nome").upper()
            preco = c3.number_input("Preço Unitário", 0.0)
            if st.form_submit_button("Salvar"):
                pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        st.dataframe(df_prod)

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        # (Mantendo a lógica simplificada de quem deve que você pediu)
        df_cascos = pd.read_csv(CASCOS_FILE)
        with st.form("cas"):
            cli = st.text_input("Cliente").upper()
            vas = st.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado"])
            qtd = st.number_input("Qtd", 1)
            if st.form_submit_button("Lançar"):
                pd.concat([df_cascos, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m"), cli, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        st.write("### Clientes Devendo")
        st.dataframe(df_cascos[df_cascos['Status'] == "DEVE"])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
