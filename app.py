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
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização Blindada (Impede qualquer KeyError)
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
    .pilar-box { background-color: #161B22; border: 1px solid #30363D; padding: 10px; border-radius: 8px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 DEFINITIVO)
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
            if key == 'ec': df = pd.DataFrame([["Coca 1L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=['Tipo', 'Qtd'])
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
                        'role': res['cargo'].values[0]
                    })
                    st.rerun()
                else: st.error("Acesso Negado.")
else:
    # Carregamento de Dados Global
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
        
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "📦 ESTOQUE INTELIGENTE", "🍻 PDV RÁPIDO", "🏗️ MAPA PILARES", "🍶 GESTÃO CASCOS", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS & EQUIPE"])
        if st.button("LOGOUT"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO 1: ESTOQUE INTELIGENTE (FARDO X AVULSO)
    # =================================================================
    if menu == "📦 ESTOQUE INTELIGENTE":
        st.title("📦 Gestão de Carga")
        with st.form("entrada_estoque"):
            p_sel = st.selectbox("Escolha o Produto", df_p['Nome'].tolist())
            col_e1, col_e2 = st.columns(2)
            qe = col_e1.number_input("Engradados/Fardos (x24)", 0)
            qa = col_e2.number_input("Unidades Avulsas", 0)
            if st.form_submit_button("REGISTRAR ENTRADA"):
                total_un = (qe * 24) + qa
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total_un
                df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Entrada de {total_un} unidades para {p_sel} confirmada!")
                st.rerun()

        st.markdown("### Estoque Real Detalhado")
        df_view = df_e.copy()
        df_view['Fardos (24un)'] = df_view['Qtd_Unidades'] // 24
        df_view['Avulsos'] = df_view['Qtd_Unidades'] % 24
        st.dataframe(df_view[['Nome', 'Fardos (24un)', 'Avulsos', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # MÓDULO 2: MAPA PILARES (GRADE VISUAL 5 COLUNAS)
    # =================================================================
    elif menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Organização de Pilares")
        
        if st.session_state['role'] == "ADMIN":
            with st.expander("🆕 Cadastrar Nova Camada no Pilar"):
                with st.form("form_pilar"):
                    p_alvo = st.selectbox("Selecione o Pilar", ["Pilar A", "Pilar B", "Pilar C"])
                    cam_n = st.number_input("Nível da Camada", 1)
                    st.write("Configuração da Camada (5 Colunas):")
                    c_cols = st.columns(5)
                    novas_pos = []
                    for i in range(5):
                        with c_cols[i]:
                            b = st.selectbox(f"Col {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p_{i}")
                            av = st.number_input(f"Avulso {i+1}", 0, key=f"a_{i}")
                            if b != "Vazio":
                                novas_pos.append([f"PI{datetime.now().microsecond}{i}", p_alvo, cam_n, i+1, b, av])
                    if st.form_submit_button("GRAVAR CAMADA"):
                        pd.concat([df_pi, pd.DataFrame(novas_pos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                        st.rerun()

        # Visualização Real
        p_ver = st.selectbox("Visualizar:", ["Pilar A", "Pilar B", "Pilar C"])
        camadas = sorted(df_pi[df_pi['Pilar'] == p_ver]['Camada'].unique(), reverse=True)

        for cam in camadas:
            st.markdown(f"#### Camada {cam}")
            cols_grade = st.columns(5)
            itens = df_pi[(df_pi['Pilar'] == p_ver) & (df_pi['Camada'] == cam)]
            for _, r in itens.iterrows():
                with cols_grade[int(r['Pos'])-1]:
                    st.markdown(f"**{r['Bebida']}**")
                    st.caption(f"Avulso: {r['Avulsos']}")
                    if st.button("BAIXA", key=f"bx_{r['ID']}"):
                        # Baixa de 1 fardo (24) + os avulsos que estavam nele
                        baixa_total = 24 + int(r['Avulsos'])
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= baixa_total
                        df_e.to_csv(DB['est'], index=False)
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.success(f"{r['Bebida']} Baixada!")
                        st.rerun()
            st.markdown("---")

    # =================================================================
    # MÓDULO 3: PDV RÁPIDO (COM FARDO E UNIDADE)
    # =================================================================
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa")
        for _, r in df_p.iterrows():
            q_est = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.markdown(f"### {r['Nome']}")
                c2.metric("No Estoque", f"{q_est // 24}F | {q_est % 24}U")
                
                if c3.button("FARDO (24)", key=f"f_{r['Nome']}") and q_est >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 24
                    df_e.to_csv(DB['est'], index=False)
                    v_d = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 24, r['Preco_Custo']*24, r['Preco_Venda']*24, st.session_state['nome']]]
                    pd.DataFrame(v_d).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
                
                if c4.button("UNIDADE", key=f"u_{r['Nome']}") and q_est >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                    df_e.to_csv(DB['est'], index=False)
                    v_d = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                    pd.DataFrame(v_d).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
            st.markdown("---")

    # =================================================================
    # MÓDULO 4: HISTÓRICO BRUTO (COM FILTRO E ESTORNO)
    # =================================================================
    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Relatório Geral de Movimentação")
        hc1, hc2 = st.columns(2)
        f_prod = hc1.text_input("Filtrar Produto").upper()
        f_user = hc2.text_input("Filtrar Operador").upper()
        
        df_h = df_v.copy()
        if f_prod: df_h = df_h[df_h['Produto'].str.contains(f_prod)]
        if f_user: df_h = df_h[df_h['Usuario'].str.contains(f_user)]
        
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        if st.session_state['role'] == "ADMIN":
            st.markdown("---")
            st.subheader("🚫 Estorno de Vendas (Últimas 10)")
            for i, row in df_h.tail(10).iloc[::-1].iterrows():
                cc1, cc2 = st.columns([5, 1])
                cc1.info(f"{row['Hora']} - {row['Produto']} ({row['Qtd']} un) - R$ {row['Venda_T']} | Operador: {row['Usuario']}")
                if cc2.button("ANULAR", key=f"est_{i}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.success("Venda Estornada!")
                    st.rerun()

    # =================================================================
    # MÓDULO 5: CONFIGS & EQUIPE (GESTÃO COMPLETA)
    # =================================================================
    elif menu == "⚙️ CONFIGS & EQUIPE":
        st.title("⚙️ Painel de Controle Administrativo")
        tab_perf, tab_prod, tab_user = st.tabs(["🖼️ Meu Perfil", "📦 Cadastro de Produtos", "👥 Gestão da Equipe"])
        
        with tab_perf:
            u_file = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
            if u_file:
                b64 = get_img_64(u_file)
                df_u_db = pd.read_csv(DB['usr'])
                df_u_db.loc[df_u_db['user'] == st.session_state['user'], 'foto'] = b64
                df_u_db.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto atualizada!")

        with tab_prod:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_p"):
                    n_p = st.text_input("Nome do Novo Produto").upper()
                    c_p = st.selectbox("Categoria", ["Romarinho", "Lata", "Refrigerante", "Long neck", "Outros"])
                    col_p1, col_p2 = st.columns(2)
                    v_custo = col_p1.number_input("Preço de Custo", 0.0)
                    v_venda = col_p2.number_input("Preço de Venda", 0.0)
                    if st.form_submit_button("CADASTRAR PRODUTO NO BANCO"):
                        if n_p:
                            new_p = pd.DataFrame([[c_p, n_p, v_custo, v_venda, 24]], columns=df_p.columns)
                            pd.concat([df_p, new_p]).to_csv(DB['prod'], index=False)
                            new_e = pd.DataFrame([[n_p, 0, "-"]], columns=df_e.columns)
                            pd.concat([df_e, new_e]).to_csv(DB['est'], index=False)
                            st.success(f"{n_p} Registrado!")
                            st.rerun()
            else: st.warning("Acesso restrito ao Administrador.")

        with tab_user:
            if st.session_state['role'] == "ADMIN":
                st.subheader("Criar Acesso para Funcionário")
                with st.form("cad_u"):
                    u_login = st.text_input("Login de Acesso")
                    u_nome = st.text_input("Nome do Colaborador")
                    u_senha = st.text_input("Senha Inicial")
                    u_cargo = st.selectbox("Nível de Permissão", ["OPERADOR", "ADMIN"])
                    if st.form_submit_button("CRIAR CONTA"):
                        df_usr_add = pd.read_csv(DB['usr'])
                        new_u = pd.DataFrame([[u_login, u_nome, u_senha, '', u_cargo]], columns=df_usr_add.columns)
                        pd.concat([df_usr_add, new_u]).to_csv(DB['usr'], index=False)
                        st.success(f"Acesso criado para {u_nome}!")
                st.dataframe(pd.read_csv(DB['usr'])[['user', 'nome', 'cargo']], use_container_width=True)
            else: st.warning("Acesso restrito ao Administrador.")

    # Módulos Dashboard, Cascos (Mantidos Brutos)
    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            st.title("📊 Indicadores de Desempenho")
            df_fin = pd.merge(df_e, df_p, on="Nome")
            df_fin['Lucro'] = (df_fin['Preco_Venda'] - df_fin['Preco_Custo']) * df_fin['Qtd_Unidades']
            st.metric("Lucro Potencial em Estoque", f"R$ {df_fin['Lucro'].sum():,.2f}")
            st.plotly_chart(px.bar(df_fin, x='Nome', y='Lucro', title="Lucro por Item", template="plotly_dark"), use_container_width=True)
        else: st.info("Consulte o Admin para ver dados financeiros.")

    elif menu == "🍶 GESTÃO CASCOS":
        st.title("🍶 Vasilhames e Dívidas")
        st.dataframe(df_c, use_container_width=True)
