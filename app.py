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
# 3. LÓGICA DE LOGIN E SISTEMA
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u, s = st.text_input("USUÁRIO"), st.text_input("SENHA", type="password")
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB['usr'])
                res = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not res.empty:
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else '',
                        'role': res['cargo'].values[0]})
                    st.rerun()
else:
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        f = st.session_state.get('foto', '')
        if f and len(f) > 50: st.markdown(f'<img src="data:image/png;base64,{f}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE", "🍻 PDV RÁPIDO", "🏗️ MAPA PILARES", "🍶 CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: MAPA PILARES (ESTILO VISUAL)
    # =================================================================
    if menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Logística de Pilares (Organização Física)")
        
        # Interface de Cadastro de Camada (SÓ ADMIN)
        if st.session_state['role'] == "ADMIN":
            with st.expander("➕ Adicionar Nova Camada ao Pilar"):
                with st.form("cad_pilar"):
                    p_alvo = st.selectbox("Selecione o Pilar", ["Pilar A", "Pilar B", "Pilar C"])
                    camada = st.number_input("Nível/Camada", 1)
                    cols = st.columns(5)
                    novos_p = []
                    for i in range(5):
                        with cols[i]:
                            beb = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pos_{i}")
                            av = st.number_input(f"Avulso {i+1}", 0, key=f"av_{i}")
                            if beb != "Vazio":
                                novos_p.append([f"PI{datetime.now().microsecond}{i}", p_alvo, camada, i+1, beb, av])
                    if st.form_submit_button("SALVAR CAMADA NO MAPA"):
                        pd.concat([df_pi, pd.DataFrame(novos_p, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                        st.rerun()

        # Visualização dos Pilares
        p_ver = st.selectbox("Ver Pilar:", ["Pilar A", "Pilar B", "Pilar C"])
        camadas_ativas = sorted(df_pi[df_pi['Pilar'] == p_ver]['Camada'].unique(), reverse=True)

        for cam in camadas_ativas:
            st.markdown(f"### Camada {cam}")
            cols_p = st.columns(5)
            itens_camada = df_pi[(df_pi['Pilar'] == p_ver) & (df_pi['Camada'] == cam)]
            
            for _, r in itens_camada.iterrows():
                with cols_p[int(r['Pos'])-1]:
                    st.markdown(f"**{r['Bebida']}**")
                    st.caption(f"Avulsos: {r['Avulsos']}")
                    if st.button("DAR BAIXA", key=f"low_{r['ID']}"):
                        # Baixa Automática no Estoque (1 fardo = 6 ou 12 ou 24, aqui baixamos 1 fardo padrão + avulsos)
                        qtd_baixa = 6 + int(r['Avulsos']) # Ajuste conforme o fardo do pilar
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= qtd_baixa
                        df_e.to_csv(DB['est'], index=False)
                        # Remove do mapa
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.success(f"Baixa de {r['Bebida']} realizada!")
                        st.rerun()
            st.markdown("---")

    # =================================================================
    # DEMAIS MÓDULOS (PRESERVADOS)
    # =================================================================
    elif menu == "📦 ESTOQUE":
        st.title("📦 Entrada (Fardo x24)")
        with st.form("e"):
            p = st.selectbox("Item", df_p['Nome'].tolist())
            c1, c2 = st.columns(2)
            qe, qa = c1.number_input("Fardos", 0), c2.number_input("Avulsos", 0)
            if st.form_submit_button("LANÇAR"):
                df_e.loc[df_e['Nome'] == p, 'Qtd_Unidades'] += (qe*24 + qa)
                df_e.to_csv(DB['est'], index=False)
                st.rerun()
        st.dataframe(df_e, use_container_width=True)

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Estoque", f"{q//24}F | {q%24}U")
            if c3.button("VENDER", key=f"v_{r['Nome']}") and q >= 1:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Relatório")
        st.dataframe(df_v.iloc[::-1], use_container_width=True)

    elif menu == "⚙️ CONFIGS":
        st.title("⚙️ Cadastros")
        if st.session_state['role'] == "ADMIN":
            with st.form("u"):
                u, n, p, r = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Role", ["OPERADOR", "ADMIN"])
                if st.form_submit_button("Criar Usuário"):
                    pd.concat([pd.read_csv(DB['usr']), pd.DataFrame([[u, n, p, '', r]], columns=pd.read_csv(DB['usr']).columns)]).to_csv(DB['usr'], index=False)
                    st.success("Criado!")
