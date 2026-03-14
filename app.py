import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import base64
from PIL import Image
import io
import zipfile

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V66 (TOTAL)
# =================================================================
st.set_page_config(
    page_title="Adega Pacaembu", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
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
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; transform: translateY(-2px); }
    div[data-testid="stMetric"] {
        background-color: #1c2128; padding: 20px; border-radius: 15px;
        border: 1px solid #30363d; border-left: 6px solid #238636;
    }
    [data-testid="stForm"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 20px; }
    .user-card { background-color: #1c2128; border: 1px solid #30363d; border-radius: 15px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #58a6ff; }
    .task-done { background-color: #1b281d; border: 1px solid #238636; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .task-pending { background-color: #21262d; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    </style>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"
DB_TAR = "tarefas_v66.csv"
TODOS_DBS = [DB_PROD, DB_EST, DB_PIL, DB_USR, DB_LOG, DB_CAS, DB_TAR]

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                      columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(DB_USR, index=False)
    arquivos = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_EST: ['Nome', 'Estoque_Total_Un'],
        DB_PIL: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB_TAR: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario']
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq): pd.DataFrame(columns=colunas).to_csv(arq, index=False)

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
# 3. SEGURANÇA E LOGIN
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

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
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': valid['nome'].values[0], 'u_a': (valid['is_admin'].values[0] == 'SIM')})
                    registrar_log(st.session_state['u_n'], "Login"); st.rerun()
                else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL), pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_TAR)

    # --- ALERTA DE BACKUP MENSAL ---
    if datetime.now().day == 1:
        st.sidebar.error("⚠️ **DIA DE BACKUP!**\nBaixe os dados em Admin Financeiro.")

    # --- SIDEBAR ---
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty:
        raw = user_row['foto'].values[0]
        if not pd.isna(raw) and raw != "": f_path = f"data:image/png;base64,{raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='100' style='border-radius: 50%; border: 3px solid #238636; height: 100px; object-fit: cover;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🏠 Dashboard", "📋 Tarefas", "🍻 PDV Romarinho", "🏗️ Pilares", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Central de Comando")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pendências Cascos", f"{len(df_cas[df_cas['Status'] == 'DEVE'])}")
        m2.metric("Itens no Catálogo", len(df_p))
        m3.metric("Tarefas Ativas", len(df_tar[df_tar['Status'] == 'PENDENTE']))
        m4.metric("Baixo Estoque", len(df_e[df_e['Estoque_Total_Un'] < 50]))
        st.divider()
        st.subheader("📊 Movimentações Recentes")
        st.table(pd.read_csv(DB_LOG).tail(8))

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Quadro de Tarefas")
        if is_adm:
            with st.expander("➕ LANÇAR NOVA TAREFA"):
                with st.form("f_tar"):
                    t_txt = st.text_area("O que precisa ser feito?")
                    if st.form_submit_button("CRIAR"):
                        if t_txt:
                            pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_txt, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_TAR, index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            with st.container():
                st.markdown(f'<div class="task-pending"><b>🔔 TAREFA:</b> {r["Tarefa"]}</div>', unsafe_allow_html=True)
                if st.button("CONCLUIR ✅", key=f"t_{r['ID']}"):
                    df_tar.at[i, 'Status'] = "CONCLUÍDO"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%d/%m %H:%M")
                    df_tar.to_csv(DB_TAR, index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "CONCLUÍDO"].iterrows():
            st.markdown(f'<div class="task-done"><b>✔️ FEITO:</b> {r["Tarefa"]}<br><small>Por: {r["QuemFez"]} às {r["Horario"]}</small></div>', unsafe_allow_html=True)
            if is_adm: 
                if st.button("EXCLUIR", key=f"d_t_{r['ID']}"): df_tar.drop(i).to_csv(DB_TAR, index=False); st.rerun()

    # --- 🍻 PDV ROMARINHO ---
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido - Romarinho")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 4])
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0]) if not df_e[df_e['Nome'] == item['Nome']].empty else 0
                u_b, t_t = get_config_bebida(item['Nome'], df_p)
                c1.markdown(f"#### {item['Nome']}")
                c2.metric("Saldo", f"{est_u//u_b} {t_t} | {est_u%u_b} un")
                b1, b2 = c3.columns(2)
                if b1.button(f"➖ {t_t.upper()}", key=f"e_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= u_b
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda {t_t} {item['Nome']}"); st.rerun()
                if b2.button("➖ UNID.", key=f"u_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Unid {item['Nome']}"); st.rerun()

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Engenharia de Pilares")
        with st.expander("➕ NOVA CAMADA"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_p = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_p:
                cat = st.selectbox("Cat", df_p['Categoria'].unique())
                c_at = 1 if df_pil[df_pil['NomePilar']==n_p].empty else int(df_pil[df_pil['NomePilar']==n_p]['Camada'].max()) + 1
                at, fr = (3, 2) if c_at % 2 != 0 else (2, 3)
                cols = st.columns(5)
                regs = []
                for i in range(at+fr):
                    b = cols[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==cat]['Nome'].tolist(), key=f"p{i}")
                    a = cols[i].number_input("Av", 0, key=f"a{i}")
                    if b != "Vazio": regs.append([f"{n_p}_{c_at}_{i}", n_p, c_at, i+1, b, a])
                if st.button("SALVAR"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()
        for p in df_pil['NomePilar'].unique():
            st.subheader(f"📍 {p}")
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                cols = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if cols[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_p, _ = get_config_bebida(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                        df_e.to_csv(DB_EST, index=False); df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False); st.rerun()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário Geral")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        st.subheader("⚙️ Ajuste Manual")
        sel_e = st.selectbox("Produto", df_p['Nome'].unique())
        u_b, t_t = get_config_bebida(sel_e, df_p)
        c_m1, c_m2, c_m3 = st.columns(3)
        tipo_m = c_m1.radio("Operação", ["➕ ENTRADA", "➖ SAÍDA"])
        qtd_f, qtd_u = c_m2.number_input(f"Qtd {t_t}s", 0), c_m3.number_input("Qtd Unid", 0)
        if st.button("EXECUTAR AJUSTE"):
            total = (qtd_f * u_b) + qtd_u
            if "SAÍDA" in tipo_m: df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] -= total
            else: df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] += total
            df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Ajuste {sel_e}"); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Catálogo")
        with st.form("f_cad"):
            c1, c2, c3 = st.columns(3)
            fc = c1.selectbox("Cat", ["Romarinho", "Refrigerante", "Cerveja Lata", "Alimentos", "Limpeza", "Outros"])
            fn = c2.text_input("Nome").upper().strip()
            fp = c3.number_input("Preço", 0.0)
            if st.form_submit_button("CADASTRAR"):
                if fn and fn not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- 🍶 CASCOS (TODAS AS OPÇÕES VOLTARAM) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        tab_deve, tab_emp, tab_vazio, tab_hist = st.tabs(["🔴 Pendentes", "🚚 Saída Empresa", "📦 Saldo Vazios", "📜 Histórico"])
        with tab_deve:
            with st.form("f_c_c"):
                c1, c2, c3 = st.columns([2, 2, 1])
                cl, va, qt = c1.text_input("Cliente").upper(), c2.selectbox("Vasilhame", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                if st.button(f"RECEBI de {r['Cliente']} ({r['Quantidade']}x {r['Vasilhame']})", key=r['ID']):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_CAS, index=False); st.rerun()
        with tab_emp:
            with st.form("f_emp"):
                e1, e2, e3 = st.columns([2, 2, 1])
                emp, tiv, qtv = e1.text_input("Empresa", value="COCA-COLA").upper(), e2.selectbox("Levado", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"]), e3.number_input("Qtd Levada", 1)
                if st.form_submit_button("REGISTRAR"):
                    pd.concat([df_cas, pd.DataFrame([[f"OUT{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), f"EMPRESA: {emp}", "", tiv, -qtv, "PAGO", n_logado]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
        with tab_vazio:
            res = df_cas[df_cas['Status'] == "PAGO"].groupby('Vasilhame')['Quantidade'].sum().reset_index()
            st.table(res)
        with tab_hist:
            st.dataframe(df_cas[df_cas['Status'] == "PAGO"].sort_index(ascending=False))

    # --- 📊 ADMIN FINANCEIRO ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Gestão e Segurança")
        df_fin = pd.merge(df_e, df_p, on="Nome")
        df_fin['Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Patrimônio em Estoque", f"R$ {df_fin['Total'].sum():,.2f}")
        st.divider()
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("💾 GERAR BACKUP ZIP"):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w') as z:
                    for f in TODOS_DBS:
                        if os.path.exists(f): z.write(f)
                st.download_button("⬇️ BAIXAR BACKUP", buf.getvalue(), f"backup_{datetime.now().strftime('%d_%m')}.zip")
        with col_b:
            if st.button("📋 GERAR EXCEL"):
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                    df_fin.to_excel(wr, sheet_name='Estoque')
                    df_cas.to_excel(wr, sheet_name='Cascos')
                st.download_button("⬇️ BAIXAR EXCEL", out.getvalue(), "relatorio_mensal.xlsx")
        with col_c:
            if st.button("🧹 LIMPAR SISTEMA"):
                df_cas = df_cas[df_cas['Status'] == 'DEVE']
                df_cas.to_csv(DB_CAS, index=False); st.warning("Histórico limpo!"); st.rerun()

    # --- 📜 LOGS ---
    elif menu == "📜 Logs" and is_adm:
        st.title("📜 Auditoria")
        st.dataframe(pd.read_csv(DB_LOG).sort_index(ascending=False), use_container_width=True)

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Equipe")
        for idx, row in df_usr.iterrows():
            st.markdown(f'<div class="user-card"><b>{row["nome"]}</b> ({row["user"]})</div>', unsafe_allow_html=True)
            if row['user'] != 'admin':
                if st.button(f"Remover {row['user']}", key=f"d_u_{row['user']}"): df_usr.drop(idx).to_csv(DB_USR, index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1: st.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='180' style='border-radius: 50%; border: 5px solid #238636; height: 180px; object-fit: cover;'></div>", unsafe_allow_html=True)
        with col_p2:
            st.info(f"**Nome:** {n_logado}")
            up = st.file_uploader("Trocar Foto", type=['png', 'jpg'])
            if st.button("SALVAR") and up:
                img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
                buf = io.BytesIO(); img.save(buf, format="PNG"); img_b64 = base64.b64encode(buf.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = img_b64; df_usr.to_csv(DB_USR, index=False); st.rerun()
