import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import time

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V220 (UNABRIDGED & FIXED)
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
    .card-equipe {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d; border-radius: 15px; padding: 15px; margin-bottom: 10px;
    }
    .task-card {
        background-color: #1c2128; border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #d29922;
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
    .welcome-container {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 70vh; text-align: center;
    }
    .welcome-text {
        font-size: 3.5em; font-weight: bold; color: #58a6ff;
        text-shadow: 0px 0px 20px rgba(88, 166, 255, 0.5);
    }
    .stButton>button {
        border-radius: 8px; font-weight: 600; background-color: #21262d; 
        border: 1px solid #30363d; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS COMPLETA
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
# 3. LOGIN COM ANIMAÇÃO PREMIUM
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    login_placeholder = st.empty()
    with login_placeholder.container():
        st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
        with st.columns(3)[1]:
            with st.form("form_login"):
                u = st.text_input("Usuário").strip()
                s = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("ENTRAR NO SISTEMA"):
                    df_u = pd.read_csv(DB_FILES["usr"])
                    match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                    if not match.empty:
                        user_info = match.iloc[0]
                        login_placeholder.empty()
                        # EXECUÇÃO DA ANIMAÇÃO
                        st.markdown(f'<div class="welcome-container"><div class="welcome-text">Bem-vindo, {user_info["nome"]}! 💎</div></div>', unsafe_allow_html=True)
                        with st.columns(5)[2]:
                            with st.spinner(""): time.sleep(2.0)
                        
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': user_info['nome'], 'u_a': (user_info['is_admin']=='SIM')})
                        st.rerun()
                    else: st.error("Credenciais Inválidas")
else:
    # CARREGAMENTO GLOBAL DOS DADOS
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR COMPLETA ---
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
        c1.markdown(f'<div class="metric-card"><h4>Patrimônio Total</h4><h2 style="color:#238636;">R$ {val_est:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Vasilhames no Pátio</h4><h2>{int(df_patio["Total_Vazio"].sum())} un</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Checklist Hoje</h4><h2>{len(df_tar[df_tar["Status"]=="OK"])}/{len(df_tar)}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE (FUNÇÕES COMPLETAS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Gestão de Inventário")
        with st.form("form_estoque"):
            col1, col2, col3 = st.columns([2,1,1])
            item_sel = col1.selectbox("Selecione o Item", df_p['Nome'].unique())
            acao = col2.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd_un = col3.number_input("Quantidade em Unidades", min_value=1, step=1)
            if st.form_submit_button("CONFIRMAR LANÇAMENTO"):
                if acao == "SAÍDA":
                    df_e.loc[df_e['Nome'] == item_sel, 'Estoque_Total_Un'] -= qtd_un
                else:
                    df_e.loc[df_e['Nome'] == item_sel, 'Estoque_Total_Un'] += qtd_un
                df_e.to_csv(DB_FILES["est"], index=False); st.success(f"{acao} realizada!"); time.sleep(0.5); st.rerun()
        
        st.divider()
        df_join = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_join.iterrows():
            u_b, tipo_un = get_config(r['Nome'], df_p)
            fardos = int(r['Estoque_Total_Un'] // u_b)
            avulsos = int(r['Estoque_Total_Un'] % u_b)
            valor_total = r['Estoque_Total_Un'] * r['Preco_Unitario']
            st.markdown(f'''
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{r["Nome"]}</b>
                        <span style="color:#58a6ff;">{r["Categoria"]}</span>
                    </div>
                    <div style="font-size:1.2em; margin-top:5px;">
                        {fardos} {tipo_un}(s) e {avulsos} un.
                    </div>
                    <div style="color:#238636; font-size:0.9em;">Valor em estoque: R$ {valor_total:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

    # --- 🏗️ PILARES (LOGICA 3/2 E BAIXA AUTOMATICA) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Estrutura de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Selecione o Pilar", ["+ NOVO PILAR"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Novo Pilar").upper() if p_sel == "+ NOVO PILAR" else p_sel
            if n_pilar:
                cat_f = st.selectbox("Filtrar Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                prods_f = df_p[df_p['Categoria'] == cat_f]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_atual = int(max_c) + 1
                atrav, frent = (3, 2) if cam_atual % 2 != 0 else (2, 3)
                st.info(f"Configurando Camada {cam_atual} ({atrav} atrás, {frent} frente)")
                cols_p = st.columns(5); cam_data = []
                for i in range(atrav + frent):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods_f, key=f"p_{i}")
                    a = cols_p[i].number_input("Avulsos", 0, key=f"a_{i}")
                    if b != "Vazio": cam_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_atual, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(cam_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    pos = int(r['Posicao']) - 1
                    if c_grid[pos].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_b, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_b + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (DEVEDORES, PÁTIO E HISTÓRICO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "🏗️ Controle do Pátio", "📜 Histórico de Baixas"])
        
        with t1:
            with st.form("form_casco"):
                c1, c2, c3 = st.columns(3)
                cli = c1.text_input("Nome do Cliente").upper().strip()
                vasi = c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
                qtd_v = c3.number_input("Qtd Devolvida", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    novo_c = pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vasi, qtd_v, "DEVE", "", ""]], columns=df_cas.columns)
                    pd.concat([df_cas, novo_c]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            st.subheader("Clientes em Aberto")
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                col_a, col_b = st.columns([4, 1])
                col_a.warning(f"⚠️ **{r['Cliente']}** está devendo **{r['Quantidade']}** un de **{r['Vasilhame']}** (Lançado em {r['Data']})")
                if col_b.button("DAR BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t2:
            st.subheader("Estoque Físico de Vasilhames Vazios")
            cols_patio = st.columns(4)
            for i, row in df_patio.iterrows():
                with cols_patio[i]:
                    st.metric(row['Vasilhame'], f"{int(row['Total_Vazio'])} un")
                    nova_qtd = st.number_input("Ajustar", value=int(row['Total_Vazio']), key=f"pat_{i}")
                    if st.button("SALVAR", key=f"btn_pat_{i}"):
                        df_patio.at[i, 'Total_Vazio'] = nova_qtd
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t3:
            st.subheader("Últimas Baixas Realizadas")
            df_pagos = df_cas[df_cas['Status']=="PAGO"].tail(10)
            if not df_pagos.empty:
                st.table(df_pagos[['Data', 'Cliente', 'Vasilhame', 'Quantidade', 'QuemBaixou', 'HoraBaixa']])
            else: st.info("Nenhum histórico recente.")

    # --- ✨ CADASTRO (TRAVA DE DUPLICIDADE E REMOÇÃO) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Central de Cadastro")
        ta1, ta2, ta3 = st.tabs(["➕ Novo Produto", "📂 Categorias", "🗑️ Área de Exclusão"])
        with ta1:
            with st.form("form_cad"):
                nome_n = st.text_input("Nome do Produto").upper().strip()
                cate_n = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                prec_n = st.number_input("Preço Unitário (Venda)", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    if nome_n in df_p['Nome'].values: st.error("Este produto já existe!")
                    elif nome_n == "": st.error("Nome não pode ser vazio!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[cate_n, nome_n, prec_n]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[nome_n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta3:
            st.warning("CUIDADO: Apagar um produto removerá seu estoque e pilares vinculados.")
            item_del = st.selectbox("Selecione o item para excluir", ["Selecione..."] + df_p['Nome'].tolist())
            if st.button("CONFIRMAR EXCLUSÃO DEFINITIVA") and item_del != "Selecione...":
                df_p[df_p['Nome'] != item_del].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != item_del].to_csv(DB_FILES["est"], index=False)
                df_pil[df_pil['Bebida'] != item_del].to_csv(DB_FILES["pil"], index=False); st.rerun()

    # --- 📋 TAREFAS (RESET AUTOMATICO 00:00) ---
    elif menu == "📋 Tarefas Diárias":
        st.title("📋 Checklist Operacional")
        if is_adm:
            with st.expander("➕ Gerenciar Rotina"):
                nt = st.text_input("Nova Tarefa")
                if st.button("ADICIONAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", nt, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            st.markdown(f'<div class="task-card { "task-done" if r["Status"]=="OK" else "" }"><b>{r["Tarefa"]}</b><br><small>{"✅ Finalizado por " + r["QuemFez"] if r["Status"]=="OK" else "🟡 Aguardando..."}</small></div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button(f"MARCAR COMO FEITO", key=f"tar_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Gestão de Equipe")
        if is_adm:
            with st.expander("👤 Novo Colaborador"):
                u, n, s, a = st.columns(4)
                ui, ni, si, ai = u.text_input("Login"), n.text_input("Nome"), s.text_input("Senha"), a.selectbox("Admin", ["NÃO", "SIM"])
                if st.button("SALVAR"):
                    pd.concat([df_usr, pd.DataFrame([[ui, ni, si, ai, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        for _, r in df_usr.iterrows():
            st.markdown(f'<div class="card-equipe"><b>{r["nome"]}</b> (@{r["user"]}) | Admin: {r["is_admin"]}</div>', unsafe_allow_html=True)

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações de Perfil")
        upload = st.file_uploader("Trocar foto de perfil", type=['png', 'jpg', 'jpeg'])
        if st.button("ATUALIZAR FOTO") and upload:
            img = Image.open(upload).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
