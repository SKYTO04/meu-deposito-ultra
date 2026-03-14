import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# =================================================================
# 1. SETUP DE INTERFACE (DARK PRESTIGE)
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
    .stButton>button:hover { border-color: #58A6FF !important; color: #58A6FF !important; }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86)
# =================================================================
V = "v86_final_prestige"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv', 'log_cad': f'log_cad_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
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
# 3. LOGIN
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
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u, 'role': res['cargo'].values[0]})
                    st.rerun()
                else: st.error("Erro de Acesso")
else:
    df_p, df_e, df_pi = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['pi'])
    df_v, df_log = pd.read_csv(DB['vendas']), pd.read_csv(DB['log_cad'])

    with st.sidebar:
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE DINÂMICO", "🍻 PDV RÁPIDO", "🏗️ MAPA PILARES", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MAPA PILARES (COM CADASTRO MÚLTIPLO E FILTRO)
    # =================================================================
    if menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Organização Física")

        # Filtro de exibição (Só Refrigerante e Outros)
        df_pi_cat = pd.merge(df_pi, df_p[['Nome', 'Categoria']], left_on='Bebida', right_on='Nome', how='left')
        df_pi_filtrado = df_pi_cat[df_pi_cat['Categoria'].isin(["Refrigerante", "Outros"])]

        if st.session_state['role'] == "ADMIN":
            with st.expander("➕ CADASTRAR/MONTAR PILARES EM LOTE"):
                with st.form("lote_pilar"):
                    col_p, col_c = st.columns(2)
                    pilar_alvo = col_p.selectbox("Selecione o Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D", "Pilar E"])
                    camada_alvo = col_c.number_input("Nível/Camada", 1)
                    
                    st.markdown("---")
                    cols = st.columns(5)
                    novos_itens = []
                    for i in range(1, 6):
                        with cols[i-1]:
                            st.write(f"Posição {i}")
                            beb = st.selectbox(f"Item {i}", ["Vazio"] + df_p['Nome'].tolist(), key=f"b_{i}")
                            avul = st.number_input(f"Avulso {i}", 0, key=f"a_{i}")
                            if beb != "Vazio":
                                novos_itens.append([f"PI{datetime.now().microsecond}{i}", pilar_alvo, camada_alvo, i, beb, avul])
                    
                    if st.form_submit_button("SALVAR CONFIGURAÇÃO DO PILAR"):
                        if novos_itens:
                            df_new = pd.DataFrame(novos_itens, columns=df_pi.columns)
                            pd.concat([df_pi, df_new]).to_csv(DB['pi'], index=False)
                            st.success("Pilar configurado!")
                            st.rerun()

        # Visualização dos Pilares (Aparece a opção de todos, mas o conteúdo é filtrado)
        pilar_view = st.selectbox("Visualizar Pilar:", ["Pilar A", "Pilar B", "Pilar C", "Pilar D", "Pilar E"])
        camadas = sorted(df_pi_filtrado[df_pi_filtrado['Pilar'] == pilar_view]['Camada'].unique(), reverse=True)

        if not camadas:
            st.warning("Nenhum Refrigerante ou item 'Outros' neste pilar.")
        
        for c in camadas:
            st.markdown(f"### Camada {c}")
            v_cols = st.columns(5)
            itens_c = df_pi_filtrado[(df_pi_filtrado['Pilar'] == pilar_view) & (df_pi_filtrado['Camada'] == c)]
            for _, r in itens_c.iterrows():
                with v_cols[int(r['Pos'])-1]:
                    st.markdown(f"**{r['Bebida']}**")
                    st.caption(f"Categoria: {r['Categoria']}")
                    if st.button("BAIXA", key=f"bx_{r['ID']}"):
                        fator_b = 6 if r['Categoria'] == "Refrigerante" else 1
                        total_b = fator_b + int(r['Avulsos'])
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total_b
                        df_e.to_csv(DB['est'], index=False)
                        # Remove do banco real
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.rerun()

    # =================================================================
    # DEMAIS MÓDULOS (ESTOQUE, PDV, CONFIGS)
    # =================================================================
    elif menu == "📦 ESTOQUE DINÂMICO":
        st.title("📦 Entrada de Mercadoria")
        p_sel = st.selectbox("Produto", df_p['Nome'].tolist())
        cat = df_p[df_p['Nome'] == p_sel]['Categoria'].values[0]
        fator = 24 if cat in ["Romarinho", "Litrinho", "Long Neck"] else 12 if cat == "Cerveja Lata" else 6 if cat == "Refrigerante" else 1
        with st.form("ent"):
            c1, c2 = st.columns(2)
            f, a = c1.number_input("Qtd Fardos/Engradados", 0), c2.number_input("Avulsos", 0)
            if st.form_submit_button("REGISTRAR"):
                total = (f * fator) + a
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                df_e.to_csv(DB['est'], index=False)
                st.rerun()

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            if c3.button("VENDER", key=f"v_{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Configurações")
        t1, t2 = st.tabs(["Produtos", "Histórico"])
        with t1:
            with st.form("cad_p"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Categoria", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
                pc, pv = st.number_input("Custo"), st.number_input("Venda")
                if st.form_submit_button("SALVAR"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    st.rerun()
