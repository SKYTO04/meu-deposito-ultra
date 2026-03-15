import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V140
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
    .badge-verde { background-color: #238636; color: white; }
    .badge-amarelo { background-color: #d29922; color: white; }
    .badge-vermelho { background-color: #f85149; color: white; }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; background-color: #21262d; 
        border: 1px solid #30363d; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS
# =================================================================
DB_FILES = {
    "prod": "produtos_v140.csv", "est": "estoque_v140.csv", "pil": "pilares_v140.csv",
    "usr": "usuarios_v140.csv", "log": "historico_v140.csv", "cas": "cascos_v140.csv",
    "tar": "tarefas_v140.csv", "cat": "categorias_v140.csv", "patio": "patio_v140.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["log"]: ['Data', 'Usuario', 'Ação'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_init = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_init = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            df_init.to_csv(f, index=False)
    
    if pd.read_csv(DB_FILES["usr"]).empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '', '']], columns=cols[DB_FILES["usr"]]).to_csv(DB_FILES["usr"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. INTERFACE PRINCIPAL
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("💎 Adega Pacaembu")
    with st.form("login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("ENTRAR"):
            df_u = pd.read_csv(DB_FILES["usr"])
            match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not match.empty:
                st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                st.rerun()
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR ---
    row_user = df_usr[df_usr['user'] == u_logado].iloc[0]
    f_src = f"data:image/png;base64,{row_user['foto']}" if row_user['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{f_src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏗️ PILARES ---
    if menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_filtro = st.selectbox("Filtrar Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata"] + df_cat['Nome'].tolist())
                c_num = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else int(df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()) + 1
                at, fr = (3, 2) if c_num % 2 != 0 else (2, 3)
                cols = st.columns(5); regs = []
                for i in range(at+fr):
                    b = cols[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==cat_filtro]['Nome'].tolist(), key=f"p{i}")
                    a = cols[i].number_input("Av", 0, key=f"a{i}")
                    if b != "Vazio": regs.append([f"PIL_{datetime.now().microsecond}_{i}", n_pilar, c_num, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_p, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        st.subheader("⚙️ Lançar Entrada ou Saída")
        with st.form("f_est"):
            sel_it = st.selectbox("Item", df_p['Nome'].unique())
            op = st.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd_un = st.number_input("Unidades Totais", 0)
            if st.form_submit_button("ATUALIZAR"):
                if op == "SAÍDA": df_e.loc[df_e['Nome'] == sel_it, 'Estoque_Total_Un'] -= qtd_un
                else: df_e.loc[df_e['Nome'] == sel_it, 'Estoque_Total_Un'] += qtd_un
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        st.divider()
        with st.expander("🔍 LISTA DE PRODUTOS"):
            for _, r in pd.merge(df_e, df_p, on="Nome").iterrows():
                u_b, t_t = get_config(r['Nome'], df_p)
                f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
                st.markdown(f'<div class="card"><b>{r["Nome"]}</b><br>{r["Estoque_Total_Un"]} un ({f} {t_t}s e {a} avulsos)</div>', unsafe_allow_html=True)

    # --- 🍶 CASCOS (COM ESTORNO NO HISTÓRICO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t_pend, t_hist, t_patio = st.tabs(["🔴 Pendentes", "📜 Histórico", "🏗️ Saldo Pátio"])
        
        with t_pend:
            with st.form("f_cas"):
                c1, c2, c3 = st.columns(3)
                cli, tipo_v, qtd_v = c1.text_input("Cliente").upper(), c2.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar Dívida"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, "", tipo_v, qtd_v, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} de {r['Vasilhame']}")
                if st.button(f"Baixa: {r['Cliente']} pagou", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t_hist:
            st.subheader("Baixas Recentes")
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                col_h1, col_h2 = st.columns([4, 1])
                col_h1.write(f"✅ {r['Cliente']} entregou {r['Quantidade']} de {r['Vasilhame']} (Baixa por: {r['QuemBaixou']})")
                if col_h2.button("ESTORNAR", key=f"est_{i}"):
                    # Devolve para DEVE
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.at[i, 'QuemBaixou'] = ""; df_cas.at[i, 'HoraBaixa'] = ""
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    # Tira do Pátio
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t_patio:
            c_r, c_c = st.columns(2)
            with c_r:
                st.markdown('<b style="color:#58a6ff">🍺 CERVEJAS</b>', unsafe_allow_html=True)
                for v in ["Romarinho", "600ml"]:
                    val = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {val} un ({val // 24} Engr.)")
                    if st.button(f"➕ Adicionar Engradado {v}", key=f"p_a_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 24
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
                st.divider()
                ret_r_t = st.selectbox("Saída Empresa Cerveja", ["Romarinho", "600ml"])
                ret_r_q = st.number_input("Qtd coletada", 1, key="ret_r_q")
                if st.button("Confirmar Saída Cerveja"):
                    df_patio.loc[df_patio['Vasilhame'] == ret_r_t, 'Total_Vazio'] -= ret_r_q
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

            with c_c:
                st.markdown('<b style="color:#f85149">🥤 COCA-COLA</b>', unsafe_allow_html=True)
                for v in ["Coca 1L", "Coca 2L"]:
                    val = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {val} un ({val // 6} Fardos)")
                    if st.button(f"➕ Adicionar Fardo {v}", key=f"p_a_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 6
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
                st.divider()
                ret_c_t = st.selectbox("Saída Empresa Coca", ["Coca 1L", "Coca 2L"])
                ret_c_q = st.number_input("Qtd coletada", 1, key="ret_c_q")
                if st.button("Confirmar Saída Coca"):
                    df_patio.loc[df_patio['Vasilhame'] == ret_c_t, 'Total_Vazio'] -= ret_c_q
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        t1, t2, t3 = st.tabs(["Item", "Categoria", "Gerenciar"])
        with t2:
            n_c = st.text_input("Nova Cat").upper()
            if st.button("Criar"): pd.concat([df_cat, pd.DataFrame([[n_c]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.rerun()
            s_c = st.selectbox("Apagar", df_cat['Nome'].unique())
            if st.button("Apagar Categoria"): df_cat[df_cat['Nome'] != s_c].to_csv(DB_FILES["cat"], index=False); st.rerun()
        with t1:
            with st.form("f_i"):
                cat = st.selectbox("Cat", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                nom = st.text_input("Nome").upper()
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_p, pd.DataFrame([[cat, nom, 0.0]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            t_nova = st.text_input("Nova Tarefa")
            if st.button("Adicionar"): pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_nova, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                if st.button(f"⭕ {r['Tarefa']}", key=f"t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M")
                    df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()
            else: st.success(f"✅ {r['Tarefa']} - {r['QuemFez']}")

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Equipe")
        with st.form("f_u"):
            c1, c2, c3, c4 = st.columns(4)
            u, n, s, a = c1.text_input("User"), c2.text_input("Nome"), c3.text_input("Senha"), c4.selectbox("Admin", ["NÃO", "SIM"])
            if st.form_submit_button("Salvar"): pd.concat([df_usr, pd.DataFrame([[u, n, s, a, "", ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 🏠 DASHBOARD ---
    elif menu == "🏠 Dashboard":
        st.title("🚀 Dashboard")
        st.metric("Estoque Total", df_e['Estoque_Total_Un'].sum())
