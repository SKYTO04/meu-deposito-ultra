import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO INDUSTRIAL (ULTRA DARK)
# =================================================================
st.set_page_config(page_title="PACAEMBU G85 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

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
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3.5em;
        text-transform: uppercase;
        border: 1px solid #30363D;
        background-color: #21262D;
        color: #C9D1D9;
        transition: 0.3s;
    }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; transform: scale(1.02); }
    h1, h2, h3 { color: #58A6FF; font-weight: 900; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    .status-deve { color: #FF7B72; font-weight: bold; }
    .status-ok { color: #7EE787; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E PERSISTÊNCIA
# =================================================================
V = "v85_PRESTIGE"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv', 'est_cascos': f'est_cascos_{V}.csv',
    'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Resp'],
        'est_cascos': ['Tipo', 'Qtd'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'is_admin', 'foto']
    }
    for key, arq in DB.items():
        if not os.path.exists(arq):
            df = pd.DataFrame(columns=structs[key])
            if key == 'est_cascos':
                df = pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=['Tipo', 'Qtd'])
            if key == 'usr':
                df = pd.DataFrame([['admin', 'GERENTE', '123', 'SIM', '']], columns=structs[key])
            df.to_csv(arq, index=False)

init_db()

# =================================================================
# 3. CONTROLE DE ACESSO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_login, _ = st.columns([1,1,1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU LOGIN</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR"):
                df_u = pd.read_csv(DB['usr'])
                val = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not val.empty:
                    st.session_state.update({'auth': True, 'nome': val['nome'].values[0]})
                    st.rerun()
                else: st.error("Incorreto.")
