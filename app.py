import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - v59", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v59) ---
DB_PRODUTOS = "produtos_v59.csv"
DB_ESTOQUE = "estoque_v59.csv"
PILAR_ESTRUTURA = "pilares_v59.csv"
USERS_FILE = "usuarios_v59.csv"
LOG_FILE = "historico_v59.csv"
CASCOS_FILE = "cascos_v59.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        # Adicionada a coluna 'foto' no CSV de usuários
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
    
    # Verificar se a coluna foto existe (migração de versão)
    df_u = pd.read_csv(USERS_FILE)
    if 'foto' not in df_u.columns:
        df_u['foto'] = ''
        df_u.to_csv(USERS_FILE, index=False)

init_files()

# --- FUNÇÕES DE UTILIDADE ---
def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def imagem_para_base64(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        # Redimensiona para não pesar o CSV
        img.thumbnail((150, 150))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

def obter_dados_categoria(nome_produto, df_produtos):
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
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
                st.session_state.update({
                    'autenticado': True, 
                    'user_login': u_in,
                    'name': check['nome'].values[0], 
                    'is_admin': check['is_admin'].values[0] == 'SIM'
                })
                registrar_log(st.session_state['name'], "Login efetuado")
                st.rerun()
            else: st.error("Erro de login.")
else:
    nome_logado = st.session_state['name']
    user_logado = st.session_state['user_login']
    sou_admin = st.session_state['is_admin']
    
    # --- SIDEBAR COM FOTO DE PERFIL ---
    st.sidebar.markdown("---")
    foto_b64 = df_users[df_users['user'] == user_logado]['foto'].values[0]
    
    if pd.isna(foto_b64) or foto_b64 == "":
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    else:
        st.sidebar.image(f"data:image/png;base64,{foto_b64}", width=100)
        
    st.sidebar.title(f"👤 {nome_logado}")
    
    menu_options = ["🏗️ Pilares", "🍻 Romarinho", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Meu Perfil"]
    if sou_admin: menu_options += ["📊 Financeiro", "📜 Histórico", "👥 Equipe"]
    menu = st.sidebar.radio("Navegação", menu_options)
    
    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    df_prod, df_e, df_pilar, df_cascos = pd.read_csv(DB_PRODUTOS), pd.read_csv(DB_ESTOQUE), pd.read_csv(PILAR_ESTRUTURA), pd.read_csv(CASCOS_FILE)

    # --- ABA: MEU PERFIL (MUDAR FOTO) ---
    if menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações de Perfil")
        st.subheader(f"Usuário: {user_logado}")
        
        uploaded_file = st.file_uploader("Escolha uma foto da sua galeria", type=["jpg", "jpeg", "png"])
        if st.button("Atualizar Minha Foto"):
            if uploaded_file:
                nova_foto = imagem_para_base64(uploaded_file)
                df_users.loc[df_users['user'] == user_logado, 'foto'] = nova_foto
                df_users.to_csv(USERS_FILE, index=False)
                st.success("Foto de perfil atualizada!")
                st.rerun()
            else:
                st.warning("Selecione uma imagem primeiro.")

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares (Refrigerante)")
        with st.expander("🆕 Adicionar Camada"):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_alvo = st.selectbox("Pilar", pilares_existentes)
            nome_p = st.text_input("Nome").upper() if pilar_alvo == "+ NOVO PILAR" else pilar_alvo
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_proxima = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inv = (cam_proxima % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                bebidas, avulsos = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    for i in range(at):
                        pos = i + 1
                        bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp{pos}{cam_proxima}")
                        avulsos[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap{pos}{cam_proxima}")
                with c2:
                    for i in range(fr):
                        pos = at + i + 1
                        bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp{pos}{cam_proxima}")
                        avulsos[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap{pos}{cam_proxima}")
                if st.button("💾 Salvar Camada"):
                    novos = [[f"{nome_p}_{cam_proxima}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_proxima, p, beb, avulsos[p]] for p, beb in bebidas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: +Camada {cam_proxima} em {nome_p}")
                        st.rerun()

        for pilar_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pilar_nome}", expanded=True):
                for cam in sorted(df_pilar[df_pilar['NomePilar'] == pilar_nome]['Camada'].unique(), reverse=True):
                    st.write(f"**Camada {cam}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == pilar_nome) & (df_pilar['Camada'] == cam)]
                    cols_p = st.columns(5)
                    for _, r in dados_c.iterrows():
                        with cols_p[int(r['Posicao'])-1]:
                            st.info(f"**{r['Bebida']}**\n+{r['Avulsos']} Av")
                            if st.button("RETIRAR", key=f"ret_{r['ID']}"):
                                un_f, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                total = un_f + r['Avulsos']
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"SAÍDA: {total}un de {r['Bebida']} ({pilar_nome})")
                                st.rerun()

    # --- ABA: ROMARINHO ---
    elif menu == "🍻 Romarinho":
        st.title("🍻 Gestão Romarinho")
        df_rom = df_prod[df_prod['Categoria'] == "Romarinho"]
        for _, row in df_rom.iterrows():
            est_un = df_e[df_e['Nome'] == row['Nome']]['Estoque_Total_Un'].values[0]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.subheader(row['Nome'])
            c2.metric("Estoque", f"{est_un//24} Eng | {est_un%24} un")
            if c3.button(f"➖ ENGRADADO", key=f"e_{row['Nome']}"):
                if est_un >= 24:
                    df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"SAÍDA ROMARINHO: 1 Engradado de {row['Nome']}")
                    st.rerun()
            if c4.button(f"➖ UNIDADE", key=f"u_{row['Nome']}"):
                if est_un >= 1:
                    df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"SAÍDA ROMARINHO: 1 Unidade de {row['Nome']}")
                    st.rerun()

    # --- ABA: CASCOS (COM ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        with st.form("f_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cl, f_te, f_va, f_qt = c1.text_input("Cliente").upper(), c2.text_input("Tel"), c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("Salvar"):
                cid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[cid, datetime.now().strftime("%d/%m %H:%M"), f_cl, f_te, f_va, f_qt, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {f_cl} deve {f_qt} {f_va}")
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"**{r['Cliente']}** - {r['Quantidade']}x {r['Vasilhame']} ({r['Data']})")
            if lc2.button("RECEBER", key=f"rc_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO RECEBIDO: {r['Cliente']}")
                st.rerun()
        
        st.write("---")
        st.subheader("✅ Baixas (Estorno)")
        for i, r in df_cascos[df_cascos['Status'] == "PAGO"].tail(5).iterrows():
            ec1, ec2 = st.columns([7, 2])
            ec1.info(f"OK: {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']} (Baixa por: {r['QuemBaixou']})")
            if ec2.button("🚫 ESTORNAR", key=f"es_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "DEVE"
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"ESTORNO CASCO: {r['Cliente']}")
                st.rerun()

    # --- ABA: ESTOQUE (ENTRADA) ---
    elif menu == "📦 Estoque":
        st.title("📦 Entrada de Estoque")
        if not df_prod.empty:
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            un_cat, t_cat = obter_dados_categoria(p_sel, df_prod)
            with st.form("e_form"):
                st.info(f"Padrão: {un_cat} por {t_cat}")
                c1, c2 = st.columns(2)
                f_q, f_a = c1.number_input(f"Qtd {t_cat}", 0), c2.number_input("Avulsos", 0)
                if st.form_submit_button("Confirmar"):
                    tot = (f_q * un_cat) + f_a
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += tot
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: +{tot}un de {p_sel}")
                    st.rerun()
        st.dataframe(df_e)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Produtos")
        with st.form("c_form"):
            c1, c2, c3 = st.columns([2, 2, 1])
            f_c = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_n, f_p = c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar") and f_n != "" and f_n not in df_prod['Nome'].values:
                pd.concat([df_prod, pd.DataFrame([[f_c, f_n, f_p]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[f_n, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        for i, r in df_prod.iterrows():
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']})")
            if col2.button("🗑️", key=f"d_{r['Nome']}"):
                df_prod[df_prod['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ABAS ADM ---
    elif menu == "📊 Financeiro" and sou_admin:
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total em Estoque", f"R$ {df_fin['Total'].sum():,.2f}")
        st.dataframe(df_fin)

    elif menu == "📜 Histórico" and sou_admin:
        st.title("📜 Histórico Detalhado")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        with st.form("eq_form"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                # Novos usuários são criados com a coluna foto vazia
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users[['user', 'nome', 'is_admin', 'telefone']])
