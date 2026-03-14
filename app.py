import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E SEGURANÇA
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

for k, v in {'auth': False, 'nome': '', 'foto': '', 'user': '', 'role': 'OPERADOR'}.items():
    if k not in st.session_state: st.session_state[k] = v

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
# 2. MOTOR DE BANCO DE DADOS
# =================================================================
V = "v86_final_prestige"
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
            if key == 'usr': df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '', 'ADMIN']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

def get_img_64(img_file):
    img = Image.open(img_file).resize((300, 300))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# =================================================================
# 3. CONTROLE DE ACESSO
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u, s = st.text_input("USUÁRIO"), st.text_input("SENHA", type="password")
            if st.form_submit_button("ACESSAR SISTEMA"):
                df_u = pd.read_csv(DB['usr'])
                res = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not res.empty:
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else '',
                        'role': res['cargo'].values[0]})
                    st.rerun()
                else: st.error("Erro.")
else:
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50: st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE INTELIGENTE", "🍻 PDV RÁPIDO", "🏗️ PILARES", "🍶 CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: ESTOQUE INTELIGENTE (O QUE VOCÊ PEDIU)
    # =================================================================
    if menu == "📦 ESTOQUE INTELIGENTE":
        st.title("📦 Gestão de Estoque (Fardo vs Unidade)")
        with st.form("entrada_f"):
            p_sel = st.selectbox("Produto", df_p['Nome'].tolist())
            c1, c2 = st.columns(2)
            qe = c1.number_input("Engradados/Fardos (x24)", 0)
            qa = c2.number_input("Unidades Avulsas", 0)
            if st.form_submit_button("REGISTRAR ENTRADA"):
                total = (qe * 24) + qa
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Adicionado {total} unidades em {p_sel}")
                st.rerun()

        st.subheader("Situação Real das Prateleiras")
        df_view = df_e.copy()
        # Lógica de conversão para visualização
        df_view['Fardos (24un)'] = df_view['Qtd_Unidades'] // 24
        df_view['Avulsos'] = df_view['Qtd_Unidades'] % 24
        st.dataframe(df_view[['Nome', 'Fardos (24un)', 'Avulsos', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # MÓDULO: PDV RÁPIDO (COM BAIXA INTELIGENTE)
    # =================================================================
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            q_est = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"### {r['Nome']}")
                c2.metric("No Estoque", f"{q_est // 24}F | {q_est % 24}U")
                
                if c3.button("VENDER FARDO", key=f"vf_{r['Nome']}") and q_est >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 24
                    df_e.to_csv(DB['est'], index=False)
                    v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 24, r['Preco_Custo']*24, r['Preco_Venda']*24, st.session_state['nome']]]
                    pd.DataFrame(v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
                
                if c4.button("VENDER UN", key=f"vu_{r['Nome']}") and q_est >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                    df_e.to_csv(DB['est'], index=False)
                    v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                    pd.DataFrame(v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
            st.markdown("---")

    # =================================================================
    # OUTROS MÓDULOS (MANTIDOS ORIGINAIS)
    # =================================================================
    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Relatório Detalhado")
        c1, c2 = st.columns(2)
        f_p, f_u = c1.text_input("Produto").upper(), c2.text_input("Operador").upper()
        df_h = df_v.copy()
        if f_p: df_h = df_h[df_h['Produto'].str.contains(f_p)]
        if f_u: df_h = df_h[df_h['Usuario'].str.contains(f_u)]
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        if st.session_state['role'] == "ADMIN":
            for i, r in df_h.tail(5).iloc[::-1].iterrows():
                cc1, cc2 = st.columns([6,1])
                cc1.warning(f"{r['Hora']} - {r['Produto']} (R$ {r['Venda_T']})")
                if cc2.button("ANULAR", key=f"del_{i}"):
                    df_e.loc[df_e['Nome'] == r['Produto'], 'Qtd_Unidades'] += r['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.rerun()

    elif menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Painel de Controle")
        with st.expander("🖼️ ALTERAR MINHA FOTO"):
            u_file = st.file_uploader("Foto", type=['png', 'jpg'])
            if u_file:
                b64 = get_img_64(u_file)
                df_u_db = pd.read_csv(DB['usr'])
                df_u_db.loc[df_u_db['user'] == st.session_state['user'], 'foto'] = b64
                df_u_db.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto salva!")
        if st.session_state['role'] == "ADMIN":
            st.subheader("👥 Cadastro Equipe")
            with st.form("c_u"):
                u, n, p = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha")
                r = st.selectbox("Acesso", ["OPERADOR", "ADMIN"])
                if st.form_submit_button("CADASTRAR FUNCIONÁRIO"):
                    pd.concat([pd.read_csv(DB['usr']), pd.DataFrame([[u, n, p, '', r]], columns=pd.read_csv(DB['usr']).columns)]).to_csv(DB['usr'], index=False)
                    st.success("OK!")
            st.subheader("📦 Novo Produto")
            with st.form("c_p"):
                nn, nc = st.text_input("Nome").upper(), st.selectbox("Cat", ["Romarinho", "Lata", "Outros"])
                pc, pv = st.number_input("Custo"), st.number_input("Venda")
                if st.form_submit_button("SALVAR ITEM"):
                    pd.concat([df_p, pd.DataFrame([[nc, nn, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[nn, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    st.rerun()

    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            df_f = pd.merge(df_e, df_p, on="Nome")
            st.metric("Lucro Estimado", f"R$ {((df_f['Preco_Venda']-df_f['Preco_Custo'])*df_f['Qtd_Unidades']).sum():,.2f}")
            st.plotly_chart(px.bar(df_f, x='Nome', y='Qtd_Unidades', template="plotly_dark"), use_container_width=True)
    
    elif menu == "🏗️ PILARES": st.dataframe(df_pi)
    elif menu == "🍶 CASCOS": st.dataframe(df_c)
