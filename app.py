import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import time

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V210 (FINAL UNABRIDGED)
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
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    .welcome-text {
        text-align: center; font-size: 2.5em; font-weight: bold;
        color: #58a6ff; margin-top: 20vh;
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
    "prod": "prod_final.csv", "est": "est_final.csv", "pil": "pil_final.csv",
    "usr": "usr_final.csv", "cas": "cas_final.csv", "tar": "tar_final.csv", 
    "cat": "cat_final.csv", "patio": "patio_final.csv", "meta": "meta_final.csv"
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
    
    # Criar admin se não existir
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_FILES["usr"], index=False)

    # LÓGICA DE RESET MEIA-NOITE
    df_m = pd.read_csv(DB_FILES["meta"])
    hoje = datetime.now().strftime("%Y-%m-%d")
    if df_m.loc[df_m['Chave']=='ultima_limpeza', 'Valor'].values[0] != hoje:
        df_t = pd.read_csv(DB_FILES["tar"])
        df_t['Status'] = "PENDENTE"; df_t['QuemFez'] = ""; df_t['Horario'] = ""
        df_t.to_csv(DB_FILES["tar"], index=False)
        df_m.loc[df_m['Chave']=='ultima_limpeza', 'Valor'] = hoje; df_m.to_csv(DB_FILES["meta"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. LOGIN COM ANIMAÇÃO DE BOAS-VINDAS
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    login_area = st.empty()
    with login_area.container():
        st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
        with st.columns(3)[1]:
            with st.form("form_login"):
                u = st.text_input("Usuário").strip()
                s = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("ENTRAR"):
                    df_u = pd.read_csv(DB_FILES["usr"])
                    match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                    if not match.empty:
                        user_data = match.iloc[0]
                        login_area.empty()
                        # ANIMAÇÃO
                        st.markdown(f'<div class="welcome-text">Bem-vindo, {user_data["nome"]}! 💎</div>', unsafe_allow_html=True)
                        with st.columns(3)[1]:
                            with st.spinner("Acessando sistema..."):
                                time.sleep(2)
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': user_data['nome'], 'u_a': (user_data['is_admin']=='SIM')})
                        st.rerun()
                    else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR ---
    row_u = df_usr[df_usr['user'] == u_logado].iloc[0]
    src = f"data:image/png;base64,{row_u['foto']}" if row_u['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas Diárias", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Dashboard")
        val_est = (pd.merge(df_e, df_p, on="Nome")['Estoque_Total_Un'] * pd.merge(df_e, df_p, on="Nome")['Preco_Unitario']).sum()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Valor em Estoque</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Vasilhames no Pátio</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Progresso Diário</h4><h2>{len(df_tar[df_tar["Status"]=="OK"])}/{len(df_tar)}</h2></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Escolha o Pilar", ["+ NOVO PILAR"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ NOVO PILAR" else p_sel
            if n_pilar:
                cat_filtro = st.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                prods_cat = df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                max_cam = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                camada_atual = int(max_cam) + 1
                atrav, frent = (3, 2) if camada_atual % 2 != 0 else (2, 3)
                st.info(f"Configurando Camada {camada_atual} ({atrav} atrás, {frent} frente)")
                cols_p = st.columns(5); data_camada = []
                for i in range(atrav + frent):
                    beb = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods_cat, key=f"sel_{i}")
                    avs = cols_p[i].number_input("Avs", 0, key=f"av_{i}")
                    if beb != "Vazio": data_camada.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, camada_atual, i+1, beb, avs])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(data_camada, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_b, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_b + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        with st.form("f_est"):
            c1, c2, c3 = st.columns([2, 1, 1])
            s_i = c1.selectbox("Item", df_p['Nome'].unique())
            op = c2.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = c3.number_input("Unidades", 0)
            if st.form_submit_button("LANÇAR"):
                if op == "SAÍDA": df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        df_j = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_j.iterrows():
            u_b, t_t = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
            st.markdown(f'<div class="card"><b>{r["Nome"]}</b><br>{f} {t_t}s e {a} un | <b>R$ {r["Estoque_Total_Un"] * r["Preco_Unitario"]:.2f}</b></div>', unsafe_allow_html=True)

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        ta1, ta2, ta3 = st.tabs(["➕ Novo Item", "📂 Categorias", "🗑️ Remover"])
        with ta1:
            with st.form("f_i"):
                n_p = st.text_input("Nome").upper().strip()
                c_p = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                p_p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Cadastrar"):
                    if n_p in df_p['Nome'].values: st.error("Produto já existe!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[c_p, n_p, p_p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[n_p, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta3:
            item_r = st.selectbox("Apagar permanentemente", ["Selecione..."] + df_p['Nome'].tolist())
            if st.button("CONFIRMAR EXCLUSÃO") and item_r != "Selecione...":
                df_p[df_p['Nome'] != item_r].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != item_r].to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 📋 TAREFAS DIÁRIAS ---
    elif menu == "📋 Tarefas Diárias":
        st.title("📋 Checklist")
        if is_adm:
            with st.expander("⚙️ Gerenciar Tarefas"):
                t_n = st.text_input("Nova Tarefa")
                if st.button("SALVAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_n, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            is_ok = r['Status'] == "OK"
            st.markdown(f'<div class="task-card {"task-done" if is_ok else ""}"><b>{r["Tarefa"]}</b><br><small>{"✅ Feito por " + r["QuemFez"] if is_ok else "🟡 Pendente"}</small></div>', unsafe_allow_html=True)
            if not is_ok:
                if st.button(f"CONCLUIR", key=f"tk_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico", "🏗️ Pátio"])
        with t1:
            with st.form("f_c"):
                c1, c2, c3 = st.columns(3); cli = c1.text_input("Cliente").upper(); tip = c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]); q_c = c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, tip, q_c, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button("Receber", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t3:
            for i, v in enumerate(["Romarinho", "600ml", "Coca 1L", "Coca 2L"]):
                at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                st.write(f"**{v}:** {at} un")

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        if is_adm:
            with st.expander("👤 Adicionar Colaborador"):
                u_i = st.text_input("Login"); n_i = st.text_input("Nome"); s_i = st.text_input("Senha"); a_i = st.selectbox("Admin", ["NÃO", "SIM"])
                if st.button("Salvar Colaborador"):
                    pd.concat([df_usr, pd.DataFrame([[u_i, n_i, s_i, a_i, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        for i, r in df_usr.iterrows():
            st.markdown(f'<div class="card-equipe"><b>{r["nome"]}</b> (@{r["user"]}) | {r["is_admin"]} Admin</div>', unsafe_allow_html=True)

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
