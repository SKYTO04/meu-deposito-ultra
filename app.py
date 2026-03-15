import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V120 (COMPLETO)
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
    .stButton>button { border-radius: 8px; font-weight: 600; background-color: #21262d; border: 1px solid #444; transition: 0.3s; width: 100%; }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E INFRAESTRUTURA
# =================================================================
DB_FILES = {
    "prod": "produtos_v120.csv", "est": "estoque_v120.csv", "pil": "pilares_v120.csv",
    "usr": "usuarios_v120.csv", "log": "historico_v120.csv", "cas": "cascos_v120.csv",
    "tar": "tarefas_v120.csv", "cat": "categorias_v120.csv", "patio": "patio_v120.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["log"]: ['Data', 'Usuario', 'Ação'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_init = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_init = pd.DataFrame([["Romarinho", 0], ["Coca 1L", 0], ["Coca 2L", 0], ["600ml", 0]], columns=c)
            df_init.to_csv(f, index=False)
    
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
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
# 3. CONTROLE DE ACESSO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 ADEGA PACAEMBU</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuário").strip()
        s = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
            df_u = pd.read_csv(DB_FILES["usr"])
            match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not match.empty:
                st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                st.rerun()
            else: st.error("Incorreto.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR ---
    row_user = df_usr[df_usr['user'] == u_logado].iloc[0]
    foto_src = f"data:image/png;base64,{row_user['foto']}" if row_user['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{foto_src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "👥 Equipe", "📋 Tarefas", "⚙️ Perfil"])
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 📦 ESTOQUE (OTIMIZADO) ---
    if menu == "📦 Estoque":
        st.title("📦 Gestão de Estoque")
        
        # Ajuste no Topo
        st.subheader("⚙️ Lançar Movimentação")
        with st.form("f_mov"):
            sel = st.selectbox("Escolha o Produto", df_p['Nome'].unique())
            c_m1, c_m2 = st.columns(2)
            tipo = c_m1.radio("Tipo", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = c_m2.number_input("Quantidade Total (Unidades)", 0)
            if st.form_submit_button("ATUALIZAR ESTOQUE", use_container_width=True):
                if tipo == "SAÍDA": df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()

        st.divider()
        
        # Lista Oculta (Expander)
        with st.expander("🔍 VER PRODUTOS EM ESTOQUE (DETALHADO)"):
            df_join = pd.merge(df_e, df_p, on="Nome")
            for _, r in df_join.iterrows():
                u_b, t_t = get_config(r['Nome'], df_p)
                fardos = r['Estoque_Total_Un'] // u_b
                avulsos = r['Estoque_Total_Un'] % u_b
                cor = "badge-verde" if r['Estoque_Total_Un'] > 15 else "badge-amarelo" if r['Estoque_Total_Un'] > 0 else "badge-vermelho"
                
                st.markdown(f'''
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="flex:2"><b>{r['Nome']}</b><br><small>{r['Categoria']}</small></div>
                        <div style="flex:1.5; text-align:center"><b>{fardos} {t_t}s</b><br>+ {avulsos} un</div>
                        <div style="flex:1; text-align:right"><span class="status-badge {cor}">{r['Estoque_Total_Un']} un</span></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

    # --- 🍶 CASCOS (CATEGORIAS E COLETA) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t_cli, t_pat = st.tabs(["🔴 Pendentes Clientes", "🏗️ Saldo Pátio (Vazios)"])
        
        with t_cli:
            with st.form("f_divida"):
                c1, c2, c3 = st.columns(3)
                cli = c1.text_input("Cliente").upper()
                v_tipo = c2.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
                v_qtd = c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, v_tipo, v_qtd, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.markdown(f'<div class="card"><b>{r["Cliente"]}</b> deve {r["Quantidade"]} {r["Vasilhame"]}</div>', unsafe_allow_html=True)
                if st.button(f"Receber de {r['Cliente']}", key=f"bx_cas_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t_pat:
            col_rom, col_coca = st.columns(2)
            with col_rom:
                st.markdown('<div style="color:#58a6ff; font-weight:bold;">🍺 ROMARINHO / 600ml</div>', unsafe_allow_html=True)
                for v in ["Romarinho", "600ml"]:
                    val = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.metric(f"{v} no Pátio", f"{val} un", f"{val // 24} Engradados")
                    if st.button(f"➕ Adicionar 1 Engradado de {v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 24
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
                
                with st.expander("➖ Coleta Empresa (Romarinho/600ml)"):
                    sel_r = st.selectbox("O que levaram?", ["Romarinho", "600ml"])
                    qtd_r = st.number_input("Qtd total coletada", 1, key="ret_r")
                    if st.button("Confirmar Saída do Pátio"):
                        df_patio.loc[df_patio['Vasilhame'] == sel_r, 'Total_Vazio'] -= qtd_r
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

            with col_coca:
                st.markdown('<div style="color:#f85149; font-weight:bold;">🥤 CATEGORIA COCA-COLA</div>', unsafe_allow_html=True)
                for v in ["Coca 1L", "Coca 2L"]:
                    val_c = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {val_c} un ({val_c // 6} fardos)")
                    if st.button(f"➕ Adicionar 1 Fardo {v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 6
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
                
                with st.expander("➖ Coleta Empresa (Coca)"):
                    sel_c = st.selectbox("Qual Coca?", ["Coca 1L", "Coca 2L"])
                    qtd_c = st.number_input("Qtd coletada", 1, key="ret_c")
                    if st.button("Confirmar Baixa Coca"):
                        df_patio.loc[df_patio['Vasilhame'] == sel_c, 'Total_Vazio'] -= qtd_c
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="card"><h3>📍 Pilar {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                cols_p = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if cols_p[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_b, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_b + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        tab1, tab2 = st.tabs(["Produto", "Categoria"])
        with tab2:
            n_cat = st.text_input("Nome Categoria").upper()
            if st.button("SALVAR CAT"): 
                pd.concat([df_cat, pd.DataFrame([[n_cat]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.rerun()
            c_rm = st.selectbox("Remover Categoria", df_cat['Nome'].unique())
            if st.button("❌ APAGAR"): 
                df_cat[df_cat['Nome'] != c_rm].to_csv(DB_FILES["cat"], index=False); st.rerun()
        with tab1:
            with st.form("f_prod"):
                cat_p = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                nom_p = st.text_input("Nome").upper()
                if st.form_submit_button("CADASTRAR"):
                    pd.concat([df_p, pd.DataFrame([[cat_p, nom_p, 0.0]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[nom_p, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 👥 EQUIPE (CADASTRAR OUTROS) ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Equipe")
        with st.form("f_eq"):
            c1, c2, c3, c4 = st.columns(4)
            u, n, s = c1.text_input("User"), c2.text_input("Nome"), c3.text_input("Senha")
            a = c4.selectbox("Admin", ["NÃO", "SIM"])
            if st.form_submit_button("CADASTRAR OPERADOR"):
                pd.concat([df_usr, pd.DataFrame([[u, n, s, a, "", ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        
        for i, row in df_usr.iterrows():
            st.write(f"👤 **{row['nome']}** ({row['user']}) - Admin: {row['is_admin']}")
            if row['user'] != 'admin' and st.button("Remover", key=f"rm_u_{i}"):
                df_usr.drop(i).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        up = st.file_uploader("Trocar Foto", type=['png', 'jpg'])
        if st.button("SALVAR") and up:
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 🏠 DASHBOARD ---
    elif menu == "🏠 Dashboard":
        st.title("🚀 Dashboard")
        st.metric("Total em Estoque", df_e['Estoque_Total_Un'].sum())
        st.metric("Cascos Devedores", len(df_cas[df_cas['Status']=="DEVE"]))
