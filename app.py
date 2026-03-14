import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E SEGURANÇA TOTAL
# =================================================================
st.set_page_config(page_title="PACAEMBU G85 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização Blindada (Evita qualquer KeyError)
for key, val in {'auth': False, 'nome': '', 'foto': '', 'user': '', 'role': 'OPERADOR'}.items():
    if key not in st.session_state: st.session_state[key] = val

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div[data-testid="metric-container"] {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: 20px; border-left: 5px solid #58A6FF;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 800; height: 3.5em;
        text-transform: uppercase; border: 1px solid #30363D;
        background-color: #21262D; color: #C9D1D9; transition: 0.3s;
    }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 FINAL)
# =================================================================
V = "v86_final"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv', 'ec': f'ec_{V}.csv', 'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Resp'],
        'ec': ['Tipo', 'Qtd'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'foto', 'cargo']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'ec': df = pd.DataFrame([["Coca 1L", 0], ["Engradado", 0]], columns=['Tipo', 'Qtd'])
            if key == 'usr': df = pd.DataFrame([['admin', 'GERENTE', '123', '', 'ADMIN']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

def get_img_64(img_file):
    img = Image.open(img_file).resize((300, 300))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# =================================================================
# 3. LOGIN
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("USUÁRIO")
            s = st.text_input("SENHA", type="password")
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB['usr'])
                res = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not res.empty:
                    st.session_state.update({
                        'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else '',
                        'role': res['cargo'].values[0] if 'cargo' in res.columns else 'OPERADOR'
                    })
                    st.rerun()
                else: st.error("Incorreto.")
else:
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50:
            st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu_items = ["📊 DASHBOARD", "📦 ESTOQUE", "🍻 PDV RÁPIDO", "🏗️ PILARES", "🍶 CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGURAÇÕES"]
        menu = st.radio("MENU", menu_items)
        if st.button("SAIR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULOS DE ACESSO RESTRITO
    # =================================================================
    if menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            st.title("📊 Resumo Financeiro")
            df_f = pd.merge(df_e, df_p, on="Nome")
            st.metric("Lucro Potencial", f"R$ {( (df_f['Preco_Venda'] - df_f['Preco_Custo']) * df_f['Qtd_Unidades'] ).sum():,.2f}")
            st.plotly_chart(px.bar(df_f, x='Nome', y='Qtd_Unidades', template="plotly_dark"), use_container_width=True)
        else: st.error("Acesso restrito ao Gerente.")

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Histórico Total")
        col1, col2 = st.columns(2)
        bp = col1.text_input("Produto").upper()
        bu = col2.text_input("Operador").upper()
        df_h = df_v.copy()
        if bp: df_h = df_h[df_h['Produto'].str.contains(bp)]
        if bu: df_h = df_h[df_h['Usuario'].str.contains(bu)]
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        if st.session_state['role'] == "ADMIN":
            st.subheader("🚫 Estorno")
            for i, r in df_h.tail(5).iterrows():
                cc1, cc2 = st.columns([5,1])
                cc1.write(f"{r['Hora']} - {r['Produto']} - R$ {r['Venda_T']}")
                if cc2.button("ANULAR", key=f"ex_{i}"):
                    df_e.loc[df_e['Nome'] == r['Produto'], 'Qtd_Unidades'] += r['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.rerun()

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Estoque", f"{q} un")
            if c3.button("VENDER", key=f"v_{r['Nome']}") and q >= 1:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                new_v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "⚙️ CONFIGURAÇÕES":
        st.title("⚙️ Painel de Controle")
        t1, t2, t3 = st.tabs(["🖼️ Meu Perfil", "📦 Cadastro Produtos", "👥 Gestão de Equipe"])
        
        with t1:
            u_f = st.file_uploader("Trocar Foto")
            if u_f:
                b64 = get_img_64(u_f)
                df_u = pd.read_csv(DB['usr'])
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = b64
                df_u.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto atualizada!")

        with t2:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_p"):
                    n = st.text_input("Nome").upper()
                    pc, pv = st.number_input("Custo"), st.number_input("Venda")
                    if st.form_submit_button("CADASTRAR"):
                        pd.concat([df_p, pd.DataFrame([['Geral', n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        st.rerun()
            else: st.warning("Apenas Admins cadastram produtos.")

        with t3:
            if st.session_state['role'] == "ADMIN":
                st.subheader("Novo Usuário")
                with st.form("cad_u"):
                    nu, nn, ns = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha")
                    cargo = st.selectbox("Nível", ["OPERADOR", "ADMIN"])
                    if st.form_submit_button("CRIAR ACESSO"):
                        df_u_at = pd.read_csv(DB['usr'])
                        new_u = pd.DataFrame([[nu, nn, ns, '', cargo]], columns=df_u_at.columns)
                        pd.concat([df_u_at, new_u]).to_csv(DB['usr'], index=False)
                        st.success(f"Acesso criado para {nn}!")
                st.dataframe(pd.read_csv(DB['usr'])[['user', 'nome', 'cargo']], use_container_width=True)
            else: st.warning("Apenas Admins gerenciam a equipe.")

    # Módulos Simples (Estoque, Pilares, Cascos)
    elif menu == "📦 ESTOQUE":
        st.title("📦 Entrada")
        p = st.selectbox("Item", df_p['Nome'].tolist())
        q = st.number_input("Qtd", 1)
        if st.button("DAR ENTRADA"):
            df_e.loc[df_e['Nome'] == p, 'Qtd_Unidades'] += q
            df_e.to_csv(DB['est'], index=False)
            st.rerun()
        st.dataframe(df_e, use_container_width=True)
    
    elif menu == "🏗️ PILARES": st.dataframe(df_pi)
    elif menu == "🍶 CASCOS": st.dataframe(df_c)
