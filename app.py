import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO INICIAL (Obrigatório ser a primeira linha)
# =================================================================
st.set_page_config(
    page_title="Depósito Pacaembu - v62 ULTRA COMPLETO", 
    page_icon="🍻", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS
# =================================================================
DB_PRODUTOS = "produtos_v62.csv"
DB_ESTOQUE = "estoque_v62.csv"
PILAR_ESTRUTURA = "pilares_v62.csv"
USERS_FILE = "usuarios_v62.csv"
LOG_FILE = "historico_v62.csv"
CASCOS_FILE = "cascos_v62.csv"

def init_db():
    """Cria arquivos e garante colunas de foto e dados"""
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
    arquivos = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)
    
    # Check de coluna 'foto' para evitar erros de versões antigas
    df_check = pd.read_csv(USERS_FILE)
    if 'foto' not in df_check.columns:
        df_check['foto'] = ''
        df_check.to_csv(USERS_FILE, index=False)

init_db()

# --- FUNÇÕES CORE ---
def log_sistema(user, acao):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[agora, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def converter_foto(file):
    if file:
        img = Image.open(file)
        img.thumbnail((150, 150))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    return ""

def get_unidades(prod, df_p):
    busca = df_p[df_p['Nome'] == prod]
    if not busca.empty:
        c = busca['Categoria'].values[0]
        if c == "Romarinho": return 24, "Engradado"
        if c == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. LÓGICA DE LOGIN (CORREÇÃO DO KEYERROR)
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_box"):
        u_field = st.text_input("Usuário")
        s_field = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            df_u = pd.read_csv(USERS_FILE)
            user_valid = df_u[(df_u['user'] == u_field) & (df_u['senha'].astype(str) == s_field)]
            if not user_valid.empty:
                st.session_state['autenticado'] = True
                st.session_state['u_login'] = u_field
                st.session_state['u_nome'] = user_valid['nome'].values[0]
                st.session_state['u_admin'] = (user_valid['is_admin'].values[0] == 'SIM')
                log_sistema(st.session_state['u_nome'], "Login realizado")
                st.rerun()
            else:
                st.error("Usuário ou Senha inválidos.")
else:
    # --- ACESSO SEGURO ÀS VARIÁVEIS ---
    login_atual = st.session_state.get('u_login')
    nome_atual = st.session_state.get('u_nome')
    sou_admin = st.session_state.get('u_admin')

    # Se por algum motivo as variáveis sumirem, força logout para evitar o KeyError
    if login_atual is None:
        st.session_state['autenticado'] = False
        st.rerun()

    # Carregar Bancos
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_est = pd.read_csv(DB_ESTOQUE)
    df_pil = pd.read_csv(PILAR_ESTRUTURA)
    df_cas = pd.read_csv(CASCOS_FILE)
    df_usr = pd.read_csv(USERS_FILE)

    # --- SIDEBAR COM FOTO DA GALERIA ---
    st.sidebar.markdown("---")
    foto_perfil = df_usr[df_usr['user'] == login_atual]['foto'].values[0]
    if pd.isna(foto_perfil) or foto_perfil == "":
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    else:
        st.sidebar.image(f"data:image/png;base64,{foto_perfil}", width=100)
    
    st.sidebar.subheader(f"Olá, {nome_atual}")
    
    menu = st.sidebar.radio("Navegação", 
        ["🏗️ Pilares", "🍻 Romarinhos", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"] + 
        (["📊 Financeiro", "📜 Logs", "👥 Equipe"] if sou_admin else []))

    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    # =================================================================
    # ABA: PERFIL (MUDAR FOTO PELA GALERIA)
    # =================================================================
    if menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        arquivo_foto = st.file_uploader("Escolha uma foto da sua Galeria", type=['png', 'jpg', 'jpeg'])
        if st.button("Salvar Foto"):
            if arquivo_foto:
                b64 = converter_foto(arquivo_foto)
                df_usr.loc[df_usr['user'] == login_atual, 'foto'] = b64
                df_usr.to_csv(USERS_FILE, index=False)
                st.success("Foto atualizada!")
                st.rerun()

    # =================================================================
    # ABA: PILARES (ESTRUTURA COMPLETA)
    # =================================================================
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🆕 Adicionar Camada"):
            pil_lista = ["+ NOVO"] + list(df_pil['NomePilar'].unique())
            sel_p = st.selectbox("Pilar", pil_lista)
            nome_p = st.text_input("Nome").upper() if sel_p == "+ NOVO" else sel_p
            if nome_p:
                cam_atual = 1 if df_pil[df_pil['NomePilar']==nome_p].empty else df_pil[df_pil['NomePilar']==nome_p]['Camada'].max() + 1
                inv = (cam_atual % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                lista_beb = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                bebidas, avulsos = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    for i in range(at):
                        p = i+1
                        bebidas[p] = st.selectbox(f"Bebida P{p}", lista_beb, key=f"b{p}{cam_atual}")
                        avulsos[p] = st.number_input(f"Av P{p}", 0, key=f"a{p}{cam_atual}")
                with c2:
                    for i in range(fr):
                        p = at+i+1
                        bebidas[p] = st.selectbox(f"Bebida P{p}", lista_beb, key=f"b{p}{cam_atual}")
                        avulsos[p] = st.number_input(f"Av P{p}", 0, key=f"a{p}{cam_atual}")
                if st.button("Gravar Camada"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, beb, avulsos[p]] for p, beb in bebidas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pil, pd.DataFrame(novos, columns=df_pil.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        for pilar in df_pil['NomePilar'].unique():
            st.subheader(f"📍 Pilar: {pilar}")
            for c in sorted(df_pil[df_pil['NomePilar']==pilar]['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                dados = df_pil[(df_pil['NomePilar']==pilar) & (df_pil['Camada']==c)]
                cols = st.columns(5)
                for _, r in dados.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.info(f"{r['Bebida']}\n+{r['Avulsos']}un")
                        if st.button("RETIRAR", key=f"rt_{r['ID']}"):
                            base, _ = get_unidades(r['Bebida'], df_prod)
                            df_est.loc[df_est['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (base + r['Avulsos'])
                            df_est.to_csv(DB_ESTOQUE, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                            st.rerun()

    # =================================================================
    # ABA: ROMARINHOS (BAIXA RÁPIDA)
    # =================================================================
    elif menu == "🍻 Romarinhos":
        st.title("🍻 Baixa de Romarinhos")
        for _, r in df_prod[df_prod['Categoria'] == "Romarinho"].iterrows():
            est_u = df_est[df_est['Nome'] == r['Nome']]['Estoque_Total_Un'].values[0]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.subheader(r['Nome'])
            c2.metric("Estoque", f"{est_u//24} Eng | {est_u%24} un")
            if c3.button("➖ ENGRADADO", key=f"en_{r['Nome']}"):
                if est_u >= 24:
                    df_est.loc[df_est['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 24
                    df_est.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
            if c4.button("➖ UNIDADE", key=f"un_{r['Nome']}"):
                if est_u >= 1:
                    df_est.loc[df_est['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 1
                    df_est.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()

    # =================================================================
    # ABA: CASCOS (ESTORNO COMPLETO)
    # =================================================================
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        with st.form("c_form"):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            fc, ft, fv, fq = col1.text_input("Cliente").upper(), col2.text_input("Tel"), col3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), col4.number_input("Qtd", 1)
            if st.form_submit_button("Lançar"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), fc, ft, fv, fq, "DEVE", ""]], columns=df_cas.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            cl1, cl2 = st.columns([7, 2])
            cl1.warning(f"**{r['Cliente']}** deve {r['Quantidade']}x {r['Vasilhame']}")
            if cl2.button("RECEBER", key=f"rc_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"
                df_cas.at[i, 'QuemBaixou'] = nome_atual
                df_cas.to_csv(CASCOS_FILE, index=False)
                st.rerun()
        
        st.write("---")
        st.subheader("✅ Histórico de Baixas (Estorno)")
        for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(5).iterrows():
            el1, el2 = st.columns([7, 2])
            el1.info(f"OK: {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']} (Baixa: {r['QuemBaixou']})")
            if el2.button("🚫 ESTORNAR", key=f"es_{r['ID']}"):
                df_cas.at[i, 'Status'] = "DEVE"
                df_cas.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # --- RESTANTE DAS ABAS (ADMIN) ---
    elif menu == "📦 Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            sel = st.selectbox("Produto", df_prod['Nome'].unique())
            un, t = get_unidades(sel, df_prod)
            with st.form("e_f"):
                st.info(f"Padrão: {un} por {t}")
                qf, qa = st.columns(2)[0].number_input(f"Qtd {t}", 0), st.columns(2)[1].number_input("Avulsos", 0)
                if st.form_submit_button("Lançar Entrada"):
                    df_est.loc[df_est['Nome'] == sel, 'Estoque_Total_Un'] += (qf * un) + qa
                    df_est.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.dataframe(df_est)

    elif menu == "✨ Cadastro":
        st.title("✨ Produtos")
        with st.form("c_f"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc, fn, fp = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Outros"]), c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar") and fn != "" and fn not in df_prod['Nome'].values:
                pd.concat([df_prod, pd.DataFrame([[fc, fn, fp]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_est, pd.DataFrame([[fn, 0]], columns=df_est.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        for i, r in df_prod.iterrows():
            st.write(f"**{r['Nome']}** ({r['Categoria']})")
            if st.button("Excluir", key=f"del_{r['Nome']}"):
                df_prod[df_prod['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_est[df_est['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    elif menu == "📊 Financeiro" and sou_admin:
        df_f = pd.merge(df_est, df_prod, on='Nome')
        df_f['Patrimônio'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("Total", f"R$ {df_f['Patrimônio'].sum():,.2f}")
        st.dataframe(df_f)

    elif menu == "📜 Logs" and sou_admin:
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        with st.form("eq_f"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("Login"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_usr.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_usr[['user', 'nome', 'is_admin', 'telefone']])
