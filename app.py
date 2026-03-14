import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import zipfile

# =================================================================
# 1. DESIGN PREMIUM & MOBILE READY (NÃO MUDA AS FUNÇÕES)
# =================================================================
st.set_page_config(
    page_title="Adega Pacaembu", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Configuração para parecer App no Celular */
    @media (max-width: 640px) { .stApp { padding-bottom: 50px; } }
    
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="stExpander"] { 
        border: 1px solid #30363d; border-radius: 15px; 
        background-color: #161b22; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .stButton>button {
        border-radius: 10px; font-weight: 700; height: 3em;
        transition: all 0.3s ease; border: 1px solid #30363d; background-color: #21262d;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    div[data-testid="stMetric"] {
        background-color: #1c2128; padding: 20px; border-radius: 15px;
        border: 1px solid #30363d; border-left: 6px solid #238636;
    }
    [data-testid="stForm"] {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 20px;
    }
    </style>
    
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (TODOS OS DBS ORIGINAIS)
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"
TODOS_DBS = [DB_PROD, DB_EST, DB_PIL, DB_USR, DB_LOG, DB_CAS]

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                      columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(DB_USR, index=False)
    arquivos = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_EST: ['Nome', 'Estoque_Total_Un'],
        DB_PIL: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)

def gerar_backup_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in TODOS_DBS:
            if os.path.exists(f): z.write(f)
    return buf.getvalue()

init_db()

def registrar_log(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user, acao]], 
                  columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)

def get_config_bebida(nome, df_p):
    busca = df_p[df_p['Nome'] == nome]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
        if cat in ["Alimentos", "Limpeza"]: return 1, "Unidade"
    return 12, "Fardo"

