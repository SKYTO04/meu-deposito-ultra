import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E CSS INDUSTRIAL (DARK PRESTIGE)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização Crítica do Session State
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'nome': '', 'foto': '', 'user': ''})

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div[data-testid="metric-container"] {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: 20px; border-left: 5px solid #58A6FF;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 800; height: 3.8em;
        text-transform: uppercase; border: 1px solid #30363D;
        background-color: #21262D; color: #C9D1D9; transition: 0.3s;
    }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; background-color: #30363D; }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 10px; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V86 BRUTO)
# =================================================================
V = "v86_bruto"
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
# 3. CONTROLE DE ACESSO
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU G85</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("USUÁRIO")
            s = st.text_input("SENHA", type="password")
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB['usr'])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({
                        'auth': True, 'nome': match['nome'].values[0],
                        'foto': str(match['foto'].values[0]) if pd.notna(match['foto'].values[0]) else '',
                        'user': u
                    })
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
else:
    # Carga de Dados
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    # --- SIDEBAR BRUTA ---
    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if st.session_state['foto'] and len(st.session_state['foto']) > 50:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" class="profile-img" width="160">', unsafe_allow_html=True)
        else:
            st.info("⚠️ Perfil sem foto")
        st.markdown(f"### {st.session_state['nome']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu = st.radio("MÓDULOS", ["📊 DASHBOARD", "📦 ENTRADA BRUTA", "🍻 PDV ROMARINHO", "🏗️ MAPA PILARES", "🍶 GESTÃO CASCOS", "🕒 HISTÓRICO TOTAL", "⚙️ CONFIGURAÇÕES"])
        
        if st.button("SAIR DO SISTEMA"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO 1: DASHBOARD (LUCRO REAL)
    # =================================================================
    if menu == "📊 DASHBOARD":
        st.title("📊 Indicadores Financeiros")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Custo_T'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['Venda_T'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Custo em Estoque", f"R$ {df_f['Custo_T'].sum():,.2f}")
            c2.metric("Venda Prevista", f"R$ {df_f['Venda_T'].sum():,.2f}")
            c3.metric("Lucro Bruto", f"R$ {(df_f['Venda_T'].sum() - df_f['Custo_T'].sum()):,.2f}")
            
            st.plotly_chart(px.bar(df_v.tail(30), x='Hora', y='Venda_T', color='Produto', template="plotly_dark", title="Fluxo de Vendas (R$)"), use_container_width=True)

    # =================================================================
    # MÓDULO 2: ENTRADA BRUTA
    # =================================================================
    elif menu == "📦 ENTRADA BRUTA":
        st.title("📦 Recebimento de Carga")
        with st.form("entrada"):
            item = st.selectbox("Produto", df_p['Nome'].tolist())
            c1, c2 = st.columns(2)
            qe, qa = c1.number_input("Engradados", 0), c2.number_input("Avulsos", 0)
            if st.form_submit_button("CONFIRMAR"):
                total = (qe*24) + qa
                df_e.loc[df_e['Nome'] == item, 'Qtd_Unidades'] += total
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Entrada de {total} unidades em {item} realizada!")
                st.rerun()
        st.dataframe(df_e, use_container_width=True)

    # =================================================================
    # MÓDULO 3: PDV ROMARINHO
    # =================================================================
    elif menu == "🍻 PDV ROMARINHO":
        st.title("🍻 Venda Rápida")
        for _, r in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            q = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.markdown(f"### {r['Nome']}")
                c2.metric("Estoque", f"{q//24}E | {q%24}U")
                if c3.button("VENDER ENG", key=f"e_{r['Nome']}") and q >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 24
                    df_e.to_csv(DB['est'], index=False)
                    v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 24, r['Preco_Custo']*24, r['Preco_Venda']*24, st.session_state['nome']]]
                    pd.DataFrame(v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
                if c4.button("VENDER UN", key=f"u_{r['Nome']}") and q >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                    df_e.to_csv(DB['est'], index=False)
                    v = [[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]
                    pd.DataFrame(v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
            st.markdown("---")

    # =================================================================
    # MÓDULO 4: HISTÓRICO BRUTO (DETALHADO)
    # =================================================================
    elif menu == "🕒 HISTÓRICO TOTAL":
        st.title("🕒 Relatório Geral de Movimentação")
        
        # Filtros de Busca
        c1, c2 = st.columns(2)
        f_prod = c1.text_input("Filtrar por Produto").upper()
        f_user = c2.text_input("Filtrar por Operador").upper()
        
        df_h = df_v.copy()
        if f_prod: df_h = df_h[df_h['Produto'].str.contains(f_prod)]
        if f_user: df_h = df_h[df_h['Usuario'].str.contains(f_user)]
        
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("⚠️ Estorno Manual")
        if not df_h.empty:
            for i, row in df_h.tail(10).iloc[::-1].iterrows():
                col1, col2 = st.columns([5, 1])
                col1.info(f"{row['Hora']} - {row['Produto']} ({row['Qtd']} un) - R$ {row['Venda_T']} - Operador: {row['Usuario']}")
                if col2.button("ANULAR", key=f"del_{i}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(i).to_csv(DB['vendas'], index=False)
                    st.success("Venda estornada e estoque devolvido!")
                    st.rerun()

    # =================================================================
    # MÓDULO 5: MAPA PILARES
    # =================================================================
    elif menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Logística de Pilares")
        p_sel = st.selectbox("Pilar", ["Pilar A", "Pilar B", "Pilar C"])
        with st.expander("➕ Nova Camada"):
            cols = st.columns(5)
            novos = []
            for i in range(5):
                with cols[i]:
                    b = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pi_{i}")
                    if b != "Vazio": novos.append([f"P{i}{datetime.now().second}", p_sel, 1, i+1, b, 0])
            if st.button("SALVAR CAMADA"):
                pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                st.rerun()
        st.dataframe(df_pi[df_pi['Pilar'] == p_sel], use_container_width=True)

    # =================================================================
    # MÓDULO 6: GESTÃO CASCOS
    # =================================================================
    elif menu == "🍶 GESTÃO CASCOS":
        st.title("🍶 Vasilhames e Dívidas")
        met = st.columns(4)
        for i, row in df_ec.iterrows():
            met[i].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        with st.form("divida"):
            cli, tip, q = st.text_input("Nome do Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR"):
                new = [[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cli, tip, q, "DEVE", st.session_state['nome']]]
                pd.concat([df_c, pd.DataFrame(new, columns=df_c.columns)]).to_csv(DB['cascos'], index=False)
                st.rerun()
        st.dataframe(df_c[df_c['Status'] == "DEVE"], use_container_width=True)

    # =================================================================
    # MÓDULO 7: CONFIGURAÇÕES
    # =================================================================
    elif menu == "⚙️ CONFIGURAÇÕES":
        st.title("⚙️ Painel de Controle")
        tab1, tab2 = st.tabs(["🖼️ Perfil do Operador", "📦 Cadastro de Itens"])
        with tab1:
            up = st.file_uploader("Subir foto de perfil (300x300)", type=['png', 'jpg'])
            if up:
                b64 = get_img_64(up)
                df_u = pd.read_csv(DB['usr'])
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = b64
                df_u.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto atualizada! O sistema será atualizado.")
                st.rerun()
        with tab2:
            with st.form("cad"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Cat", ["Romarinho", "Lata", "Outros"])
                pc, pv = st.number_input("Custo"), st.number_input("Venda")
                if st.form_submit_button("CADASTRAR PRODUTO"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    st.rerun()
