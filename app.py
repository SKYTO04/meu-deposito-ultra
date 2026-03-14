import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO DE INTERFACE E ESTILO
# =================================================================
st.set_page_config(
    page_title="Depósito Pacaembu - GESTÃO TOTAL v61", 
    page_icon="🍻", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização para os cards dos pilares e alertas
st.markdown("""
    <style>
    .pilar-container {
        background-color: #121212;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    .stMetric {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E ARQUIVOS (INFRAESTRUTURA)
# =================================================================
DB_PRODUTOS = "produtos_v61.csv"
DB_ESTOQUE = "estoque_v61.csv"
PILAR_ESTRUTURA = "pilares_v61.csv"
USERS_FILE = "usuarios_v61.csv"
LOG_FILE = "historico_v61.csv"
CASCOS_FILE = "cascos_v61.csv"

def inicializar_sistema():
    """Garante que todos os arquivos existam e tenham as colunas corretas"""
    # Criar arquivo de usuários com suporte a foto (Base64)
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
    # Estruturas padrão
    tabelas = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=cols).to_csv(arq, index=False)
    
    # Migração: Garantir que a coluna 'foto' existe no CSV de usuários
    df_u = pd.read_csv(USERS_FILE)
    if 'foto' not in df_u.columns:
        df_u['foto'] = ''
        df_u.to_csv(USERS_FILE, index=False)

inicializar_sistema()

# =================================================================
# 3. FUNÇÕES AUXILIARES DE LÓGICA
# =================================================================
def registrar_acao(usuario, texto):
    """Grava logs com data e hora exata (segundos)"""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[agora, usuario, texto]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def processar_imagem_perfil(file):
    """Converte foto da galeria para string Base64 para salvar no CSV"""
    if file:
        img = Image.open(file)
        img.thumbnail((150, 150)) # Reduz tamanho para otimizar desempenho
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    return ""

def regra_unidades(nome_prod, df_p):
    """Define quantas unidades vem em cada fardo/engradado conforme a categoria"""
    busca = df_p[df_p['Nome'] == nome_prod]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Long Neck": return 24, "Fardo"
    return 12, "Fardo"

# =================================================================
# 4. SISTEMA DE LOGIN SEGURO
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso - Depósito Pacaembu")
    with st.container():
        with st.form("form_login"):
            u_input = st.text_input("Usuário")
            s_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                df_u = pd.read_csv(USERS_FILE)
                validacao = df_u[(df_u['user'] == u_input) & (df_u['senha'].astype(str) == s_input)]
                if not validacao.empty:
                    st.session_state['autenticado'] = True
                    st.session_state['u_login'] = u_input
                    st.session_state['u_nome'] = validacao['nome'].values[0]
                    st.session_state['u_admin'] = (validacao['is_admin'].values[0] == 'SIM')
                    registrar_acao(st.session_state['u_nome'], "Login realizado")
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")
else:
    # --- VARIÁVEIS DE SESSÃO ATIVAS ---
    login_atual = st.session_state['u_login']
    nome_atual = st.session_state['u_nome']
    is_admin = st.session_state['u_admin']

    # Carregamento de dados
    df_p = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilares = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)
    df_users = pd.read_csv(USERS_FILE)

    # --- SIDEBAR COM FOTO DINÂMICA ---
    st.sidebar.markdown("---")
    try:
        foto_b64 = df_users[df_users['user'] == login_atual]['foto'].values[0]
        if pd.isna(foto_b64) or foto_b64 == "":
            st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
        else:
            st.sidebar.image(f"data:image/png;base64,{foto_b64}", width=100)
    except:
        st.sidebar.warning("Erro ao carregar foto.")

    st.sidebar.subheader(f"Bem-vindo, {nome_atual}")
    
    opcoes = ["🏗️ Pilares", "🍻 Romarinhos", "📦 Estoque (Entrada)", "✨ Cadastro", "🍶 Vasilhames (Cascos)", "⚙️ Meu Perfil"]
    if is_admin:
        opcoes += ["📊 Financeiro", "📜 Histórico Completo", "👥 Gestão de Equipe"]
    
    menu = st.sidebar.radio("Selecione a ferramenta:", opcoes)

    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: MEU PERFIL (FOTO DA GALERIA) ---
    if menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações do meu Usuário")
        st.write(f"Você está logado como: **{login_atual}**")
        
        foto_escolhida = st.file_uploader("Escolha uma foto da sua Galeria", type=['png', 'jpg', 'jpeg'])
        if st.button("💾 Atualizar minha Foto"):
            if foto_escolhida:
                b64_resultado = processar_imagem_perfil(foto_escolhida)
                df_users.loc[df_users['user'] == login_atual, 'foto'] = b64_resultado
                df_users.to_csv(USERS_FILE, index=False)
                st.success("Foto salva! Atualizando...")
                st.rerun()
            else:
                st.info("Por favor, selecione um arquivo primeiro.")

    # --- ABA: GESTÃO DE PILARES (DETALHADA) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares e Camadas")
        
        with st.expander("🆕 Criar Nova Camada no Pilar"):
            p_lista = ["+ NOVO PILAR"] + list(df_pilares['NomePilar'].unique())
            p_alvo = st.selectbox("Escolha o Pilar", p_lista)
            nome_pilar = st.text_input("Nome do Pilar").upper() if p_alvo == "+ NOVO PILAR" else p_alvo
            
            if nome_pilar:
                d_pilar = df_pilares[df_pilares['NomePilar'] == nome_pilar]
                cam_n = 1 if d_pilar.empty else d_pilar['Camada'].max() + 1
                
                # Lógica de Amarração (Intercala 3-2 e 2-3)
                inverter = (cam_n % 2 == 0)
                q_atras, q_frente = (3, 2) if not inverter else (2, 3)
                
                lista_refri = ["Vazio"] + df_p[df_p['Categoria'] == "Refrigerante"]['Nome'].tolist()
                bebidas_f, avulsos_f = {}, {}
                
                st.write(f"### Configurando Camada {cam_n}")
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Trás**")
                    for i in range(q_atras):
                        pos = i + 1
                        bebidas_f[pos] = st.selectbox(f"Produto P{pos}", lista_refri, key=f"p{pos}{cam_n}")
                        avulsos_f[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_n}")
                with c2:
                    st.write("**Frente**")
                    for i in range(q_frente):
                        pos = q_atras + i + 1
                        bebidas_f[pos] = st.selectbox(f"Produto P{pos}", lista_refri, key=f"p{pos}{cam_n}")
                        avulsos_f[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_n}")
                
                if st.button(f"💾 Confirmar Camada {cam_n}"):
                    novos_registros = []
                    for pos, beb in bebidas_f.items():
                        if beb != "Vazio":
                            id_u = f"{nome_pilar}_{cam_n}_{pos}_{datetime.now().strftime('%S')}"
                            novos_registros.append([id_u, nome_pilar, cam_n, pos, beb, avulsos_f[pos]])
                    
                    if novos_registros:
                        df_pilares = pd.concat([df_pilares, pd.DataFrame(novos_registros, columns=df_pilares.columns)])
                        df_pilares.to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_atual, f"PILAR: Criou Camada {cam_n} em {nome_pilar}")
                        st.rerun()

        # Visualização e Retirada
        for pilar in df_pilares['NomePilar'].unique():
            with st.container():
                st.markdown(f"### 📍 Pilar: {pilar}")
                camadas = sorted(df_pilares[df_pilares['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
                for c in camadas:
                    st.write(f"Camada {c}")
                    dados_c = df_pilares[(df_pilares['NomePilar'] == pilar) & (df_pilares['Camada'] == c)]
                    cols_visual = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols_visual[int(row['Posicao'])-1]:
                            st.info(f"**{row['Bebida']}**\n+{row['Avulsos']} un")
                            if st.button("RETIRAR", key=f"ret_{row['ID']}"):
                                base_un, _ = regra_unidades(row['Bebida'], df_p)
                                total_retirada = base_un + row['Avulsos']
                                # Baixa no estoque
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_retirada
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                # Remove do pilar
                                df_pilares = df_pilares[df_pilares['ID'] != row['ID']]
                                df_pilares.to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_acao(nome_atual, f"PILAR: Retirada de {total_retirada}un de {row['Bebida']}")
                                st.rerun()

    # --- ABA: ROMARINHOS (ENGRADADO E UNIDADE) ---
    elif menu == "🍻 Romarinhos":
        st.title("🍻 Baixa Rápida de Romarinhos")
        df_rom = df_p[df_p['Categoria'] == "Romarinho"]
        for _, r in df_rom.iterrows():
            est_atual = df_e[df_e['Nome'] == r['Nome']]['Estoque_Total_Un'].values[0]
            col_n, col_m, col_b1, col_b2 = st.columns([3, 2, 2, 2])
            col_n.subheader(r['Nome'])
            col_m.metric("Saldo", f"{est_atual//24} Eng | {est_atual%24} un")
            if col_b1.button(f"➖ ENGRADADO (24)", key=f"e_{r['Nome']}"):
                if est_atual >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_acao(nome_atual, f"SAÍDA: 1 Engradado {r['Nome']}")
                    st.rerun()
            if col_b2.button(f"➖ UNIDADE (1)", key=f"u_{r['Nome']}"):
                if est_atual >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_acao(nome_atual, f"SAÍDA: 1 Avulso {r['Nome']}")
                    st.rerun()

    # --- ABA: VASILHAMES (COM HISTÓRICO E ESTORNO) ---
    elif menu == "🍶 Vasilhames (Cascos)":
        st.title("🍶 Controle de Vasilhames e Cascos")
        
        with st.form("form_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cli = c1.text_input("Cliente").upper()
            f_tel = c2.text_input("Celular")
            f_tipo = c3.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "600ml"])
            f_qtd = c4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar Devedor"):
                novo_id = f"C{datetime.now().strftime('%M%S')}"
                data_h = datetime.now().strftime("%d/%m %H:%M")
                df_cascos = pd.concat([df_cascos, pd.DataFrame([[novo_id, data_h, f_cli, f_tel, f_tipo, f_qtd, "DEVE", ""]], columns=df_cascos.columns)])
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_acao(nome_atual, f"CASCO: {f_cli} deve {f_qtd} {f_tipo}")
                st.rerun()

        st.subheader("⚠️ Clientes Pendentes")
        for idx, row in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            l1, l2 = st.columns([7, 2])
            l1.warning(f"**{row['Cliente']}** deve {row['Quantidade']}x {row['Vasilhame']} ({row['Data']})")
            if l2.button("BAIXAR / PAGOU", key=f"bx_{row['ID']}"):
                df_cascos.at[idx, 'Status'] = "PAGO"
                df_cascos.at[idx, 'QuemBaixou'] = nome_atual
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_acao(nome_atual, f"CASCO: Recebido de {row['Cliente']}")
                st.rerun()

        st.write("---")
        st.subheader("📜 Histórico de Devoluções (Estorno)")
        # Mostra os últimos 10 que pagaram para caso precise desfazer
        df_recentes = df_cascos[df_cascos['Status'] == "PAGO"].tail(10)
        if not df_recentes.empty:
            for idx, row in df_recentes.iloc[::-1].iterrows():
                e1, e2 = st.columns([7, 2])
                e1.info(f"RECEBIDO: {row['Cliente']} - {row['Quantidade']} {row['Vasilhame']} (Baixa por: {row['QuemBaixou']})")
                if e2.button("🚫 ESTORNAR", key=f"est_{row['ID']}"):
                    df_cascos.at[idx, 'Status'] = "DEVE"
                    df_cascos.at[idx, 'QuemBaixou'] = ""
                    df_cascos.to_csv(CASCOS_FILE, index=False)
                    registrar_acao(nome_atual, f"ESTORNO: Casco de {row['Cliente']} voltou para devedor")
                    st.rerun()

    # --- ABA: ESTOQUE (ENTRADA) ---
    elif menu == "📦 Estoque (Entrada)":
        st.title("📦 Lançar Entrada de Caminhão")
        if not df_p.empty:
            p_sel = st.selectbox("Selecione o Produto", df_p['Nome'].unique())
            un_base, tipo_un = regra_unidades(p_sel, df_p)
            with st.form("form_est"):
                st.write(f"Padrão para este item: **{un_base} unidades por {tipo_un}**")
                c1, c2 = st.columns(2)
                f_qtd_fardo = c1.number_input(f"Qtd de {tipo_un}s", 0)
                f_qtd_un = c2.number_input("Unidades Soltas", 0)
                if st.form_submit_button("Lançar no Sistema"):
                    total_entrada = (f_qtd_fardo * un_base) + f_qtd_un
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total_entrada
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_acao(nome_atual, f"ENTRADA: +{total_entrada}un de {p_sel}")
                    st.rerun()
        st.subheader("Estoque Atual")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Itens")
        with st.form("form_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nome = c2.text_input("Nome do Produto").upper().strip()
            f_preco = c3.number_input("Preço de Venda", 0.0)
            if st.form_submit_button("Cadastrar Produto"):
                if f_nome and f_nome not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[f_cat, f_nome, f_preco]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_acao(nome_atual, f"CADASTRO: Criou {f_nome}")
                    st.rerun()

        st.write("---")
        for idx, row in df_p.iterrows():
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{row['Nome']}** | {row['Categoria']} | R$ {row['Preco_Unitario']}")
            if col2.button("🗑️", key=f"del_{row['Nome']}"):
                df_p[df_p['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != row['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ABAS DE ADMINISTRADOR ---
    elif menu == "📊 Financeiro" and is_admin:
        st.title("📊 Avaliação de Estoque")
        df_fin = pd.merge(df_e, df_p, on='Nome')
        df_fin['Valor_Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Patrimônio Total em Bebidas", f"R$ {df_fin['Valor_Total'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    elif menu == "📜 Histórico Completo" and is_admin:
        st.title("📜 Logs de Auditoria")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "👥 Gestão de Equipe" and is_admin:
        st.title("👥 Funcionários")
        with st.form("form_equipe"):
            u1, u2, u3, u4, u5 = st.columns(5)
            n_login = u1.text_input("Login")
            n_nome = u2.text_input("Nome")
            n_senha = u3.text_input("Senha")
            n_tel = u4.text_input("Telefone")
            n_adm = u5.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Adicionar Membro"):
                pd.concat([df_users, pd.DataFrame([[n_login, n_nome, n_senha, n_adm, n_tel, ""]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users[['user', 'nome', 'is_admin', 'telefone']])
