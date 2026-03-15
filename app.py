import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import time

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V225 (ULTRA STABLE ANIMATION)
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
    .welcome-container {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 80vh; text-align: center;
        background-color: #0E1117;
    }
    .welcome-text {
        font-size: 3.5em; font-weight: bold; color: #58a6ff;
        text-shadow: 0px 0px 20px rgba(88, 166, 255, 0.5);
        animation: fadeIn 1.5s;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .metric-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 10px;
        padding: 15px; text-align: center;
    }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    .task-card {
        background-color: #1c2128; border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #d29922;
    }
    .task-done { border-left: 4px solid #238636; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRA E BANCO DE DADOS (SEM CORTES)
# =================================================================
DB_FILES = {
    "prod": "prod_f.csv", "est": "est_f.csv", "pil": "pil_f.csv",
    "usr": "usr_f.csv", "cas": "cas_f.csv", "tar": "tar_f.csv", 
    "cat": "cat_f.csv", "patio": "patio_f.csv", "meta": "meta_f.csv"
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
# 3. LÓGICA DE NAVEGAÇÃO E ANIMAÇÃO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'em_transicao' not in st.session_state: st.session_state['em_transicao'] = False

# TELA DE LOGIN
if not st.session_state['autenticado'] and not st.session_state['em_transicao']:
    st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login_form"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({
                        'em_transicao': True, 
                        'u_l': u, 
                        'u_n': match.iloc[0]['nome'], 
                        'u_a': (match.iloc[0]['is_admin']=='SIM')
                    })
                    st.rerun()
                else: st.error("Acesso Negado")

# TELA DE ANIMAÇÃO (O SEGREDO PARA NÃO FICAR BRANCO)
elif st.session_state['em_transicao']:
    st.markdown(f"""
        <div class="welcome-container">
            <div class="welcome-text">Bem-vindo, {st.session_state['u_n']}! 💎</div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.0)
    st.session_state['em_transicao'] = False
    st.session_state['autenticado'] = True
    st.rerun()

# SISTEMA PRINCIPAL
elif st.session_state['autenticado']:
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
        c1.markdown(f'<div class="metric-card"><h4>Patrimônio</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Pátio (Vazios)</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Checklist</h4><h2>{len(df_tar[df_tar["Status"]=="OK"])}/{len(df_tar)}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE (COMPLETO) ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        with st.form("f_est"):
            c1, c2, c3 = st.columns([2,1,1])
            s_i = c1.selectbox("Item", df_p['Nome'].unique())
            op = c2.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = c3.number_input("Qtd (Unidades)", 1)
            if st.form_submit_button("LANÇAR"):
                if op == "SAÍDA": df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == s_i, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        df_j = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_j.iterrows():
            u_b, t_u = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
            st.markdown(f'<div class="card"><b>{r["Nome"]}</b><br>{int(f)} {t_u}(s) e {int(a)} un | <span style="color:#238636;">R$ {r["Estoque_Total_Un"]*r["Preco_Unitario"]:,.2f}</span></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2 INTEGRAL) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Pilares")
        with st.expander("🧱 Adicionar Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO PILAR"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO PILAR" else p_sel
            if n_pilar:
                cat_f = st.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                prods_f = df_p[df_p['Categoria'] == cat_f]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods_f, key=f"p_{i}")
                    a = cols_p[i].number_input("Avs", 0, key=f"a_{i}")
                    if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR"): pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

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

    # --- 🍶 CASCOS (DEVEDORES E PÁTIO INTEGRADOS) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "🏗️ Pátio", "📜 Histórico"])
        with t1:
            with st.form("f_c"):
                c1, c2, c3 = st.columns(3)
                cli, vasi, qv = c1.text_input("Cliente").upper(), c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vasi, qv, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                col_a, col_b = st.columns([4,1])
                col_a.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if col_b.button("BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t2:
            for i, r in df_patio.iterrows():
                st.write(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} un")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        with st.form("f_cad"):
            n, c, p = st.columns(3)
            ni, ci, pi = n.text_input("Nome").upper(), c.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()), p.number_input("Preço", 0.0)
            if st.form_submit_button("SALVAR"):
                if ni and ni not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[ci, ni, pi]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[ni, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas Diárias":
        st.title("📋 Checklist")
        for i, r in df_tar.iterrows():
            st.markdown(f'<div class="task-card {"task-done" if r["Status"]=="OK" else ""}"><b>{r["Tarefa"]}</b></div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("FEITO", key=f"t_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
