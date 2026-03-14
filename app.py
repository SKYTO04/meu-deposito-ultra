import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão v52", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v52) ---
DB_PRODUTOS = "produtos_v52.csv"
DB_ESTOQUE = "estoque_v52.csv"
PILAR_ESTRUTURA = "pilares_v52.csv"
USERS_FILE = "usuarios_v52.csv"
LOG_FILE = "historico_v52.csv"
CASCOS_FILE = "cascos_v52.csv"

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
                st.session_state.update({'autenticado': True, 'name': check['nome'].values[0], 'is_admin': check['is_admin'].values[0] == 'SIM'})
                registrar_log(st.session_state['name'], "Login")
                st.rerun()
            else: st.error("Acesso Negado.")
else:
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']
    
    menu_options = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin: menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    menu = st.sidebar.radio("Navegação", menu_options)

    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: GESTÃO DE PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares")
        with st.expander("🆕 Criar Novo Pilar ou Adicionar Camada"):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_alvo = st.selectbox("Selecione o Pilar", pilares_existentes)
            nome_p = st.text_input("Nome do Pilar").upper() if pilar_alvo == "+ NOVO PILAR" else pilar_alvo
            
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_proxima = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inverter = (cam_proxima % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                lista_bebidas = ["Vazio"] + df_prod['Nome'].tolist()
                bebidas, avulsos = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    st.write("⬅️ ATRÁS")
                    for i in range(n_atras):
                        pos = i + 1
                        bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp{pos}{nome_p}{cam_proxima}")
                        avulsos[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap{pos}{nome_p}{cam_proxima}")
                with c2:
                    st.write("➡️ FRENTE")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp{pos}{nome_p}{cam_proxima}")
                        avulsos[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap{pos}{nome_p}{cam_proxima}")
                
                if st.button(f"💾 Salvar Camada no {nome_p}"):
                    novos = [[f"{nome_p}_{cam_proxima}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_proxima, p, beb, avulsos[p]] for p, beb in bebidas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: +Camada {cam_proxima} em {nome_p}")
                        st.rerun()

        for pilar_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pilar_nome}", expanded=True):
                for cam in sorted(df_pilar[df_pilar['NomePilar'] == pilar_nome]['Camada'].unique(), reverse=True):
                    st.write(f"**Camada {cam}**")
                    dados = df_pilar[(df_pilar['NomePilar'] == pilar_nome) & (df_pilar['Camada'] == cam)]
                    col_p = st.columns(5)
                    for _, r in dados.iterrows():
                        with col_p[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#262730; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;">{r["Bebida"]}<br>+{r["Avulsos"]} Av</div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"ret_{r['ID']}"):
                                q_p, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                total = q_p + r['Avulsos']
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"RETIRADA: {total}un de {r['Bebida']}")
                                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            p_alvo = st.selectbox("Produto", df_prod['Nome'].unique())
            un_cat, termo = obter_dados_categoria(p_alvo, df_prod)
            with st.form("entrada"):
                st.info(f"Padrão: {un_cat} por {termo}")
                c1, c2, c3 = st.columns(3)
                u_por_f = c1.number_input(f"Un por {termo}", value=un_cat)
                q_f = c2.number_input(f"Qtd {termo}s", 0)
                q_a = c3.number_input("Avulsos", 0)
                if st.form_submit_button("Lançar"):
                    total = (q_f * u_por_f) + q_a
                    df_e.loc[df_e['Nome'] == p_alvo, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: {total}un de {p_alvo}")
                    st.rerun()
        st.dataframe(df_e)

    # --- ABA: CADASTRO DE PRODUTOS (COM REMOÇÃO) ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos")
        
        # Parte 1: Formulário de Cadastro
        with st.form("cad_p", clear_on_submit=True):
            st.subheader("Cadastrar Novo")
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nom = c2.text_input("Nome").upper().strip()
            f_pre = c3.number_input("Preço", 0.0)
            
            if st.form_submit_button("Cadastrar"):
                if f_nom != "" and f_nom not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[f_cat, f_nom, f_pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"CADASTRO: {f_nom}")
                    st.success(f"{f_nom} salvo!")
                    st.rerun()
                elif f_nom in df_prod['Nome'].values:
                    st.warning("Este produto já existe.")

        st.write("---")
        
        # Parte 2: Lista de Produtos com Opção de Remover
        st.subheader("📋 Produtos Cadastrados")
        if not df_prod.empty:
            for i, row in df_prod.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                col1.write(f"**{row['Nome']}**")
                col2.write(f"{row['Categoria']}")
                col3.write(f"R$ {row['Preco_Unitario']:.2f}")
                
                # Botão de Excluir
                if col4.button("🗑️", key=f"del_{row['Nome']}"):
                    # Remove de Produtos
                    df_prod = df_prod[df_prod['Nome'] != row['Nome']]
                    df_prod.to_csv(DB_PRODUTOS, index=False)
                    # Remove do Estoque
                    df_e = df_e[df_e['Nome'] != row['Nome']]
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    
                    registrar_log(nome_logado, f"REMOÇÃO: {row['Nome']} excluído do sistema")
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        with st.form("cas"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cl, f_te = c1.text_input("Cliente").upper(), c2.text_input("Tel")
            f_va, f_qt = c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("Salvar"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), f_cl, f_te, f_va, f_qt, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"r{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("✅ Recebidos (Estorno)")
        for i, r in df_cascos[df_cascos['Status'] == "PAGO"].tail(5).iterrows():
            rc1, rc2 = st.columns([7, 2])
            rc1.info(f"OK: {r['QuemBaixou']} | {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
            if rc2.button("🚫 ESTORNAR", key=f"e{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.at[i, 'QuemBaixou'] = ""
                df_cascos.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # --- ABAS FINANCEIRO / HISTÓRICO / EQUIPE ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total", f"R$ {df_fin['Total'].sum():,.2f}")
        st.dataframe(df_fin)

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        with st.form("eq"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users)
