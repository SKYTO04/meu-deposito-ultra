import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_v13.csv"
DB_ESTOQUE = "estoque_v13.csv"
PILAR_ESTRUTURA = "pilares_v13.csv"
USERS_FILE = "usuarios_v13.csv"
LOG_FILE = "historico_v13.csv"
CASCOS_FILE = "cascos_v13.csv"

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
        st.title("🏗️ Gestão de Pilares (Amarração Cruzada)")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        with st.expander("➕ Adicionar Nova Camada", expanded=True):
            nome_p = st.text_input("NOME DO PILAR (Ex: Pilar A)").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Escolha de Início na Camada 1
                if cam_atual == 1:
                    inicio = st.radio("Como começar este pilar?", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                    st.session_state[f"layout_{nome_p}"] = inicio
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                # Lógica de Inversão
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)

                st.subheader(f"Camada {cam_atual}")
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                
                num_atras = 3 if not inverter else 2
                num_frente = 2 if not inverter else 3
                
                escolhas = {}
                avulsos_camada = {}

                st.write("**ATRÁS**")
                c_atras = st.columns(num_atras)
                for i in range(num_atras):
                    pos = i + 1
                    escolhas[pos] = c_atras[i].selectbox(f"Pos {pos}", lista_bebidas, key=f"s_{pos}_{cam_atual}")
                    avulsos_camada[pos] = c_atras[i].number_input(f"Avulsos P{pos}", min_value=0, key=f"av_{pos}_{cam_atual}")
                
                st.write("**FRENTE**")
                c_frente = st.columns(num_frente)
                for i in range(num_frente):
                    pos = num_atras + i + 1
                    escolhas[pos] = c_frente[i].selectbox(f"Pos {pos}", lista_bebidas, key=f"s_{pos}_{cam_atual}")
                    avulsos_camada[pos] = c_frente[i].number_input(f"Avulsos P{pos}", min_value=0, key=f"av_{pos}_{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            fardo_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            qtd_av = avulsos_camada.get(pos, 0)
                            novos.append([fardo_id, nome_p, cam_atual, pos, beb, qtd_av])
                            
                            # Abate estoque
                            un_f = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                            df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= (un_f + qtd_av)
                    
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        registrar_log(nome_logado, f"Montou camada {cam_atual} pilar {nome_p}")
                        st.success("Salvo!")
                        st.rerun()

        # --- VISUALIZAÇÃO COM BOTÃO DE RETIRADA ---
        st.divider()
        st.subheader("📋 Mapa de Pilares (Baixa Individual)")
        
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f"""<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;">
                                <small>Pos {row['Posicao']}</small><br><b>{row['Bebida']}</b><br><small>+{row['Avulsos']} un</small></div>""", unsafe_allow_html=True)
                            
                            if st.button("Retirar", key=f"btn_{row['ID']}"):
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Venda: Retirou {row['Bebida']} do pilar {np}")
                                st.rerun()
                
                if st.button(f"Zerar Pilar {np}", key=f"zerar_{np}"):
                    df_pilar = df_pilar[df_pilar['NomePilar'] != np]
                    df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                    st.rerun()

    # --- OUTRAS ABAS (Recuperadas) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Reposição de Estoque")
        df_prod = pd.read_csv(DB_PRODUTOS)
        if not df_prod.empty:
            with st.form("f_est"):
                b = st.selectbox("Bebida", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b].iloc[0]
                f, s = st.columns(2)
                qtd_f = f.number_input("Fardos Novos", min_value=0)
                qtd_s = s.number_input("Soltas Novas", min_value=0)
                if st.form_submit_button("Atualizar Estoque"):
                    total = (qtd_f * info['Un_por_Volume']) + qtd_s
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] = total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Estoque Atualizado!")
                    st.rerun()
        st.dataframe(pd.read_csv(DB_ESTOQUE))

    elif menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro de Itens")
        with st.form("f_cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome da Bebida").upper()
            padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
            if st.form_submit_button("Salvar Produto"):
                df_p = pd.read_csv(DB_PRODUTOS)
                pd.concat([df_p, pd.DataFrame([[cat, nome, padrao, 0, 0]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                df_e = pd.read_csv(DB_ESTOQUE)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Log")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
