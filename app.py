import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão Total", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v47) ---
DB_PRODUTOS = "produtos_v47.csv"
DB_ESTOQUE = "estoque_v47.csv"
PILAR_ESTRUTURA = "pilares_v47.csv"
USERS_FILE = "usuarios_v47.csv"
LOG_FILE = "historico_v47.csv"
CASCOS_FILE = "cascos_v47.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

# --- FUNÇÕES AUXILIARES ---
def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    if df_produtos.empty: return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# --- 3. SISTEMA DE LOGIN ---
df_users = pd.read_csv(USERS_FILE)
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_form"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            check = df_users[(df_users['user'] == u_in) & (df_users['senha'].astype(str) == s_in)]
            if not check.empty:
                st.session_state['autenticado'] = True
                st.session_state['username'] = u_in
                st.session_state['name'] = check['nome'].values[0]
                st.session_state['is_admin'] = check['is_admin'].values[0] == 'SIM'
                registrar_log(st.session_state['name'], "Login realizado")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
else:
    # --- VARIÁVEIS DE SESSÃO ---
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']

    # --- MENU LATERAL ---
    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair"):
        registrar_log(nome_logado, "Logout realizado")
        st.session_state['autenticado'] = False
        st.rerun()

    menu_options = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_options)

    # Carregar Dataframes
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        
        with st.expander("➕ Montar Nova Camada"):
            nome_p = st.text_input("NOME DO PILAR (ex: PILAR A)").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inverter = (cam_atual % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                
                escolhas, av_in = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    st.write("--- ATRÁS ---")
                    for i in range(n_atras):
                        p = i + 1
                        escolhas[p] = st.selectbox(f"Bebida Pos {p}", lista_b, key=f"sel{p}{cam_atual}")
                        av_in[p] = st.number_input(f"Avulsos Pos {p}", 0, key=f"av{p}{cam_atual}")
                with c2:
                    st.write("--- FRENTE ---")
                    for i in range(n_frente):
                        p = n_atras + i + 1
                        escolhas[p] = st.selectbox(f"Bebida Pos {p}", lista_b, key=f"sel{p}{cam_atual}")
                        av_in[p] = st.number_input(f"Avulsos Pos {p}", 0, key=f"av{p}{cam_atual}")
                
                if st.button("💾 Salvar Camada"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, beb, av_in[p]] 
                             for p, beb in escolhas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"Montou Camada {cam_atual} no {nome_p}")
                        st.success("Camada salva!")
                        st.rerun()

        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><small>{row["Bebida"]}</small><br><b style="color:#FFD700;">+{row["Avulsos"]} Av</b></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"ret_{row['ID']}"):
                                # INTERLIGAÇÃO COM ESTOQUE
                                q_padrao, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                total_a_retirar = q_padrao + row['Avulsos']
                                
                                # 1. Baixa no Estoque
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_a_retirar
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                # 2. Remove do Pilar
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                # 3. Log
                                registrar_log(nome_logado, f"RETIRADA: {total_a_retirar}un de {row['Bebida']} ({np})")
                                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
            un_auto, termo = obter_dados_categoria(p_sel, df_prod)
            with st.form("form_entrada"):
                c1, c2 = st.columns(2)
                qtd_f = c1.number_input(f"Quantidade de {termo}s", 0)
                qtd_a = c2.number_input("Unidades Avulsas", 0)
                if st.form_submit_button("Confirmar Entrada"):
                    total = (qtd_f * un_auto) + qtd_a
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: {total}un de {p_sel}")
                    st.success("Estoque atualizado!")
                    st.rerun()
        st.subheader("Estoque Geral")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro de Itens")
        with st.form("cad_p"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nom = c2.text_input("Nome").upper()
            pre = c3.number_input("Preço Unitário", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nom and nom not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nom, pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"CADASTRO: Criou {nom}")
                    st.rerun()

        st.subheader("📋 Produtos no Sistema")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1])
            cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
            cc2.write(f"R$ {row['Preco_Unitario']:.2f}")
            if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"EXCLUSÃO: Deletou {row['Nome']}")
                st.rerun()

    # --- ABA: CASCOS (COM TELEFONE E ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("vas"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            cli = c1.text_input("Cliente").upper()
            tel = c2.text_input("Telefone/WhatsApp")
            tipo = c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            qtd = c4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar Dívida"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, tel, tipo, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {cli} ({tel}) deve {qtd} {tipo}")
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"ok_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Recebeu de {r['Cliente']}")
                st.rerun()

        st.subheader("✅ Recebidos (Opção de Voltar)")
        recentes = df_cascos[df_cascos['Status'] == "PAGO"].tail(5)
        for i, r in recentes.iterrows():
            rc1, rc2 = st.columns([7, 2])
            rc1.info(f"Recebido por {r['QuemBaixou']} | {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
            if rc2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.at[i, 'QuemBaixou'] = ""
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"ESTORNO: Dívida de {r['Cliente']} restaurada")
                st.rerun()

    # --- ABA: FINANCEIRO (ADM) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo de Valores")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Investido'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total Investido em Estoque", f"R$ {df_fin['Investido'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    # --- ABA: HISTÓRICO (ADM) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico de Movimentações")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- ABA: EQUIPE (ADM) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Usuários")
        with st.form("user"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                registrar_log(nome_logado, f"EQUIPE: Criou conta para {nn}")
                st.rerun()
        st.dataframe(df_users)
