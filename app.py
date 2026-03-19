import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO (VISUAL PRESTIGE v55)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu - Sistema Integral", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; text-align: center;
    }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    .profile-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 20px;
        padding: 30px; text-align: center; border-bottom: 4px solid #58a6ff;
    }
    .avatar-round { border-radius: 50%; border: 4px solid #58a6ff; object-fit: cover; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (v55 - PROTEÇÃO DE CABEÇALHO)
# =================================================================
DB = {
    "prod": "p_v55.csv", "est": "e_v55.csv", "pil": "pil_v55.csv",
    "usr": "u_v55.csv", "cas": "c_v55.csv", "tar": "t_v55.csv", 
    "cat": "cat_v55.csv", "patio": "pat_v55.csv", "log": "log_v55.csv"
}

COLS = {
    "prod": ['Categoria', 'Nome', 'Preco_Unitario'],
    "est": ['Nome', 'Estoque_Total_Un'],
    "pil": ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
    "cas": ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
    "tar": ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
    "cat": ['Nome'],
    "usr": ['user', 'nome', 'senha', 'is_admin', 'foto'],
    "patio": ['Vasilhame', 'Total_Vazio'],
    "log": ['DataHora', 'Usuario', 'Acao']
}

def safe_read(key):
    path = DB[key]
    c = COLS[key]
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        df = pd.DataFrame(columns=c)
        if key == "patio": df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
        if key == "usr": df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
        if key == "cat": df = pd.DataFrame([["Romarinho"], ["Cerveja"], ["Refrigerante"]], columns=c)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        # Se faltar qualquer coluna, reconstrói o DF garantindo as colunas
        if not all(col in df.columns for col in c):
            for col in c:
                if col not in df.columns: df[col] = ""
        return df[c]
    except:
        return pd.DataFrame(columns=c)

def registrar_log(usuario, acao):
    now = datetime.now().strftime("%d/%m/%y %H:%M")
    try:
        df_l = safe_read("log")
        pd.concat([df_l, pd.DataFrame([[now, usuario, acao]], columns=COLS["log"])]).to_csv(DB["log"], index=False)
    except: pass

# =================================================================
# 3. LOGIN E LOGICA
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u, s = st.text_input("Usuário").strip(), st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                df_u = safe_read("usr")
                try:
                    match = df_u[df_u['user'].astype(str) == str(u)]
                    if not match.empty and str(match.iloc[0]['senha']) == str(s):
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                        registrar_log(u, "Entrou.")
                        st.rerun()
                    else: st.error("Acesso negado.")
                except: st.error("Erro no banco. admin/123")
else:
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio, df_log = [safe_read(k) for k in DB.keys()]
    u_l, n_l, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    f_b64 = ""
    try:
        u_row = df_usr[df_usr['user'] == u_l]
        if not u_row.empty: f_b64 = u_row.iloc[0]['foto'] if not pd.isna(u_row.iloc[0]['foto']) else ""
    except: pass
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_l}</b></center>', unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"] + (["📜 Log Geral"] if is_adm else []))
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title("Painel Geral")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        try: d_at = len(df_cas[df_cas['Status'] == "DEVE"])
        except: d_at = 0
        c2.metric("Dívidas Ativas", f"{d_at} un")
        c3.metric("Versão", "v55")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        cat_sel = st.selectbox("Categoria", [""] + df_cat['Nome'].tolist())
        if cat_sel:
            prods_cat = df_p[df_p['Categoria'] == cat_sel]['Nome'].tolist()
            df_f = df_e[df_e['Nome'].isin(prods_cat)]
            with st.expander("🔄 Movimentação"):
                with st.form("mov"):
                    p, t, q = st.selectbox("Produto", prods_cat), st.radio("Tipo", ["ENTRADA (+)", "SAÍDA (-)"], horizontal=True), st.number_input("Qtd", 1)
                    if st.form_submit_button("Lançar"):
                        df_e.loc[df_e['Nome'] == p, 'Estoque_Total_Un'] += (q if "ENTRADA" in t else -q)
                        df_e.to_csv(DB["est"], index=False); registrar_log(u_l, f"Estoque {p}: {t} {q}"); st.rerun()
            cols = st.columns(4)
            for i, r in df_f.reset_index().iterrows():
                with cols[i % 4]: st.markdown(f'<div class="product-card"><h4>{r["Nome"]}</h4><p>Qtd: <b>{int(r["Estoque_Total_Un"])}</b></p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                prods = df_p['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"P{i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avs", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("CONFIRMAR"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=COLS["pil"])]).to_csv(DB["pil"], index=False); st.rerun()
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    with c_grid[int(r['Posicao'])-1]:
                        if st.button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (12 + r['Avulsos'])
                            df_e.to_csv(DB["est"], index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (PROTEÇÃO NA LINHA DO ERRO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico / Estorno", "🚚 Saída Empresa"])
        agora = datetime.now().strftime("%d/%m %H:%M")
        
        # GARANTE QUE A COLUNA 'Status' EXISTE ANTES DE FILTRAR
        if 'Status' not in df_cas.columns:
            df_cas = pd.DataFrame(columns=COLS["cas"])
            df_cas.to_csv(DB["cas"], index=False)

        with t1:
            with st.form("div"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", agora, cli, vas, q, "DEVE", ""]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()
            
            # FILTRO SEGURO PARA DEVEDORES
            try:
                df_deve = df_cas[df_cas['Status'] == "DEVE"]
                for i, r in df_deve.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.warning(f"⚠️ **{r['Data']}** - {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                    if c2.button("BAIXA", key=f"bx_{i}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_l; df_cas.at[i, 'Data'] = agora
                        df_cas.to_csv(DB["cas"], index=False); df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB["patio"], index=False); st.rerun()
            except: st.error("Erro ao listar devedores. O arquivo foi resetado.")

        with t2:
            try:
                df_pago = df_cas[df_cas['Status'] == "PAGO"]
                for i, r in df_pago.iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ **{r['Data']}** | {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Rec: {r['QuemBaixou']})")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB["cas"], index=False); df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']; df_patio.to_csv(DB["patio"], index=False); st.rerun()
            except: pass
        with t3:
            for _, r in df_patio.iterrows(): st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} no pátio")
            with st.form("saida_emp"):
                emp, v_t, v_q = st.text_input("Caminhão").upper(), st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Confirmar Saída"):
                    idx = df_patio[df_patio['Vasilhame'] == v_t].index[0]
                    if df_patio.at[idx, 'Total_Vazio'] >= v_q:
                        df_patio.at[idx, 'Total_Vazio'] -= v_q; df_patio.to_csv(DB["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", agora, emp, v_t, v_q, "TROCA", n_l]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão")
        tab1, tab2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with tab1:
            with st.form("cp"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Cat", df_cat['Nome'].tolist()), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=COLS["prod"])]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=COLS["est"])]).to_csv(DB["est"], index=False); st.rerun()
            p_exc = st.selectbox("Apagar Produto", df_p['Nome'].tolist())
            if st.button("EXCLUIR PRODUTO", type="primary"):
                df_p[df_p['Nome'] != p_exc].to_csv(DB["prod"], index=False); df_e[df_e['Nome'] != p_exc].to_csv(DB["est"], index=False); st.rerun()
        with tab2:
            nova = st.text_input("Nova Categoria").upper()
            if st.button("Criar"): pd.concat([df_cat, pd.DataFrame([[nova]], columns=COLS["cat"])]).to_csv(DB["cat"], index=False); st.rerun()
            c_exc = st.selectbox("Apagar Categoria", df_cat['Nome'].tolist())
            if st.button("EXCLUIR CATEGORIA", type="primary"):
                if df_p[df_p['Categoria'] == c_exc].empty:
                    df_cat[df_cat['Nome'] != c_exc].to_csv(DB["cat"], index=False); st.rerun()
                else: st.error("Remova os produtos primeiro!")

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Membros")
        st.markdown(f'<div class="profile-card"><img src="{src}" width="150" class="avatar-round"><h3>{n_l}</h3></div>', unsafe_allow_html=True)
        if is_adm:
            with st.form("nu"):
                lu, ln, ls, la = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Admin?", ["NÃO", "SIM"])
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_usr, pd.DataFrame([[lu, ln, ls, la, ""]], columns=COLS["usr"])]).to_csv(DB["usr"], index=False); st.rerun()
            try: st.table(df_usr[['user', 'nome', 'is_admin']])
            except: pass
