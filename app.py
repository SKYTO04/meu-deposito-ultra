import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V180 (FULL SYSTEM)
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
        border-left: 5px solid #58a6ff;
    }
    .card-equipe {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .task-card {
        background-color: #1c2128;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid #d29922;
    }
    .task-done { border-left: 4px solid #238636; opacity: 0.7; }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .metric-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 10px;
        padding: 15px; text-align: center;
    }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 8px; font-weight: 600; background-color: #21262d; 
        border: 1px solid #30363d; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E LÓGICA DE RESET 00:00
# =================================================================
DB_FILES = {
    "prod": "produtos_v180.csv", "est": "estoque_v180.csv", "pil": "pilares_v180.csv",
    "usr": "usuarios_v180.csv", "cas": "cascos_v180.csv", "tar": "tarefas_v180.csv", 
    "cat": "categorias_v180.csv", "patio": "patio_v180.csv", "meta": "metadata_v180.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio'],
        DB_FILES["meta"]: ['Chave', 'Valor']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_i = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_i = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            if f == DB_FILES["meta"]:
                df_i = pd.DataFrame([["ultima_limpeza", datetime.now().strftime("%Y-%m-%d")]], columns=c)
            df_i.to_csv(f, index=False)
    
    # Garantia de Administrador Padrão
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_FILES["usr"], index=False)
    
    # RESET DE TAREFAS À MEIA-NOITE
    df_m = pd.read_csv(DB_FILES["meta"])
    hoje = datetime.now().strftime("%Y-%m-%d")
    if df_m.loc[df_m['Chave']=='ultima_limpeza', 'Valor'].values[0] != hoje:
        df_t = pd.read_csv(DB_FILES["tar"])
        df_t['Status'] = "PENDENTE"
        df_t['QuemFez'] = ""
        df_t['Horario'] = ""
        df_t.to_csv(DB_FILES["tar"], index=False)
        df_m.loc[df_m['Chave']=='ultima_limpeza', 'Valor'] = hoje
        df_m.to_csv(DB_FILES["meta"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. AUTENTICAÇÃO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso Negado")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR ---
    row_u = df_usr[df_usr['user'] == u_logado].iloc[0]
    src = f"data:image/png;base64,{row_u['foto']}" if row_u['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas Diárias", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Dashboard")
        val_est = (pd.merge(df_e, df_p, on="Nome")['Estoque_Total_Un'] * pd.merge(df_e, df_p, on="Nome")['Preco_Unitario']).sum()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Valor Estoque</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Pátio (Vasilhames)</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Tarefas Pendentes</h4><h2 style="color:#d29922;">{len(df_tar[df_tar["Status"]=="PENDENTE"])}</h2></div>', unsafe_allow_html=True)

    # --- 📋 TAREFAS DIÁRIAS (RESET AUTOMÁTICO) ---
    elif menu == "📋 Tarefas Diárias":
        st.title("📋 Checklist da Rotina")
        if is_adm:
            with st.expander("⚙️ Gerenciar Tarefas de Rotina"):
                t_n = st.text_input("Nova Tarefa Recorrente")
                if st.button("SALVAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_n, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
                st.divider()
                for i, r in df_tar.iterrows():
                    col1, col2 = st.columns([4,1])
                    col1.write(f"• {r['Tarefa']}")
                    if col2.button("🗑️", key=f"dt_{i}"):
                        df_tar.drop(i).to_csv(DB_FILES["tar"], index=False); st.rerun()

        for i, r in df_tar.iterrows():
            is_ok = r['Status'] == "OK"
            st.markdown(f'<div class="task-card {"task-done" if is_ok else ""}"><b>{r["Tarefa"]}</b><br><small>{"✅ Feito por " + r["QuemFez"] if is_ok else "🟡 Pendente"}</small></div>', unsafe_allow_html=True)
            if not is_ok:
                if st.button(f"CONCLUIR", key=f"tk_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M")
                    df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Nossa Equipe")
        if is_adm:
            with st.expander("👤 Adicionar Colaborador"):
                with st.form("f_equipe"):
                    u, n, s, a = st.columns(4)
                    u_i = u.text_input("Login")
                    n_i = n.text_input("Nome")
                    s_i = s.text_input("Senha")
                    a_i = a.selectbox("Admin", ["NÃO", "SIM"])
                    if st.form_submit_button("ADICIONAR"):
                        pd.concat([df_usr, pd.DataFrame([[u_i, n_i, s_i, a_i, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        
        st.divider()
        cols = st.columns(2)
        for i, r in df_usr.iterrows():
            f = f"data:image/png;base64,{r['foto']}" if r['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            with cols[i % 2]:
                st.markdown(f'''
                <div class="card-equipe">
                    <div style="display:flex; align-items:center; gap:15px;">
                        <img src="{f}" class="avatar-round" width="60" height="60">
                        <div><b>{r['nome']}</b><br><small>{r['user']} | { "Gerente" if r['is_admin'] == "SIM" else "Equipe"}</small></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                if is_adm and r['user'] != 'admin':
                    if st.button(f"Remover {r['user']}", key=f"rem_{i}"):
                        df_usr.drop(i).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        with st.form("f_est"):
            c1, c2, c3 = st.columns([2, 1, 1])
            s_i = c1.selectbox("Item", df_p['Nome'].unique())
            op = c2.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = c3.number_input("Qtd Unidades", 0)
            if st.form_submit_button("LANÇAR"):
                if op == "SAÍDA": df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        st.divider()
        df_j = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_j.iterrows():
            u_b, t_t = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
            st.markdown(f'<div class="card"><b>{r["Nome"]}</b><br>{f} {t_t}s e {a} un | <b>R$ {r["Estoque_Total_Un"] * r["Preco_Unitario"]:.2f}</b></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Pilares")
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

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico", "🏗️ Pátio"])
        with t1:
            with st.form("f_c"):
                c1, c2, c3 = st.columns(3); cli = c1.text_input("Cliente").upper(); tip = c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]); q_c = c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, tip, q_c, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button("Receber Casco", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t2:
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                ch1, ch2 = st.columns([4,1]); ch1.write(f"✅ {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
                if ch2.button("ESTORNAR", key=f"est_{i}"):
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB_FILES["cas"], index=False); df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t3:
            c_c1, c_c2 = st.columns(2)
            for i, v in enumerate(["Romarinho", "600ml", "Coca 1L", "Coca 2L"]):
                at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                with (c_c1 if i < 2 else c_c2):
                    st.write(f"**{v}:** {at} un")
                    if st.button(f"➕ Add Vol {v}", key=f"p_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += (24 if i < 2 else 6); df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        ta1, ta2 = st.tabs(["Item", "Categorias"])
        with ta1:
            with st.form("f_i"):
                n_p = st.text_input("Nome").upper(); c_p = st.selectbox("Cat", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()); p_p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c_p, n_p, p_p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n_p, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            n_c = st.text_input("Nova Cat").upper()
            if st.button("Criar"): pd.concat([df_cat, pd.DataFrame([[n_c]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
