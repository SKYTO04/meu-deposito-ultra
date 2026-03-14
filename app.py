import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E CSS BRUTALISTA (ULTRA DARK)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização de Segurança do Session State (IMPEDE O KEYERROR)
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'nome': '', 'foto': '', 'user': ''})

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #58A6FF;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 800; height: 3.8em;
        text-transform: uppercase; border: 1px solid #30363D;
        background-color: #21262D; color: #C9D1D9; transition: all 0.3s ease;
    }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; transform: translateY(-2px); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; text-transform: uppercase; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE BANCO DE DADOS (V86 FINAL)
# =================================================================
V = "v86_final"
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
# 3. LÓGICA DE LOGIN
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("USUÁRIO")
            s = st.text_input("SENHA", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                df_u = pd.read_csv(DB['usr'])
                user_match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not user_match.empty:
                    st.session_state.update({
                        'auth': True, 'nome': user_match['nome'].values[0],
                        'foto': str(user_match['foto'].values[0]) if pd.notna(user_match['foto'].values[0]) else '',
                        'user': u
                    })
                    st.rerun()
                else: st.error("Credenciais Inválidas.")
else:
    # Carregamento Global
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])

    # --- SIDEBAR COM TRAVA DE SEGURANÇA ---
    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        # Checa se a foto existe e não é vazia
        if st.session_state.get('foto') and len(st.session_state['foto']) > 10:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" class="profile-img" width="160">', unsafe_allow_html=True)
        else:
            st.warning("Sem Foto de Perfil")
        
        st.markdown(f'<h3>{st.session_state["nome"]}</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu = st.radio("NAVEGAÇÃO MESTRE", ["📊 DASHBOARD", "📦 ENTRADA BRUTA", "🍻 PDV ROMARINHO", "🏗️ MAPA PILARES", "🍶 GESTÃO CASCOS", "🕒 HISTÓRICO", "⚙️ CONFIGURAÇÕES"])
        
        if st.button("DESCONECTAR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULOS DO SISTEMA
    # =================================================================
    if menu == "📊 DASHBOARD":
        st.title("📊 Painel de Patrimônio")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Pat_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['Pat_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            c1, c2, c3 = st.columns(3)
            c1.metric("Investimento", f"R$ {df_f['Pat_Custo'].sum():,.2f}")
            c2.metric("Venda Total", f"R$ {df_f['Pat_Venda'].sum():,.2f}")
            c3.metric("Lucro Bruto", f"R$ {(df_f['Pat_Venda'].sum() - df_f['Pat_Custo'].sum()):,.2f}")
            st.plotly_chart(px.bar(df_v.tail(20), x='Hora', y='Venda_T', color='Produto', template="plotly_dark"), use_container_width=True)

    elif menu == "📦 ENTRADA BRUTA":
        st.title("📦 Entrada de Mercadoria")
        with st.form("f_ent"):
            p_sel = st.selectbox("Selecione o Item", df_p['Nome'].tolist())
            c1, c2 = st.columns(2)
            qe, qa = c1.number_input("Engradados (x24)", 0), c2.number_input("Avulsos", 0)
            if st.form_submit_button("REGISTRAR CARGA"):
                tot = (qe*24) + qa
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += tot
                df_e.to_csv(DB['est'], index=False)
                st.rerun()
        st.dataframe(df_e, use_container_width=True)

    elif menu == "🍻 PDV ROMARINHO":
        st.title("🍻 Ponto de Venda")
        for _, it in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            q = df_e[df_e['Nome'] == it['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.markdown(f"### {it['Nome']}")
            c2.metric("Estoque", f"{q//24}E | {q%24}U")
            if c3.button("VENDER ENG", key=f"e_{it['Nome']}") and q >= 24:
                df_e.loc[df_e['Nome'] == it['Nome'], 'Qtd_Unidades'] -= 24
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), it['Nome'], 24, it['Preco_Custo']*24, it['Preco_Venda']*24, st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()
            if c4.button("VENDER UN", key=f"u_{it['Nome']}") and q >= 1:
                df_e.loc[df_e['Nome'] == it['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                pd.DataFrame([[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), it['Nome'], 1, it['Preco_Custo'], it['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "🏗️ MAPA PILARES":
        st.title("🏗️ Logística de Pilares")
        p_sel = st.selectbox("Pilar", ["Pilar A", "Pilar B", "Pilar C"])
        for c in sorted(df_pi[df_pi['Pilar'] == p_sel]['Camada'].unique(), reverse=True):
            st.subheader(f"Camada {c}")
            cols = st.columns(5)
            for _, r in df_pi[(df_pi['Pilar'] == p_sel) & (df_pi['Camada'] == c)].iterrows():
                with cols[int(r['Pos'])-1]:
                    st.write(f"**{r['Bebida']}**")
                    if st.button("BAIXA", key=f"b_{r['ID']}"):
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                        df_e.to_csv(DB['est'], index=False)
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.rerun()

    elif menu == "🍶 GESTÃO CASCOS":
        st.title("🍶 Vasilhames")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("casco"):
                cli, tip, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_c, pd.DataFrame([[f"C{datetime.now().second}", "14/03", cli, tip, q, "DEVE", st.session_state['nome']]], columns=df_c.columns)]).to_csv(DB['cascos'], index=False)
                    st.rerun()
        st.dataframe(df_c[df_c['Status'] == "DEVE"], use_container_width=True)

    elif menu == "🕒 HISTÓRICO":
        st.title("🕒 Relatório Geral")
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
        if not df_v.empty:
            if st.button("ESTORNAR ÚLTIMA VENDA"):
                last = df_v.iloc[-1]
                df_e.loc[df_e['Nome'] == last['Produto'], 'Qtd_Unidades'] += last['Qtd']
                df_e.to_csv(DB['est'], index=False)
                df_v.drop(df_v.index[-1]).to_csv(DB['vendas'], index=False)
                st.rerun()

    elif menu == "⚙️ CONFIGURAÇÕES":
        st.title("⚙️ Painel de Controle")
        tab1, tab2 = st.tabs(["Meu Perfil", "Cadastro de Itens"])
        with tab1:
            up = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
            if up:
                b64 = get_img_64(up)
                df_u = pd.read_csv(DB['usr'])
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = b64
                df_u.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto salva! Atualize a página.")
        with tab2:
            with st.form("novo_p"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Cat", ["Romarinho", "Lata", "Outros"])
                pc, pv = st.number_input("Custo"), st.number_input("Venda")
                if st.form_submit_button("CADASTRAR"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, 24]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    st.rerun()
