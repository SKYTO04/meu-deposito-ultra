import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE PRESTIGE (DARK MODE)
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
    .stButton>button:hover { border-color: #58A6FF !important; color: #58A6FF !important; transform: scale(1.01); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86)
# =================================================================
V = "v86_final_prestige"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv', 'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv', 
    'log_cad': f'log_cad_{V}.csv'
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
# 3. SEGURANÇA E LOGIN
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
                else: st.error("Acesso Negado.")
else:
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_pi, df_log = pd.read_csv(DB['pi']), pd.read_csv(DB['log_cad'])

    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if len(st.session_state['foto']) > 50:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" class="profile-img" width="160">', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state['nome']}\n`{st.session_state['role']}`")
        st.markdown('</div>', unsafe_allow_html=True)
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE DINÂMICO", "🍻 PDV RÁPIDO", "🏗️ MAPA PILARES", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & CADASTROS"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO: ESTOQUE DINÂMICO (REATIVO POR CATEGORIA)
    # =================================================================
    if menu == "📦 ESTOQUE DINÂMICO":
        st.title("📦 Entrada de Mercadoria")
        
        if df_p.empty:
            st.warning("Cadastre produtos primeiro nas Configurações.")
        else:
            p_sel = st.selectbox("Selecione o Produto para Entrada", df_p['Nome'].tolist())
            
            # Lógica que muda tudo baseado na categoria cadastrada
            cat_atual = df_p[df_p['Nome'] == p_sel]['Categoria'].values[0]
            
            if cat_atual == "Romarinho": fator = 24; txt = "Engradado (x24)"
            elif cat_atual == "Long Neck": fator = 24; txt = "Caixa/Fardo (x24)"
            elif cat_atual == "Litrinho": fator = 24; txt = "Engradado (x24)"
            elif cat_atual == "Cerveja Lata": fator = 12; txt = "Fardo (x12)"
            elif cat_atual == "Refrigerante": fator = 6; txt = "Fardo 2L (x6)"
            else: fator = 1; txt = "Unidade/Caixa"

            st.info(f"**CATEGORIA:** {cat_atual} | **MODO DE ENTRADA:** {txt}")
            
            with st.form("form_estoque"):
                c1, c2 = st.columns(2)
                qtd_f = c1.number_input(f"Qtd de {txt}", min_value=0, step=1)
                qtd_a = c2.number_input("Unidades Avulsas", min_value=0, step=1)
                
                if st.form_submit_button("REGISTRAR NO ESTOQUE"):
                    total = (qtd_f * fator) + qtd_a
                    df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                    df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                    df_e.to_csv(DB['est'], index=False)
                    st.success(f"Registrado! +{total} unidades de {p_sel}")
                    st.rerun()

        st.markdown("---")
        st.subheader("Estoque Geral")
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # MÓDULO: CONFIGS & HISTÓRICO DE CADASTRO (AUDITORIA)
    # =================================================================
    elif menu == "⚙️ CONFIGS & CADASTROS":
        st.title("⚙️ Painel de Controle")
        t1, t2, t3 = st.tabs(["👥 Gerir Equipe", "📦 Cadastrar Produtos", "📜 Histórico de Cadastro"])

        with t1:
            if st.session_state['role'] == "ADMIN":
                with st.form("u_c"):
                    u, n, s, r = st.text_input("Login"), st.text_input("Nome Completo"), st.text_input("Senha"), st.selectbox("Nível", ["OPERADOR", "ADMIN"])
                    if st.form_submit_button("CRIAR ACESSO"):
                        pd.concat([pd.read_csv(DB['usr']), pd.DataFrame([[u,n,s,'',r]], columns=pd.read_csv(DB['usr']).columns)]).to_csv(DB['usr'], index=False)
                        # Log de Auditoria
                        new_log = pd.DataFrame([[datetime.now().strftime("%d/%m/%y"), datetime.now().strftime("%H:%M"), "CADASTRO USUÁRIO", n, st.session_state['nome']]], columns=df_log.columns)
                        pd.concat([df_log, new_log]).to_csv(DB['log_cad'], index=False)
                        st.success("Usuário criado com sucesso!")
            st.dataframe(pd.read_csv(DB['usr'])[['user', 'nome', 'cargo']], use_container_width=True)

        with t2:
            if st.session_state['role'] == "ADMIN":
                with st.form("p_c"):
                    nn = st.text_input("Nome do Item").upper()
                    cc = st.selectbox("Categoria", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
                    pc, pv = st.number_input("Preço Custo"), st.number_input("Preço Venda")
                    if st.form_submit_button("CADASTRAR PRODUTO"):
                        pd.concat([df_p, pd.DataFrame([[cc, nn, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[nn, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        # Log de Auditoria
                        new_log = pd.DataFrame([[datetime.now().strftime("%d/%m/%y"), datetime.now().strftime("%H:%M"), "CADASTRO PROD", nn, st.session_state['nome']]], columns=df_log.columns)
                        pd.concat([pd.read_csv(DB['log_cad']), new_log]).to_csv(DB['log_cad'], index=False)
                        st.rerun()

        with t3:
            st.subheader("📜 Auditoria: Quem cadastrou o quê?")
            st.dataframe(pd.read_csv(DB['log_cad']).iloc[::-1], use_container_width=True, hide_index=True)

    # =================================================================
    # MAPA PILARES E PDV
    # =================================================================
    elif menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Organização Física")
        if st.session_state['role'] == "ADMIN":
            with st.expander("🆕 Adicionar Camada"):
                with st.form("pilar_cad"):
                    p_alvo = st.selectbox("Pilar", ["Pilar A", "Pilar B", "Pilar C"])
                    cam_n = st.number_input("Nível", 1)
                    st.write("Configurar 5 Colunas:")
                    c_cols = st.columns(5)
                    novas_pos = []
                    for i in range(5):
                        with c_cols[i]:
                            b = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p_{i}")
                            av = st.number_input(f"Avulso {i+1}", 0, key=f"a_{i}")
                            if b != "Vazio": novas_pos.append([f"PI{datetime.now().microsecond}{i}", p_alvo, cam_n, i+1, b, av])
                    if st.form_submit_button("GRAVAR"):
                        pd.concat([df_pi, pd.DataFrame(novas_pos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                        st.rerun()

        p_ver = st.selectbox("Ver Pilar:", ["Pilar A", "Pilar B", "Pilar C"])
        camadas = sorted(df_pi[df_pi['Pilar'] == p_ver]['Camada'].unique(), reverse=True)
        for cam in camadas:
            st.markdown(f"#### Camada {cam}")
            cols_grade = st.columns(5)
            itens = df_pi[(df_pi['Pilar'] == p_ver) & (df_pi['Camada'] == cam)]
            for _, r in itens.iterrows():
                with cols_grade[int(r['Pos'])-1]:
                    st.markdown(f"**{r['Bebida']}**")
                    if st.button("DAR BAIXA", key=f"bx_{r['ID']}"):
                        # Baixa baseada na categoria
                        cat_b = df_p[df_p['Nome']==r['Bebida']]['Categoria'].values[0]
                        f_b = 24 if cat_b in ["Romarinho", "Litrinho", "Long Neck"] else 6 if cat_b == "Refrigerante" else 12
                        total_b = f_b + int(r['Avulsos'])
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total_b
                        df_e.to_csv(DB['est'], index=False)
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.rerun()

    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Rápida")
        for _, r in df_p.iterrows():
            q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"### {r['Nome']}")
            c2.metric("Saldo", f"{q} un")
            if c3.button("VENDER 1 UN", key=f"v_{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Registro de Saídas")
        st.dataframe(df_v.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            df_fin = pd.merge(df_e, df_p, on="Nome")
            lucro = ((df_fin['Preco_Venda'] - df_fin['Preco_Custo']) * df_fin['Qtd_Unidades']).sum()
            st.metric("Lucro Potencial em Estoque", f"R$ {lucro:,.2f}")
            st.plotly_chart(px.bar(df_fin, x='Nome', y='Qtd_Unidades', title="Volume em Estoque", template="plotly_dark"), use_container_width=True)
