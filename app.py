import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v46) ---
DB_PRODUTOS = "produtos_v46.csv"
DB_ESTOQUE = "estoque_v46.csv"
PILAR_ESTRUTURA = "pilares_v46.csv"
USERS_FILE = "usuarios_v46.csv"
LOG_FILE = "historico_v46.csv"
CASCOS_FILE = "cascos_v46.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '']], columns=['user', 'nome', 'senha', 'is_admin', 'telefone']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        # Adicionado 'Telefone' na estrutura de Cascos
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

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

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            user_check = df_users[(df_users['user'] == u_in) & (df_users['senha'].astype(str) == s_in)]
            if not user_check.empty:
                st.session_state.update({'autenticado': True, 'username': u_in, 'name': user_check['nome'].values[0], 'is_admin': user_check['is_admin'].values[0] == 'SIM'})
                registrar_log(st.session_state['name'], "Entrou no sistema")
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
else:
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']
    
    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Menu", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos", "📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"] if sou_admin else ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"])

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: CASCOS (COM TELEFONE E ESTORNO) ---
    if menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        
        with st.form("novo_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            cli = c1.text_input("Nome do Cliente").upper()
            tel = c2.text_input("Telefone (WhatsApp)")
            vas = c3.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            qtd = c4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar Dívida"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                nova_divida = pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, tel, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)
                pd.concat([df_cascos, nova_divida]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {cli} ({tel}) deve {qtd} {vas}")
                st.rerun()

        st.subheader("⚠️ Devedores")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            cc1, cc2 = st.columns([7, 2])
            # Exibe Nome e Telefone na lista
            cc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if cc2.button("RECEBER", key=f"pag_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Recebeu de {r['Cliente']}")
                st.rerun()

        st.write("---")
        st.subheader("✅ Recebidos (Opção de Estornar)")
        recentes = df_cascos[df_cascos['Status'] == "PAGO"].tail(10)
        for i, r in recentes.iterrows():
            rc1, rc2 = st.columns([7, 2])
            rc1.info(f"OK: {r['QuemBaixou']} | {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
            if rc2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.at[i, 'QuemBaixou'] = ""
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"ESTORNO: Voltou dívida de {r['Cliente']}")
                st.rerun()

    # --- ABA: EQUIPE (COM TELEFONE) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        with st.form("add_user"):
            u, n, s, t, a = st.columns(5)
            nu = u.text_input("User")
            nn = n.text_input("Nome")
            ns = s.text_input("Senha")
            nt = t.text_input("Telefone")
            na = a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Usuário"):
                if nu and ns:
                    pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                    registrar_log(nome_logado, f"EQUIPE: Criou usuário {nn}")
                    st.rerun()
        st.dataframe(df_users)

    # --- ABA: GESTÃO DE PILARES (BAIXA AUTOMÁTICA) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        # Mantendo a lógica de retirada interligada ao estoque
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
                                q_auto, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                total_unidades = q_auto + row['Avulsos']
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_unidades
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"RETIRADA: {total_unidades}un de {row['Bebida']} ({np})")
                                st.rerun()

    # --- OUTRAS ABAS (Financeiro, Histórico, Entrada, Cadastro) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Estoque'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total em Mercadoria", f"R$ {df_fin['Valor_Estoque'].sum():,.2f}")
        st.dataframe(df_fin)

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico Geral")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)
    
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
        un_auto, termo = obter_dados_categoria(p_sel, df_prod)
        with st.form("entrada"):
            c1, c2 = st.columns(2)
            qtd_f = c1.number_input(f"Qtd {termo}s", 0)
            qtd_a = c2.number_input("Unidades Soltas", 0)
            if st.form_submit_button("Salvar"):
                total = (qtd_f * un_auto) + qtd_a
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"ENTRADA: {total}un de {p_sel}")
                st.rerun()
                
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("novo_p"):
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nom = c2.text_input("Nome").upper()
            pre = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Cadastrar"):
                pd.concat([df_prod, pd.DataFrame([[cat, nom, pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"CADASTRO: {nom}")
                st.rerun()
        st.dataframe(df_prod)
