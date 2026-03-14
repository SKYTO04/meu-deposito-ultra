import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# =================================================================
# 1. SETUP DE INTERFACE (PRESTIGE DARK)
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
        background-color: #21262D; color: #C9D1D9; transition: 0.2s;
    }
    .stButton>button:hover { border-color: #58A6FF !important; color: #58A6FF !important; transform: scale(1.01); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 DEFINITIVO)
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
# 3. SEGURANÇA
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
                    st.session_state.update({'auth': True, 'nome': res['nome'].values[0], 'user': u, 'role': res['cargo'].values[0]})
                    st.rerun()
                else: st.error("Acesso Negado.")
else:
    df_p, df_e, df_pi = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['pi'])
    df_v, df_log = pd.read_csv(DB['vendas']), pd.read_csv(DB['log_cad'])

    with st.sidebar:
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE DINÂMICO", "🍻 PDV RÁPIDO", "🏗️ MAPA DE PILARES", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # ESTOQUE DINÂMICO (COM MULTIPLICADORES POR CATEGORIA)
    # =================================================================
    if menu == "📦 ESTOQUE DINÂMICO":
        st.title("📦 Entrada de Mercadoria")
        p_sel = st.selectbox("Selecione o Produto", df_p['Nome'].tolist())
        cat = df_p[df_p['Nome'] == p_sel]['Categoria'].values[0]
        
        fator = 24 if cat in ["Romarinho", "Litrinho", "Long Neck"] else 12 if cat == "Cerveja Lata" else 6 if cat == "Refrigerante" else 1
        txt = "Engradado (x24)" if fator == 24 else "Fardo (x12)" if fator == 12 else "Fardo 2L (x6)" if fator == 6 else "Unidade"

        st.info(f"Categoria: **{cat}** | Multiplicador: **{txt}**")
        with st.form("f_est"):
            c1, c2 = st.columns(2)
            qtd_f = c1.number_input(f"Qtd de {txt}", 0)
            qtd_a = c2.number_input("Avulsas", 0)
            if st.form_submit_button("REGISTRAR ENTRADA"):
                total = (qtd_f * fator) + qtd_a
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Estoque OK: +{total} un.")
                st.rerun()
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # MAPA DE PILARES (DINÂMICO + AMARRAÇÃO + FILTRO REFRI/OUTROS)
    # =================================================================
    elif menu == "🏗️ MAPA DE PILARES":
        st.title("🏗️ Gestão de Pilares e Amarração")

        if st.session_state['role'] == "ADMIN":
            with st.expander("🆕 CRIAR / CONFIGURAR AMARRAÇÃO DE PILAR"):
                with st.form("form_pilar_lote"):
                    c1, c2 = st.columns(2)
                    nome_pilar = c1.text_input("Nome do Pilar (Ex: COCA, BRAHMA, SKOL)").upper()
                    num_camada = c2.number_input("Nível da Camada", 1)
                    
                    st.markdown("---")
                    st.write("Configuração da Amarração (5 Posições):")
                    cols = st.columns(5)
                    novos_dados = []
                    for i in range(1, 6):
                        with cols[i-1]:
                            st.write(f"Pos {i}")
                            item = st.selectbox(f"Item {i}", ["Vazio"] + df_p['Nome'].tolist(), key=f"sel_{i}")
                            av = st.number_input(f"Avulso {i}", 0, key=f"av_{i}")
                            if item != "Vazio" and nome_pilar != "":
                                novos_dados.append([f"PI{datetime.now().microsecond}{i}", nome_pilar, num_camada, i, item, av])
                    
                    if st.form_submit_button("GRAVAR AMARRAÇÃO"):
                        if novos_dados:
                            pd.concat([df_pi, pd.DataFrame(novos_dados, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                            st.success(f"Pilar {nome_pilar} atualizado com sucesso!")
                            st.rerun()

        # Visualização Dinâmica
        pilares_ativos = sorted(df_pi['Pilar'].unique())
        if pilares_ativos:
            pilar_sel = st.selectbox("Selecione o Pilar para gerenciar:", pilares_ativos)
            
            # FILTRO CRÍTICO: Só mostra o que for Refrigerante ou Outros
            df_merged = pd.merge(df_pi, df_p[['Nome', 'Categoria']], left_on='Bebida', right_on='Nome', how='left')
            df_render = df_merged[(df_merged['Pilar'] == pilar_sel) & (df_merged['Categoria'].isin(["Refrigerante", "Outros"]))]
            
            camadas = sorted(df_render['Camada'].unique(), reverse=True)
            for cam in camadas:
                st.markdown(f"#### Camada {cam}")
                grid = st.columns(5)
                itens_cam = df_render[df_render['Camada'] == cam]
                for _, r in itens_cam.iterrows():
                    with grid[int(r['Pos'])-1]:
                        st.markdown(f"📦 **{r['Bebida']}**")
                        st.caption(f"Avulso: {r['Avulsos']}")
                        if st.button("DAR BAIXA", key=f"bx_{r['ID']}"):
                            fator_b = 6 if r['Categoria'] == "Refrigerante" else 1
                            total_bx = fator_b + int(r['Avulsos'])
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total_bx
                            df_e.to_csv(DB['est'], index=False)
                            # Remove do banco real de pilares
                            df_pi_orig = pd.read_csv(DB['pi'])
                            df_pi_orig[df_pi_orig['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                            st.rerun()
        else:
            st.info("Nenhum pilar cadastrado ainda.")

    # =================================================================
    # PDV RÁPIDO
    # =================================================================
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Rápida")
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

    # =================================================================
    # CONFIGURAÇÕES E AUDITORIA
    # =================================================================
    elif menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Gerenciamento")
        t1, t2, t3 = st.tabs(["👥 Equipe", "📦 Produtos", "📜 Auditoria"])
        with t2:
            with st.form("p_c"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Categoria", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
                pc, pv = st.number_input("Custo"), st.number_input("Venda")
                if st.form_submit_button("CADASTRAR PRODUTO"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    pd.concat([df_log, pd.DataFrame([[datetime.now().strftime("%d/%m/%y"), datetime.now().strftime("%H:%M"), "CADASTRO PROD", n, st.session_state['nome']]], columns=df_log.columns)]).to_csv(DB['log_cad'], index=False)
                    st.rerun()
        with t3:
            st.dataframe(pd.read_csv(DB['log_cad']).iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Registro de Saídas")
        st.dataframe(df_v.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            df_fin = pd.merge(df_e, df_p, on="Nome")
            st.metric("Lucro Potencial Total", f"R$ {((df_fin['Preco_Venda']-df_fin['Preco_Custo'])*df_fin['Qtd_Unidades']).sum():,.2f}")
            st.plotly_chart(px.bar(df_fin, x='Nome', y='Qtd_Unidades', color='Categoria', template="plotly_dark"), use_container_width=True)
