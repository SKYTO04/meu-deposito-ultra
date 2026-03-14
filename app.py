import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_v12.csv"
DB_ESTOQUE = "estoque_v12.csv"
PILAR_ESTRUTURA = "pilares_v12.csv"
USERS_FILE = "usuarios_v12.csv"
LOG_FILE = "historico_v12.csv"
CASCOS_FILE = "cascos_v12.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos']).to_csv(PILAR_ESTRUTURA, index=False)
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
    menu_opcoes = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Novo Produto", "🍶 Cascos"]
    if sou_admin:
        menu_opcoes += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        
        df_m = pd.merge(df_prod, df_e, on="Nome")
        refri_ok = df_m[(df_m['Categoria'] == "Refrigerante") & (df_m['Estoque_Total_Un'] >= 1)]
        lista_refri = ["Vazio"] + refri_ok['Nome'].unique().tolist()

        with st.expander("➕ Adicionar/Configurar Camada", expanded=True):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Escolha do início se for a primeira camada
                if cam_atual == 1:
                    tipo_inicio = st.radio("Como deseja começar este pilar?", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"])
                    st.session_state[f"inicio_{nome_p}"] = tipo_inicio
                
                # Lógica de inversão baseada na escolha inicial
                escolha_base = st.session_state.get(f"inicio_{nome_p}", "3 Atrás / 2 Frente")
                if escolha_base == "3 Atrás / 2 Frente":
                    inverter = (cam_atual % 2 == 0)
                else:
                    inverter = (cam_atual % 2 != 0)

                st.subheader(f"Camada {cam_atual}")
                escolhas = {}
                avulsos = {}

                if not inverter:
                    st.info("Layout: 3 Atrás / 2 Frente")
                    st.write("**ATRÁS**")
                    cols = st.columns(3)
                    for i in range(1, 4):
                        escolhas[i] = cols[i-1].selectbox(f"Pos {i}", lista_refri, key=f"p{i}_{cam_atual}")
                        if escolhas[i] != "Vazio":
                            avulsos[i] = cols[i-1].number_input(f"Un. Avulsas P{i}", min_value=0, key=f"av{i}_{cam_atual}")
                    st.write("**FRENTE**")
                    cols = st.columns(2)
                    for i in range(4, 6):
                        escolhas[i] = cols[i-4].selectbox(f"Pos {i}", lista_refri, key=f"p{i}_{cam_atual}")
                        if escolhas[i] != "Vazio":
                            avulsos[i] = cols[i-4].number_input(f"Un. Avulsas P{i}", min_value=0, key=f"av{i}_{cam_atual}")
                else:
                    st.info("Layout: 2 Atrás / 3 Frente")
                    st.write("**ATRÁS**")
                    cols = st.columns(2)
                    for i in range(1, 3):
                        escolhas[i] = cols[i-1].selectbox(f"Pos {i}", lista_refri, key=f"p{i}_{cam_atual}")
                        if escolhas[i] != "Vazio":
                            avulsos[i] = cols[i-1].number_input(f"Un. Avulsas P{i}", min_value=0, key=f"av{i}_{cam_atual}")
                    st.write("**FRENTE**")
                    cols = st.columns(3)
                    for i in range(3, 6):
                        escolhas[i] = cols[i-3].selectbox(f"Pos {i}", lista_refri, key=f"p{i}_{cam_atual}")
                        if escolhas[i] != "Vazio":
                            avulsos[i] = cols[i-3].number_input(f"Un. Avulsas P{i}", min_value=0, key=f"av{i}_{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos_dados = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            qtd_avulsa = avulsos.get(pos, 0)
                            novos_dados.append([nome_p, cam_atual, pos, beb, qtd_avulsa])
                            # Abate estoque: 1 fardo + avulsos
                            un_fardo = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                            df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= (un_fardo + qtd_avulsa)
                    
                    if novos_dados:
                        pd.concat([df_pilar, pd.DataFrame(novos_dados, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        registrar_log(nome_logado, f"Montou camada {cam_atual} pilar {nome_p}")
                        st.rerun()

        # Visualização (Mantém o histórico visual)
        st.divider()
        for np in df_pilar['NomePilar'].unique():
            st.subheader(f"📍 {np}")
            cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
            for c in cms:
                st.write(f"Camada {c}")
                d_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                # Aqui o visual se adapta à quantidade de itens na frente/atrás daquela camada
                num_atras = len(d_c[d_c['Posicao'] <= (3 if d_c['Posicao'].max() <= 5 and 3 in d_c['Posicao'].values and 4 not in d_c[d_c['Posicao']==3].values else 2)]) # Lógica simplificada para o grid
                # Para simplificar o visual, usamos colunas dinâmicas
                st.write(f"Bebidas: {', '.join(d_c['Bebida'].tolist())}")
            if st.button(f"🗑️ Desmanchar {np}"):
                df_pilar = df_pilar[df_pilar['NomePilar'] != np]
                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (Configuração Recuperada) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        df_prod = pd.read_csv(DB_PRODUTOS)
        if not df_prod.empty:
            with st.form("ent"):
                b = st.selectbox("Produto", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b].iloc[0]
                c1, c2 = st.columns(2)
                f = c1.number_input("Fardos/Engradados", min_value=0)
                s = c2.number_input("Unidades Soltas", min_value=0)
                if st.form_submit_button("Atualizar Saldo"):
                    total = (f * info['Un_por_Volume']) + s
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == b, 'Estoque_Total_Un'] = total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Estoque Atualizado!")
                    st.rerun()
        st.dataframe(pd.read_csv(DB_ESTOQUE))

    # --- ABA: CADASTRAR PRODUTO (Configuração Recuperada) ---
    elif menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro")
        with st.form("cad_p"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome").upper()
            padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
            custo = st.number_input("Custo Unitário", 0.0)
            venda = st.number_input("Venda Unitária", 0.0)
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(DB_PRODUTOS)
                pd.concat([df_p, pd.DataFrame([[cat, nome, padrao, custo, venda]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                df_e = pd.read_csv(DB_ESTOQUE)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.success("Produto Criado!")
                st.rerun()

    # --- DEMAIS OPÇÕES (Cascos, Histórico, Financeiro, Equipe) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))
    
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico de Ações")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_f = pd.merge(pd.read_csv(DB_ESTOQUE), pd.read_csv(DB_PRODUTOS), on="Nome")
        total_inv = (df_f['Estoque_Total_Un'] * df_f['Custo']).sum()
        st.metric("Total em Estoque (Custo)", f"R$ {total_inv:,.2f}")

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        st.dataframe(df_users[['nome', 'is_admin']])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
