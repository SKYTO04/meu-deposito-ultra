import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_lista_v9.csv"
DB_ESTOQUE = "estoque_movimentacao_v9.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v9.csv"
USERS_FILE = "usuarios_v9.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
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
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Novo Produto"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem e Visualização de Pilares")
        
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        
        # Filtra refrigerantes com estoque
        df_m = pd.merge(df_prod, df_e, on="Nome")
        refri_ok = df_m[(df_m['Categoria'] == "Refrigerante") & (df_m['Estoque_Total_Un'] >= df_m['Un_por_Volume'])]
        lista_refri = ["Vazio"] + refri_ok['Nome'].unique().tolist()
        
        with st.expander("➕ Adicionar Nova Camada ao Pilar", expanded=True):
            nome_p = st.text_input("NOME DO PILAR (Ex: Pilar 1)").upper()
            if nome_p:
                camada_atual = 1 if df_pilar[df_pilar['NomePilar']==nome_p].empty else df_pilar[df_pilar['NomePilar']==nome_p]['Camada'].max() + 1
                st.write(f"Montando a **{camada_atual}ª Camada**")
                
                st.markdown("**ATRÁS**")
                c_atras = st.columns(3)
                p1 = c_atras[0].selectbox("P1", lista_refri, key="p1")
                p2 = c_atras[1].selectbox("P2", lista_refri, key="p2")
                p3 = c_atras[2].selectbox("P3", lista_refri, key="p3")
                
                st.markdown("**FRENTE**")
                c_frente = st.columns(2)
                p4 = c_frente[0].selectbox("P4", lista_refri, key="p4")
                p5 = c_frente[1].selectbox("P5", lista_refri, key="p5")

                if st.button("💾 Salvar Camada"):
                    escolhas = {1:p1, 2:p2, 3:p3, 4:p4, 5:p5}
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            novos.append([nome_p, camada_atual, pos, beb])
                            un_f = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                            df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= un_f
                    
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        st.success(f"Camada {camada_atual} salva!")
                        st.rerun()

        # --- VISUALIZAÇÃO DOS PILARES SALVOS ---
        st.divider()
        st.subheader("📋 Mapa de Pilares no Pátio")
        
        if df_pilar.empty:
            st.info("Nenhum pilar montado ainda.")
        else:
            nomes_pilares = df_pilar['NomePilar'].unique()
            for n_pilar in nomes_pilares:
                with st.container():
                    st.markdown(f"### 📍 {n_pilar}")
                    # Mostra as camadas da mais alta para a mais baixa
                    camadas = sorted(df_pilar[df_pilar['NomePilar'] == n_pilar]['Camada'].unique(), reverse=True)
                    
                    for c in camadas:
                        st.write(f"**Camada {c}**")
                        dados_c = df_pilar[(df_pilar['NomePilar'] == n_pilar) & (df_pilar['Camada'] == c)]
                        
                        # Grade visual 3x2
                        g_atras = st.columns(3)
                        g_frente = st.columns(2)
                        
                        for i in range(1, 6):
                            item = dados_c[dados_c['Posicao'] == i]
                            # Define qual grid usar (atrás ou frente)
                            target_grid = g_atras[i-1] if i <= 3 else g_frente[i-4]
                            
                            with target_grid:
                                if not item.empty:
                                    st.markdown(f"""
                                        <div style="background-color:#0E1117; border:2px solid #4CAF50; padding:8px; border-radius:8px; text-align:center;">
                                            <span style="font-size:10px; color:#aaa;">Pos {i}</span><br>
                                            <b style="font-size:12px;">{item['Bebida'].values[0]}</b>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown('<div style="text-align:center; color:#444;">---</div>', unsafe_allow_html=True)
                    
                    if st.button(f"🗑️ Desmanchar {n_pilar}", key=f"del_{n_pilar}"):
                        df_pilar = df_pilar[df_pilar['NomePilar'] != n_pilar]
                        df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()
                    st.divider()

    # --- ABA: CADASTRO DE PRODUTO ---
    elif menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome da Bebida").upper()
            padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(DB_PRODUTOS)
                pd.concat([df_p, pd.DataFrame([[cat, nome, padrao]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                df_e = pd.read_csv(DB_ESTOQUE)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.success("Cadastrado!")
                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Estoque")
        df_prod = pd.read_csv(DB_PRODUTOS)
        if not df_prod.empty:
            with st.form("estoque"):
                b_sel = st.selectbox("Bebida", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b_sel].iloc[0]
                c1, c2 = st.columns(2)
                f = c1.number_input("Fardos/Engradados", min_value=0)
                s = c2.number_input("Soltas", min_value=0)
                if st.form_submit_button("Salvar Estoque"):
                    total = (f * info['Un_por_Volume']) + s
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == b_sel, 'Estoque_Total_Un'] = total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Estoque Atualizado!")
                    st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
