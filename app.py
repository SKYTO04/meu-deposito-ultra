import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão v56 EXTREME", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v56) ---
# Nomes de arquivos únicos para evitar conflitos de versões anteriores
DB_PRODUTOS = "produtos_v56.csv"
DB_ESTOQUE = "estoque_v56.csv"
PILAR_ESTRUTURA = "pilares_v56.csv"
USERS_FILE = "usuarios_v56.csv"
LOG_FILE = "historico_v56.csv"
CASCOS_FILE = "cascos_v56.csv"

def init_files():
    """Inicialização completa de todos os bancos de dados CSV"""
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
    """Registra cada movimento no sistema para auditoria"""
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    """Define as regras de negócio por categoria de produto"""
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
        if st.form_submit_button("Entrar no Sistema"):
            check = df_users[(df_users['user'] == u_in) & (df_users['senha'].astype(str) == s_in)]
            if not check.empty:
                st.session_state['autenticado'] = True
                st.session_state['username'] = u_in
                st.session_state['name'] = check['nome'].values[0]
                st.session_state['is_admin'] = check['is_admin'].values[0] == 'SIM'
                registrar_log(st.session_state['name'], "Realizou Login")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
else:
    # --- VARIÁVEIS DE SESSÃO ---
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']
    
    # --- SIDEBAR E NAVEGAÇÃO ---
    st.sidebar.title(f"👤 {nome_logado}")
    menu_options = ["🏗️ Gestão de Pilares", "🍻 Gestão Romarinho", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_options)
    
    if st.sidebar.button("Sair do Sistema"):
        st.session_state['autenticado'] = False
        st.rerun()

    # CARREGAMENTO DOS DADOS PARA AS ABAS
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: GESTÃO DE PILARES (FOCO EM COCA/REFRIGERANTES) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares (Refrigerantes)")
        
        with st.expander("🆕 Criar Novo Pilar ou Adicionar Camada"):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_alvo = st.selectbox("Selecione o Pilar", pilares_existentes)
            nome_p = st.text_input("Nome do Pilar").upper() if pilar_alvo == "+ NOVO PILAR" else pilar_alvo
            
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_proxima = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Regra de amarração: alterna 3/2 e 2/3
                inverter = (cam_proxima % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                # Somente categoria Refrigerante pode ser selecionada aqui
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                bebidas_escolhidas, avulsos_digitados = {}, {}
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("⬅️ POSIÇÕES ATRÁS")
                    for i in range(n_atras):
                        pos = i + 1
                        bebidas_escolhidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp_{nome_p}_{cam_proxima}_{pos}")
                        avulsos_digitados[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"ap_{nome_p}_{cam_proxima}_{pos}")
                with c2:
                    st.write("➡️ POSIÇÕES FRENTE")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        bebidas_escolhidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp_{nome_p}_{cam_proxima}_{pos}")
                        avulsos_digitados[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"ap_{nome_p}_{cam_proxima}_{pos}")
                
                if st.button(f"💾 Salvar Camada {cam_proxima} no {nome_p}"):
                    novos_dados = []
                    for p, beb in bebidas_escolhidas.items():
                        if beb != "Vazio":
                            id_camada = f"{nome_p}_{cam_proxima}_{p}_{datetime.now().strftime('%S')}"
                            novos_dados.append([id_camada, nome_p, cam_proxima, p, beb, avulsos_digitados[p]])
                    
                    if novos_dados:
                        pd.concat([df_pilar, pd.DataFrame(novos_dados, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: Adicionou Camada {cam_proxima} em {nome_p}")
                        st.rerun()

        # Visualização dos Pilares Ativos
        for pilar_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pilar_nome}", expanded=True):
                camadas_ord = sorted(df_pilar[df_pilar['NomePilar'] == pilar_nome]['Camada'].unique(), reverse=True)
                for cam in camadas_ord:
                    st.write(f"**Camada {cam}**")
                    dados_cam = df_pilar[(df_pilar['NomePilar'] == pilar_nome) & (df_pilar['Camada'] == cam)]
                    col_pil = st.columns(5)
                    for _, r in dados_cam.iterrows():
                        with col_pil[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#262730; border:2px solid #4CAF50; padding:10px; border-radius:10px; text-align:center;"><b>{r["Bebida"]}</b><br><span style="color:#FFD700;">+{r["Avulsos"]} Av</span></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"btn_ret_{r['ID']}"):
                                qtd_base, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                total_baixar = qtd_base + r['Avulsos']
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_baixar
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"PILAR: Retirada de {total_baixar}un de {r['Bebida']}")
                                st.rerun()

    # --- ABA: GESTÃO ROMARINHO (BAIXA DE ENGRADADO E AVULSO) ---
    elif menu == "🍻 Gestão Romarinho":
        st.title("🍻 Painel de Romarinho")
        st.info("Controle rápido para saída de engradados (24 un) ou garrafas avulsas.")
        
        df_roms = df_prod[df_prod['Categoria'] == "Romarinho"]
        if not df_roms.empty:
            for _, row in df_roms.iterrows():
                estoque_total = df_e[df_e['Nome'] == row['Nome']]['Estoque_Total_Un'].values[0]
                engradados_fechados = estoque_total // 24
                sobra_unidades = estoque_total % 24
                
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.subheader(row['Nome'])
                    c2.metric("No Estoque", f"{engradados_fechados} Eng. | {sobra_unidades} un")
                    
                    if c3.button(f"➖ REMOVER ENGRADADO", key=f"rem_eng_{row['Nome']}"):
                        if estoque_total >= 24:
                            df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 24
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_logado, f"ROMARINHO: Saiu 1 Engradado de {row['Nome']}")
                            st.rerun()
                        else:
                            st.error("Não há 1 engradado completo no estoque!")
                            
                    if c4.button(f"➖ REMOVER AVULSO", key=f"rem_avu_{row['Nome']}"):
                        if estoque_total >= 1:
                            df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 1
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_logado, f"ROMARINHO: Saiu 1 Unidade Avulsa de {row['Nome']}")
                            st.rerun()
                        else:
                            st.error("Estoque totalmente zerado!")
                st.write("---")
        else:
            st.warning("Nenhum produto cadastrado na categoria 'Romarinho'.")

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            p_alvo = st.selectbox("Escolha o Produto que chegou", df_prod['Nome'].unique())
            un_p_cat, termo_cat = obter_dados_categoria(p_alvo, df_prod)
            
            with st.form("form_entrada_estoque"):
                st.info(f"O sistema detectou: {termo_cat} ({un_p_cat} un por unidade de medida).")
                c1, c2, c3 = st.columns(3)
                f_un_base = c1.number_input(f"Unidades por {termo_cat}", value=un_p_cat)
                f_qtd_medida = c2.number_input(f"Quantidade de {termo_cat}s", 0)
                f_un_avulsas = c3.number_input("Unidades Avulsas (Soltas)", 0)
                
                if st.form_submit_button("Confirmar Entrada no Banco"):
                    total_entrando = (f_qtd_medida * f_un_base) + f_un_avulsas
                    df_e.loc[df_e['Nome'] == p_alvo, 'Estoque_Total_Un'] += total_entrando
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: +{total_entrando}un de {p_alvo}")
                    st.success(f"Estoque atualizado: +{total_entrando} unidades.")
                    st.rerun()
        st.subheader("Situação Geral do Estoque")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS (COM TRAVA E REMOÇÃO) ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Produtos do Depósito")
        
        with st.form("form_novo_produto", clear_on_submit=True):
            st.subheader("Cadastrar Novo Item")
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria do Produto", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nom = c2.text_input("Nome do Produto (Ex: COCA 2L)").upper().strip()
            f_pre = c3.number_input("Preço de Venda Unitário", 0.0)
            
            if st.form_submit_button("Salvar no Sistema"):
                if f_nom != "" and f_nom not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[f_cat, f_nom, f_pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"CADASTRO: Adicionou {f_nom}")
                    st.success(f"{f_nom} cadastrado com sucesso!")
                    st.rerun()
                elif f_nom in df_prod['Nome'].values:
                    st.error("ERRO: Este produto já está cadastrado!")

        st.write("---")
        st.subheader("📋 Todos os Produtos Cadastrados")
        for i, row in df_prod.iterrows():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
            col1.write(f"**{row['Nome']}**")
            col2.write(f"*{row['Categoria']}*")
            col3.write(f"R$ {row['Preco_Unitario']:.2f}")
            if col4.button("🗑️", key=f"del_prod_{row['Nome']}"):
                df_prod = df_prod[df_prod['Nome'] != row['Nome']]
                df_prod.to_csv(DB_PRODUTOS, index=False)
                df_e = df_e[df_e['Nome'] != row['Nome']]
                df_e.to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"REMOÇÃO: Excluiu {row['Nome']} do sistema")
                st.rerun()

    # --- ABA: CASCOS (CONTROLE DE VASILHAMES) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames e Cascos")
        with st.form("form_vasilhame"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cliente = c1.text_input("Nome do Cliente").upper()
            f_tel = c2.text_input("Telefone para Contato")
            f_tipo = c3.selectbox("Tipo de Vasilhame", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "Garrafa 600ml"])
            f_qtd_v = c4.number_input("Quantidade", 1)
            
            if st.form_submit_button("Registrar Dívida"):
                id_casco = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[id_casco, datetime.now().strftime("%d/%m %H:%M"), f_cliente, f_tel, f_tipo, f_qtd_v, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {f_cliente} ficou devendo {f_qtd_v} {f_tipo}")
                st.rerun()

        st.subheader("⚠️ Devedores Ativos")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("BAIXAR DÍVIDA", key=f"pay_casco_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {r['Cliente']} devolveu os vasilhames")
                st.rerun()

    # --- ABA: FINANCEIRO (SOMENTE ADMIN) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Avaliação de Patrimônio em Estoque")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        total_estoque = df_fin['Valor_Total'].sum()
        st.metric("Total Investido em Estoque", f"R$ {total_estoque:,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    # --- ABA: HISTÓRICO (SOMENTE ADMIN) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Log Completo de Atividades")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- ABA: EQUIPE (SOMENTE ADMIN) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Usuários")
        with st.form("form_equipe"):
            u, n, s, t, a = st.columns(5)
            nu = u.text_input("ID Login")
            nn = n.text_input("Nome Completo")
            ns = s.text_input("Senha")
            nt = t.text_input("Telefone")
            na = a.selectbox("Nível Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Cadastrar Funcionário"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users)
