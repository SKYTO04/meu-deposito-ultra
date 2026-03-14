import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. CONFIGURAÇÃO DE UI ULTRA-DARK (ESTILO INDUSTRIAL)
# =================================================================
st.set_page_config(page_title="PACAEMBU G81 BRUTO", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    /* Fundo e Texto Geral */
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* Cards de Métricas */
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #58A6FF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Botões Brutalistas */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3.5em;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s;
        border: 1px solid #30363D;
        background-color: #21262D;
        color: #C9D1D9;
    }
    .stButton>button:hover {
        border-color: #58A6FF;
        color: #58A6FF;
        background-color: #30363D;
        transform: scale(1.01);
    }
    
    /* Títulos e Alertas */
    h1, h2, h3 { color: #58A6FF; font-weight: 800; text-transform: uppercase; }
    .stAlert { background-color: #161B22; border: 1px solid #30363D; color: #58A6FF; }
    
    /* Tabelas */
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE BANCO DE DADOS (CSV PERSISTENTE)
# =================================================================
V = "v81"
FILES = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'pil': f'pil_{V}.csv',
    'vendas': f'vendas_{V}.csv', 'cascos': f'cas_{V}.csv',
    'est_cascos': f'est_cascos_{V}.csv', 'usr': f'usr_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'pil': ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        'vendas': ['ID', 'Data', 'Produto', 'Qtd', 'Custo_Total', 'Venda_Total', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        'est_cascos': ['Tipo', 'Qtd'],
        'usr': ['user', 'nome', 'senha', 'is_admin', 'foto']
    }
    for key, path in FILES.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'est_cascos':
                df = pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=structs[key])
            if key == 'usr':
                df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', 'SIM', '']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

# =================================================================
# 3. LÓGICA DE ACESSO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1,1,1])
    with col:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("👤 USUÁRIO")
            pwd = st.text_input("🔑 SENHA", type="password")
            if st.form_submit_button("ACESSAR SISTEMA"):
                df_u = pd.read_csv(FILES['usr'])
                valid = df_u[(df_u['user'] == user) & (df_u['senha'].astype(str) == pwd)]
                if not valid.empty:
                    st.session_state.update({'auth': True, 'nome': valid['nome'].values[0]})
                    st.rerun()
                else: st.error("Acesso Negado.")
