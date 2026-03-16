import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import json

# =================================================================
# 1. DESIGN & ESTILO (DARK PRESTIGE V17 - COMPLETO)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Cards de Estoque */
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; transition: 0.3s;
        text-align: center;
    }
    .product-card:hover { border-color: #58a6ff; background: #21262d; transform: translateY(-3px); }
    
    /* Cards de Tarefa */
    .task-card {
        background: #1c2128; border-left: 5px solid #d29922;
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
    }
    .task-done { border-left-color: #238636; opacity: 0.6; text-decoration: line-through; }
    
    /* Equipe Estilo Crachá */
    .user-card {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d; border-radius: 15px; padding: 20px;
        text-align: center; height: 100%;
    }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; margin-bottom: 10px; }
    
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; margin-bottom: 8px; }
    .badge-blue { background: #388bfd; color: white; }
    .badge-gold { background: #d29922; color: white; }
    
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V17 - ESTRUTURA COMPLETA)
# =================================================================
DB_FILES = {
    "prod": "p_v17.csv", "est": "e_v17.csv", "pil": "pil_v17.csv",
    "usr": "u_v17.csv", "cas": "c_v17.csv", "tar": "t_v17.csv", 
    "cat": "cat_v17.csv", "patio": "pat_v17.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg', 'QuemFez'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_i = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_i = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            df_i.to_csv(f, index=False)
    
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
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
# 3. LÓGICA DE LOGIN
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
                else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB_FILES.values()]

    # Sidebar
    row_u = df_usr[df_usr['user'] == u_logado].iloc[0]
    foto_src = f"data:image/png;base64,{row_u['foto']}" if row_u['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{foto_src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title(f"Bem-vindo, {n_logado}! 💎")
        df_j = pd.merge(df_e, df_p, on="Nome")
        val_est = (df_j['Estoque_Total_Un'] * df_j['Preco_Unitario']).sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Estoque", f"R$ {val_est:,.2f}")
        c2.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        hoje_check = datetime.now().strftime("%Y-%m-%d")
        pend = len(df_tar[((df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hoje_check)) & (df_tar['Status'] == "PENDENTE")])
        c3.metric("Tarefas de Hoje", pend)

    # --- 📦 ESTOQUE (CARDS BONITOS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Gestão de Estoque")
        with st.expander("➕ Lançar Movimentação"):
            with st.form("mov"):
                c1, c2, c3 = st.columns([2,1,1])
                sel = c1.selectbox("Produto", df_p['Nome'].unique())
                op = c2.radio("Tipo", ["ENTRADA", "SAÍDA"])
                qtd = c3.number_input("Quantidade", 1)
                if st.form_submit_button("Confirmar"):
                    df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (qtd if op == "ENTRADA" else -qtd)
                    df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        st.divider()
        df_full = pd.merge(df_e, df_p, on="Nome")
        cols_e = st.columns(3)
        for i, r in df_full.iterrows():
            ub, t_nome = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // ub, r['Estoque_Total_Un'] % ub
            with cols_e[i % 3]:
                st.markdown(f"""
                <div class="product-card">
                    <span class="badge badge-blue">{r['Categoria']}</span>
                    <h3>{r['Nome']}</h3>
                    <p style="font-size: 1.2em;"><b>{int(f)}</b> {t_nome}(s) e <b>{int(a)}</b> un.</p>
                </div>
                """, unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Estrutura de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Camada {cam_at}: Layout {atrav}x{frent}")
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                    a = cols_p[i].number_input("Avulsos", 0, key=f"a_{i}")
                    if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR"): pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 Pilar: {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        ub, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (ub + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (DEVEDORES + PATIO + TROCA) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2 = st.tabs(["🔴 Devedores", "🚚 Pátio e Trocas"])
        with t1:
            with st.form("d"):
                c1, c2, c3 = st.columns(3)
                cli, vas, q = c1.text_input("Cliente").upper(), c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar Dívida"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, q, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button("BAIXAR DÍVIDA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t2:
            st.subheader("🚚 Saída para Troca Empresa")
            with st.form("tr"):
                tv, qv = st.selectbox("O que saiu?", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Confirmar Saída"):
                    if df_patio.loc[df_patio['Vasilhame'] == tv, 'Total_Vazio'].values[0] >= qv:
                        df_patio.loc[df_patio['Vasilhame'] == tv, 'Total_Vazio'] -= qv; df_patio.to_csv(DB_FILES["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), "TROCA", tv, qv, "TROCA", n_logado, ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            st.divider()
            for _, r in df_patio.iterrows(): st.info(f"**Pátio {r['Vasilhame']}:** {int(r['Total_Vazio'])} un")

    # --- ✨ CADASTRO (CATEGORIA + PRODUTO) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        ta1, ta2 = st.tabs(["📦 Novo Produto", "📂 Nova Categoria"])
        with ta1:
            with st.form("p"):
                n, c, p = st.text_input("Nome").upper(), st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())))), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            nc = st.text_input("Nome da Categoria")
            if st.button("Criar Categoria"):
                pd.concat([df_cat, pd.DataFrame([[nc]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.success("Criada!"); st.rerun()

    # --- 📋 TAREFAS (BONITO + DATAS) ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.expander("➕ Nova Tarefa"):
                with st.form("t"):
                    d, tp = st.text_input("Tarefa"), st.selectbox("Tipo", ["Diária", "Data Específica"])
                    dt = st.date_input("Data")
                    if st.form_submit_button("Add"):
                        pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", tp, str(dt), ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        hj = datetime.now().strftime("%Y-%m-%d")
        for i, r in df_tar[(df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hj)].iterrows():
            st.markdown(f'<div class="task-card {"task-done" if r["Status"]=="OK" else ""}"><b>{r["Tarefa"]}</b> ({r["Tipo"]})</div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("CONCLUIR", key=f"t_{i}"):
                df_tar.loc[df_tar['ID'] == r['ID'], 'Status'] = "OK"; df_tar.loc[df_tar['ID'] == r['ID'], 'QuemFez'] = n_logado; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE (VISUAL CRACHÁ) ---
    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        if is_adm:
            with st.expander("👤 Novo Membro"):
                with st.form("u"):
                    l, n, s, a = st.columns(4)
                    li, ni, si, ai = l.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), a.selectbox("Adm", ["NÃO", "SIM"])
                    if st.form_submit_button("Add"):
                        pd.concat([df_usr, pd.DataFrame([[li, ni, si, ai, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        cols_eq = st.columns(4)
        for i, r in df_usr.iterrows():
            f = f"data:image/png;base64,{r['foto']}" if r['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            with cols_eq[i % 4]:
                st.markdown(f'<div class="user-card"><img src="{f}" class="avatar-round" width="90"><h4>{r["nome"]}</h4><span class="badge badge-blue">{"ADMIN" if r["is_admin"]=="SIM" else "EQUIPE"}</span></div>', unsafe_allow_html=True)

    # --- ⚙️ PERFIL & BACKUP ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Ajustes")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); b = io.BytesIO(); img.save(b, format="PNG")
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(b.getvalue()).decode()
            df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
        st.divider()
        st.download_button("💾 Backup Geral", json.dumps({k: pd.read_csv(v).to_dict() for k, v in DB_FILES.items()}), "backup_completo.json")
