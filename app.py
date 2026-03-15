import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V150
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
    .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; background-color: #21262d; 
        border: 1px solid #30363d; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
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
    "prod": "produtos_v150.csv", "est": "estoque_v150.csv", "pil": "pilares_v150.csv",
    "usr": "usuarios_v150.csv", "cas": "cascos_v150.csv", "tar": "tarefas_v150.csv", 
    "cat": "categorias_v150.csv", "patio": "patio_v150.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
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
        else:
            # Garante que a coluna Preco_Unitario existe
            df = pd.read_csv(f)
            if f == DB_FILES["prod"] and 'Preco_Unitario' not in df.columns:
                df['Preco_Unitario'] = 0.0
                df.to_csv(f, index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. INTERFACE
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

    # --- 🏠 DASHBOARD (COM TOTAL EM REAIS) ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Painel Geral")
        
        # Cálculo de valor total
        df_total = pd.merge(df_e, df_p, on="Nome")
        df_total['Valor_Total'] = df_total['Estoque_Total_Un'] * df_total['Preco_Unitario']
        valor_estoque = df_total['Valor_Total'].sum()
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><h4>Estoque Total</h4><h2>{int(df_e["Estoque_Total_Un"].sum())} un</h2></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><h4>Valor em Mercadoria</h4><h2 style="color:#238636;">R$ {valor_estoque:,.2f}</h2></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><h4>Cascos Devedores</h4><h2 style="color:#f85149;">{len(df_cas[df_cas["Status"]=="DEVE"])}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        with st.form("f_est"):
            col1, col2, col3 = st.columns([2, 1, 1])
            sel_it = col1.selectbox("Item", df_p['Nome'].unique())
            op = col2.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd_un = col3.number_input("Qtd Unidades", 0)
            if st.form_submit_button("ATUALIZAR ESTOQUE"):
                if op == "SAÍDA": df_e.loc[df_e['Nome'] == sel_it, 'Estoque_Total_Un'] -= qtd_un
                else: df_e.loc[df_e['Nome'] == sel_it, 'Estoque_Total_Un'] += qtd_un
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        
        st.divider()
        with st.expander("🔍 VER LISTA COMPLETA"):
            df_join = pd.merge(df_e, df_p, on="Nome")
            for _, r in df_join.iterrows():
                u_b, t_t = get_config(r['Nome'], df_p)
                f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
                valor_it = r['Estoque_Total_Un'] * r['Preco_Unitario']
                st.markdown(f'''
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r["Nome"]}</b> | <small>{r["Categoria"]}</small><br>{f} {t_t}s e {a} avulsos</div>
                        <div style="text-align:right"><b>R$ {valor_it:.2f}</b><br><small>{r["Estoque_Total_Un"]} un</small></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

    # --- ✨ CADASTRO (BONITO E COM PREÇO) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Produtos")
        
        t1, t2 = st.tabs(["➕ Cadastrar Novo Item", "📂 Gerenciar Categorias"])
        
        with t1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            with st.form("f_novo_prod"):
                c1, c2 = st.columns(2)
                nome_n = c1.text_input("Nome do Produto").upper()
                cat_n = c2.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                
                c3, c4 = st.columns(2)
                preco_n = c3.number_input("Preço de Venda (Unidade)", min_value=0.0, step=0.05, format="%.2f")
                st.info("O preço é usado para calcular o valor total do seu estoque no Dashboard.")
                
                if st.form_submit_button("✅ SALVAR PRODUTO"):
                    if nome_n:
                        pd.concat([df_p, pd.DataFrame([[cat_n, nome_n, preco_n]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[nome_n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False)
                        st.success(f"{nome_n} adicionado com sucesso!")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with t2:
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.subheader("Nova Categoria")
                n_c = st.text_input("Nome").upper()
                if st.button("CRIAR CATEGORIA"):
                    pd.concat([df_cat, pd.DataFrame([[n_c]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.rerun()
            with col_c2:
                st.subheader("Remover Categoria")
                s_c = st.selectbox("Escolha", df_cat['Nome'].unique())
                if st.button("❌ APAGAR DEFINITIVAMENTE"):
                    df_cat[df_cat['Nome'] != s_c].to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        # Mantendo lógica original de camadas e baixas
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="card"><h3>📍 {p}</h3>', unsafe_allow_html=True)
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
        st.title("🍶 Vasilhames")
        t_p, t_h, t_pa = st.tabs(["🔴 Pendentes", "📜 Histórico/Estorno", "🏗️ Pátio"])
        
        with t_p:
            with st.form("f_c"):
                c1, c2, c3 = st.columns(3)
                cli, tipo, qtd = c1.text_input("Cliente").upper(), c2.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, "", tipo, qtd, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"{r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button(f"Receber", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t_h:
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                c_h1, c_h2 = st.columns([4, 1])
                c_h1.write(f"✅ {r['Cliente']} - {r['Quantidade']} {r['Vasilhame']}")
                if c_h2.button("ESTORNAR", key=f"est_{i}"):
                    df_cas.at[i, 'Status'] = "DEVE"
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t_pa:
            col_cer, col_ref = st.columns(2)
            with col_cer:
                st.subheader("Cervejas")
                for v in ["Romarinho", "600ml"]:
                    v_at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {v_at} un")
                    if st.button(f"➕ 1 Engradado {v}", key=f"p_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 24
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
            with col_ref:
                st.subheader("Cocas")
                for v in ["Coca 1L", "Coca 2L"]:
                    v_at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {v_at} un")
                    if st.button(f"➕ 1 Fardo {v}", key=f"p_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 6
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
            
            st.divider()
            st.subheader("Retirada da Empresa")
            c_ret1, c_ret2 = st.columns(2)
            t_ret = c_ret1.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
            q_ret = c_ret2.number_input("Quantidade levada", 1)
            if st.button("Confirmar Coleta da Empresa"):
                df_patio.loc[df_patio['Vasilhame'] == t_ret, 'Total_Vazio'] -= q_ret
                df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Equipe")
        with st.form("f_u"):
            c1, c2, c3, c4 = st.columns(4)
            u, n, s, a = c1.text_input("User"), c2.text_input("Nome"), c3.text_input("Senha"), c4.selectbox("Admin", ["NÃO", "SIM"])
            if st.form_submit_button("Salvar"):
                pd.concat([df_usr, pd.DataFrame([[u, n, s, a, "", ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                if st.button(f"⭕ {r['Tarefa']}", key=f"t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado
                    df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()
            else: st.success(f"✅ {r['Tarefa']} - {r['QuemFez']}")

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Trocar Foto")
        if st.button("Salvar Foto") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
