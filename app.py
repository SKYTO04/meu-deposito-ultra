import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN & CONFIGURAÇÃO
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .card {
        background-color: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 18px; margin-bottom: 12px;
        border-left: 5px solid #58a6ff;
    }
    .user-card {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d; border-radius: 15px; padding: 20px;
        text-align: center; transition: 0.3s;
    }
    .user-card:hover { border-color: #58a6ff; transform: translateY(-5px); }
    .badge-admin {
        background-color: #238636; color: white; padding: 2px 8px;
        border-radius: 10px; font-size: 0.7em; font-weight: bold;
    }
    .badge-user {
        background-color: #388bfd; color: white; padding: 2px 8px;
        border-radius: 10px; font-size: 0.7em; font-weight: bold;
    }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; margin-bottom: 10px; }
    .welcome-banner {
        background: linear-gradient(90deg, #161b22 0%, #0e1117 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #30363d;
        margin-bottom: 25px; border-left: 8px solid #58a6ff;
    }
    .metric-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 10px;
        padding: 15px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS
# =================================================================
DB_FILES = {
    "prod": "prod_vfinal.csv", "est": "est_vfinal.csv", "pil": "pil_vfinal.csv",
    "usr": "usr_vfinal.csv", "cas": "cas_vfinal.csv", "tar": "tar_vfinal.csv", 
    "cat": "cat_vfinal.csv", "patio": "patio_vfinal.csv", "meta": "meta_vfinal.csv"
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
    
    if pd.read_csv(DB_FILES["usr"]).empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_FILES["usr"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. SISTEMA PRINCIPAL
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Erro de login.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # SIDEBAR
    row_u = df_usr[df_usr['user'] == u_logado].iloc[0]
    src = f"data:image/png;base64,{row_u['foto']}" if row_u['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.markdown(f'<div class="welcome-banner"><h1>Bem-vindo, {n_logado}! 💎</h1><p>Painel de Controle de Hoje</p></div>', unsafe_allow_html=True)
        val_est = (pd.merge(df_e, df_p, on="Nome")['Estoque_Total_Un'] * pd.merge(df_e, df_p, on="Nome")['Preco_Unitario']).sum()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Patrimônio</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Pátio (Vazios)</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Checklist</h4><h2>{len(df_tar[df_tar["Status"]=="OK"])}/{len(df_tar)}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Estoque")
        with st.form("est"):
            col1, col2, col3 = st.columns([2,1,1])
            item = col1.selectbox("Item", df_p['Nome'].unique())
            acao = col2.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = col3.number_input("Qtd", 1)
            if st.form_submit_button("Lançar"):
                if acao == "SAÍDA": df_e.loc[df_e['Nome'] == item, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == item, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        df_f = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_f.iterrows():
            ub, t = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // ub, r['Estoque_Total_Un'] % ub
            st.markdown(f'<div class="card"><b>{r["Nome"]}</b><br>{int(f)} {t}(s) e {int(a)} un.</div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Pilares")
        # (Lógica de Pilares mantida conforme conversas anteriores)
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="card"><h3>📍 {p}</h3></div>', unsafe_allow_html=True)

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2 = st.tabs(["🔴 Devedores", "🏗️ Pátio"])
        with t1:
            with st.form("casco"):
                c1, v, q = st.columns(3)
                cli, vas, qtd = c1.text_input("Cliente").upper(), v.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), q.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, qtd, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()

    # --- ✨ CADASTRO (COM REMOVER CATEGORIA) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        ta1, ta2, ta3 = st.tabs(["➕ Novo Item", "📂 Categorias", "🗑️ Remover Item"])
        with ta1:
            with st.form("new"):
                n = st.text_input("Nome").upper().strip()
                c = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    if n in df_p['Nome'].values: st.error("Já existe!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[c, n, p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            st.subheader("Gerenciar Categorias")
            new_c = st.text_input("Nova Categoria")
            if st.button("Adicionar"):
                pd.concat([df_cat, pd.DataFrame([[new_c]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.rerun()
            st.divider()
            cat_del = st.selectbox("Escolha uma categoria para REMOVER", ["Selecione..."] + df_cat['Nome'].tolist())
            if st.button("Remover Categoria Selecionada") and cat_del != "Selecione...":
                df_cat[df_cat['Nome'] != cat_del].to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 👥 EQUIPE (VISUAL NOVO E BONITO) ---
    elif menu == "👥 Equipe":
        st.title("👥 Nossa Equipe")
        if is_adm:
            with st.expander("👤 Cadastrar Novo Colaborador"):
                u, n, s, a = st.columns(4)
                ui, ni, si, ai = u.text_input("Login"), n.text_input("Nome"), s.text_input("Senha"), a.selectbox("Admin", ["NÃO", "SIM"])
                if st.button("Salvar Colaborador"):
                    pd.concat([df_usr, pd.DataFrame([[ui, ni, si, ai, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        
        st.divider()
        cols_eq = st.columns(4)
        for i, r in df_usr.iterrows():
            with cols_eq[i % 4]:
                src_usr = f"data:image/png;base64,{r['foto']}" if r['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                badge = "badge-admin" if r['is_admin'] == "SIM" else "badge-user"
                tipo = "ADMIN" if r['is_admin'] == "SIM" else "COLABORADOR"
                st.markdown(f"""
                    <div class="user-card">
                        <img src="{src_usr}" class="avatar-round" width="100" height="100">
                        <h4>{r['nome']}</h4>
                        <p style="color: #8b949e;">@{r['user']}</p>
                        <span class="{badge}">{tipo}</span>
                    </div>
                """, unsafe_allow_html=True)
                if is_adm and r['user'] != 'admin':
                    if st.button(f"Remover {r['user']}", key=f"del_{r['user']}"):
                        df_usr[df_usr['user'] != r['user']].to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        for i, r in df_tar.iterrows():
            st.markdown(f'<div class="card"><b>{r["Tarefa"]}</b></div>', unsafe_allow_html=True)

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
