import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO (VISUAL PRESTIGE v46)
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
# 2. BANCO DE DADOS (v46 - BLINDAGEM DE COLUNAS)
# =================================================================
DB = {
    "prod": "p_v46.csv", "est": "e_v46.csv", "pil": "pil_v46.csv",
    "usr": "u_v46.csv", "cas": "c_v46.csv", "tar": "t_v46.csv", 
    "cat": "cat_v46.csv", "patio": "pat_v46.csv", "log": "log_v46.csv"
}

def registrar_log(usuario, acao):
    now = datetime.now().strftime("%d/%m/%y %H:%M")
    try:
        df_l = pd.read_csv(DB["log"])
        pd.concat([df_l, pd.DataFrame([[now, usuario, acao]], columns=['DataHora', 'Usuario', 'Acao'])]).to_csv(DB["log"], index=False)
    except: pass

def init_db():
    conf = {
        DB["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB["est"]: ['Nome', 'Estoque_Total_Un'],
        DB["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB["cat"]: ['Nome'],
        DB["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB["patio"]: ['Vasilhame', 'Total_Vazio'],
        DB["log"]: ['DataHora', 'Usuario', 'Acao']
    }
    for f, c in conf.items():
        recriar = False
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            recriar = True
        else:
            try:
                temp = pd.read_csv(f)
                if not all(col in temp.columns for col in c): recriar = True
            except: recriar = True
        
        if recriar:
            df = pd.DataFrame(columns=c)
            if f == DB["patio"]: df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
            if f == DB["usr"]: df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            if f == DB["cat"]: df = pd.DataFrame([["Romarinho"], ["Cerveja"], ["Refrigerante"]], columns=c)
            df.to_csv(f, index=False)

init_db()

# =================================================================
# 3. LOGIN
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u, s = st.text_input("Usuário").strip(), st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB["usr"])
                match = df_u[df_u['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    registrar_log(u, "Entrou no sistema.")
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    # Carregamento com proteção total
    data = {}
    for k, v in DB.items():
        try: data[k] = pd.read_csv(v)
        except: data[k] = pd.DataFrame() # Fallback para não travar
    
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio, df_log = data.values()
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    f_b64 = ""
    if not df_usr.empty and 'user' in df_usr.columns:
        u_row = df_usr[df_usr['user'] == u_logado]
        if not u_row.empty: f_b64 = u_row.iloc[0]['foto'] if not pd.isna(u_row.iloc[0]['foto']) else ""
    
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    
    nav = ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"]
    if is_adm: nav.append("📜 Log Geral")
    menu = st.sidebar.radio("Navegação", nav)
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title("Painel Geral")
        c1, c2, c3 = st.columns(3)
        vazios = df_patio['Total_Vazio'].sum() if not df_patio.empty and 'Total_Vazio' in df_patio.columns else 0
        c1.metric("No Pátio", f"{int(vazios)} un")
        
        dividas = 0
        if not df_cas.empty and 'Status' in df_cas.columns:
            dividas = len(df_cas[df_cas['Status'] == "DEVE"])
        c2.metric("Dívidas Ativas", dividas)
        
        cap = 0
        if is_adm and not df_e.empty and not df_p.empty:
            try:
                df_v = pd.merge(df_e, df_p, on="Nome")
                cap = (df_v['Estoque_Total_Un'] * df_v['Preco_Unitario']).sum()
            except: pass
        c3.metric("Capital Estoque", f"R$ {cap:,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        cat_sel = st.selectbox("Categoria", [""] + df_cat['Nome'].tolist()) if not df_cat.empty else st.selectbox("Categoria", [""])
        if cat_sel:
            prods_cat = df_p[df_p['Categoria'] == cat_sel]['Nome'].tolist()
            df_f = df_e[df_e['Nome'].isin(prods_cat)]
            with st.expander("🔄 Movimentação"):
                with st.form("mov"):
                    p, t, q = st.selectbox("Produto", prods_cat), st.radio("Tipo", ["ENTRADA (+)", "SAÍDA (-)"], horizontal=True), st.number_input("Qtd", 1)
                    if st.form_submit_button("Lançar"):
                        df_e.loc[df_e['Nome'] == p, 'Estoque_Total_Un'] += (q if "ENTRADA" in t else -q)
                        df_e.to_csv(DB["est"], index=False); registrar_log(u_logado, f"Estoque {p}: {t} {q}"); st.rerun()
            cols = st.columns(4)
            for i, r in df_f.reset_index().iterrows():
                with cols[i % 4]: st.markdown(f'<div class="product-card"><h4>{r["Nome"]}</h4><p>Qtd: <b>{int(r["Estoque_Total_Un"])}</b></p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist())) if not df_pil.empty else st.selectbox("Pilar", ["+ NOVO"])
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Carga", df_cat['Nome'].tolist()) if not df_cat.empty else ""
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist() if cat_p else []
                max_c = 0 if df_pil.empty or df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"P{i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avs", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("CONFIRMAR"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB["pil"], index=False); st.rerun()
        if not df_pil.empty:
            for p in df_pil['NomePilar'].unique():
                st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
                for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                    c_grid = st.columns(5)
                    for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                        with c_grid[int(r['Posicao'])-1]:
                            if st.button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                                df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (12 + r['Avulsos'])
                                df_e.to_csv(DB["est"], index=False)
                                df_pil[df_pil['ID'] != r['ID']].to_csv(DB["pil"], index=False); registrar_log(u_logado, f"Baixa {p}: {r['Bebida']}"); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico / Estorno", "🚚 Saída Empresa"])
        agora = datetime.now().strftime("%d/%m %H:%M")
        with t1:
            with st.form("div"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", agora, cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB["cas"], index=False); st.rerun()
            if not df_cas.empty and 'Status' in df_cas.columns:
                for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.warning(f"⚠️ **{r['Data']}** - {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                    if c2.button("BAIXA", key=f"bx_{i}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'Data'] = agora
                        df_cas.to_csv(DB["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                        df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t2:
            if not df_cas.empty and 'Status' in df_cas.columns:
                for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ **{r['Data']}** | {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Rec: {r['QuemBaixou']})")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                        df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t3:
            for _, r in df_patio.iterrows(): st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} no pátio")
            with st.form("saida_emp"):
                emp, v_t, v_q = st.text_input("Caminhão").upper(), st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Confirmar Saída"):
                    idx = df_patio[df_patio['Vasilhame'] == v_t].index[0]
                    if df_patio.at[idx, 'Total_Vazio'] >= v_q:
                        df_patio.at[idx, 'Total_Vazio'] -= v_q
                        df_patio.to_csv(DB["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", agora, emp, v_t, v_q, "TROCA", n_logado]], columns=df_cas.columns)]).to_csv(DB["cas"], index=False)
                        registrar_log(u_logado, f"Saída {emp}: {v_q} {v_t}"); st.success("Registrado!"); st.rerun()
            st.subheader("📜 Histórico de Saídas")
            if not df_cas.empty and 'Status' in df_cas.columns:
                for _, r in df_cas[df_cas['Status']=="TROCA"].iterrows(): st.text(f"🚚 {r['Data']} - {r['Cliente']} levou {int(r['Quantidade'])} {r['Vasilhame']} (Resp: {r['QuemBaixou']})")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão")
        tab1, tab2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with tab1:
            with st.form("cp"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Cat", df_cat['Nome'].tolist()) if not df_cat.empty else "", st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar") and c:
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB["est"], index=False); st.rerun()
            st.divider(); p_exc = st.selectbox("Apagar", df_p['Nome'].tolist()) if not df_p.empty else ""
            if st.button("EXCLUIR PRODUTO", type="primary") and p_exc:
                df_p[df_p['Nome'] != p_exc].to_csv(DB["prod"], index=False); df_e[df_e['Nome'] != p_exc].to_csv(DB["est"], index=False); st.rerun()
        with tab2:
            with st.form("cc"):
                nova = st.text_input("Nova Categoria").upper()
                if st.form_submit_button("Criar"): pd.concat([df_cat, pd.DataFrame([[nova]], columns=df_cat.columns)]).to_csv(DB["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.form("nt"):
                txt = st.text_input("Tarefa")
                if st.form_submit_button("Add"): pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", txt, "PENDENTE", "DIÁRIA", ""]], columns=df_tar.columns)]).to_csv(DB["tar"], index=False); st.rerun()
        if not df_tar.empty:
            for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
                if st.button(f"OK: {r['Tarefa']}", key=f"t_{i}"): df_tar.at[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()

    # --- 📜 LOG GERAL (SÓ ADM) ---
    elif menu == "📜 Log Geral" and is_adm:
        st.title("📜 Log de Atividades")
        if not df_log.empty: st.dataframe(df_log.sort_values(by="DataHora", ascending=False), use_container_width=True)
