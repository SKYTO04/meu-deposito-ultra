import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v16) ---
DB_PRODUTOS = "produtos_v16.csv"
DB_ESTOQUE = "estoque_v16.csv"
PILAR_ESTRUTURA = "pilares_v16.csv"
USERS_FILE = "usuarios_v16.csv"
LOG_FILE = "historico_v16.csv"
CASCOS_FILE = "cascos_v16.csv"

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
        st.title("🏗️ Gestão de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)

        with st.expander("➕ Adicionar Camada", expanded=True):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                if cam_atual == 1:
                    inicio = st.radio("Começar com:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                    st.session_state[f"st_{nome_p}"] = inicio
                
                layout = st.session_state.get(f"st_{nome_p}", "3 Atrás / 2 Frente")
                inv = (cam_atual % 2 == 0) if layout == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)

                st.subheader(f"Camada {cam_atual}")
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                
                n_atras = 3 if not inv else 2
                n_frente = 2 if not inv else 3
                
                escolhas, av_in = {}, {}
                st.write("**ATRÁS**")
                cols_a = st.columns(n_atras)
                for i in range(n_atras):
                    pos = i + 1
                    escolhas[pos] = cols_a[i].selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}")
                    av_in[pos] = cols_a[i].number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")
                
                st.write("**FRENTE**")
                cols_f = st.columns(n_frente)
                for i in range(n_frente):
                    pos = n_atras + i + 1
                    escolhas[pos] = cols_f[i].selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}")
                    av_in[pos] = cols_f[i].number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            f_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            novos.append([f_id, nome_p, cam_atual, pos, beb, av_in[pos]])
                            # Nota: O estoque já foi baixado na entrada ou permanece igual, aqui apenas registramos a posição física.
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.success("Camada registrada!")
                        st.rerun()

        # --- MAPA VISUAL COM BAIXA REAL ---
        st.divider()
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        p = int(row['Posicao'])
                        with cols[p-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:8px; text-align:center;"><b>{row["Bebida"]}</b><br><small>{row["Avulsos"]} Avulsos</small></div>', unsafe_allow_html=True)
                            
                            c1, c2 = st.columns(2)
                            if c1.button("Retirar", key=f"r{row['ID']}", help="Venda do fardo"):
                                # BAIXA AUTOMÁTICA NO ESTOQUE
                                un_por_fardo = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                total_sair = un_por_fardo + row['Avulsos']
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_sair
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                
                                # Remove do Pilar
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"VENDA: {row['Bebida']} (Fardo+{row['Avulsos']} un) de {np}")
                                st.rerun()
                            
                            if c2.button("1 Un", key=f"u{row['ID']}"):
                                if row['Avulsos'] > 0:
                                    # BAIXA DE 1 UNIDADE NO ESTOQUE
                                    df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= 1
                                    df_e.to_csv(DB_ESTOQUE, index=False)
                                    
                                    # Atualiza no Pilar
                                    df_pilar.loc[df_pilar['ID'] == row['ID'], 'Avulsos'] -= 1
                                    df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                    registrar_log(nome_logado, f"VENDA AVULSA: 1 un {row['Bebida']} de {np}")
                                    st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (ONDE TUDO COMEÇA) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada e Saldo Total")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        if not df_prod.empty:
            with st.form("f_e"):
                b = st.selectbox("Bebida", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b].iloc[0]
                f, s = st.columns(2)
                nf = f.number_input("Adicionar Fardos", 0)
                ns = s.number_input("Adicionar Soltas", 0)
                if st.form_submit_button("Lançar no Estoque"):
                    qtd_nova = (nf * info['Un_por_Volume']) + ns
                    df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] += qtd_nova
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success(f"Adicionado {qtd_nova} unidades de {b}")
                    st.rerun()
        st.subheader("Saldo Geral em Unidades")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro")
        df_p = pd.read_csv(DB_PRODUTOS)
        with st.form("f_cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            # Define padrão de volume
            if cat == "Romarinho": u = 24
            elif cat == "Cerveja Lata": u = 12
            elif cat == "Long Neck": u = 6
            else: u = 6 # Refrigerante pet 2L geralmente 6
            
            if st.form_submit_button("Salvar"):
                if nome in df_p['Nome'].values:
                    st.warning("Já cadastrado!")
                else:
                    pd.concat([df_p, pd.DataFrame([[cat, nome, u, 0, 0]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                    df_e = pd.read_csv(DB_ESTOQUE)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success("Criado!")
                    st.rerun()

    elif menu == "📜 Histórico (Adm)":
        st.title("📜 Log de Vendas e Movimentação")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
