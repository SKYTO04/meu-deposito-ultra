import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v17 - Integrada) ---
DB_PRODUTOS = "produtos_v17.csv"
DB_ESTOQUE = "estoque_v17.csv"
PILAR_ESTRUTURA = "pilares_v17.csv"
USERS_FILE = "usuarios_v17.csv"
LOG_FILE = "historico_v17.csv"
CASCOS_FILE = "cascos_v17.csv"

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
    
    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Produto", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    # --- CARREGAR DADOS ---
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- 1. GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares e Vendas")
        
        with st.expander("➕ Nova Camada / Novo Pilar", expanded=False):
            nome_p = st.text_input("NOME DO PILAR (Ex: PILAR 01)").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                if cam_atual == 1:
                    inicio = st.radio("Início da Amarração:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                    st.session_state[f"layout_{nome_p}"] = inicio
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)

                st.subheader(f"Camada {cam_atual} - {'Layout Invertido' if inverter else 'Layout Padrão'}")
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                
                n_atras = 3 if not inverter else 2
                n_frente = 2 if not inverter else 3
                
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
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"Montou camada {cam_atual} no pilar {nome_p}")
                        st.rerun()

        # Visualização e Baixas
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
                            cor = "#FFD700" if row['Avulsos'] > 0 else "#4CAF50"
                            st.markdown(f'<div style="background-color:#1E1E1E; border:2px solid {cor}; padding:5px; border-radius:8px; text-align:center;"><b style="font-size:11px;">{row["Bebida"]}</b><br><small>{row["Avulsos"]} Avulsos</small></div>', unsafe_allow_html=True)
                            
                            c1, c2 = st.columns(2)
                            if c1.button("Fardo", key=f"r{row['ID']}", help="Venda fardo + avulsos"):
                                vol = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= (vol + row['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar = df_pilar[df_pilar['ID'] != row['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"Venda Fardo: {row['Bebida']} de {np}")
                                st.rerun()
                            
                            if c2.button("1un", key=f"u{row['ID']}", help="Tira 1 unidade"):
                                if row['Avulsos'] > 0:
                                    df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= 1
                                    df_e.to_csv(DB_ESTOQUE, index=False)
                                    df_pilar.loc[df_pilar['ID'] == row['ID'], 'Avulsos'] -= 1
                                    df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                    registrar_log(nome_logado, f"Venda 1un: {row['Bebida']} de {np}")
                                    st.rerun()

    # --- 2. ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("entrada"):
            bebida_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
            vol_un = df_prod[df_prod['Nome'] == bebida_sel]['Un_por_Volume'].values[0]
            c1, c2 = st.columns(2)
            qtd_f = c1.number_input("Adicionar Fardos", 0)
            qtd_s = c2.number_input("Adicionar Soltas", 0)
            if st.form_submit_button("Confirmar Entrada"):
                total_entrada = (qtd_f * vol_un) + qtd_s
                df_e.loc[df_e['Nome'] == bebida_sel, 'Estoque_Total_Un'] += total_entrada
                df_e.to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"Entrada: {total_entrada} un de {bebida_sel}")
                st.success("Estoque atualizado!")
                st.rerun()
        st.subheader("Saldo Atual")
        st.dataframe(df_e, use_container_width=True)

    # --- 3. CADASTRAR PRODUTO ---
    elif menu == "✨ Cadastrar Produto":
        st.title("✨ Novo Cadastro")
        with st.form("cadastro"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome do Produto").upper()
            custo = st.number_input("Preço de Custo (Unidade)", 0.0)
            venda = st.number_input("Preço de Venda (Unidade)", 0.0)
            if st.form_submit_button("Gravar"):
                if nome in df_prod['Nome'].values:
                    st.error("Produto já existe!")
                elif nome == "":
                    st.error("Insira um nome!")
                else:
                    vol = 24 if cat == "Romarinho" else (12 if cat == "Cerveja Lata" else 6)
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, vol, custo, venda]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success("Cadastrado com sucesso!")
                    st.rerun()

    # --- 4. CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos / Vasilhames")
        df_c = pd.read_csv(CASCOS_FILE)
        with st.form("casco_f"):
            c1, c2, c3 = st.columns(3)
            p_nome = c1.text_input("Nome do Cliente")
            p_tipo = c2.selectbox("Tipo", ["Engradado", "Garrafa Solta"])
            p_qtd = c3.number_input("Quantidade", 1)
            if st.form_submit_button("Registar"):
                novo_c = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), p_nome, p_tipo, p_qtd, "", "PENDENTE"]], columns=df_c.columns)
                pd.concat([df_c, novo_c]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        st.dataframe(df_c)

    # --- 5. HISTÓRICO (ADM) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Logs do Sistema")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- 6. FINANCEIRO (ADM) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on="Nome")
        total_estoque = (df_fin['Estoque_Total_Un'] * df_fin['Custo']).sum()
        st.metric("Total Investido em Estoque", f"R$ {total_estoque:,.2f}")
        st.dataframe(df_fin[['Nome', 'Estoque_Total_Un', 'Custo', 'Venda']])

    # --- 7. EQUIPE (ADM) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Utilizadores")
        st.table(df_users[['nome', 'is_admin']])

elif st.session_state["authentication_status"] is False:
    st.error('Palavra-passe ou utilizador incorreto.')
