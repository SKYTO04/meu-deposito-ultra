import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v14) ---
DB_PRODUTOS = "produtos_v14.csv"
DB_ESTOQUE = "estoque_v14.csv"
PILAR_ESTRUTURA = "pilares_v14.csv"
USERS_FILE = "usuarios_v14.csv"
LOG_FILE = "historico_v14.csv"
CASCOS_FILE = "cascos_v14.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos']).to_csv(PILAR_ESTRUTURA, index=False)
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
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Novo Produto", "🍶 Cascos", "📜 Histórico (Adm)"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares e Amarração")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        with st.expander("➕ Adicionar Nova Camada", expanded=True):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                if cam_atual == 1:
                    inicio = st.radio("Como começar este pilar?", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                    st.session_state[f"layout_{nome_p}"] = inicio
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)

                st.subheader(f"Montando Camada {cam_atual}")
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                
                num_atras = 3 if not inverter else 2
                num_frente = 2 if not inverter else 3
                
                escolhas = {}
                avulsos_input = {}

                st.write("**ATRÁS**")
                c_atras = st.columns(num_atras)
                for i in range(num_atras):
                    pos = i + 1
                    escolhas[pos] = c_atras[i].selectbox(f"Pos {pos}", lista_bebidas, key=f"s_{pos}_{cam_atual}")
                    avulsos_input[pos] = c_atras[i].number_input(f"Avulsos P{pos}", min_value=0, key=f"av_{pos}_{cam_atual}")
                
                st.write("**FRENTE**")
                c_frente = st.columns(num_frente)
                for i in range(num_frente):
                    pos = num_atras + i + 1
                    escolhas[pos] = c_frente[i].selectbox(f"Pos {pos}", lista_bebidas, key=f"s_{pos}_{cam_atual}")
                    avulsos_input[pos] = c_frente[i].number_input(f"Avulsos P{pos}", min_value=0, key=f"av_{pos}_{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            fardo_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            qtd_av = avulsos_input.get(pos, 0)
                            novos.append([fardo_id, nome_p, cam_atual, pos, beb, qtd_av])
                            un_f = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                            df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= (un_f + qtd_av)
                    
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        st.rerun()

        # --- VISUALIZAÇÃO COM AVULSOS EM DESTAQUE ---
        st.divider()
        st.subheader("📋 Mapa de Pilares (Visualização de Carga)")
        
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    
                    # Grade de 5 colunas para o visual
                    cols = st.columns(5)
                    
                    for _, row in dados_c.iterrows():
                        p = int(row['Posicao'])
                        with cols[p-1]:
                            # Estilo para destacar os avulsos se existirem
                            cor_borda = "#FFD700" if row['Avulsos'] > 0 else "#4CAF50"
                            texto_avulso = f"<br><span style='color:{cor_borda}; font-size:13px;'>➕ {row['Avulsos']} UN</span>" if row['Avulsos'] > 0 else ""
                            
                            st.markdown(f"""
                                <div style="background-color:#1E1E1E; border:2px solid {cor_borda}; padding:8px; border-radius:8px; text-align:center; min-height:80px;">
                                    <small style="color:#888;">Pos {p}</small><br>
                                    <b style="font-size:14px;">{row['Bebida']}</b>
                                    {texto_avulso}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Retirar", key=f"ret_{row['ID']}"):
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Baixa: {row['Bebida']} do pilar {np}")
                                st.rerun()
                
                if st.button(f"Zerar {np}", key=f"clear_{np}"):
                    df_pilar = df_pilar[df_pilar['NomePilar'] != np]
                    df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                    st.rerun()

    # --- ABAS DE APOIO ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Reposição")
        df_prod = pd.read_csv(DB_PRODUTOS)
        if not df_prod.empty:
            with st.form("est"):
                b = st.selectbox("Bebida", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b].iloc[0]
                f, s = st.columns(2)
                nf = f.number_input("Novos Fardos", 0)
                ns = s.number_input("Novas Soltas", 0)
                if st.form_submit_button("Atualizar"):
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] = (nf * info['Un_por_Volume']) + ns
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Estoque Atualizado!")
        st.dataframe(pd.read_csv(DB_ESTOQUE))

    elif menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro")
        with st.form("cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            u = 24 if "Romarinho" in cat or "Long" in cat else (12 if "Lata" in cat else 6)
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(DB_PRODUTOS)
                pd.concat([df_p, pd.DataFrame([[cat, nome, u, 0, 0]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                df_e = pd.read_csv(DB_ESTOQUE)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Log")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))

elif st.session_state["authentication_status"] is False:
    st.error('Acesso negado.')