else:
    # Carregamento de Tabelas
    df_p = pd.read_csv(FILES['prod'])
    df_e = pd.read_csv(FILES['est'])
    df_v = pd.read_csv(FILES['vendas'])
    df_ec = pd.read_csv(FILES['est_cascos'])
    df_c = pd.read_csv(FILES['cascos'])
    df_pi = pd.read_csv(FILES['pil'])
    user_now = st.session_state['nome']

    # --- NAVEGAÇÃO LATERAL ---
    with st.sidebar:
        st.title("PACAEMBU 🏦")
        st.write(f"Operador: **{user_now}**")
        menu = st.radio("MÓDULOS", ["📊 Dashboard", "📦 Entrada", "🍻 PDV", "🏗️ Pilares", "🍶 Cascos", "✨ Itens"])
        if st.button("SAIR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # ABA: DASHBOARD (O CORAÇÃO FINANCEIRO)
    # =================================================================
    if menu == "📊 Dashboard":
        st.title("📊 Painel de Patrimônio")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Pat_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['Pat_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            df_f['Lucro'] = df_f['Pat_Venda'] - df_f['Pat_Custo']

            c1, c2, c3 = st.columns(3)
            c1.metric("Investimento (Custo)", f"R$ {df_f['Pat_Custo'].sum():,.2f}")
            c2.metric("Retorno (Venda)", f"R$ {df_f['Pat_Venda'].sum():,.2f}")
            c3.metric("Lucro Estimado", f"R$ {df_f['Lucro'].sum():,.2f}")

            st.markdown("---")
            col_l, col_r = st.columns(2)
            with col_l:
                fig = px.pie(df_f, values='Pat_Venda', names='Categoria', hole=0.4, title="Valor por Categoria", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            with col_r:
                fig2 = px.bar(df_f.nlargest(8, 'Lucro'), x='Nome', y='Lucro', title="Top Lucrativos (R$)", template="plotly_dark", color_discrete_sequence=['#58A6FF'])
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Sem dados para exibir o Dashboard.")

    # =================================================================
    # ABA: ENTRADA DE ESTOQUE (CONTROLE DE AVULSOS)
    # =================================================================
    elif menu == "📦 Entrada":
        st.title("📦 Entrada de Carga")
        with st.form("entrada_bruta"):
            item_sel = st.selectbox("Escolha o Produto", df_p['Nome'].tolist())
            col_en, col_av = st.columns(2)
            qtd_eng = col_en.number_input("Engradados Fechados (x24)", 0, step=1)
            qtd_solta = col_av.number_input("Unidades Soltas", 0, step=1)
            total_un = (qtd_eng * 24) + qtd_solta
            
            if st.form_submit_button("REGISTRAR ENTRADA NA BASE"):
                if total_un > 0:
                    df_e.loc[df_e['Nome'] == item_sel, 'Qtd_Unidades'] += total_un
                    df_e.loc[df_e['Nome'] == item_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                    df_e.to_csv(FILES['est'], index=False)
                    st.success(f"Carga de {total_un} unidades para {item_sel} registrada!")
                    st.rerun()

        st.subheader("Estoque Físico Atual")
        df_vis = df_e.copy()
        df_vis['Eng'] = df_vis['Qtd_Unidades'] // 24
        df_vis['Avu'] = df_vis['Qtd_Unidades'] % 24
        st.dataframe(df_vis[['Nome', 'Eng', 'Avu', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: PDV (SAÍDAS E ESTORNO)
    # =================================================================
    elif menu == "🍻 PDV":
        st.title("🍻 Ponto de Venda")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            st_data = df_e[df_e['Nome'] == item['Nome']]
            if not st_data.empty:
                q = int(st_data['Qtd_Unidades'].values[0])
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.markdown(f"**{item['Nome']}**\nVenda: R$ {item['Preco_Venda']:.2f}")
                    c2.metric("Estoque", f"{q//24}E | {q%24}U")
                    if c3.button("ENG", key=f"v_e_{item['Nome']}") and q >= 24:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                        df_e.to_csv(FILES['est'], index=False)
                        v_id = f"V{datetime.now().strftime('%M%S')}"
                        new_v = [[v_id, datetime.now().strftime("%H:%M"), item['Nome'], 24, item['Preco_Custo']*24, item['Preco_Venda']*24, user_now]]
                        pd.DataFrame(new_v).to_csv(FILES['vendas'], mode='a', header=False, index=False)
                        st.rerun()
                    if c4.button("UN", key=f"v_u_{item['Nome']}") and q >= 1:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                        df_e.to_csv(FILES['est'], index=False)
                        v_id = f"V{datetime.now().strftime('%M%S')}"
                        new_v = [[v_id, datetime.now().strftime("%H:%M"), item['Nome'], 1, item['Preco_Custo'], item['Preco_Venda'], user_now]]
                        pd.DataFrame(new_v).to_csv(FILES['vendas'], mode='a', header=False, index=False)
                        st.rerun()
                st.markdown("---")
        
        with st.expander("🕒 Estornar Erros"):
            v_hist = df_v.tail(5).iloc[::-1]
            for idx, row in v_hist.iterrows():
                cc1, cc2 = st.columns([4, 1])
                cc1.write(f"{row['ID']} | {row['Produto']} | {row['Qtd']} un")
                if cc2.button("🚫", key=f"est_{idx}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(FILES['est'], index=False)
                    df_v.drop(idx).to_csv(FILES['vendas'], index=False)
                    st.rerun()

    # =================================================================
    # ABA: PILARES (LÓGICA AUTOMÁTICA)
    # =================================================================
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Mapa de Empilhamento")
        with st.expander("➕ Montar Camada (3x2 ou 2x3)"):
            p_name = st.selectbox("Pilar", ["Pilar 1", "Pilar 2", "Pilar 3"])
            exist = df_pi[df_pi['Pilar'] == p_name]
            cam = 1 if exist.empty else exist['Camada'].max() + 1
            logica = "3x2 (Amarrada)" if cam % 2 != 0 else "2x3 (Invertida)"
            st.info(f"Camada {cam}: {logica}")
            
            p_items = []
            cols_p = st.columns(5)
            for i in range(5):
                with cols_p[i]:
                    beb = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pb_{i}")
                    avu = st.number_input(f"Avu {i+1}", 0, key=f"pa_{i}")
                    if beb != "Vazio":
                        p_items.append([f"{p_name}_{cam}_{i}", p_name, cam, i+1, beb, avu])
            if st.button("SALVAR CAMADA"):
                pd.concat([df_pi, pd.DataFrame(p_items, columns=df_pi.columns)]).to_csv(FILES['pil'], index=False)
                st.rerun()

        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            p_data = df_pi[df_pi['Pilar'] == p]
            for c in sorted(p_data['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                slots = st.columns(5)
                for _, r in p_data[p_data['Camada'] == c].iterrows():
                    with slots[int(r['Posicao'])-1]:
                        st.write(f"**{r['Bebida']}**")
                        if st.button("SAÍDA", key=f"p_out_{r['ID']}"):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                            df_e.to_csv(FILES['est'], index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(FILES['pil'], index=False)
                            st.rerun()

    # =================================================================
    # ABA: CASCOS (ESTOQUE E CLIENTES)
    # =================================================================
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        metrics_c = st.columns(4)
        for i, row in df_ec.iterrows():
            metrics_c[i].metric(row['Tipo'], f"{row['Qtd']} un")
            
        st.markdown("---")
        cl, cr = st.columns([1, 1.5])
        with cl:
            st.subheader("Nova Dívida")
            with st.form("f_casco"):
                cli, tip, qtd = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    if cli:
                        cid = f"C{datetime.now().strftime('%M%S')}"
                        pd.concat([df_c, pd.DataFrame([[cid, datetime.now().strftime("%d/%m"), cli, tip, qtd, "DEVE", user_now]], columns=df_c.columns)]).to_csv(FILES['cascos'], index=False)
                        st.rerun()
        with cr:
            st.subheader("Pendentes")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"{r['Cliente']} - {r['Qtd']} {r['Tipo']}"):
                    if st.button("RECEBER CASCO", key=f"dev_{i}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(FILES['cascos'], index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(FILES['est_cascos'], index=False)
                        st.rerun()

    # =================================================================
    # ABA: ITENS (CADASTRO BRUTO)
    # =================================================================
    elif menu == "✨ Itens":
        st.title("✨ Cadastro de Itens")
        with st.form("f_itens"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Refrigerante", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            c3, c4, c5 = st.columns(3)
            pc = c3.number_input("Preço Custo (Un)", 0.0, format="%.2f")
            pv = c4.number_input("Preço Venda (Un)", 0.0, format="%.2f")
            me = c5.number_input("Estoque Mínimo", 24)
            if st.form_submit_button("CADASTRAR PRODUTO"):
                if nom:
                    pd.concat([df_p, pd.DataFrame([[cat, nom, pc, pv, me]], columns=df_p.columns)]).to_csv(FILES['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0, "-"]], columns=df_e.columns)]).to_csv(FILES['est'], index=False)
                    st.success(f"{nom} cadastrado no sistema!")
                    st.rerun()
        st.dataframe(df_p, use_container_width=True, hide_index=True)