else:
    # Carga de Dados
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['est_cascos']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])
    u_nome = st.session_state['nome']

    # --- NAVEGAÇÃO ---
    st.sidebar.title("PACAEMBU 🏦")
    menu = st.sidebar.radio("MÓDULOS", ["📊 Dashboard", "📦 Entrada Bruta", "🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "🍶 Gestão de Cascos", "✨ Cadastro & Usuários"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # 4. MÓDULO: DASHBOARD
    # =================================================================
    if menu == "📊 Dashboard":
        st.title("📊 Resumo Bruto do Depósito")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['V_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['V_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Dinheiro em Produto", f"R$ {df_f['V_Custo'].sum():,.2f}")
            c2.metric("Potencial de Venda", f"R$ {df_f['V_Venda'].sum():,.2f}")
            c3.metric("Lucro Estimado", f"R$ {(df_f['V_Venda'].sum() - df_f['V_Custo'].sum()):,.2f}")
            
            st.markdown("---")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.plotly_chart(px.pie(df_f, values='V_Venda', names='Categoria', hole=.4, title="Valor por Categoria", template="plotly_dark"), use_container_width=True)
            with col_g2:
                st.plotly_chart(px.bar(df_f.nlargest(10, 'Qtd_Unidades'), x='Nome', y='Qtd_Unidades', title="Top 10 Estoque (Un)", template="plotly_dark"), use_container_width=True)
        else: st.info("Sem dados.")

    # =================================================================
    # 5. MÓDULO: ENTRADA BRUTA (AVULSOS)
    # =================================================================
    elif menu == "📦 Entrada Bruta":
        st.title("📦 Entrada de Carga")
        with st.form("f_ent"):
            p_sel = st.selectbox("Produto", df_p['Nome'].tolist())
            col_en, col_av = st.columns(2)
            qe = col_en.number_input("Engradados (x24)", 0, step=1)
            qa = col_av.number_input("Unidades Avulsas", 0, step=1)
            total = (qe * 24) + qa
            if st.form_submit_button("REGISTRAR ENTRADA"):
                if total > 0:
                    df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                    df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                    df_e.to_csv(DB['est'], index=False)
                    st.success(f"Adicionado {total} un de {p_sel}")
                    st.rerun()

        st.subheader("Estoque Físico Atual")
        df_vis = df_e.copy()
        df_vis['Eng'] = df_vis['Qtd_Unidades'] // 24
        df_vis['Avu'] = df_vis['Qtd_Unidades'] % 24
        st.dataframe(df_vis[['Nome', 'Eng', 'Avu', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # 6. MÓDULO: PDV ROMARINHO
    # =================================================================
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda")
        for _, r in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            est_un = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            with st.container():
                c1, c2, c3, c4 = st.columns([3,2,1,1])
                c1.write(f"### {r['Nome']}")
                c2.metric("Estoque", f"{est_un//24}E | {est_un%24}U")
                if c3.button("VENDER ENG", key=f"v_e_{r['Nome']}") and est_un >= 24:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 24
                    df_e.to_csv(DB['est'], index=False)
                    new = [[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 24, r['Preco_Custo']*24, r['Preco_Venda']*24, u_nome]]
                    pd.DataFrame(new).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
                if c4.button("VENDER UN", key=f"v_u_{r['Nome']}") and est_un >= 1:
                    df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                    df_e.to_csv(DB['est'], index=False)
                    new = [[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], u_nome]]
                    pd.DataFrame(new).to_csv(DB['vendas'], mode='a', header=False, index=False)
                    st.rerun()
            st.markdown("---")
        
        with st.expander("🕒 Estornar Últimas Vendas"):
            if not df_v.empty:
                for i, row in df_v.tail(5).iloc[::-1].iterrows():
                    cc1, cc2 = st.columns([4,1])
                    cc1.write(f"{row['Hora']} - {row['Produto']} ({row['Qtd']} un) - R$ {row['Venda_T']}")
                    if cc2.button("🚫", key=f"est_{i}"):
                        df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                        df_e.to_csv(DB['est'], index=False)
                        df_v.drop(i).to_csv(DB['vendas'], index=False)
                        st.rerun()

    # =================================================================
    # 7. MÓDULO: MAPA DE PILARES
    # =================================================================
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Logística de Pilares")
        p_sel = st.selectbox("Selecione o Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D"])
        
        with st.expander("➕ Nova Camada"):
            ex = df_pi[df_pi['Pilar'] == p_sel]
            cam = 1 if ex.empty else ex['Camada'].max() + 1
            st.info(f"Montando Camada {cam} (Amarração Automática)")
            novos_p = []
            cols_pi = st.columns(5)
            for i in range(5):
                with cols_pi[i]:
                    b = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pi_b_{i}")
                    a = st.number_input(f"Avu {i+1}", 0, key=f"pi_a_{i}")
                    if b != "Vazio":
                        novos_p.append([f"{p_sel}_{cam}_{i}", p_sel, cam, i+1, b, a])
            if st.button("CONFIRMAR CAMADA"):
                pd.concat([df_pi, pd.DataFrame(novos_p, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                st.rerun()

        for c in sorted(df_pi[df_pi['Pilar'] == p_sel]['Camada'].unique(), reverse=True):
            st.write(f"**Camada {c}**")
            cols_v = st.columns(5)
            for _, r in df_pi[(df_pi['Pilar'] == p_sel) & (df_pi['Camada'] == c)].iterrows():
                with cols_v[int(r['Pos'])-1]:
                    st.write(f"{r['Bebida']}")
                    if st.button("BAIXA", key=f"p_out_{r['ID']}"):
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                        df_e.to_csv(DB['est'], index=False)
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.rerun()

    # =================================================================
    # 8. MÓDULO: GESTÃO DE CASCOS
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Controle de Vasilhames")
        met = st.columns(4)
        for i, row in df_ec.iterrows():
            met[i].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("Nova Dívida")
            with st.form("f_cas"):
                cli, tip, q_c = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    new_c = [[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cli, tip, q_c, "DEVE", u_nome]]
                    pd.concat([df_c, pd.DataFrame(new_c, columns=df_c.columns)]).to_csv(DB['cascos'], index=False)
                    st.rerun()
        with cl2:
            st.subheader("Pendências")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"{r['Cliente']} - {r['Qtd']} {r['Tipo']}"):
                    if st.button("📥 RECEBER", key=f"rc_{i}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(DB['cascos'], index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(DB['est_cascos'], index=False)
                        st.rerun()

    # =================================================================
    # 9. MÓDULO: CADASTRO E USUÁRIOS
    # =================================================================
    elif menu == "✨ Cadastro & Usuários":
        st.title("⚙️ Configurações do Sistema")
        tab1, tab2 = st.tabs(["Produtos", "Usuários"])
        with tab1:
            with st.form("f_cad_p"):
                nom = st.text_input("Nome").upper()
                cat = st.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Litro", "Refrigerante", "Outros"])
                c_c, c_v, c_m = st.columns(3)
                pc, pv, em = c_c.number_input("Custo"), c_v.number_input("Venda"), c_m.number_input("Mínimo", 24)
                if st.form_submit_button("CADASTRAR PRODUTO"):
                    if nom:
                        pd.concat([df_p, pd.DataFrame([[cat, nom, pc, pv, em]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[nom, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        st.rerun()
            st.dataframe(df_p, use_container_width=True)
        with tab2:
            st.subheader("Gerenciar Equipe")
            with st.form("f_usr"):
                n_u, n_n, n_s = st.text_input("User"), st.text_input("Nome Completo"), st.text_input("Senha")
                if st.form_submit_button("CRIAR USUÁRIO"):
                    new_u = [[n_u, n_n, n_s, "NÃO", ""]]
                    pd.concat([pd.read_csv(DB['usr']), pd.DataFrame(new_u, columns=pd.read_csv(DB['usr']).columns)]).to_csv(DB['usr'], index=False)
                    st.rerun()
