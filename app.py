import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E INICIALIZAÇÃO (PREVINE KEYERROR)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização Blindada do Session State
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
if 'nome' not in st.session_state:
    st.session_state['nome'] = ''
if 'foto' not in st.session_state:
    st.session_state['foto'] = ''
if 'user' not in st.session_state:
    st.session_state['user'] = ''

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
# 2. BANCO DE DADOS (V86 DEFINITIVO)
# =================================================================
V = "v86_definitivo"
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
        'usr': ['user', 'nome', 'senha', 'foto']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'ec':
                df = pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=['Tipo', 'Qtd'])
            if key == 'usr':
                df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

def get_img_64(img_file):
    img = Image.open(img_file).resize((300, 300))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# =================================================================
# 3. LÓGICA DE ACESSO
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
                    st.session_state['auth'] = True
                    st.session_state['nome'] = res['nome'].values[0]
                    st.session_state['user'] = u
                    st.session_state['foto'] = str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else ''
                    st.rerun()
                else: st.error("Incorreto.")
else:
    # Carga Global
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    # --- SIDEBAR (SEM ERRO DE KEY) ---
    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50:
            st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        else:
            st.warning("Sem Foto")
        st.markdown(f"### {st.session_state.get('nome', 'Usuário')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu = st.radio("MENU", ["📊 DASHBOARD", "📦 ESTOQUE", "🍻 PDV RÁPIDO", "🏗️ PILARES", "🍶 CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS"])
        
        if st.button("SAIR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: HISTÓRICO BRUTO (O QUE VOCÊ PEDIU)
    # =================================================================
    if menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Histórico de Transações")
        
        col_f1, col_f2 = st.columns(2)
        busca_p = col_f1.text_input("Buscar Produto").upper()
        busca_u = col_f2.text_input("Buscar Operador").upper()
        
        df_h = df_v.copy()
        if busca_p: df_h = df_h[df_h['Produto'].str.contains(busca_p)]
        if busca_u: df_h = df_h[df_h['Usuario'].str.contains(busca_u)]
        
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🚫 Área de Estorno")
        if not df_h.empty:
            for i, row in df_h.tail(10).iloc[::-1].iterrows():
                c1, c2 = st.columns([5, 1])
                c1.info(f"Venda: {row['Produto']} | Qtd: {row['Qtd']} | Total: R$ {row['Venda_T']} | {row['Hora']}")
                if c2.button("ANULAR", key=f"btn_{i}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.success("Estornado!")
                    st.rerun()

    # =================================================================
    # DEMAIS MÓDULOS (COMPLETOS)
    # =================================================================
    elif menu == "📊 DASHBOARD":
        st.title("📊 Resumo Financeiro")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Lucro'] = (df_f['Preco_Venda'] - df_f['Preco_Custo']) * df_f['Qtd_Unidades']
            st.metric("Lucro Estimado em Estoque", f"R$ {df_f['Lucro'].sum():,.2f}")
            st.plotly_chart(px.bar(df_f, x='Nome', y='Qtd_Unidades', color='Categoria', template="plotly_dark"), use_container_width=True)

    elif menu == "📦 ESTOQUE":
        st.title("📦 Entrada de Mercadoria")
        with st.form("ent"):
            p = st.selectbox("Produto", df_p['Nome'].tolist())
            q = st.number_input("Quantidade Total (Unidades)", 1)
            if st.form_submit_button("ADICIONAR"):
                df_e.loc[df_e['Nome'] == p, 'Qtd_Unidades'] += q
                df_e.to_csv(DB['est'], index=False)
                st.rerun()
        st.dataframe(df_e, use_container_width=True)

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            st_q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Estoque", f"{st_q} un")
            if c3.button("VENDER UN", key=f"v_{r['Nome']}") and st_q >= 1:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                new_v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🏗️ PILARES":
        st.title("🏗️ Mapa de Pilares")
        st.dataframe(df_pi, use_container_width=True)

    elif menu == "🍶 CASCOS":
        st.title("🍶 Dívidas de Cascos")
        st.dataframe(df_c[df_c['Status']=="DEVE"], use_container_width=True)

    elif menu == "⚙️ CONFIGS":
        st.title("⚙️ Perfil e Cadastro")
        u_file = st.file_uploader("Trocar Foto", type=['png', 'jpg'])
        if u_file:
            b64 = get_img_64(u_file)
            df_u = pd.read_csv(DB['usr'])
            df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = b64
            df_u.to_csv(DB['usr'], index=False)
            st.session_state['foto'] = b64
            st.success("Foto salva! Recarregue.")
