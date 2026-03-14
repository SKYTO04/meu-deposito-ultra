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
        DB_CAS: ['ID', 'Data_Lanc', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'Data_Baixa'],
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
        m1, m2, m3 = st.columns(3)
        m1.metric("Clientes Devendo", len(df_cas[df_cas['Status'] == 'DEVE']))
        m2.metric("Tarefas Pendentes", len(df_tar[df_tar['Status'] == 'PENDENTE']))
        m3.metric("Itens Catálogo", len(df_p))
        st.divider()
        st.subheader("📊 Últimas Atividades")
        st.table(pd.read_csv(DB_LOG).tail(5))

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Tarefas da Equipe")
        if is_adm:
            with st.expander("➕ NOVA TAREFA"):
                with st.form("nt"):
                    txt = st.text_input("Descrição")
                    if st.form_submit_button("LANÇAR"):
                        pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", txt, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_TAR, index=False); st.rerun()
        
        for i, r in df_tar.iterrows():
            cor = "task-pending" if r['Status'] == "PENDENTE" else "task-done"
            with st.container():
                st.markdown(f'<div class="{cor}"><b>{r["Status"]}:</b> {r["Tarefa"]}</div>', unsafe_allow_html=True)
                if r['Status'] == "PENDENTE":
                    if st.button("CONCLUIR ✅", key=f"ct_{r['ID']}"):
                        df_tar.at[i, 'Status'] = "CONCLUÍDO"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M"); df_tar.to_csv(DB_TAR, index=False); st.rerun()
                elif is_adm:
                    if st.button("APAGAR", key=f"dt_{r['ID']}"): df_tar.drop(i).to_csv(DB_TAR, index=False); st.rerun()

    # --- 🍻 PDV ROMARINHO ---
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 Venda Rápida")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 4])
                u_b, t_t = get_config_bebida(item['Nome'], df_p)
                c1.markdown(f"### {item['Nome']}")
                if c3.button(f"BAIXAR {t_t.upper()}", key=f"v_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= u_b
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda {item['Nome']}"); st.rerun()

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        # (Mantendo lógica original de Pilares para não bugar)
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
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()
        for p in df_pil['NomePilar'].unique():
            st.subheader(f"📍 {p}")
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                cols = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if cols[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_p, _ = get_config_bebida(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                        df_e.to_csv(DB_EST, index=False); df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False); st.rerun()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Estoque Atual")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        with st.expander("⚙️ AJUSTE MANUAL"):
            prod = st.selectbox("Produto", df_p['Nome'].unique())
            qtd = st.number_input("Quantidade (Unid)", value=0)
            if st.button("ATUALIZAR"):
                df_e.loc[df_e['Nome'] == prod, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_EST, index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Novos Itens")
        with st.form("fc"):
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Lata", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            pre = c3.number_input("Preço Venda", 0.0)
            if st.form_submit_button("CADASTRAR"):
                pd.concat([df_p, pd.DataFrame([[cat, nom, pre]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- 🍶 CASCOS (PROFISSIONAL COM ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        t1, t2, t3, t4 = st.tabs(["🔴 PENDENTES (DÍVIDA)", "📜 HISTÓRICO DE BAIXAS", "🚚 SAÍDA EMPRESA", "📦 SALDO ATUAL"])
        
        with t1:
            with st.form("f_casco"):
                c1, c2, c3 = st.columns([2, 2, 1])
                cli = c1.text_input("Nome do Cliente").upper()
                vas = c2.selectbox("Tipo de Casco", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"])
                qtd = c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    novo = [f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, "", vas, qtd, "DEVE", "", ""]
                    pd.concat([df_cas, pd.DataFrame([novo], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
            
            st.markdown("### Clientes Devendo")
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.warning(f"🕒 {r['Data_Lanc']} | **{r['Cliente']}** deve {r['Quantidade']}x {r['Vasilhame']}")
                if col_c2.button("BAIXAR ✅", key=f"b_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "PAGO"
                    df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.at[i, 'Data_Baixa'] = datetime.now().strftime("%d/%m %H:%M")
                    df_cas.to_csv(DB_CAS, index=False); registrar_log(n_logado, f"Recebeu casco de {r['Cliente']}"); st.rerun()

        with t2:
            st.markdown("### Histórico de Recebimentos")
            hist = df_cas[df_cas['Status'] == "PAGO"].copy().sort_index(ascending=False)
            if not hist.empty:
                for i, r in hist.iterrows():
                    c_h1, c_h2 = st.columns([4, 1])
                    detalhe = f"✅ **{r['Cliente']}** devolveu {r['Quantidade']}x {r['Vasilhame']} | **Baixado por:** {r['QuemBaixou']} às {r['Data_Baixa']}"
                    if "EMPRESA" in str(r['Cliente']):
                        st.info(f"🚚 {r['Cliente']} | Levou {abs(r['Quantidade'])}x {r['Vasilhame']} em {r['Data_Lanc']}")
                    else:
                        c_h1.success(detalhe)
                        if c_h2.button("ESTORNAR ↩️", key=f"est_{r['ID']}"):
                            df_cas.at[i, 'Status'] = "DEVE"
                            df_cas.at[i, 'QuemBaixou'] = ""
                            df_cas.at[i, 'Data_Baixa'] = ""
                            df_cas.to_csv(DB_CAS, index=False); registrar_log(n_logado, f"ESTORNO: Voltou divida de {r['Cliente']}"); st.rerun()

        with t3:
            st.markdown("### Registrar Saída (Empresa/Caminhão)")
            with st.form("f_emp"):
                e1, e2, e3 = st.columns([2, 2, 1])
                emp = e1.text_input("Empresa", value="COCA-COLA").upper()
                v_t = e2.selectbox("O que levaram?", ["Romarinho", "Coca 1L", "600ml"])
                v_q = e3.number_input("Quantidade", 1)
                if st.form_submit_button("REGISTRAR SAÍDA"):
                    novo = [f"OUT{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), f"EMPRESA: {emp}", "", v_t, -v_q, "PAGO", n_logado, datetime.now().strftime("%d/%m %H:%M")]
                    pd.concat([df_cas, pd.DataFrame([novo], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()

        with t4:
            st.markdown("### Saldo de Cascos Vazios na Adega")
            saldo = df_cas[df_cas['Status'] == "PAGO"].groupby('Vasilhame')['Quantidade'].sum().reset_index()
            st.table(saldo)

    # --- 📊 ADMIN FINANCEIRO ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Gestão e Segurança")
        df_fin = pd.merge(df_e, df_p, on="Nome")
        df_fin['Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Patrimônio em Estoque", f"R$ {df_fin['Total'].sum():,.2f}")
        st.divider()
        c_a, c_b, c_c = st.columns(3)
        if c_a.button("💾 GERAR BACKUP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as z:
                for f in TODOS_DBS:
                    if os.path.exists(f): z.write(f)
            st.download_button("⬇️ BAIXAR ZIP", buf.getvalue(), "backup_adega.zip")
        if c_b.button("📊 RELATÓRIO EXCEL"):
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_fin.to_excel(wr, sheet_name='Estoque')
                df_cas.to_excel(wr, sheet_name='Cascos')
            st.download_button("⬇️ BAIXAR EXCEL", out.getvalue(), "relatorio.xlsx")
        if c_c.button("🧹 LIMPAR PAGO"):
            df_cas = df_cas[df_cas['Status'] == 'DEVE']
            df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- 📜 LOGS ---
    elif menu == "📜 Logs" and is_adm:
        st.title("📜 Histórico de Ações")
        st.dataframe(pd.read_csv(DB_LOG).sort_index(ascending=False), use_container_width=True)

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gerenciar Equipe")
        for i, row in df_usr.iterrows():
            st.markdown(f'<div class="user-card"><b>{row["nome"]}</b></div>', unsafe_allow_html=True)
            if row['user'] != 'admin':
                if st.button(f"Remover {row['user']}", key=f"du_{row['user']}"): df_usr.drop(i).to_csv(DB_USR, index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        col1, col2 = st.columns([1, 2])
        with col1: st.markdown(f"<img src='{f_path}' width='180' style='border-radius: 50%; border: 4px solid #238636;'>", unsafe_allow_html=True)
        with col2:
            st.write(f"Usuário: {u_logado}")
            up = st.file_uploader("Nova Foto")
            if st.button("SALVAR") and up:
                img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
                buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_USR, index=False); st.rerun()
