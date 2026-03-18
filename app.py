import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO (VISUAL DARK PRESTIGE v35)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu - Ultra", page_icon="💎", layout="wide")

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
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; margin-bottom: 10px; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; background: #388bfd; color: white; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (AUTO-REPARO AGRESSIVO v35)
# =================================================================
DB = {
    "prod": "p_v35.csv", "est": "e_v35.csv", "pil": "pil_v35.csv",
    "usr": "u_v35.csv", "cas": "c_v35.csv", "tar": "t_v35.csv", 
    "cat": "cat_v35.csv", "patio": "pat_v35.csv"
}

def init_db():
    conf = {
        DB["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB["est"]: ['Nome', 'Estoque_Total_Un'],
        DB["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB["cat"]: ['Nome'],
        DB["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in conf.items():
        rebuild = False
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            rebuild = True
        else:
            try:
                test = pd.read_csv(f)
                if not all(col in test.columns for col in c): rebuild = True
            except: rebuild = True
        
        if rebuild:
            if os.path.exists(f): os.remove(f)
            df = pd.DataFrame(columns=c)
            if f == DB["patio"]: df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
            if f == DB["usr"]: df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            if f == DB["cat"]: df = pd.DataFrame([["Romarinho"], ["Cerveja"], ["Refrigerante"]], columns=c)
            df.to_csv(f, index=False)

init_db()

# =================================================================
# 3. SISTEMA DE SESSÃO E LOGIN
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

df_usr = pd.read_csv(DB["usr"])

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR"):
                try:
                    match = df_usr[df_usr['user'].astype(str) == str(u)]
                    if not match.empty and str(match.iloc[0]['senha']) == str(s):
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                        st.rerun()
                    else: st.error("Acesso negado.")
                except: st.error("Erro no Banco. Reiniciando...")
else:
    # Carregamento SEGURO
    df_p, df_e, df_pil, df_cas, df_tar, df_cat, df_patio = [pd.read_csv(DB[k]) for k in ["prod", "est", "pil", "cas", "tar", "cat", "patio"]]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    u_row = df_usr[df_usr['user'] == u_logado] if 'user' in df_usr.columns else pd.DataFrame()
    f_b64 = u_row.iloc[0]['foto'] if not u_row.empty and not pd.isna(u_row.iloc[0]['foto']) else ""
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title(f"Dashboard Adega")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Pendências Cascos", len(df_cas[df_cas['Status'] == "DEVE"]) if 'Status' in df_cas.columns else 0)
        if is_adm and not df_e.empty:
            df_v = pd.merge(df_e, df_p, on="Nome")
            c3.metric("Patrimônio", f"R$ {(df_v['Estoque_Total_Un']*df_v['Preco_Unitario']).sum():,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        df_f = pd.merge(df_e, df_p, on="Nome")
        cols = st.columns(4)
        for i, r in df_f.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="product-card"><h4>{r["Nome"]}</h4><p>Qtd: {int(r["Estoque_Total_Un"])}</p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria", df_cat['Nome'].tolist())
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Camada {cam_at}: Layout {atrav}x{frent}")
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avulsos", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB["pil"], index=False); st.rerun()
        
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

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico", "🚚 Saída"])
        with t1:
            with st.form("div"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB["cas"], index=False); st.rerun()
            if 'Status' in df_cas.columns:
                for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.warning(f"⚠️ {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                    if c2.button("BAIXA", key=f"bx_{i}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.to_csv(DB["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                        df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t2:
            if 'Status' in df_cas.columns:
                for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']}")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                        df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t3:
            for _, r in df_patio.iterrows(): st.info(f"{r['Vasilhame']}: {int(r['Total_Vazio'])}")
            with st.form("tr"):
                emp, v_t, v_q = st.text_input("Empresa").upper(), st.selectbox("Casco", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Sair"):
                    df_patio.loc[df_patio['Vasilhame'] == v_t, 'Total_Vazio'] -= v_q
                    df_patio.to_csv(DB["patio"], index=False); st.rerun()

    # --- ✨ CADASTRO (EXCLUSÃO TOTAL) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Produtos")
        with st.form("cad"):
            n, c, pr = st.text_input("Nome").upper(), st.selectbox("Cat", df_cat['Nome'].tolist()), st.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB["prod"], index=False)
                pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB["est"], index=False); st.rerun()
        st.divider()
        st.subheader("🗑️ Apagar")
        p_exc = st.selectbox("Escolha", df_p['Nome'].tolist())
        if st.button("EXCLUIR", type="primary"):
            df_p[df_p['Nome'] != p_exc].to_csv(DB["prod"], index=False)
            df_e[df_e['Nome'] != p_exc].to_csv(DB["est"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.form("new_t"):
                d = st.text_input("Obrigação")
                if st.form_submit_button("Add"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", "DIÁRIA", ""]], columns=df_tar.columns)]).to_csv(DB["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            st.info(f"🔹 {r['Tarefa']}")
            if st.button("OK", key=f"t_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Perfil")
        st.markdown(f'<div class="profile-card"><img src="{src}" width="150" class="avatar-round"><h3>{n_logado}</h3></div>', unsafe_allow_html=True)
        f = st.file_uploader("Foto")
        if st.button("Salvar Foto") and f:
            img = Image.open(f).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG")
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(buf.getvalue()).decode()
            df_usr.to_csv(DB["usr"], index=False); st.rerun()
