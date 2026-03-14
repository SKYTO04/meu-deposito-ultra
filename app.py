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
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; transform: scale(1.02); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 DEFINITIVO)
# =================================================================
V = "v86_final_prestige"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv', 'ec': f'ec_{V}.csv', 'pi': f'pi_{V}.csv', 
    'usr': f'usr_{V}.csv', 'log_cad': f'log_cad_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Resp'],
        'ec': ['Tipo', 'Qtd'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'foto', 'cargo'],
        'log_cad': ['Data', 'Hora', 'Acao', 'Item', 'Usuario']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'usr': df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '', 'ADMIN']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

# =================================================================
# 3. LÓGICA DE LOGIN
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
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else '',
                        'role': res['cargo'].values[0]})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_pi, df_log = pd.read_csv(DB['pi']), pd.read_csv(DB['log_cad'])

    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50:
            st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE DINÂMICO", "🍻 PDV RÁPIDO", "🏗️ MAPA PILARES", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: ESTOQUE DINÂMICO (COM TROCA DE TEXTO AUTOMÁTICA)
    # =================================================================
    if menu == "📦 ESTOQUE DINÂMICO":
        st.title("📦 Entrada de Mercadoria")
        
        # Selectbox que dispara a mudança de fator
        p_sel = st.selectbox("Escolha o Produto", df_p['Nome'].tolist())
        
        # Localiza a categoria do produto selecionado
        cat_atual = df_p[df_p['Nome'] == p_sel]['Categoria'].values[0]
        
        # Define o multiplicador baseado na categoria
        if cat_atual == "Romarinho": fator = 24; txt = "Engradado (x24)"
        elif cat_atual == "Long Neck": fator = 24; txt = "Caixa/Fardo (x24)"
        elif cat_atual == "Litrinho": fator = 24; txt = "Engradado (x24)"
        elif cat_atual == "Cerveja Lata": fator = 12; txt = "Fardo (x12)"
        elif cat_atual == "Refrigerante": fator = 6; txt = "Fardo 2L (x6)"
        else: fator = 1; txt = "Unidade/Caixa"

        st.warning(f"CATEGORIA: **{cat_atual}** | ENTRADA PADRÃO: **{txt}**")
        
        with st.form("form_estoque"):
            c1, c2 = st.columns(2)
            qtd_fardo = c1.number_input(f"Quantidade de {txt}", min_value=0, step=1)
            qtd_avulso = c2.number_input("Unidades Avulsas", min_value=0, step=1)
            
            if st.form_submit_button("REGISTRAR NO ESTOQUE"):
                total_entrada = (qtd_fardo * fator) + qtd_avulso
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total_entrada
                df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Sucesso! Adicionadas {total_entrada} unidades de {p_sel}.")
                st.rerun()

        st.markdown("---")
        st.subheader("Estoque em Tempo Real")
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # MÓDULO: CONFIGS E HISTÓRICO DE CADASTRO
    # =================================================================
    elif menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Painel de Controle")
        t1, t2, t3 = st.tabs(["👥 Equipe", "📦 Produtos", "📜 Histórico de Cadastro"])

        with t1:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_u"):
                    u, n, s, r = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Cargo", ["OPERADOR", "ADMIN"])
                    if st.form_submit_button("CADASTRAR"):
                        pd.concat([pd.read_csv(DB['usr']), pd.DataFrame([[u,n,s,'',r]], columns=pd.read_csv(DB['usr']).columns)]).to_csv(DB['usr'], index=False)
                        pd.concat([df_log, pd.DataFrame([[datetime.now().strftime("%d/%m/%y"), datetime.now().strftime("%H:%M"), "CADASTRO USUÁRIO", n, st.session_state['nome']]], columns=df_log.columns)]).to_csv(DB['log_cad'], index=False)
                        st.success("Usuário criado!")
            st.dataframe(pd.read_csv(DB['usr'])[['user', 'nome', 'cargo']], use_container_width=True)

        with t2:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_p"):
                    nn = st.text_input("Nome").upper()
                    # IMPORTANTE: Use as categorias EXATAS para bater com a lógica do estoque
                    cc = st.selectbox("Categoria", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
                    pc, pv = st.number_input("Custo"), st.number_input("Venda")
                    if st.form_submit_button("SALVAR"):
                        pd.concat([df_p, pd.DataFrame([[cc, nn, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[nn, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        pd.concat([pd.read_csv(DB['log_cad']), pd.DataFrame([[datetime.now().strftime("%d/%m/%y"), datetime.now().strftime("%H:%M"), "CADASTRO PROD", nn, st.session_state['nome']]], columns=df_log.columns)]).to_csv(DB['log_cad'], index=False)
                        st.rerun()

        with t3:
            st.subheader("📜 Auditoria de Ações")
            st.dataframe(pd.read_csv(DB['log_cad']).iloc[::-1], use_container_width=True, hide_index=True)

    # Módulos PDV e Pilares (Preservados)
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda")
        for _, r in df_p.iterrows():
            q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Saldo", f"{q} un")
            if c3.button("VENDER", key=f"v_{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Pilares")
        st.dataframe(df_pi, use_container_width=True)

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Vendas")
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
