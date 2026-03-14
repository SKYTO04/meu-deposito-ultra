import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_cadastrados.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v3.csv"
USERS_FILE = "usuarios_v2.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Unidade_por_Volume']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida']).to_csv(PILAR_ESTRUTURA, index=False)

init_files()

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials, 'pacaembu_cookie', 'auth_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    st.sidebar.title(f"👤 {st.session_state['name']}")
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Cadastro de Produtos", "🍶 Cascos"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CADASTRO ---
    if menu == "📦 Cadastro de Produtos":
        st.title("📦 Cadastro de Bebidas")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome_b = st.text_input("Nome da Bebida").upper()
            u_vol = st.number_input("Unidades por Volume", value=6 if cat=="Refrigerante" else 24)
            if st.form_submit_button("Cadastrar"):
                df = pd.read_csv(DB_PRODUTOS)
                pd.concat([df, pd.DataFrame([[cat, nome_b, u_vol]], columns=df.columns)]).to_csv(DB_PRODUTOS, index=False)
                st.success("Cadastrado!")
                st.rerun()
        st.dataframe(pd.read_csv(DB_PRODUTOS))

    # --- ABA: GESTÃO DE PILARES (MISTURA DE BEBIDAS NA AMARRAÇÃO) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montar Pilar (Misturando Sabores)")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        # Filtra apenas REFRIGERANTES para a amarração
        lista_refri = df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].unique().tolist()
        lista_refri = ["Vazio"] + lista_refri

        nome_pilar = st.text_input("NOME DO PILAR (Ex: Pilar Coca)").upper()
        
        if nome_pilar:
            dados_p = df_pilar[df_pilar['NomePilar'] == nome_pilar]
            camada = 1 if dados_p.empty else dados_p['Camada'].max() + 1
            
            st.subheader(f"Arrumação da {camada}ª Camada")
            st.write("Escolha a bebida para cada posição da amarração:")

            # Interface de seleção individual por posição
            escolhas_camada = {}
            
            st.markdown("### 🧱 Atrás (3 espaços)")
            c1, c2, c3 = st.columns(3)
            escolhas_camada[1] = c1.selectbox("Posição 1", lista_refri, key="pos1")
            escolhas_camada[2] = c2.selectbox("Posição 2", lista_refri, key="pos2")
            escolhas_camada[3] = c3.selectbox("Posição 3", lista_refri, key="pos3")
            
            st.markdown("### 🧱 Frente (2 espaços)")
            f1, f2 = st.columns(2)
            escolhas_camada[4] = f1.selectbox("Posição 4", lista_refri, key="pos4")
            escolhas_camada[5] = f2.selectbox("Posição 5", lista_refri, key="pos5")

            if st.button("💾 Salvar Camada e Ir para a Próxima"):
                novos = []
                for pos, beb in escolhas_camada.items():
                    if beb != "Vazio":
                        novos.append([nome_pilar, camada, pos, beb])
                
                if novos:
                    df_novo = pd.DataFrame(novos, columns=df_pilar.columns)
                    pd.concat([df_pilar, df_novo]).to_csv(PILAR_ESTRUTURA, index=False)
                    st.success(f"Camada {camada} salva!")
                    st.rerun()

            # --- VISUALIZAÇÃO DO PILAR ---
            st.divider()
            if not df_pilar[df_pilar['NomePilar'] == nome_pilar].empty:
                st.subheader(f"Visão Atual: {nome_pilar}")
                camadas_v = sorted(df_pilar[df_pilar['NomePilar'] == nome_pilar]['Camada'].unique(), reverse=True)
                for cv in camadas_v:
                    with st.expander(f"Camada {cv}", expanded=True):
                        itens = df_pilar[(df_pilar['NomePilar'] == nome_pilar) & (df_pilar['Camada'] == cv)]
                        g = st.columns(5)
                        for p_idx in range(1, 6):
                            it = itens[itens['Posicao'] == p_idx]
                            with g[p_idx-1]:
                                if not it.empty:
                                    st.markdown(f'<div style="background-color:#0E1117; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center; font-size:10px;">{it["Bebida"].values[0]}</div>', unsafe_allow_html=True)
                
                if st.button("🗑️ Desmanchar Pilar"):
                    df_pilar = df_pilar[df_pilar['NomePilar'] != nome_pilar]
                    df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                    st.rerun()

    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.info("Espaço para controle de garrafas.")

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
