import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E BLINDAGEM DE SESSÃO
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização Crítica (Impede qualquer erro de KeyError)
chaves = {'auth': False, 'nome': '', 'foto': '', 'user': '', 'role': 'admin'}
for k, v in chaves.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; transform: scale(1.01); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE BANCO DE DADOS (V86 DEFINITIVO)
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
# 3. CONTROLE DE LOGIN
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("USUÁRIO")
            s = st.text_input("SENHA", type="password")
            if st.form_submit_button("ACESSAR SISTEMA"):
                df_u = pd.read_csv(DB['usr'])
                res = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not res.empty:
                    st.session_state.update({
                        'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else '',
                        'role': res['cargo'].values[0] if 'cargo' in res.columns else 'OPERADOR'
                    })
                    st.rerun()
                else: st.error("Acesso Negado.")
else:
    # Carregamento de tabelas
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    # --- SIDEBAR INDUSTRIAL ---
    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50:
            st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE", "🍻 PDV RÁPIDO", "🏗️ PILARES", "🍶 CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: CONFIGS & CADASTROS (O QUE ESTAVA FALTANDO)
    # =================================================================
    if menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Painel Administrativo")
        
        # PARTE 1: PERFIL PESSOAL (Sempre visível)
        with st.expander("🖼️ MEU PERFIL (ALTERAR FOTO)"):
            u_file = st.file_uploader("Escolha uma foto quadrada", type=['png', 'jpg'])
            if u_file:
                b64 = get_img_64(u_file)
                df_u_db = pd.read_csv(DB['usr'])
                df_u_db.loc[df_u_db['user'] == st.session_state['user'], 'foto'] = b64
                df_u_db.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto atualizada! Reinicie o app.")

        # PARTE 2: GESTÃO DE EQUIPE (SÓ ADMIN)
        if st.session_state['role'] == "ADMIN":
            st.markdown("---")
            st.subheader("👥 Cadastro de Funcionários")
            with st.form("cad_equipe"):
                c1, c2, c3 = st.columns(3)
                new_user = c1.text_input("Login (Ex: joao)")
                new_nome = c2.text_input("Nome Completo")
                new_pass = c3.text_input("Senha", type="password")
                new_role = st.selectbox("Nível de Acesso", ["OPERADOR", "ADMIN"])
                if st.form_submit_button("CRIAR NOVO ACESSO"):
                    if new_user and new_nome and new_pass:
                        df_usr_add = pd.read_csv(DB['usr'])
                        new_line = pd.DataFrame([[new_user, new_nome, new_pass, '', new_role]], columns=df_usr_add.columns)
                        pd.concat([df_usr_add, new_line]).to_csv(DB['usr'], index=False)
                        st.success(f"Usuário {new_nome} cadastrado como {new_role}!")
                    else: st.warning("Preencha todos os campos.")
            
            # Lista de Usuários
            st.dataframe(pd.read_csv(DB['usr'])[['user', 'nome', 'cargo']], use_container_width=True)

            st.markdown("---")
            st.subheader("📦 Cadastro de Novos Produtos")
            with st.form("cad_produto"):
                c_n = st.text_input("Nome do Produto").upper()
                c_c = st.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Outros"])
                col_p1, col_p2 = st.columns(2)
                c_custo = col_p1.number_input("Preço de Custo", format="%.2f")
                c_venda = col_p2.number_input("Preço de Venda", format="%.2f")
                if st.form_submit_button("REGISTRAR PRODUTO NO BANCO"):
                    if c_n:
                        pd.concat([df_p, pd.DataFrame([[c_c, c_n, c_custo, c_venda, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[c_n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        st.success(f"{c_n} adicionado ao sistema!")
                        st.rerun()
        else:
            st.warning("⚠️ Você não tem permissão para cadastrar funcionários ou produtos.")

    # =================================================================
    # MÓDULO: HISTÓRICO BRUTO (DETALHADO)
    # =================================================================
    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Relatório de Vendas")
        c1, c2 = st.columns(2)
        f_p = c1.text_input("Produto").upper()
        f_u = c2.text_input("Operador").upper()
        
        df_h = df_v.copy()
        if f_p: df_h = df_h[df_h['Produto'].str.contains(f_p)]
        if f_u: df_h = df_h[df_h['Usuario'].str.contains(f_u)]
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        if st.session_state['role'] == "ADMIN":
            st.subheader("🗑️ Estorno Individual")
            for i, r in df_h.tail(5).iloc[::-1].iterrows():
                cc1, cc2 = st.columns([6,1])
                cc1.warning(f"{r['Hora']} - {r['Produto']} (R$ {r['Venda_T']})")
                if cc2.button("ANULAR", key=f"del_{i}"):
                    df_e.loc[df_e['Nome'] == r['Produto'], 'Qtd_Unidades'] += r['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.rerun()

    # Módulos Funcionais
    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            st.title("📊 Indicadores de Lucro")
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Lucro'] = (df_f['Preco_Venda'] - df_f['Preco_Custo']) * df_f['Qtd_Unidades']
            st.metric("Lucro Total Estimado", f"R$ {df_f['Lucro'].sum():,.2f}")
            st.plotly_chart(px.bar(df_f, x='Nome', y='Lucro', template="plotly_dark"), use_container_width=True)
        else: st.info("O Dashboard financeiro é visível apenas para Admins.")

    elif menu == "📦 ESTOQUE":
        st.title("📦 Entrada de Carga")
        p_sel = st.selectbox("Produto", df_p['Nome'].tolist())
        q_sel = st.number_input("Quantidade", 1)
        if st.button("EXECUTAR ENTRADA"):
            df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += q_sel
            df_e.to_csv(DB['est'], index=False)
            st.success("Estoque Atualizado.")
            st.rerun()
        st.dataframe(df_e, use_container_width=True)

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            q_est = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Qtd", f"{q_est} un")
            if c3.button("VENDER 1", key=f"v_{r['Nome']}") and q_est >= 1:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                new_v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🏗️ PILARES": st.dataframe(df_pi)
    elif menu == "🍶 CASCOS": st.dataframe(df_c)
