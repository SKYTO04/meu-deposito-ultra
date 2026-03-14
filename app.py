import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# =================================================================
# 1. SETUP DE INTERFACE (DARK INDUSTRIAL)
# =================================================================
st.set_page_config(page_title="PACAEMBU G82 - SISTEMA BRUTO", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 20px; border-left: 5px solid #58A6FF; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; border: 1px solid #30363D; background-color: #21262D; color: #C9D1D9; }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (PERSISTÊNCIA)
# =================================================================
V = "v82"
DB = {
    'prod': f'prod_{V}.csv', 
    'est': f'est_{V}.csv', 
    'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv',
    'est_cascos': f'est_cascos_{V}.csv',
    'pi': f'pi_{V}.csv'
}

def init_db():
    # Tabelas base
    if not os.path.exists(DB['prod']):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo']).to_csv(DB['prod'], index=False)
    if not os.path.exists(DB['est']):
        pd.DataFrame(columns=['Nome', 'Qtd_Unidades', 'Ultima_Entrada']).to_csv(DB['est'], index=False)
    if not os.path.exists(DB['vendas']):
        pd.DataFrame(columns=['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario']).to_csv(DB['vendas'], index=False)
    if not os.path.exists(DB['cascos']):
        pd.DataFrame(columns=['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status']).to_csv(DB['cascos'], index=False)
    if not os.path.exists(DB['est_cascos']):
        pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=['Tipo', 'Qtd']).to_csv(DB['est_cascos'], index=False)
    if not os.path.exists(DB['pi']):
        pd.DataFrame(columns=['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos']).to_csv(DB['pi'], index=False)

init_db()

# Carga de dados
df_p = pd.read_csv(DB['prod'])
df_e = pd.read_csv(DB['est'])
df_v = pd.read_csv(DB['vendas'])
df_ec = pd.read_csv(DB['est_cascos'])
df_c = pd.read_csv(DB['cascos'])
df_pi = pd.read_csv(DB['pi'])

# =================================================================
# 3. NAVEGAÇÃO
# =================================================================
menu = st.sidebar.radio("SISTEMA", ["📊 DASHBOARD", "📦 ENTRADA/ESTOQUE", "🍻 PDV ROMARINHO", "🏗️ MAPA PILARES", "🍶 GESTÃO CASCOS", "⚙️ CADASTRO"])

