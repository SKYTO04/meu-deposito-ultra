import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import random

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO (VISUAL PRESTIGE v67)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu - Sistema Integral", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .product-card, .team-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; text-align: center;
    }
    .stock-low { border: 2px solid #ff4b4b !important; border-top: 5px solid #ff4b4b !important; }
    .profile-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 20px;
        padding: 30px; text-align: center; border-bottom: 4px solid #58a6ff;
    }
    .avatar-round { border-radius: 50%; border: 4px solid #58a6ff; object-fit: cover; margin-bottom: 15px; }
    .avatar-team { border-radius: 50%; border: 2px solid #ab7ffb; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (v67)
# =================================================================
VERSION = "v67"
DB = {k: f"{k}_{VERSION}.csv" for k in ["prod", "est", "pil", "usr", "cas", "tar", "cat", "patio", "log"]}

COLS = {
    "prod": ['Categoria', 'Nome', 'Preco_Unitario'],
    "est": ['Nome', 'Estoque_Total_Un'],
    "pil": ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
    "cas": ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
    "tar": ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
    "cat": ['Nome', 'Unidades_Fardo'], # Nova Coluna aqui!
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
        if key == "cat": df = pd.DataFrame([["ROMARINHO", 24], ["CERVEJA LATA", 12], ["REFRI 2L", 6]], columns=c)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        for col in c:
            if col not in df.columns: df[col] = 12 if col == 'Unidades_Fardo' else ""
        return df[c]
    except: return pd.DataFrame(columns=c)

# =================================================================
# 3. LÓGICA DE LOGIN
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u, s = st.text_input("Usuário").strip(), st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                df_u = safe_read("usr")
                match = df_u[df_u['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio, df_log = [safe_read(k) for k in ["prod", "est", "pil", "cas", "usr", "tar", "cat", "patio", "log"]]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # Função para pegar unidades pelo nome da categoria
    def get_units_by_cat(nome_cat):
        row = df_cat[df_cat['Nome'] == nome_cat]
        if not row.empty: return int(row.iloc[0]['Unidades_Fardo'])
        return 12

    # SIDEBAR
    f_b64 = ""
    try:
        u_row = df_usr[df_usr['user'].astype(str) == str(u_logado)]
        if not u_row.empty: f_b64 = u_row.iloc[0]['foto'] if not pd.isna(u_row.iloc[0]['foto']) else ""
    except: pass
    src_side = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src_side}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title("Painel Geral")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(pd.to_numeric(df_patio['Total_Vazio'], errors='coerce').fillna(0).sum())} un")
        c2.metric("Dívidas Ativas", f"{len(df_cas[df_cas['Status'] == 'DEVE'])} un")
        try:
            df_m = pd.merge(df_e, df_p, on="Nome")
            capital = (pd.to_numeric(df_m['Estoque_Total_Un']).fillna(0) * pd.to_numeric(df_m['Preco_Unitario']).fillna(0)).sum()
        except: capital = 0
        c3.metric("Capital em Estoque", f"R$ {capital:,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário por Categoria")
        cat_sel = st.selectbox("Selecione a Categoria", [""] + df_cat['Nome'].tolist())
        if cat_sel:
            un_fardo = get_units_by_cat(cat_sel)
            df_lista = pd.merge(df_p[df_p['Categoria'] == cat_sel], df_e, on="Nome")
            
            with st.expander("🔄 Lançar Movimento"):
                with st.form("mov"):
                    p = st.selectbox("Produto", df_lista['Nome'].tolist())
                    t = st.radio("Tipo", ["ENTRADA (+)", "SAÍDA (-)"], horizontal=True)
                    modo = st.radio("Modo", [f"Fardos ({un_fardo}un)", "Unidades Avulsas"], horizontal=True)
                    q = st.number_input("Qtd", 1)
                    if st.form_submit_button("Confirmar"):
                        fator = un_fardo if "Fardos" in modo else 1
                        df_e.loc[df_e['Nome'] == p, 'Estoque_Total_Un'] = pd.to_numeric(df_e.loc[df_e['Nome'] == p, 'Estoque_Total_Un']).fillna(0) + (q*fator if "ENTRADA" in t else -(q*fator))
                        df_e.to_csv(DB["est"], index=False); st.rerun()
            
            cols = st.columns(4)
            for i, r in df_lista.reset_index().iterrows():
                total = int(pd.to_numeric(r['Estoque_Total_Un'], errors='coerce') or 0)
                f, a = total // un_fardo, total % un_fardo
                css = "stock-low" if f < 2 else ""
                with cols[i % 4]:
                    st.markdown(f'<div class="product-card {css}"><h4>{r["Nome"]}</h4><p style="font-size: 18px;"><b>{f}</b> fds | <b>{a}</b> un</p><p style="font-size: 11px; color: gray;">Config: {un_fardo}un/fardo</p><hr><p>Total: {total} un</p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                prods_df = pd.merge(df_p, df_cat, left_on='Categoria', right_on='Nome', suffixes=('', '_cat'))
                cam_at = int(df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1 if not df_pil[df_pil['NomePilar']==n_pilar].empty else 1)
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"Bebida {i+1}", ["Vazio"] + prods_df['Nome'].tolist(), key=f"p_{i}")
                        av = st.number_input("Av", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{random.randint(0,99999)}", n_pilar, cam_at, i+1, b, av])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=COLS["pil"])]).to_csv(DB["pil"], index=False); st.rerun()
        
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div style="background:#1c2128; padding:15px; border-radius:10px; margin-bottom:10px;"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    with c_grid[int(r['Posicao'])-1]:
                        if st.button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                            # Achar categoria do produto para saber o fardo
                            cat_prod = df_p[df_p['Nome'] == r['Bebida']]['Categoria'].iloc[0]
                            fator = get_units_by_cat(cat_prod)
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (fator + int(r['Avulsos']))
                            df_e.to_csv(DB["est"], index=False); df_pil[df_pil['ID'] != r['ID']].to_csv(DB["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- ✨ CADASTRO (COM CONFIG DE CATEGORIA) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão e Configurações")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Produtos")
            with st.form("cp"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Categoria", df_cat['Nome'].tolist()), st.number_input("Preço Unitário", 0.0)
                if st.form_submit_button("Salvar Produto"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=COLS["prod"])]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=COLS["est"])]).to_csv(DB["est"], index=False); st.rerun()
            p_del = st.selectbox("Apagar Produto", [""] + df_p['Nome'].tolist())
            if p_del and st.button("DELETAR PRODUTO", type="primary"):
                df_p[df_p['Nome'] != p_del].to_csv(DB["prod"], index=False); df_e[df_e['Nome'] != p_del].to_csv(DB["est"], index=False); st.rerun()
        
        with c2:
            st.subheader("Categorias")
            with st.form("cc"):
                new_cat = st.text_input("Nome da Categoria (Ex: REFRI 2L)").upper()
                un_cat = st.number_input("Unidades por Fardo/Caixa", 1, 100, 12)
                if st.form_submit_button("Criar Categoria"):
                    pd.concat([df_cat, pd.DataFrame([[new_cat, un_cat]], columns=COLS["cat"])]).to_csv(DB["cat"], index=False); st.rerun()
            st.divider()
            st.write("Configuração Atual:")
            st.dataframe(df_cat, use_container_width=True)
            cat_del = st.selectbox("Apagar Categoria", [""] + df_cat['Nome'].tolist())
            if cat_del and st.button("DELETAR CATEGORIA"):
                df_cat[df_cat['Nome'] != cat_del].to_csv(DB["cat"], index=False); st.rerun()

    # --- 👥 EQUIPE / 🍶 CASCOS / 📋 TAREFAS (Mantidos v65/66) ---
    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        st.markdown(f'<div class="profile-card"><img src="{src_side}" width="150" class="avatar-round"><h3>{n_logado}</h3></div>', unsafe_allow_html=True)
        f_up = st.file_uploader("Foto", type=['png', 'jpg'])
        if f_up and st.button("CONFIRMAR"):
            img = Image.open(f_up).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG")
            df_usr.loc[df_usr['user'].astype(str) == str(u_logado), 'foto'] = base64.b64encode(buf.getvalue()).decode()
            df_usr.to_csv(DB["usr"], index=False); st.rerun()
        if is_adm:
            cols_e = st.columns(4)
            for idx, row in df_usr.iterrows():
                f_e = row['foto'] if not pd.isna(row['foto']) else ""
                s_e = f"data:image/png;base64,{f_e}" if f_e else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                with cols_e[idx % 4]:
                    st.markdown(f'<div class="team-card"><img src="{s_e}" width="60" class="avatar-team"><h6>{row["nome"]}</h6></div>', unsafe_allow_html=True)
                    if st.button("👁️", key=f"v_{idx}"): st.info(f"L: {row['user']} P: {row['senha']}")

    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        t1, t2 = st.tabs(["🔴 Devedores", "🚚 Saída"])
        with t1:
            with st.form("c"):
                cli, v, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{random.randint(0,99)}", datetime.now().strftime("%d/%m"), cli, v, q, "DEVE", ""]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                st.warning(f"{r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                if st.button("PAGO", key=f"p_{i}"):
                    df_cas.loc[i, 'Status'] = "PAGO"; df_cas.to_csv(DB["cas"], index=False); st.rerun()

    elif menu == "📋 Tarefas":
        st.title("📋 Tarefas")
        t = st.text_input("Nova")
        if st.button("Adicionar"): pd.concat([df_tar, pd.DataFrame([[f"T{random.randint(0,99)}", t, "PENDENTE", "DIA", ""]], columns=COLS["tar"])]).to_csv(DB["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            if st.button(f"OK: {r['Tarefa']}", key=f"tk_{i}"):
                df_tar.loc[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()
