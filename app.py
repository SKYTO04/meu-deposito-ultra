import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
import base64

# =================================================================
# 1. SETUP DE INTERFACE (DARK PRESTIGE V86 - OMONI)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

for key, val in {'auth': False, 'nome': '', 'user': '', 'role': 'OPERADOR', 'foto': ''}.items():
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
        background-color: #21262D; color: #C9D1D9; transition: 0.2s;
    }
    .stButton>button:hover { border-color: #58A6FF !important; color: #58A6FF !important; }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .card-pilar { background: #1C2128; border: 1px solid #30363D; border-radius: 10px; padding: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 BRUTO)
# =================================================================
V = "v86_final_prestige"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv', 'cascos': f'cascos_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'foto', 'cargo'],
        'cascos': ['Nome', 'Qtd_Vazios']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'usr': df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '', 'ADMIN']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

# =================================================================
# 3. LOGIN E SEGURANÇA
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
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u, 'role': res['cargo'].values[0], 'foto': str(res['foto'].values[0])})
                    st.rerun()
                else: st.error("Erro de Acesso")
else:
    df_p, df_e, df_pi = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['pi'])
    df_v, df_c = pd.read_csv(DB['vendas']), pd.read_csv(DB['cascos'])

    with st.sidebar:
        if len(st.session_state['foto']) > 100:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" style="border-radius:50%; width:100px; border:2px solid #58A6FF;">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        menu = st.radio("MENU", ["📊 DASHBOARD", "📦 ESTOQUE & CASCOS", "🏗️ MAPA DE PILARES", "🍻 PDV RÁPIDO", "🕒 HISTÓRICO", "⚙️ CONFIGS"])
        if st.button("SAIR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # 4. MAPA DE PILARES (FILTRO AUTOMÁTICO POR CATEGORIA)
    # =================================================================
    if menu == "🏗️ MAPA DE PILARES":
        st.title("🏗️ Gestão de Pilares e Amarração")

        if st.session_state['role'] == "ADMIN":
            with st.expander("➕ NOVA AMARRAÇÃO"):
                with st.form("lote"):
                    c1, c2 = st.columns(2)
                    pilar_n = c1.text_input("NOME DO PILAR (Ex: ROMARINHO, COCA, SKOL)").upper()
                    nivel = c2.number_input("CAMADA", 1)
                    cols = st.columns(5)
                    novos = []
                    for i in range(1, 6):
                        with cols[i-1]:
                            st.write(f"Pos {i}")
                            beb = st.selectbox(f"Item {i}", ["Vazio"] + df_p['Nome'].tolist(), key=f"b_{i}")
                            av = st.number_input(f"Avulso {i}", 0, key=f"a_{i}")
                            if beb != "Vazio" and pilar_n != "":
                                novos.append([f"PI{datetime.now().microsecond}{i}", pilar_n, nivel, i, beb, av])
                    if st.form_submit_button("SALVAR"):
                        pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                        st.rerun()

        # LOGICA DE FILTRO: Só mostra itens da categoria que dá nome ao pilar
        pilares = sorted(df_pi['Pilar'].unique())
        if pilares:
            p_sel = st.selectbox("Escolha o Pilar:", pilares)
            df_merged = pd.merge(df_pi, df_p[['Nome', 'Categoria']], left_on='Bebida', right_on='Nome', how='left')
            
            # FILTRO BRUTO: Se o pilar chama 'ROMARINHO', só mostra categoria 'ROMARINHO'
            df_render = df_merged[(df_merged['Pilar'] == p_sel) & (df_merged['Categoria'].str.contains(p_sel, case=False, na=False) | (df_merged['Categoria'].isin(["Refrigerante", "Outros"])))]
            
            camadas = sorted(df_render['Camada'].unique(), reverse=True)
            for cam in camadas:
                st.markdown(f"#### Camada {cam}")
                grade = st.columns(5)
                itens = df_render[df_render['Camada'] == cam]
                for _, r in itens.iterrows():
                    with grade[int(r['Pos'])-1]:
                        st.markdown(f'<div class="card-pilar"><b>{r["Bebida"]}</b><br>{r["Avulsos"]} Av.</div>', unsafe_allow_html=True)
                        if st.button("BAIXA", key=f"bx_{r['ID']}"):
                            fator = 24 if "Romarinho" in r['Categoria'] else 6 if "Refrigerante" in r['Categoria'] else 1
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (fator + r['Avulsos'])
                            df_e.to_csv(DB['est'], index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                            st.rerun()

    # =================================================================
    # 5. ESTOQUE & CASCOS (DEVOLUÇÃO DE CASCO)
    # =================================================================
    elif menu == "📦 ESTOQUE & CASCOS":
        st.title("📦 Controle de Estoque e Vasilhames")
        t1, t2 = st.tabs(["📥 ENTRADA", "🔄 DEVOLUÇÃO DE CASCO"])
        
        with t1:
            p_ent = st.selectbox("Produto", df_p['Nome'].tolist())
            cat = df_p[df_p['Nome'] == p_ent]['Categoria'].values[0]
            f = 24 if "Romarinho" in cat else 12 if "Lata" in cat else 6 if "Refrigerante" in cat else 1
            with st.form("e"):
                c1, c2 = st.columns(2)
                qtd_f = c1.number_input("Cargas/Fardos", 0)
                qtd_a = c2.number_input("Avulsos", 0)
                if st.form_submit_button("REGISTRAR"):
                    df_e.loc[df_e['Nome'] == p_ent, 'Qtd_Unidades'] += (qtd_f * f) + qtd_a
                    df_e.to_csv(DB['est'], index=False)
                    st.rerun()

        with t2:
            st.markdown("### Retorno de Casco Vazio")
            p_casco = st.selectbox("Casco de qual produto?", df_p[df_p['Categoria'].isin(["Romarinho", "Litrinho", "Long Neck"])]['Nome'].tolist())
            with st.form("vasilhame"):
                qtd_v = st.number_input("Qtd de Cascos Devolvidos", 0)
                if st.form_submit_button("CONFIRMAR DEVOLUÇÃO"):
                    if p_casco in df_c['Nome'].values:
                        df_c.loc[df_c['Nome'] == p_casco, 'Qtd_Vazios'] += qtd_v
                    else:
                        df_c = pd.concat([df_c, pd.DataFrame([[p_casco, qtd_v]], columns=df_c.columns)])
                    df_c.to_csv(DB['cascos'], index=False)
                    st.success(f"Cascos de {p_casco} adicionados ao estoque de vazios!")
                    st.rerun()
            st.write("#### Estoque de Vazios")
            st.dataframe(df_c, use_container_width=True, hide_index=True)

    # =================================================================
    # 6. PDV RÁPIDO E CONFIGS
    # =================================================================
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Rápida")
        for _, r in df_p.iterrows():
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            if c3.button("VENDER", key=f"v_{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                st.rerun()

    elif menu == "⚙️ CONFIGS":
        with st.form("cad_p"):
            n = st.text_input("Nome").upper()
            c = st.selectbox("Categoria", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
            pc, pv = st.number_input("Custo"), st.number_input("Venda")
            if st.form_submit_button("SALVAR"):
                pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                st.rerun()
