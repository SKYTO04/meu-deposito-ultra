import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v43) ---
DB_PRODUTOS = "produtos_v43.csv"
DB_ESTOQUE = "estoque_v43.csv"
PILAR_ESTRUTURA = "pilares_v43.csv"
USERS_FILE = "usuarios_v43.csv"
LOG_FILE = "historico_v43.csv"
CASCOS_FILE = "cascos_v43.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    if df_produtos.empty:
        return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# --- 3. SISTEMA DE LOGIN (SEM CRIPTOGRAFIA PARA EQUIPE ENTRAR) ---
df_users = pd.read_csv(USERS_FILE)

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            # Compara texto simples para facilitar criação de equipe
            user_check = df_users[(df_users['user'] == usuario_input) & (df_users['senha'].astype(str) == senha_input)]
            if not user_check.empty:
                st.session_state['autenticado'] = True
                st.session_state['username'] = usuario_input
                st.session_state['name'] = user_check['nome'].values[0]
                st.session_state['is_admin'] = user_check['is_admin'].values[0] == 'SIM'
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
else:
    # --- VARIÁVEIS DE SESSÃO ---
    nome_logado = st.session_state['name']
    user_logado = st.session_state['username']
    sou_admin = st.session_state['is_admin']

    # --- SIDEBAR ---
    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair / Logout"):
        st.session_state['autenticado'] = False
        st.rerun()

    opcoes_menu = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        opcoes_menu += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", opcoes_menu)

    # Carregar Dados
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        
        with st.expander("➕ Montar Nova Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
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
                        pos = i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")
                with c2:
                    st.write("--- FRENTE ---")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}")

                if st.button("💾 Salvar Camada"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, beb, av_in[p]] for p, beb in escolhas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"Montou Camada {cam_atual} no {nome_p}")
                        st.rerun()

        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><small>{row["Bebida"]}</small><br><b style="color:#FFD700;">+{row["Avulsos"]} Av</b></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                st.session_state[f"ask_{row['ID']}"] = True
                            
                            if st.session_state.get(f"ask_{row['ID']}", False):
                                q_auto, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                with st.form(f"baixa_{row['ID']}"):
                                    q_f = st.number_input(f"Unidades no {termo.lower()}?", value=q_auto)
                                    if st.form_submit_button("Confirmar Baixa"):
                                        total = q_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        registrar_log(nome_logado, f"Retirou {row['Bebida']} ({total}un)")
                                        st.session_state[f"ask_{row['ID']}"] = False
                                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (DINÂMICA) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique())
            un_auto, termo = obter_dados_categoria(p_sel, df_prod)
            with st.form("ent_v43"):
                c1, c2 = st.columns(2)
                u_f = c1.number_input(f"Unidades por {termo.lower()}", value=un_auto)
                n_f = c1.number_input(f"Quantidade de {termo}s", 0)
                n_s = c2.number_input("Unidades Soltas", 0)
                if st.form_submit_button("Confirmar Entrada"):
                    total = (n_f * u_f) + n_s
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Entrada: {total}un de {p_sel}")
                    st.success("Estoque Atualizado!")
                    st.rerun()
        st.subheader("Estoque Geral")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad_v43"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco = c3.number_input("Preço Unitário (R$)", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome and nome not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Cadastrou: {nome}")
                    st.rerun()

        st.subheader("📋 Produtos Cadastrados")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1])
            cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
            cc2.write(f"Preço: R$ {row['Preco_Unitario']:.2f}")
            if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"Excluiu: {row['Nome']}")
                st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        with st.form("casco_v43"):
            cli, vas, qtd = st.columns(3)
            c_cli = cli.text_input("Cliente").upper()
            c_vas = vas.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            c_qtd = qtd.number_input("Qtd", 1)
            if st.form_submit_button("Lançar"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m"), c_cli, c_vas, c_qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        st.dataframe(df_cascos[df_cascos['Status'] == "DEVE"], use_container_width=True)

    # --- ABA: FINANCEIRO (ADM) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Total_Investido'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Valor Total em Estoque", f"R$ {df_fin['Total_Investido'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    # --- ABA: HISTÓRICO (ADM) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico de Ações")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- ABA: EQUIPE (ADM) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Usuários")
        with st.form("user_v43"):
            u, n, s, a = st.columns(4)
            nu, nn, ns, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Usuário"):
                if nu and ns:
                    pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                    st.success(f"Usuário {nu} criado!")
                    st.rerun()
        st.dataframe(df_users)