# =================================================================
# ABA: DASHBOARD (BRUTO)
# =================================================================
if menu == "📊 DASHBOARD":
    st.title("📊 Painel de Controle Financeiro")
    
    if not df_e.empty and not df_p.empty:
        df_f = pd.merge(df_e, df_p, on="Nome")
        df_f['Pat_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
        df_f['Pat_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Patrimônio (Custo)", f"R$ {df_f['Pat_Custo'].sum():,.2f}")
        c2.metric("📈 Potencial de Venda", f"R$ {df_f['Pat_Venda'].sum():,.2f}")
        c3.metric("💎 Lucro Estimado", f"R$ {(df_f['Pat_Venda'].sum() - df_f['Pat_Custo'].sum()):,.2f}")
        
        st.markdown("---")
        # Gráfico de Vendas por Dia
        if not df_v.empty:
            st.subheader("Vendas Recentes")
            fig_v = px.bar(df_v.tail(20), x="Hora", y="Venda_T", color="Produto", template="plotly_dark", title="Fluxo de Caixa (Últimas 20)")
            st.plotly_chart(fig_v, use_container_width=True)
    else:
        st.info("Cadastre produtos para ver o financeiro.")

# =================================================================
# ABA: ENTRADA (ENG + AVULSO)
# =================================================================
elif menu == "📦 ENTRADA/ESTOQUE":
    st.title("📦 Entrada de Mercadoria")
    with st.form("f_entrada"):
        p_sel = st.selectbox("Selecione o Produto", df_p['Nome'].tolist())
        c1, c2 = st.columns(2)
        qtd_e = c1.number_input("Engradados (x24)", 0)
        qtd_a = c2.number_input("Avulsos", 0)
        total = (qtd_e * 24) + qtd_a
        
        if st.form_submit_button("CONFIRMAR ENTRADA"):
            if total > 0:
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB['est'], index=False)
                st.success(f"Entrada de {total} un para {p_sel} confirmada!")
                st.rerun()

    st.subheader("Estoque Físico")
    df_vis = df_e.copy()
    df_vis['📦 Eng'] = df_vis['Qtd_Unidades'] // 24
    df_vis['🍺 Avu'] = df_vis['Qtd_Unidades'] % 24
    st.dataframe(df_vis[['Nome', '📦 Eng', '🍺 Avu', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

# =================================================================
# ABA: PDV (SAÍDA RÁPIDA + ESTORNO)
# =================================================================
elif menu == "🍻 PDV ROMARINHO":
    st.title("🍻 Ponto de Venda")
    romas = df_p[df_p['Categoria'] == "Romarinho"]
    
    for i, r in romas.iterrows():
        est_at = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
        with st.container():
            c1, c2, c3, c4 = st.columns([3,2,1,1])
            c1.write(f"### {r['Nome']}")
            c2.metric("Estoque", f"{est_at//24} Eng | {est_at%24} Un")
            if c3.button("VENDER ENG", key=f"v_e_{i}") and est_at >= 24:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 24
                df_e.to_csv(DB['est'], index=False)
                new_v = [[f"V{i}{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 24, r['Preco_Custo']*24, r['Preco_Venda']*24, "Admin"]]
                pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()
            if c4.button("VENDER UN", key=f"v_u_{i}") and est_at >= 1:
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                new_v = [[f"V{i}{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], "Admin"]]
                pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()
        st.markdown("---")

    with st.expander("🕒 Histórico / Estorno"):
        if not df_v.empty:
            v_recente = df_v.tail(10).iloc[::-1]
            for idx, row in v_recente.iterrows():
                cc1, cc2 = st.columns([4,1])
                cc1.write(f"{row['Hora']} - {row['Produto']} ({row['Qtd']}un) - R$ {row['Venda_T']}")
                if cc2.button("🚫", key=f"est_{idx}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    # Remove do CSV de vendas
                    df_v.drop(idx).to_csv(DB['vendas'], index=False)
                    st.rerun()

# =================================================================
# ABA: PILARES (LOGICA 3x2 / 2x3)
# =================================================================
elif menu == "🏗️ MAPA PILARES":
    st.title("🏗️ Gestão de Pilares")
    p_sel = st.selectbox("Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D"])
    
    with st.expander("➕ Nova Camada"):
        exist = df_pi[df_pi['Pilar'] == p_sel]
        camada = 1 if exist.empty else exist['Camada'].max() + 1
        st.write(f"Montando Camada: **{camada}**")
        
        novos = []
        cols_p = st.columns(5)
        for i in range(5):
            with cols_p[i]:
                b = st.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p_{i}")
                a = st.number_input(f"Avu {i+1}", 0, key=f"a_{i}")
                if b != "Vazio":
                    novos.append([f"{p_sel}_{camada}_{i}", p_sel, camada, i+1, b, a])
        if st.button("SALVAR CAMADA"):
            pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
            st.rerun()

    # Visualização do Pilar
    p_data = df_pi[df_pi['Pilar'] == p_sel]
    for c in sorted(p_data['Camada'].unique(), reverse=True):
        st.write(f"**Camada {c}**")
        cols = st.columns(5)
        for _, r in p_data[p_data['Camada'] == c].iterrows():
            with cols[int(r['Pos'])-1]:
                st.write(f"{r['Bebida']}")
                if st.button("SAÍDA", key=f"out_{r['ID']}"):
                    df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                    df_e.to_csv(DB['est'], index=False)
                    df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                    st.rerun()

# =================================================================
# ABA: CASCOS (DÍVIDA E ESTOQUE)
# =================================================================
elif menu == "🍶 GESTÃO CASCOS":
    st.title("🍶 Vasilhames e Cascos")
    
    # Estoque de Cascos
    c_met = st.columns(4)
    for i, row in df_ec.iterrows():
        c_met[i].metric(row['Tipo'], f"{row['Qtd']} un")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Registrar Dívida")
        with st.form("f_casco"):
            cli = st.text_input("Nome do Cliente").upper()
            tip = st.selectbox("Tipo de Casco", df_ec['Tipo'].tolist())
            qtd = st.number_input("Quantidade", 1)
            if st.form_submit_button("LANÇAR"):
                new_c = [[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cli, tip, qtd, "DEVE"]]
                pd.concat([df_c, pd.DataFrame(new_c, columns=df_c.columns)]).to_csv(DB['cascos'], index=False)
                st.rerun()
    with col2:
        st.subheader("Pendências Ativas")
        for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
            with st.expander(f"⚠️ {r['Cliente']} - {r['Qtd']} {r['Tipo']}"):
                if st.button("📥 RECEBER", key=f"rec_{i}"):
                    df_c.at[i, 'Status'] = "DEVOLVEU"
                    df_c.to_csv(DB['cascos'], index=False)
                    df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                    df_ec.to_csv(DB['est_cascos'], index=False)
                    st.rerun()

# =================================================================
# ABA: CADASTRO
# =================================================================
elif menu == "⚙️ CADASTRO":
    st.title("⚙️ Cadastro de Produtos")
    with st.form("f_cad"):
        cat = st.selectbox("Categoria", ["Romarinho", "Lata", "Refrigerante", "Litro", "Outros"])
        nom = st.text_input("Nome").upper()
        c1, c2, c3 = st.columns(3)
        pc = c1.number_input("Custo Unitário", 0.0)
        pv = c2.number_input("Venda Unitária", 0.0)
        em = c3.number_input("Estoque Mínimo", 24)
        if st.form_submit_button("CADASTRAR"):
            if nom:
                pd.concat([df_p, pd.DataFrame([[cat, nom, pc, pv, em]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                st.rerun()
    st.dataframe(df_p, use_container_width=True)
