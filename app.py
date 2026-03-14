import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre no topo) ---
st.set_page_config(page_title="Depósito Pacaembu - v60 ULTRA", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v60) ---
DB_PRODUTOS = "produtos_v60.csv"
DB_ESTOQUE = "estoque_v60.csv"
PILAR_ESTRUTURA = "pilares_v60.csv"
USERS_FILE = "usuarios_v60.csv"
LOG_FILE = "historico_v60.csv"
CASCOS_FILE = "cascos_v60.csv"

def init_files():
    """Garante a integridade de todos os arquivos e colunas"""
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
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
    
    # Migração automática de coluna de foto se necessário
    df_u = pd.read_csv(USERS_FILE)
    if 'foto' not in df_u.columns:
        df_u['foto'] = ''
        df_u.to_csv(USERS_FILE, index=False)

init_files()

# --- FUNÇÕES CORE ---
def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def imagem_para_base64(uploaded_file):
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((200, 200)) # Qualidade boa sem pesar o CSV
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    return ""

def obter_dados_categoria(nome, df_p):
    busca = df_p[df_p['Nome'] == nome]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
    return 12, "Fardo"

# --- 3. CONTROLE DE SESSÃO E LOGIN (CORREÇÃO DO KEYERROR) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_box"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            df_u = pd.read_csv(USERS_FILE)
            user_check = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not user_check.empty:
                st.session_state['autenticado'] = True
                st.session_state['user_login'] = u # Aqui define a chave para evitar o erro
                st.session_state['name'] = user_check['nome'].values[0]
                st.session_state['is_admin'] = (user_check['is_admin'].values[0] == 'SIM')
                registrar_log(st.session_state['name'], "Acessou o sistema")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
