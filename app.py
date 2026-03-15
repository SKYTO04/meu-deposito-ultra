import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V160 (FULL)
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
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E CONFIGURAÇÕES
# =================================================================
DB_FILES = {
    "prod": "produtos_v160.csv", "est": "estoque_v160.csv", "pil": "pilares_v160.csv",
    "usr": "usuarios_v160.csv", "cas": "cascos_v160.csv", "tar": "tarefas_v160.csv", 
    "cat": "categorias_v160.csv", "patio": "patio_v160.csv"
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
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_init = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_init = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            df_init.to_csv(f, index=False)
        else:
            df = pd.read_csv(f)
            if f == DB_FILES["prod"] and 'Preco_Unitario' not in df.columns:
                df['Preco_Unitario'] = 0.0
                df.to_csv(f, index=False)
    
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
# 3. CONTROLE DE ACESSO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuário").strip()
        s = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("ACESSAR SISTEMA"):
            df_u = pd.read_csv(DB_FILES["usr"])
            match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not match.empty:
                st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"]), pd.read_csv(DB_FILES["patio"])

    # --- SIDEBAR ---
    row_user = df_usr[df_usr['user'] == u_logado].iloc[0]
    src = f"data:image/png;base64,{row_user['foto']}" if row_user['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Painel de Controle")
        df_val = pd.merge(df_e, df_p, on="Nome")
        total_reais = (df_val['Estoque_Total_Un'] * df_val['Preco_Unitario']).sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Itens em Estoque</h4><h2>{int(df_e["Estoque_Total_Un"].sum())} un</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Valor em Estoque</h4><h2 style="color:#238636;">R$ {total_reais:,.2f}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Cascos Devedores</h4><h2 style="color:#f85149;">{len(df_cas[df_cas["Status"]=="DEVE"])}</h2></div>', unsafe_allow_html=True)

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Gestão de Estoque")
        st.subheader("⚙️ Ajuste de Quantidade")
        with st.form("f_estoque"):
            col1, col2, col3 = st.columns([2, 1, 1])
            sel = col1.selectbox("Produto", df_p['Nome'].unique())
            tipo = col2.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
            qtd = col3.number_input("Qtd (Unidades)", 0)
            if st.form_submit_button("ATUALIZAR"):
                if tipo == "SAÍDA": df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] -= qtd
                else: df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += qtd
                df_e.to_csv(DB_FILES["est"], index=False); st.rerun()

        st.divider()
        with st.expander("🔍 VER PRODUTOS EM ESTOQUE"):
            df_full = pd.merge(df_e, df_p, on="Nome")
            for _, r in df_full.iterrows():
                u_b, t_t = get_config(r['Nome'], df_p)
                f, a = r['Estoque_Total_Un'] // u_b, r['Estoque_Total_Un'] % u_b
                val_total = r['Estoque_Total_Un'] * r['Preco_Unitario']
                st.markdown(f'''
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r["Nome"]}</b><br><small>{r["Categoria"]}</small></div>
                        <div style="text-align:center">{f} {t_t}s e {a} un</div>
                        <div style="text-align:right"><b>R$ {val_total:.2f}</b><br><small>{r["Estoque_Total_Un"]} un</small></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Pilares")
        # Lógica de criação de camada
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_f = st.selectbox("Filtrar Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                c_num = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else int(df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()) + 1
                at, fr = (3, 2) if c_num % 2 != 0 else (2, 3)
                cols_p = st.columns(5); data_p = []
                for i in range(at+fr):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==cat_f]['Nome'].tolist(), key=f"pil{i}")
                    av = cols_p[i].number_input("Av", 0, key=f"av{i}")
                    if b != "Vazio": data_p.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, c_num, i+1, b, av])
                if st.button("SALVAR"):
                    pd.concat([df_pil, pd.DataFrame(data_p, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

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
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico/Estorno", "🏗️ Pátio"])
        
        with t1:
            with st.form("f_casco"):
                cli, tipo, qtd = st.columns(3)
                c_n = cli.text_input("Cliente").upper()
                v_t = tipo.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
                v_q = qtd.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), c_n, v_t, v_q, "DEVE", "", ""]], columns=['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'])]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} {r['Vasilhame']}")
                if st.button(f"Receber de {r['Cliente']}", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t2:
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                ch1, ch2 = st.columns([4,1])
                ch1.write(f"✅ {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']}")
                if ch2.button("ESTORNAR", key=f"es_{i}"):
                    df_cas.at[i, 'Status'] = "DEVE"
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t3:
            c_cer, c_ref = st.columns(2)
            with c_cer:
                st.subheader("Cervejas")
                for v in ["Romarinho", "600ml"]:
                    at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {at} un")
                    if st.button(f"➕ Engradado {v}", key=f"p_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 24
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
            with c_ref:
                st.subheader("Cocas")
                for v in ["Coca 1L", "Coca 2L"]:
                    at = df_patio[df_patio['Vasilhame']==v]['Total_Vazio'].values[0]
                    st.write(f"**{v}:** {at} un")
                    if st.button(f"➕ Fardo {v}", key=f"p_{v}"):
                        df_patio.loc[df_patio['Vasilhame'] == v, 'Total_Vazio'] += 6
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
            st.divider()
            t_ret = st.selectbox("Coleta Empresa", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
            q_ret = st.number_input("Qtd coletada", 1)
            if st.button("Confirmar Saída Empresa"):
                df_patio.loc[df_patio['Vasilhame'] == t_ret, 'Total_Vazio'] -= q_ret
                df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        tab1, tab2 = st.tabs(["Novo Item", "Categorias"])
        with tab1:
            with st.form("f_item"):
                n_p = st.text_input("Nome").upper()
                c_p = st.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                p_p = st.number_input("Preço Unidade", 0.0, format="%.2f")
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_p, pd.DataFrame([[c_p, n_p, p_p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n_p, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with tab2:
            n_c = st.text_input("Nova Categoria").upper()
            if st.button("Criar"): pd.concat([df_cat, pd.DataFrame([[n_c]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.rerun()
            s_c = st.selectbox("Apagar", df_cat['Nome'].unique())
            if st.button("Remover"): df_cat[df_cat['Nome'] != s_c].to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Tarefas")
        if is_adm:
            t_n = st.text_input("Nova Tarefa")
            if st.button("Adicionar"): pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_n, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                if st.button(f"⭕ {r['Tarefa']}", key=f"t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado
                    df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()
            else: st.success(f"✅ {r['Tarefa']} - Feito por {r['QuemFez']}")

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Equipe")
        with st.form("f_user"):
            u, n, s, a = st.columns(4)
            u_u = u.text_input("User")
            n_u = n.text_input("Nome")
            s_u = s.text_input("Senha")
            a_u = a.selectbox("Admin", ["NÃO", "SIM"])
            if st.form_submit_button("Salvar"):
                pd.concat([df_usr, pd.DataFrame([[u_u, n_u, s_u, a_u, ""]], columns=['user', 'nome', 'senha', 'is_admin', 'foto'])]).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        up = st.file_uploader("Foto de Perfil")
        if st.button("Salvar"):
            img = Image.open(up).convert("RGB"); img.thumbnail((300, 300))
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
