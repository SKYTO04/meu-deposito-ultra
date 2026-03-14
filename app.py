import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v24 - Versão Consolidada) ---
DB_PRODUTOS = "produtos_v24.csv"
DB_ESTOQUE = "estoque_v24.csv"
PILAR_ESTRUTURA = "pilares_v24.csv"
USERS_FILE = "usuarios_v24.csv"
LOG_FILE = "historico_v24.csv"
CASCOS_FILE = "cascos_v24.csv"
CASCOS_HISTORICO = "cascos_historico_v24.csv"

def init_files():
    # Inicializa todos os arquivos necessários se não existirem
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda'],
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

    # --- MENU LATERAL ---
    st.sidebar.title(f"👤 {nome_logado}")
    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Produto", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    authenticator.logout('Sair', 'sidebar')

    # Carregamento de dados globais
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares e Vendas")
        
        with st.expander("➕ Montar Nova Camada no Pilar"):
            nome_p = st.text_input("NOME DO PILAR (Ex: Pilar A)").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Lógica de Layout
                if cam_atual == 1:
                    st.session_state[f"layout_{nome_p}"] = st.radio("Configuração de Base:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)
                
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                n_atras = 3 if not inverter else 2
                n_frente = 2 if not inverter else 3
                
                escolhas, av_in = {}, {}
                st.write(f"**Camada {cam_atual}**")
                c_atras, c_frente = st.columns(2)
                with c_atras:
                    st.write("--- ATRÁS ---")
                    for i in range(n_atras):
                        pos = i + 1
                        escolhas[pos] = st.selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}{nome_p}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}{nome_p}")
                with c_frente:
                    st.write("--- FRENTE ---")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        escolhas[pos] = st.selectbox(f"Pos {pos}", lista_b, key=f"s{pos}{cam_atual}{nome_p}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}{nome_p}")

                if st.button("💾 Salvar Camada"):
                    novos_dados = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            f_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            novos_dados.append([f_id, nome_p, cam_atual, pos, beb, av_in[pos]])
                    if novos_dados:
                        pd.concat([df_pilar, pd.DataFrame(novos_dados, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.success("Camada salva!")
                        st.rerun()

        # Visualização dos Pilares
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
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><b>{row["Bebida"]}</b><br><small>{row["Avulsos"]} Avulsos</small></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR FARDO", key=f"btn_{row['ID']}"):
                                vol = df_prod[df_prod['Nome'] == row['Bebida']]['Un_por_Volume'].values[0]
                                total_baixar = vol + row['Avulsos']
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_baixar
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"VENDA: {row['Bebida']} ({total_baixar}un) do {np}")
                                st.rerun()

    # --- ABA: CASCOS (O QUE O CLIENTE LEVOU) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        df_hist_cascos = pd.read_csv(CASCOS_HISTORICO)
        
        tab_ativa, tab_hist = st.tabs(["🔴 Pendências Ativas", "📜 Histórico de Devoluções"])

        with tab_ativa:
            with st.form("form_novo_casco", clear_on_submit=True):
                st.subheader("Registrar que o Cliente pegou Casco")
                c1, c2, c3 = st.columns([2, 2, 1])
                cli = c1.text_input("NOME DO CLIENTE").upper()
                tipo = c2.selectbox("VASILHAME LEVADO", ["Coca-Cola 1L Retornável", "Coca-Cola 2L Retornável", "Engradado Completo", "Litrinho (Romarinho) Avulso"])
                qtd = c3.number_input("QUANTIDADE", 1, step=1)
                if st.form_submit_button("Lançar Pendência"):
                    novo_id = f"C{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    nova_pendencia = pd.DataFrame([[novo_id, datetime.now().strftime("%d/%m/%Y %H:%M"), cli, tipo, qtd, "DEVE CASCO", ""]], columns=df_cascos.columns)
                    pd.concat([df_cascos, nova_pendencia]).to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"Casco: {cli} levou {qtd}x {tipo}")
                    st.rerun()

            st.divider()
            if not df_cascos.empty:
                for _, row in df_cascos.iterrows():
                    r1, r2, r3, r4 = st.columns([1, 2, 2, 1])
                    r1.text(row['Data'])
                    r2.markdown(f"**👤 {row['Cliente']}**")
                    r3.error(f"LEVOU: {row['Quantidade']}x {row['Vasilhame']}")
                    if r4.button("DEVOLVEU", key=f"dev_{row['ID']}"):
                        row_h = df_cascos[df_cascos['ID'] == row['ID']].copy()
                        row_h['QuemBaixou'] = nome_logado
                        row_h['Status'] = "DEVOLVIDO"
                        pd.concat([df_hist_cascos, row_h]).to_csv(CASCOS_HISTORICO, index=False)
                        df_cascos[df_cascos['ID'] != row['ID']].to_csv(CASCOS_FILE, index=False)
                        registrar_log(nome_logado, f"Recebeu casco de: {row['Cliente']}")
                        st.rerun()
            else:
                st.info("Nenhuma pendência ativa.")

        with tab_hist:
            st.subheader("Histórico de Cascos que voltaram")
            if not df_hist_cascos.empty:
                for _, row in df_hist_cascos.iterrows():
                    h1, h2, h3, h4 = st.columns([1, 3, 2, 1])
                    h1.text(row['Data'])
                    h2.text(f"✅ {row['Cliente']} devolveu {row['Quantidade']}x {row['Vasilhame']}")
                    h3.info(f"Recebido por: {row['QuemBaixou']}")
                    if h4.button("REATIVAR", key=f"und_{row['ID']}"):
                        pd.concat([df_cascos, df_hist_cascos[df_hist_cascos['ID'] == row['ID']]]).to_csv(CASCOS_FILE, index=False)
                        df_hist_cascos[df_hist_cascos['ID'] != row['ID']].to_csv(CASCOS_HISTORICO, index=False)
                        st.rerun()
            else:
                st.info("O histórico está vazio.")

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("form_entrada"):
            prod_sel = st.selectbox("Escolha o Produto", df_prod['Nome'].unique())
            fardos = st.number_input("Qtd Fardos", 0)
            soltas = st.number_input("Qtd Unidades Soltas", 0)
            if st.form_submit_button("Confirmar Entrada"):
                vol_un = df_prod[df_prod['Nome'] == prod_sel]['Un_por_Volume'].values[0]
                total = (fardos * vol_un) + soltas
                df_e.loc[df_e['Nome'] == prod_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"Entrada de Estoque: {prod_sel} (+{total}un)")
                st.success(f"Estoque de {prod_sel} atualizado!")

        st.subheader("Saldo em Estoque")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRAR PRODUTO ---
    elif menu == "✨ Cadastrar Produto":
        st.title("✨ Novo Produto")
        with st.form("form_cad_prod"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck", "Coca Retornável"])
            nome_p = st.text_input("Nome do Produto").upper()
            custo = st.number_input("Custo Unitário", 0.0)
            venda = st.number_input("Venda Unitária", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome_p in df_prod['Nome'].values:
                    st.error("Produto já cadastrado!")
                else:
                    vol = 24 if cat == "Romarinho" else (12 if "Lata" in cat else 6)
                    novo_p = pd.DataFrame([[cat, nome_p, vol, custo, venda]], columns=df_prod.columns)
                    pd.concat([df_prod, novo_p]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome_p, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.success("Produto cadastrado com sucesso!")
                    st.rerun()

    # --- ABA: EQUIPE (ADMIN) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        with st.form("form_equipe"):
            n_nome = st.text_input("Nome Completo")
            n_user = st.text_input("Usuário / Login")
            n_pass = st.text_input("Senha Inicial")
            n_adm = st.selectbox("Dar acesso de Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Acesso"):
                if n_user in df_users['user'].values:
                    st.error("Usuário já existe!")
                else:
                    novo_u = pd.DataFrame([[n_user, n_nome, n_pass, n_adm]], columns=df_users.columns)
                    pd.concat([df_users, novo_u]).to_csv(USERS_FILE, index=False)
                    st.success(f"Acesso de {n_user} criado!")
                    st.rerun()
        
        st.subheader("Usuários Ativos")
        st.dataframe(df_users[['nome', 'user', 'is_admin']])

    # --- HISTÓRICO E FINANCEIRO ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico Geral de Operações")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Total_Estoque'] = df_fin['Estoque_Total_Un'] * df_fin['Custo']
        st.metric("Total em Mercadoria (Custo)", f"R$ {df_fin['Valor_Total_Estoque'].sum():,.2f}")
        st.dataframe(df_fin[['Nome', 'Estoque_Total_Un', 'Custo', 'Valor_Total_Estoque']])

# Mensagem de erro para login
elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha incorretos.')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, faça o login.')