# =================================================================
# 3. SISTEMA DE LOGIN
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff; margin-top: 50px;'>🍺 ADEGA PACAEMBU </h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in = st.text_input("👤 Usuário").strip()
            s_in = st.text_input("🔑 Senha", type="password").strip()
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DB_USR)
                valid = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not valid.empty:
                    st.session_state.update({
                        'autenticado': True, 'u_l': u_in, 
                        'u_n': valid['nome'].values[0], 
                        'u_a': (valid['is_admin'].values[0] == 'SIM')
                    })
                    registrar_log(st.session_state['u_n'], "Login")
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    # --- CARREGAMENTO DE DADOS ---
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p = pd.read_csv(DB_PROD); df_e = pd.read_csv(DB_EST); df_pil = pd.read_csv(DB_PIL)
    df_cas = pd.read_csv(DB_CAS); df_usr = pd.read_csv(DB_USR)

    # --- SIDEBAR ---
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 1.2em;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    menu = st.sidebar.radio("MENU", ["🏠 Dashboard", "🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏗️ FUNÇÃO DOS PILARES (LÓGICA ORIGINAL COMPLETA) ---
    if menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Engenharia de Pilares")
        with st.expander("➕ MONTAR NOVA CAMADA (ESTRUTURA AMARRADA)"):
            p_alvo = st.selectbox("Pilar Destino", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Identificação do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_filtro = st.selectbox("Filtrar Categoria", df_p['Categoria'].unique())
            
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3) # Lógica de amarração original
                st.info(f"🏗️ Camada {c_atual} | Padrão: {at}x{fr}")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                cols_grid = st.columns(max(at, fr))
                for i in range(at + fr):
                    pos = i + 1
                    with cols_grid[i % len(cols_grid)]:
                        beb_dict[pos] = st.selectbox(f"Pos {pos}", lista_beb, key=f"p_{pos}")
                        av_dict[pos] = st.number_input(f"Avulsos", 0, key=f"a_{pos}")
                
                if st.button("FINALIZAR MONTAGEM"):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        st.success("Montagem registrada!"); st.rerun()

        st.markdown("---")
        for pilar in df_pil['NomePilar'].unique():
            with st.container():
                st.subheader(f"📍 Pilar: {pilar}")
                camadas = sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
                for cam in camadas:
                    dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                    st.write(f"**Camada {cam}**")
                    cols = st.columns(5)
                    for _, r in dados_cam.iterrows():
                        with cols[int(r['Posicao'])-1]:
                            st.markdown(f"**{r['Bebida']}**\n\n+{r['Avulsos']}un")
                            if st.button("BAIXA", key=f"bx_p_{r['ID']}"):
                                u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                                df_e.to_csv(DB_EST, index=False)
                                df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                                st.rerun()

    # --- 🍻 PDV ROMARINHO (COM TRAVA DE SEGURANÇA) ---
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido")
        df_pdv = df_p[df_p['Categoria'] == "Romarinho"]
        for _, item in df_pdv.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 4])
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                u_b, t_t = get_config_bebida(item['Nome'], df_p)
                c1.markdown(f"#### {'🔴' if est_u < u_b else '🟢'} {item['Nome']}")
                c2.metric("Saldo", f"{est_u//u_b} {t_t}")
                b1, b2 = c3.columns(2)
                if b1.button(f"➖ {t_t}", key=f"e_{item['Nome']}", disabled=(est_u < u_b)):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= u_b
                    df_e.to_csv(DB_EST, index=False); st.rerun()
                if b2.button("➖ UNID.", key=f"u_{item['Nome']}", disabled=(est_u < 1)):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_EST, index=False); st.rerun()

    # --- 🏠 DASHBOARD (COM VISÃO FINANCEIRA) ---
    elif menu == "🏠 Dashboard":
        st.title("🚀 Dashboard")
        m1, m2, m3 = st.columns(3)
        df_inv = pd.merge(df_e, df_p, on="Nome")
        patrimonio = (df_inv['Estoque_Total_Un'] * df_inv['Preco_Unitario']).sum()
        m1.metric("Pendências Cascos", f"{len(df_cas[df_cas['Status'] == 'DEVE'])}")
        m2.metric("Valor em Estoque", f"R$ {patrimonio:,.2f}")
        m3.metric("Alertas Críticos", f"{len(df_e[df_e['Estoque_Total_Un'] < 15])}")
        st.subheader("📋 Log de Atividades")
        st.table(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False).head(10))

    # --- 🍶 CONTROLE DE CASCOS (LÓGICA COMPLETA) ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Gestão de Cascos")
        tab1, tab2, tab3 = st.tabs(["🔴 Pendentes", "📦 Saldo Pátio", "📜 Recibos"])
        with tab1:
            with st.form("f_casco"):
                c1, c2, c3 = st.columns(3); cli = c1.text_input("Cliente").upper()
                vas = c2.selectbox("Tipo", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"]); qtd = c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÉBITO"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, "", vas, qtd, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                st.warning(f"{r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button("RECEBER", key=f"pag_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- 📊 ADMIN FINANCEIRO (CORREÇÃO DO ERRO ANTERIOR) ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Painel ADM")
        st.download_button("📥 BACKUP ZIP", gerar_backup_zip(), "backup.zip")
        df_fin = pd.merge(df_e, df_p, on="Nome")
        df_fin['Subtotal'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.subheader("Relatório de Valor de Mercado")
        st.dataframe(df_fin, use_container_width=True)

    # --- ✨ CADASTRO, PERFIL E EQUIPE (MANTIDOS) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        with st.form("cad_p"):
            c1, c2, c3 = st.columns(3)
            ct = c1.selectbox("Cat", ["Romarinho", "Refrigerante", "Cerveja", "Outros"])
            nm = c2.text_input("Nome").upper(); pr = c3.number_input("Preço")
            if st.form_submit_button("SALVAR"):
                pd.concat([df_p, pd.DataFrame([[ct, nm, pr]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                pd.concat([df_e, pd.DataFrame([[nm, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Equipe")
        st.dataframe(df_usr[['user', 'nome', 'is_admin']])

    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        st.write(f"Usuário: {u_logado} | Nível: {'Admin' if is_adm else 'Operador'}")
