import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_cadastrados.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v2.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Unidade_por_Volume']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida', 'Qtd_Fardo']).to_csv(PILAR_ESTRUTURA, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)

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
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Cadastro de Produtos", "📜 Histórico", "🍶 Cascos"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CADASTRO DE PRODUTOS (BASE DE TUDO) ---
    if menu == "📦 Cadastro de Produtos":
        st.title("📦 Cadastro Geral de Bebidas")
        st.info("Cadastre aqui as bebidas que existem na loja. Elas aparecerão depois na hora de montar o pilar.")
        
        with st.form("form_cadastro"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck", "Outros"])
            nome_b = st.text_input("Nome da Bebida (ex: Coca Normal, Guaraná, Skol)").upper()
            
            # Valores padrão baseados na categoria
            val_padrao = 6 if cat == "Refrigerante" else (24 if cat in ["Romarinho", "Long Neck"] else 12)
            u_vol = st.number_input("Unidades por Volume (Fardo/Engradado)", value=val_padrao)
            
            if st.form_submit_button("Cadastrar Bebida"):
                if nome_b:
                    df_prod = pd.read_csv(DB_PRODUTOS)
                    novo_p = pd.DataFrame([[cat, nome_b, u_vol]], columns=df_prod.columns)
                    pd.concat([df_prod, novo_p]).to_csv(DB_PRODUTOS, index=False)
                    st.success(f"{nome_b} cadastrado com sucesso!")
                    st.rerun()
        
        st.subheader("Bebidas Cadastradas")
        st.dataframe(pd.read_csv(DB_PRODUTOS), use_container_width=True)

    # --- ABA: GESTÃO DE PILARES (CONSTRUTOR VISUAL) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Construtor Visual de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        if df_prod.empty:
            st.warning("⚠️ Você precisa cadastrar as bebidas primeiro na aba 'Cadastro de Produtos'!")
        else:
            tab1, tab2 = st.tabs(["➕ Montar/Adicionar Camada", "📊 Ver Mapa de Pilares"])

            with tab1:
                nome_pilar = st.text_input("Nome do Pilar (ex: Pilar da Frente, Pilar Coca)").upper()
                if nome_pilar:
                    # Lógica de camadas
                    dados_pilar = df_pilar[df_pilar['NomePilar'] == nome_pilar]
                    camada_atual = 1 if dados_pilar.empty else dados_pilar['Camada'].max() + 1
                    
                    st.subheader(f"Arrumação da {camada_atual}ª Camada")
                    
                    col_b, col_q = st.columns(2)
                    bebida_da_vez = col_b.selectbox("Selecione a Bebida para esta posição", df_prod['Nome'].unique())
                    qtd_por_posicao = col_q.number_input("Qtd de fardos em cada '+' marcado", min_value=1, value=1)

                    st.write("Clique nos **+** onde você quer colocar essa bebida:")
                    
                    # Grade Visual 3 atrás e 2 na frente
                    st.markdown("---")
                    st.write("**ATRÁS (3 espaços)**")
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.checkbox("➕ Pos 1", key="pos1")
                    p2 = c2.checkbox("➕ Pos 2", key="pos2")
                    p3 = c3.checkbox("➕ Pos 3", key="pos3")
                    
                    st.write("**FRENTE (2 espaços)**")
                    f1, f2 = st.columns(2)
                    p4 = f1.checkbox("➕ Pos 4", key="pos4")
                    p5 = f2.checkbox("➕ Pos 5", key="pos5")
                    
                    if st.button("💾 Salvar esta Camada"):
                        posicoes_marcadas = {1: p1, 2: p2, 3: p3, 4: p4, 5: p5}
                        novos_itens = []
                        for pos, check in posicoes_marcadas.items():
                            if check:
                                novos_itens.append([nome_pilar, camada_atual, pos, bebida_da_vez, qtd_por_posicao])
                        
                        if novos_itens:
                            df_novo = pd.DataFrame(novos_itens, columns=df_pilar.columns)
                            pd.concat([df_pilar, df_novo]).to_csv(PILAR_ESTRUTURA, index=False)
                            st.success(f"Camada {camada_atual} do {nome_pilar} salva!")
                            st.rerun()

            with tab2:
                if df_pilar.empty:
                    st.info("Nenhum pilar montado.")
                else:
                    pilares_ativos = df_pilar['NomePilar'].unique()
                    for p in pilares_ativos:
                        with st.expander(f"📍 {p}", expanded=True):
                            # Inverter para mostrar o topo primeiro
                            camadas = sorted(df_pilar[df_pilar['NomePilar'] == p]['Camada'].unique(), reverse=True)
                            for cam in camadas:
                                st.write(f"**Camada {cam}**")
                                c_dados = df_pilar[(df_pilar['NomePilar'] == p) & (df_pilar['Camada'] == cam)]
                                
                                # Mostra o layout físico
                                grid = st.columns(5)
                                for i in range(1, 6):
                                    item = c_dados[c_dados['Posicao'] == i]
                                    with grid[i-1]:
                                        if not item.empty:
                                            st.markdown(f"""<div style="background-color:#262730; border:2px solid #4CAF50; padding:10px; border-radius:10px; text-align:center;">
                                                <b>{item['Bebida'].values[0]}</b><br>{item['Qtd_Fardo'].values[0]} un</div>""", unsafe_allow_html=True)
                                        else:
                                            st.markdown("<div style='text-align:center; color:#555;'>---</div>", unsafe_allow_html=True)
                            
                            if st.button(f"🗑️ Desmanchar {p}", key=f"del_{p}"):
                                df_pilar = df_pilar[df_pilar['NomePilar'] != p]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                st.rerun()

    # --- MANTER HISTÓRICO E CASCOS ---
    elif menu == "📜 Histórico":
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE))
    
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.info("Controle de garrafas e engradados emprestados.")

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
