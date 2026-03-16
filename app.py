import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN & CONFIGURAÇÃO (ESTÁVEL - DARK MODE)
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
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .welcome-banner {
        background: linear-gradient(90deg, #161b22 0%, #0e1117 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #30363d;
        margin-bottom: 25px; border-left: 8px solid #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS COMPLETO
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
# 3. AUTENTICAÇÃO SIMPLIFICADA (SEM ERRO DE TELA BRANCA)
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login_direct"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR SISTEMA"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Usuário ou Senha incorretos.")
else:
    # CARREGAMENTO GLOBAL
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # SIDEBAR
    row_u = df_usr[df_usr['user'] == u_logado].iloc[0]
    src = f"data:image/png;base64,{row_u['foto']}" if row_u['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas Diárias", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD (BEM-VINDO AQUI) ---
    if menu == "🏠 Dashboard":
        st.markdown(f'<div class="welcome-banner"><h1>Bem-vindo, {n_logado}! 💎</h1><p>{datetime.now().strftime("%d/%m/%Y")}</p></div>', unsafe_allow_html=True)
        val_est = (pd.merge(df_e, df_p, on="Nome")['Estoque_Total_Un'] * pd.merge(df_e, df_p, on="Nome")['Preco_Unitario']).sum()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Patrimônio</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Pátio (Vazios)</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Checklist</h4><h2>{len(df_tar[df_tar["Status"]=="OK"])}/{len(df_tar)}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE (FUNÇÕES COMPLETAS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Gestão de Estoque")
        with st.form("lancar_est"):
            col1, col2, col3 = st.columns([2,1,1])
            item = col1.selectbox("Produto", df_p['Nome'].unique())
            acao = col2.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = col3.number_input("Unidades", 1)
            if st.form_submit_button("Lançar"):
                if acao == "SAÍDA": df_e.loc[df_e['Nome'] == item, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == item, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        st.divider()
        df_full = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_full.iterrows():
            u_b, tipo = get_config(r['Nome'], df_p)
            f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
            st.markdown(f'''
                <div class="card">
                    <b>{r["Nome"]}</b> ({r["Categoria"]})<br>
                    {int(f)} {tipo}(s) e {int(a)} un. | <span style="color:#238636;">R$ {r["Estoque_Total_Un"]*r["Preco_Unitario"]:,.2f}</span>
                </div>
            ''', unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2 E BAIXA AUTOMÁTICA) ---
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
                if st.button("SALVAR CAMADA"): pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

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

    # --- 🍶 CASCOS (DEVEDORES, PÁTIO E HISTÓRICO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Cascos")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "🏗️ Pátio (Vazios)", "📜 Histórico"])
        with t1:
            with st.form("cas_f"):
                c1, c2, c3 = st.columns(3)
                cli, vas, qv = c1.text_input("Cliente").upper(), c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, qv, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
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
                novo_v = st.number_input(f"Ajustar {r['Vasilhame']}", value=int(r['Total_Vazio']), key=f"adj_{i}")
                if st.button("Salvar", key=f"btn_{i}"):
                    df_patio.at[i, 'Total_Vazio'] = novo_v; df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t3:
            st.table(df_cas[df_cas['Status']=="PAGO"].tail(10))

    # --- ✨ CADASTRO (TODAS AS ABAS: ITEM, CATEGORIA E REMOVER) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Central de Cadastro")
        ta1, ta2, ta3 = st.tabs(["➕ Novo Item", "📂 Categorias", "🗑️ Remover Item"])
        with ta1:
            with st.form("f_new"):
                n_p = st.text_input("Nome").upper().strip()
                c_p = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                p_p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Cadastrar"):
                    if n_p in df_p['Nome'].values: st.error("Produto já existe!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[c_p, n_p, p_p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[n_p, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            new_cat = st.text_input("Nome da Categoria").title()
            if st.button("Adicionar Categoria"):
                pd.concat([df_cat, pd.DataFrame([[new_cat]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.rerun()
        with ta3:
            item_del = st.selectbox("Escolha o item para APAGAR", ["Selecione..."] + df_p['Nome'].tolist())
            if st.button("EXCLUIR DEFINITIVAMENTE") and item_del != "Selecione...":
                df_p[df_p['Nome'] != item_del].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != item_del].to_csv(DB_FILES["est"], index=False)
                df_pil[df_pil['Bebida'] != item_del].to_csv(DB_FILES["pil"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas Diárias":
        st.title("📋 Checklist")
        if is_adm:
            with st.expander("Nova Tarefa"):
                nt = st.text_input("Descrição")
                if st.button("Salvar"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", nt, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            st.markdown(f'<div class="task-card {"task-done" if r["Status"]=="OK" else ""}"><b>{r["Tarefa"]}</b></div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("CONCLUIR", key=f"t_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
