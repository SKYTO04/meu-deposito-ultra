import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_v6.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v6.csv"
USERS_FILE = "usuarios_v6.csv"
LOG_FILE = "historico_v6.csv"
CASCOS_FILE = "cascos_v6.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Estoque_Total_Un', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida']).to_csv(PILAR_ESTRUTURA, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Tipo', 'Qtd', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 3. LOGIN ---
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
    menu_opcoes = ["🏗️ Gestão de Pilares", "📦 Estoque & Conferência", "🍶 Cascos"]
    if sou_admin:
        menu_opcoes += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: ESTOQUE ---
    if menu == "📦 Estoque & Conferência":
        st.title("📦 Controle de Estoque")
        tab_cad, tab_ver = st.tabs(["➕ Cadastrar/Ajustar", "📋 Saldo Geral"])
        
        with tab_cad:
            with st.form("form_estoque"):
                cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
                nome = st.text_input("Nome da Bebida").upper()
                padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
                
                c1, c2 = st.columns(2)
                q_fechada = c1.number_input("Fardos/Engradados FECHADOS", min_value=0, step=1)
                q_avulsa = c2.number_input("Unidades SOLTAS", min_value=0, step=1)
                
                total_un = (q_fechada * padrao) + q_avulsa
                if st.form_submit_button("Salvar Estoque"):
                    df_p = pd.read_csv(DB_PRODUTOS)
                    df_p = df_p[df_p['Nome'] != nome]
                    pd.concat([df_p, pd.DataFrame([[cat, nome, total_un, padrao, 0.0, 0.0]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                    st.success(f"Estoque de {nome} atualizado!")
                    st.rerun()

        with tab_ver:
            st.dataframe(pd.read_csv(DB_PRODUTOS))

    # --- ABA: GESTÃO DE PILARES (COM TRAVA DE ESTOQUE) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem com Trava de Estoque")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        # Filtra apenas refrigerantes que REALMENTE têm estoque (pelo menos 1 fardo)
        refri_disponiveis = df_prod[(df_prod['Categoria'] == "Refrigerante") & (df_prod['Estoque_Total_Un'] >= df_prod['Un_por_Volume'])]
        lista_refri = ["Vazio"] + refri_disponiveis['Nome'].unique().tolist()

        nome_pilar = st.text_input("NOME DO PILAR").upper()
        
        if nome_pilar:
            dados_p = df_pilar[df_pilar['NomePilar'] == nome_pilar]
            camada = 1 if dados_p.empty else dados_p['Camada'].max() + 1
            
            st.subheader(f"Montando Camada {camada}")
            st.info("O sistema só mostra bebidas que possuem fardos no estoque.")

            escolhas = {}
            st.write("**ATRÁS**")
            c1, c2, c3 = st.columns(3)
            escolhas[1] = c1.selectbox("Posição 1", lista_refri, key="p1")
            escolhas[2] = c2.selectbox("Posição 2", lista_refri, key="p2")
            escolhas[3] = c3.selectbox("Posição 3", lista_refri, key="p3")
            
            st.write("**FRENTE**")
            f1, f2 = st.columns(2)
            escolhas[4] = f1.selectbox("Posição 4", lista_refri, key="p4")
            escolhas[5] = f2.selectbox("Posição 5", lista_refri, key="p5")

            if st.button("💾 Salvar e Abater Estoque"):
                # Conta quantos fardos de cada bebida o usuário tentou colocar
                contagem_uso = {}
                for beb in escolhas.values():
                    if beb != "Vazio":
                        contagem_uso[beb] = contagem_uso.get(beb, 0) + 1
                
                # Validação de estoque
                erro_estoque = False
                for beb, qtd_pedida in contagem_uso.items():
                    estoque_atual_un = df_prod[df_prod['Nome'] == beb]['Estoque_Total_Un'].values[0]
                    un_por_fardo = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                    fardos_disponiveis = estoque_atual_un // un_por_fardo
                    
                    if qtd_pedida > fardos_disponiveis:
                        st.error(f"❌ Erro: Você tentou colocar {qtd_pedida} fardos de {beb}, mas só tem {int(fardos_disponiveis)} no estoque!")
                        erro_estoque = True
                
                if not erro_estoque:
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            novos.append([nome_pilar, camada, pos, beb])
                            # Abater do estoque
                            un_fardo = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                            df_prod.loc[df_prod['Nome'] == beb, 'Estoque_Total_Un'] -= un_fardo
                    
                    pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                    df_prod.to_csv(DB_PRODUTOS, index=False) # Salva estoque atualizado
                    st.success("Camada salva e estoque baixado!")
                    st.rerun()

            # Visualização do Pilar
            st.divider()
            cms = sorted(df_pilar[df_pilar['NomePilar'] == nome_pilar]['Camada'].unique(), reverse=True)
            for c in cms:
                with st.expander(f"Camada {c}"):
                    itens = df_pilar[(df_pilar['NomePilar']==nome_pilar) & (df_pilar['Camada']==c)]
                    cols = st.columns(5)
                    for i in range(1, 6):
                        it = itens[itens['Posicao'] == i]
                        if not it.empty:
                            cols[i-1].markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:10px; border-radius:5px; text-align:center; font-size:10px;">{it["Bebida"].values[0]}</div>', unsafe_allow_html=True)

    # --- DEMAIS ABAS (CASCOS, HISTORICO, FINANCEIRO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "📊 Financeiro":
        st.title("📊 Financeiro")
        st.write("Cálculo de lucros e investimentos.")

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
