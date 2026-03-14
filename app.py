import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO DE INTERFACE
# =================================================================
st.set_page_config(
    page_title="Depósito Pacaembu - v63 FULL ESTOQUE", 
    page_icon="🍻", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================================
# 2. BANCO DE DADOS (INFRAESTRUTURA REAL)
# =================================================================
DB_PRODUTOS = "produtos_v63.csv"
DB_ESTOQUE = "estoque_v63.csv"
PILAR_ESTRUTURA = "pilares_v63.csv"
USERS_FILE = "usuarios_v63.csv"
LOG_FILE = "historico_v63.csv"
CASCOS_FILE = "cascos_v63.csv"

def garantir_banco_dados():
    """Cria e verifica a integridade de todos os arquivos e colunas"""
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
    tabelas_necessarias = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, cols in tabelas_necessarias.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=cols).to_csv(arq, index=False)
    
    # Check migração de foto
    df_u = pd.read_csv(USERS_FILE)
    if 'foto' not in df_u.columns:
        df_u['foto'] = ''
        df_u.to_csv(USERS_FILE, index=False)

garantir_banco_dados()

# --- FUNÇÕES DE LÓGICA BRUTA ---
def registrar_log(user, acao):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[agora, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def imagem_base64(file):
    if file:
        img = Image.open(file)
        img.thumbnail((150, 150))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    return ""

def unidades_por_categoria(produto_nome, df_p):
    """Retorna a quantidade padrão de unidades por fardo/engradado"""
    filtro = df_p[df_p['Nome'] == produto_nome]
    if not filtro.empty:
        cat = filtro['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. CONTROLE DE ACESSO (PROTEÇÃO KEYERROR)
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("form_login"):
        u_box = st.text_input("Usuário")
        s_box = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema"):
            df_users_db = pd.read_csv(USERS_FILE)
            validacao = df_users_db[(df_users_db['user'] == u_box) & (df_users_db['senha'].astype(str) == s_box)]
            if not validacao.empty:
                st.session_state.update({
                    'autenticado': True,
                    'u_login': u_box,
                    'u_nome': validacao['nome'].values[0],
                    'u_admin': (validacao['is_admin'].values[0] == 'SIM')
                })
                registrar_log(st.session_state['u_nome'], "Acesso concedido")
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos.")
else:
    # --- VARIÁVEIS SEGURAS ---
    user_logado = st.session_state.get('u_login')
    nome_logado = st.session_state.get('u_nome')
    adm_privilegio = st.session_state.get('u_admin')

    # Redirecionamento de segurança caso a sessão expire
    if user_logado is None:
        st.session_state['autenticado'] = False
        st.rerun()

    # CARREGAMENTO DOS DADOS ATUAIS
    df_p = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pil = pd.read_csv(PILAR_ESTRUTURA)
    df_cas = pd.read_csv(CASCOS_FILE)
    df_usr = pd.read_csv(USERS_FILE)

    # --- SIDEBAR COM FOTO DA GALERIA ---
    st.sidebar.markdown("---")
    try:
        foto_data = df_usr[df_usr['user'] == user_logado]['foto'].values[0]
        if pd.isna(foto_data) or foto_data == "":
            st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
        else:
            st.sidebar.image(f"data:image/png;base64,{foto_data}", width=100)
    except:
        st.sidebar.warning("Foto não carregada.")
    
    st.sidebar.title(f"👤 {nome_logado}")
    
    opcoes_menu = ["🏗️ Pilares", "🍻 Romarinhos", "📦 Estoque (Entrada)", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"]
    if adm_privilegio:
        opcoes_menu += ["📊 Financeiro", "📜 Histórico", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação:", opcoes_menu)

    if st.sidebar.button("Logoff"):
        st.session_state['autenticado'] = False
        st.rerun()

    # =================================================================
    # ABA: ROMARINHOS (LÓGICA DE BAIXA FUNCIONAL)
    # =================================================================
    if menu == "🍻 Romarinhos":
        st.title("🍻 Baixa Real de Romarinhos")
        st.info("As baixas feitas aqui descontam automaticamente do estoque central.")
        
        df_rom_only = df_p[df_p['Categoria'] == "Romarinho"]
        
        if df_rom_only.empty:
            st.warning("Nenhum Romarinho cadastrado no sistema.")
        else:
            for _, item in df_rom_only.iterrows():
                # Busca o estoque exato deste item
                estoque_item = df_e[df_e['Nome'] == item['Nome']]
                
                if not estoque_item.empty:
                    unidades_totais = int(estoque_item['Estoque_Total_Un'].values[0])
                    engradados = unidades_totais // 24
                    avulsos = unidades_totais % 24
                    
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.markdown(f"### {item['Nome']}")
                    c2.metric("Estoque", f"{engradados} Eng | {avulsos} un")
                    
                    # BOTÃO BAIXA ENGRADADO
                    if c3.button(f"➖ ENGRADADO", key=f"eng_{item['Nome']}"):
                        if unidades_totais >= 24:
                            nova_qtd = unidades_totais - 24
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] = nova_qtd
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_logado, f"BAIXA ROMARINHO: -1 Engradado de {item['Nome']}")
                            st.success(f"Engradado de {item['Nome']} retirado!")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente!")

                    # BOTÃO BAIXA UNIDADE
                    if c4.button(f"➖ UNIDADE", key=f"uni_{item['Nome']}"):
                        if unidades_totais >= 1:
                            nova_qtd = unidades_totais - 1
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] = nova_qtd
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_logado, f"BAIXA ROMARINHO: -1 Unidade de {item['Nome']}")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente!")
                st.write("---")

    # =================================================================
    # ABA: PERFIL (FOTO DA GALERIA)
    # =================================================================
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Gerenciar Perfil")
        upload = st.file_uploader("Escolha sua foto na galeria do celular", type=['png', 'jpg', 'jpeg'])
        if st.button("💾 Salvar Foto de Perfil"):
            if upload:
                b64_img = imagem_base64(upload)
                df_usr.loc[df_usr['user'] == user_logado, 'foto'] = b64_img
                df_usr.to_csv(USERS_FILE, index=False)
                st.success("Foto atualizada com sucesso!")
                st.rerun()

    # =================================================================
    # ABA: PILARES (ESTRUTURA BRUTA)
    # =================================================================
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Controle de Pilares (Refri)")
        with st.expander("🆕 Nova Camada"):
            pilar_alvo = st.selectbox("Pilar", ["+ NOVO PILAR"] + list(df_pil['NomePilar'].unique()))
            nome_p = st.text_input("Nome").upper() if pilar_alvo == "+ NOVO PILAR" else pilar_alvo
            if nome_p:
                dados_p = df_pil[df_pil['NomePilar'] == nome_p]
                cam_n = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inv = (cam_n % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                beb_list = ["Vazio"] + df_p[df_p['Categoria'] == "Refrigerante"]['Nome'].tolist()
                b_form, a_form = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    for i in range(at):
                        p = i+1
                        b_form[p] = st.selectbox(f"Bebida P{p}", beb_list, key=f"p{p}{cam_n}")
                        a_form[p] = st.number_input(f"Av P{p}", 0, key=f"a{p}{cam_n}")
                with c2:
                    for i in range(fr):
                        p = at+i+1
                        b_form[p] = st.selectbox(f"Bebida P{p}", beb_list, key=f"p{p}{cam_n}")
                        a_form[p] = st.number_input(f"Av P{p}", 0, key=f"a{p}{cam_n}")
                if st.button("Confirmar Camada"):
                    regs = [[f"{nome_p}_{cam_n}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_n, p, b, a_form[p]] for p, b in b_form.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        for pn in df_pil['NomePilar'].unique():
            st.subheader(f"📍 {pn}")
            for c in sorted(df_pil[df_pil['NomePilar'] == pn]['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                dados = df_pil[(df_pil['NomePilar'] == pn) & (df_pil['Camada'] == c)]
                cols = st.columns(5)
                for _, r in dados.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.info(f"{r['Bebida']}\n+{r['Avulsos']}un")
                        if st.button("RETIRAR", key=f"ret_pil_{r['ID']}"):
                            base_u, _ = unidades_por_categoria(r['Bebida'], df_p)
                            total_r = base_u + r['Avulsos']
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_r
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                            registrar_log(nome_logado, f"PILAR: Retirada {total_r}un de {r['Bebida']}")
                            st.rerun()

    # =================================================================
    # ABA: CASCOS (ESTORNO E HISTÓRICO)
    # =================================================================
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("form_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            fcl, fte, fva, fqt = c1.text_input("Cliente").upper(), c2.text_input("Tel"), c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar Devedor"):
                novo_casco = [[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), fcl, fte, fva, fqt, "DEVE", ""]]
                pd.concat([df_cas, pd.DataFrame(novo_casco, columns=df_cas.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"**{r['Cliente']}** deve {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"rc_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"
                df_cas.at[i, 'QuemBaixou'] = nome_logado
                df_cas.to_csv(CASCOS_FILE, index=False)
                st.rerun()
        
        st.write("---")
        st.subheader("✅ Histórico de Baixas (Possibilidade de Estorno)")
        for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(5).iterrows():
            el1, el2 = st.columns([7, 2])
            el1.info(f"OK: {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
            if el2.button("🚫 ESTORNAR", key=f"es_{r['ID']}"):
                df_cas.at[i, 'Status'] = "DEVE"
                df_cas.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # =================================================================
    # ABA: ESTOQUE (ENTRADA)
    # =================================================================
    elif menu == "📦 Estoque (Entrada)":
        st.title("📦 Entrada de Mercadoria")
        if not df_p.empty:
            sel_prod = st.selectbox("Produto", df_p['Nome'].unique())
            u_padrao, t_tipo = unidades_por_categoria(sel_prod, df_p)
            with st.form("form_entrada"):
                st.info(f"Padrão: {u_padrao} unidades por {t_tipo}")
                f_qtd_p, f_qtd_a = st.columns(2)[0].number_input(f"Qtd {t_tipo}", 0), st.columns(2)[1].number_input("Avulsos", 0)
                if st.form_submit_button("Lançar no Estoque"):
                    total_entrada = (f_qtd_p * u_padrao) + f_qtd_a
                    df_e.loc[df_e['Nome'] == sel_prod, 'Estoque_Total_Un'] += total_entrada
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: +{total_entrada}un de {sel_prod}")
                    st.rerun()
        st.subheader("Situação Atual do Estoque")
        st.dataframe(df_e)

    # =================================================================
    # ABAS ADMINISTRATIVAS
    # =================================================================
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Novos Produtos")
        with st.form("form_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fcate = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            fnome = c2.text_input("Nome").upper().strip()
            fprec = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Cadastrar"):
                if fnome and fnome not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fcate, fnome, fprec]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[fnome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.write("---")
        for i, r in df_p.iterrows():
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']})")
            if col2.button("🗑️", key=f"del_{r['Nome']}"):
                df_p[df_p['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    elif menu == "📊 Financeiro" and adm_privilegio:
        st.title("📊 Valor de Estoque")
        df_f = pd.merge(df_e, df_p, on='Nome')
        df_f['Patrimônio'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("Total em Mercadoria", f"R$ {df_f['Patrimônio'].sum():,.2f}")
        st.dataframe(df_f)

    elif menu == "📜 Histórico" and adm_privilegio:
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "👥 Equipe" and adm_privilegio:
        st.title("👥 Funcionários")
        with st.form("form_equipe"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("Login"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Adicionar Membro"):
                pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_usr.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_usr[['user', 'nome', 'is_admin', 'telefone']])
