import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import json

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO (DARK PRESTIGE V22)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide")

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
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; }
    .badge-blue { background: #388bfd; color: white; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V22)
# =================================================================
DB_FILES = {
    "prod": "p_v22.csv", "est": "e_v22.csv", "pil": "pil_v22.csv",
    "usr": "u_v22.csv", "cas": "c_v22.csv", "tar": "t_v22.csv", 
    "cat": "cat_v22.csv", "patio": "pat_v22.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f):
            df_i = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_i = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca Retornável", 0]], columns=c)
            if f == DB_FILES["usr"]:
                df_i = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            df_i.to_csv(f, index=False)

init_db()

# =================================================================
# 3. INTERFACE PRINCIPAL
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[df_u['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB_FILES.values()]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # Sidebar
    u_row = df_usr[df_usr['user'] == u_logado]
    f_b64 = u_row.iloc[0]['foto'] if not u_row.empty and not pd.isna(u_row.iloc[0]['foto']) else ""
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title(f"Bem-vindo, {n_logado}")
        c1, c2 = st.columns(2)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Pessoas Devendo", len(df_cas[df_cas['Status'] == "DEVE"]))

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Controle de Estoque")
        with st.expander("Lançar Movimento"):
            with st.form("mov"):
                sel = st.selectbox("Produto", df_p['Nome'].unique())
                tp = st.radio("Tipo", ["ENTRADA", "SAÍDA"], horizontal=True)
                qt = st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (qt if tp == "ENTRADA" else -qt)
                    df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        st.divider()
        df_f = pd.merge(df_e, df_p, on="Nome")
        cols = st.columns(4)
        for i, r in df_f.iterrows():
            with cols[i % 4]: st.markdown(f'<div class="product-card"><b>{r["Nome"]}</b><br>{int(r["Estoque_Total_Un"])} un</div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (3/2) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                    a = cols_p[i].number_input("Avs", 0, key=f"a_{i}")
                    if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR"): pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= 12 
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (COM ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        t1, t2, t3 = st.tabs(["🔴 Devedores & Estorno", "📦 Pátio (Vazios)", "🚚 Troca Empresa"])
        
        with t1:
            st.subheader("Nova Dívida")
            with st.form("div"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            st.divider()
            st.subheader("Pendentes")
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"**{r['Cliente']}** deve {int(r['Quantidade'])} un de {r['Vasilhame']}")
                if c2.button("BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

            st.divider()
            with st.expander("📜 Histórico e Estorno (Voltar para a lista)"):
                hist = df_cas[df_cas['Status']=="PAGO"]
                for i, r in hist.iterrows():
                    c_h1, c_h2 = st.columns([3, 1])
                    c_h1.write(f"✅ {r['Cliente']} pagou {int(r['Quantidade'])} {r['Vasilhame']} (Por: {r['QuemBaixou']})")
                    if c_h2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.at[i, 'QuemBaixou'] = ""
                        df_cas.to_csv(DB_FILES["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t2:
            st.subheader("Pátio")
            for _, r in df_patio.iterrows(): st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} un")

        with t3:
            st.subheader("Saída para Empresa")
            with st.form("troca"):
                vt, qt = st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Confirmar Saída"):
                    if df_patio.loc[df_patio['Vasilhame'] == vt, 'Total_Vazio'].values[0] >= qt:
                        df_patio.loc[df_patio['Vasilhame'] == vt, 'Total_Vazio'] -= qt
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.success("Registrado!"); st.rerun()
                    else: st.error("Saldo insuficiente no pátio.")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastros")
        ta1, ta2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with ta1:
            with st.form("p"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())))), st.number_input("Preço", 0.0)
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
            st.divider()
            p_rem = st.selectbox("Excluir", df_p['Nome'].tolist())
            if st.button("Remover Produto", type="primary"):
                df_p[df_p['Nome'] != p_rem].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != p_rem].to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            nc = st.text_input("Nova Categoria")
            if st.button("Salvar Categoria"):
                pd.concat([df_cat, pd.DataFrame([[nc]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.form("t"):
                d, tp, dt = st.text_input("Tarefa"), st.selectbox("Tipo", ["Diária", "Data Específica"]), st.date_input("Data")
                if st.form_submit_button("Add"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", tp, str(dt)]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        hj = datetime.now().strftime("%Y-%m-%d")
        for i, r in df_tar[(df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hj)].iterrows():
            st.markdown(f'<div class="product-card"><b>{r["Tarefa"]}</b></div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("FEITO", key=f"t_{i}"):
                df_tar.loc[i, 'Status'] = "OK"; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        if is_adm:
            with st.form("u"):
                li, ni, si, ai = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Adm", ["NÃO", "SIM"])
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_usr, pd.DataFrame([[li, ni, si, ai, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        st.divider()
        f = st.file_uploader("Foto")
        if st.button("Salvar Foto") and f:
            img = Image.open(f).convert("RGB"); img.thumbnail((300, 300)); b = io.BytesIO(); img.save(b, format="PNG")
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(b.getvalue()).decode()
            df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