else:
    # --- VARIÁVEIS SEGURAS (SÓ ACESSADAS APÓS LOGIN) ---
    user_logado = st.session_state.get('user_login', 'admin')
    nome_logado = st.session_state.get('name', 'Usuário')
    sou_admin = st.session_state.get('is_admin', False)

    # Carregar Dados Atualizados
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)
    df_users = pd.read_csv(USERS_FILE)

    # --- SIDEBAR COM FOTO DA GALERIA ---
    st.sidebar.markdown("### Perfil")
    foto_raw = df_users[df_users['user'] == user_logado]['foto'].values[0]
    if pd.isna(foto_raw) or foto_raw == "":
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    else:
        st.sidebar.image(f"data:image/png;base64,{foto_raw}", width=100)
    
    st.sidebar.title(f"Olá, {nome_logado}")
    
    menu = st.sidebar.radio("Navegação", 
        ["🏗️ Gestão de Pilares", "🍻 Gestão Romarinho", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Meu Perfil"] + 
        (["📊 Financeiro", "📜 Histórico", "👥 Equipe"] if sou_admin else []))

    if st.sidebar.button("Deslogar"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: MEU PERFIL (FOTO DA GALERIA) ---
    if menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações de Perfil")
        st.write(f"Alterar foto para o usuário: **{user_logado}**")
        nova_foto_arq = st.file_uploader("Selecione uma foto da galeria do celular", type=['png', 'jpg', 'jpeg'])
        if st.button("Salvar Nova Foto"):
            if nova_foto_arq:
                b64_img = imagem_para_base64(nova_foto_arq)
                df_users.loc[df_users['user'] == user_logado, 'foto'] = b64_img
                df_users.to_csv(USERS_FILE, index=False)
                st.success("Foto atualizada com sucesso!")
                st.rerun()
            else:
                st.warning("Escolha uma imagem antes de salvar.")

    # --- ABA: PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Pilares (Refrigerantes)")
        with st.expander("🆕 Adicionar Nova Camada"):
            p_alvo = st.selectbox("Pilar", ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique()))
            n_p = st.text_input("Nome").upper() if p_alvo == "+ NOVO PILAR" else p_alvo
            if n_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == n_p]
                cam = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inv = (cam % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                b, a = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    for i in range(at):
                        pos = i+1
                        b[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"b{pos}{n_p}{cam}")
                        a[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{n_p}{cam}")
                with c2:
                    for i in range(fr):
                        pos = at+i+1
                        b[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"b{pos}{n_p}{cam}")
                        a[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{n_p}{cam}")
                if st.button("💾 Salvar Camada"):
                    regs = [[f"{n_p}_{cam}_{p}_{datetime.now().strftime('%S')}", n_p, cam, p, beb, a[p]] for p, beb in b.items() if beb != "Vazio"]
                    if regs:
                        pd.concat([df_pilar, pd.DataFrame(regs, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: +Camada {cam} no {n_p}")
                        st.rerun()

        for pn in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pn}", expanded=True):
                for c in sorted(df_pilar[df_pilar['NomePilar'] == pn]['Camada'].unique(), reverse=True):
                    st.write(f"**Camada {c}**")
                    dc = df_pilar[(df_pilar['NomePilar'] == pn) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, r in dc.iterrows():
                        with cols[int(r['Posicao'])-1]:
                            st.info(f"{r['Bebida']}\n+{r['Avulsos']} Av")
                            if st.button("RETIRAR", key=f"rt_{r['ID']}"):
                                uf, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                tot = uf + r['Avulsos']
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= tot
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"RETIRADA PILAR: {tot}un {r['Bebida']}")
                                st.rerun()

    # --- ABA: ROMARINHO (BAIXA AVULSA E ENGRADADO) ---
    elif menu == "🍻 Gestão Romarinho":
        st.title("🍻 Baixa Romarinho")
        for _, r in df_prod[df_prod['Categoria'] == "Romarinho"].iterrows():
            est_un = df_e[df_e['Nome'] == r['Nome']]['Estoque_Total_Un'].values[0]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.subheader(r['Nome'])
            c2.metric("Estoque", f"{est_un//24} Eng | {est_un%24} un")
            if c3.button("➖ ENGRADADO", key=f"eng_{r['Nome']}"):
                if est_un >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"BAIXA: 1 Engradado {r['Nome']}")
                    st.rerun()
            if c4.button("➖ UNIDADE", key=f"un_{r['Nome']}"):
                if est_un >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"BAIXA: 1 Avulso {r['Nome']}")
                    st.rerun()

    # --- ABA: CASCOS (ESTORNO E HISTÓRICO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos e Vasilhames")
        with st.form("casco_form"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            fcl, fte, fva, fqt = c1.text_input("Cliente").upper(), c2.text_input("Tel"), c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("Salvar"):
                pd.concat([df_cascos, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), fcl, fte, fva, fqt, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {fcl} deve {fqt} {fva}")
                st.rerun()

        st.subheader("⚠️ Devedores")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"**{r['Cliente']}** - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"rec_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"RECEBIDO: Casco de {r['Cliente']}")
                st.rerun()
        
        st.write("---")
        st.subheader("✅ Recebidos (Estorno)")
        for i, r in df_cascos[df_cascos['Status'] == "PAGO"].tail(10).iterrows():
            ec1, ec2 = st.columns([7, 2])
            ec1.info(f"OK: {r['Cliente']} - {r['Quantidade']} {r['Vasilhame']} (Baixa: {r['QuemBaixou']})")
            if ec2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"ESTORNO: Voltou dívida de {r['Cliente']}")
                st.rerun()

    # --- ABA: ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            ps = st.selectbox("Produto", df_prod['Nome'].unique())
            un, t = obter_dados_categoria(ps, df_prod)
            with st.form("e"):
                st.info(f"Padrão: {un} por {t}")
                qf, qa = st.columns(2)[0].number_input(f"Qtd {t}", 0), st.columns(2)[1].number_input("Avulsos", 0)
                if st.form_submit_button("Lançar"):
                    df_e.loc[df_e['Nome'] == ps, 'Estoque_Total_Un'] += (qf * un) + qa
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.dataframe(df_e)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Produtos")
        with st.form("c"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            fn, fp = c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar") and fn != "" and fn not in df_prod['Nome'].values:
                pd.concat([df_prod, pd.DataFrame([[fc, fn, fp]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        for i, r in df_prod.iterrows():
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']})")
            if col2.button("🗑️", key=f"d_{r['Nome']}"):
                df_prod[df_prod['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ADMIN ---
    elif menu == "📊 Financeiro" and sou_admin:
        df_f = pd.merge(df_e, df_prod, on='Nome')
        df_f['Total'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("Total Patrimônio", f"R$ {df_f['Total'].sum():,.2f}")
        st.dataframe(df_f)

    elif menu == "📜 Histórico" and sou_admin:
        st.title("📜 Logs")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Funcionários")
        with st.form("eq"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users[['user', 'nome', 'is_admin', 'telefone']])
