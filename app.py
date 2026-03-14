import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão Bruta", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v49) ---
DB_PRODUTOS = "produtos_v49.csv"
DB_ESTOQUE = "estoque_v49.csv"
PILAR_ESTRUTURA = "pilares_v49.csv"
USERS_FILE = "usuarios_v49.csv"
LOG_FILE = "historico_v49.csv"
CASCOS_FILE = "cascos_v49.csv"

def init_files():
    """Garante que todos os arquivos existam com as colunas corretas desde o início"""
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

# --- FUNÇÕES DE APOIO ---
def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    """Define automaticamente a quantidade de unidades por engradado/fardo"""
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
                registrar_log(st.session_state['name'], "Realizou Login")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
else:
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']

    # --- MENU LATERAL ---
    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair / Logout"):
        registrar_log(nome_logado, "Realizou Logout")
        st.session_state['autenticado'] = False
        st.rerun()

    menu_options = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_options)

    # Carregar Bancos de Dados para as abas
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: GESTÃO DE PILARES (DINÂMICOS) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares Dinâmicos")
        
        with st.expander("🆕 Criar Novo Pilar ou Adicionar Camada"):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_alvo = st.selectbox("Selecione o Pilar", pilares_existentes)
            
            if pilar_alvo == "+ NOVO PILAR":
                nome_p = st.text_input("Nome do Novo Pilar (ex: COCA 2L)").upper()
            else:
                nome_p = pilar_alvo
            
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_proxima = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Lógica de Amarração (Inverte a cada camada do pilar específico)
                inverter = (cam_proxima % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                st.subheader(f"Configurando Camada {cam_proxima} de {nome_p}")
                st.info(f"Amarração: {'Invertida (2 atrás, 3 frente)' if inverter else 'Normal (3 atrás, 2 frente)'}")
                
                lista_bebidas = ["Vazio"] + df_prod['Nome'].tolist()
                escolhas_bebida = {}
                escolhas_avulso = {}
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("⬅️ ATRÁS")
                    for i in range(n_atras):
                        pos = i + 1
                        escolhas_bebida[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"b{pos}{nome_p}{cam_proxima}")
                        escolhas_avulso[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{nome_p}{cam_proxima}")
                with c2:
                    st.write("➡️ FRENTE")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        escolhas_bebida[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"b{pos}{nome_p}{cam_proxima}")
                        escolhas_avulso[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{nome_p}{cam_proxima}")
                
                if st.button(f"💾 Salvar Camada no pilar {nome_p}"):
                    novos_itens = []
                    for pos, beb in escolhas_bebida.items():
                        if beb != "Vazio":
                            id_gerado = f"{nome_p}_{cam_proxima}_{pos}_{datetime.now().strftime('%S')}"
                            novos_itens.append([id_gerado, nome_p, cam_proxima, pos, beb, escolhas_avulso[pos]])
                    
                    if novos_itens:
                        pd.concat([df_pilar, pd.DataFrame(novos_itens, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: Adicionou Camada {cam_proxima} em {nome_p}")
                        st.success("Camada adicionada!")
                        st.rerun()

        # Visualização de todos os pilares
        for pilar_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pilar_nome}", expanded=True):
                camadas_pilar = sorted(df_pilar[df_pilar['NomePilar'] == pilar_nome]['Camada'].unique(), reverse=True)
                for cam in camadas_pilar:
                    st.write(f"**Camada {cam}**")
                    dados_camada = df_pilar[(df_pilar['NomePilar'] == pilar_nome) & (df_pilar['Camada'] == cam)]
                    col_pilars = st.columns(5)
                    for _, r in dados_camada.iterrows():
                        with col_pilars[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#262730; border:2px solid #4CAF50; padding:10px; border-radius:10px; text-align:center;"><b>{r["Bebida"]}</b><br><span style="color:#FFD700;">+{r["Avulsos"]} Avulsos</span></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"btn_{r['ID']}"):
                                # BAIXA AUTOMÁTICA NO ESTOQUE
                                q_p, termo = obter_dados_categoria(r['Bebida'], df_prod)
                                total_unidades = q_p + r['Avulsos']
                                
                                # Atualiza Estoque
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_unidades
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                # Remove do Pilar
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                # Log
                                registrar_log(nome_logado, f"RETIRADA: {total_unidades}un de {r['Bebida']} ({pilar_nome})")
                                st.rerun()

    # --- ABA: CASCOS (TELEFONE + ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("form_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cli = c1.text_input("Cliente").upper()
            f_tel = c2.text_input("Telefone")
            f_vas = c3.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            f_qtd = c4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar"):
                if f_cli:
                    nid = f"C{datetime.now().strftime('%M%S')}"
                    novo_casco = pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), f_cli, f_tel, f_vas, f_qtd, "DEVE", ""]], columns=df_cascos.columns)
                    pd.concat([df_cascos, novo_casco]).to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"CASCO: {f_cli} ({f_tel}) deve {f_qtd} {f_vas}")
                    st.rerun()

        st.subheader("⚠️ Pendentes de Devolução")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"rec_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Recebeu vasilhame de {r['Cliente']}")
                st.rerun()

        st.write("---")
        st.subheader("✅ Recebidos Recentemente (Controle de Erro)")
        recebidos = df_cascos[df_cascos['Status'] == "PAGO"].tail(5)
        for i, r in recebidos.iterrows():
            rc1, rc2 = st.columns([7, 2])
            rc1.info(f"Baixa: {r['QuemBaixou']} | {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
            if rc2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.at[i, 'QuemBaixou'] = ""
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"ESTORNO: Erro na baixa de {r['Cliente']}, voltou a dever")
                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            p_alvo = st.selectbox("Escolha o Produto", df_prod['Nome'].unique())
            un_cat, termo = obter_dados_categoria(p_alvo, df_prod)
            with st.form("entrada_est"):
                c1, c2 = st.columns(2)
                q_fardos = c1.number_input(f"Qtd de {termo}s", 0)
                q_avulsos = c2.number_input("Unidades Avulsas", 0)
                if st.form_submit_button("Confirmar Entrada"):
                    total = (q_fardos * un_cat) + q_avulsos
                    df_e.loc[df_e['Nome'] == p_alvo, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: {total}un de {p_alvo}")
                    st.success(f"Adicionado {total}un ao estoque!")
                    st.rerun()
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro de Novos Produtos")
        with st.form("cad_produto"):
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nom = c2.text_input("Nome do Produto").upper()
            f_pre = c3.number_input("Preço Unitário", 0.0)
            if st.form_submit_button("Cadastrar"):
                if f_nom and f_nom not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[f_cat, f_nom, f_pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"CADASTRO: Criou {f_nom}")
                    st.rerun()

        st.subheader("📋 Produtos Cadastrados")
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4, 3, 1])
            cc1.write(f"**{row['Nome']}** ({row['Categoria']})")
            cc2.write(f"R$ {row['Preco_Unitario']:.2f}")
            if cc3.button("Excluir", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"EXCLUSÃO: Deletou {row['Nome']}")
                st.rerun()

    # --- ABA: FINANCEIRO (ADM) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Estoque'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total em Mercadoria", f"R$ {df_fin['Valor_Estoque'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    # --- ABA: HISTÓRICO (ADM) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico de Ações")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- ABA: EQUIPE (ADM) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Usuários")
        with st.form("form_user"):
            u, n, s, t, a = st.columns(5)
            n_u, n_n, n_s, n_t, n_a = u.text_input("Login"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar Usuário"):
                pd.concat([df_users, pd.DataFrame([[n_u, n_n, n_s, n_a, n_t]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                registrar_log(nome_logado, f"EQUIPE: Criou conta para {n_n}")
                st.rerun()
        st.dataframe(df_users)
