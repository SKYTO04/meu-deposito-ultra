import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. CONFIGURAÇÃO DE INTERFACE
# =================================================================
st.set_page_config(page_title="PACAEMBU G80 OMNI", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 20px; border-left: 5px solid #58A6FF; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; transition: 0.3s; border: 1px solid #30363D; background-color: #21262D; color: #C9D1D9; }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; background-color: #30363D; transform: scale(1.02); }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. SISTEMA DE ARQUIVOS (BANCO DE DADOS)
# =================================================================
V = "v80"
DBS = {
    'prod': f'prod_{V}.csv',
    'est': f'est_{V}.csv',
    'pil': f'pil_{V}.csv',
    'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv',
    'est_cascos': f'est_cascos_{V}.csv',
    'usr': f'usr_{V}.csv'
}

def init_db():
    # Estruturas das tabelas
    struct = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'pil': ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        'vendas': ['ID', 'Data', 'Produto', 'Qtd', 'Custo_Total', 'Venda_Total', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        'est_cascos': ['Tipo', 'Qtd'],
        'usr': ['user', 'nome', 'senha', 'is_admin', 'foto']
    }
    for key, arq in DBS.items():
        if not os.path.exists(arq):
            df = pd.DataFrame(columns=struct[key])
            if key == 'est_cascos':
                df = pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=struct[key])
            if key == 'usr':
                df = pd.DataFrame([['admin', 'GERENTE', '123', 'SIM', '']], columns=struct[key])
            df.to_csv(arq, index=False)

init_db()

# =================================================================
# 3. AUTENTICAÇÃO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU G80 LOGIN</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.form_submit_button("ENTRAR"):
            df_u = pd.read_csv(DBS['usr'])
            valido = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not valido.empty:
                st.session_state.update({'auth': True, 'nome': valido['nome'].values[0]})
                st.rerun()
else:
    # Carregamento Global de Dados
    df_p = pd.read_csv(DBS['prod'])
    df_e = pd.read_csv(DBS['est'])
    df_v = pd.read_csv(DBS['vendas'])
    df_ec = pd.read_csv(DBS['est_cascos'])
    df_c = pd.read_csv(DBS['cascos'])
    df_pi = pd.read_csv(DBS['pil'])
    nome_usuario = st.session_state['nome']

    menu = st.sidebar.radio("NAVEGAÇÃO", ["📊 Dashboard", "📦 Entrada Estoque", "🍻 PDV Saídas", "🏗️ Mapa Pilares", "🍶 Gestão Cascos", "✨ Cadastro Itens"])

    # =================================================================
    # ABA: DASHBOARD FINANCEIRO
    # =================================================================
    if menu == "📊 Dashboard":
        st.title("📊 Resumo Financeiro e Patrimonial")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Patrimonio_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['Venda_Total'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            df_f['Lucro_Estimado'] = df_f['Venda_Total'] - df_f['Patrimonio_Custo']

            c1, c2, c3 = st.columns(3)
            c1.metric("Dinheiro em Produto (Custo)", f"R$ {df_f['Patrimonio_Custo'].sum():,.2f}")
            c2.metric("Estimativa Bruta (Venda)", f"R$ {df_f['Venda_Total'].sum():,.2f}")
            c3.metric("Lucro Projetado", f"R$ {df_f['Lucro_Estimado'].sum():,.2f}")

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.pie(df_f, values='Venda_Total', names='Categoria', title="Distribuição por Categoria", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                fig2 = px.bar(df_f.nlargest(10, 'Venda_Total'), x='Nome', y='Venda_Total', title="Top 10 Produtos (Valor de Venda)", template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aguardando dados para gerar indicadores.")

    # =================================================================
    # ABA: ENTRADA DE ESTOQUE (COM AVULSOS)
    # =================================================================
    elif menu == "📦 Entrada Estoque":
        st.title("📦 Entrada de Carga")
        with st.form("f_entrada"):
            p_sel = st.selectbox("Produto", df_p['Nome'].tolist())
            col1, col2 = st.columns(2)
            e_eng = col1.number_input("Qtd Engradados (x24)", 0, step=1)
            e_avu = col2.number_input("Unidades Avulsas", 0, step=1)
            total = (e_eng * 24) + e_avu
            if st.form_submit_button("REGISTRAR ENTRADA"):
                if total > 0:
                    df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += total
                    df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                    df_e.to_csv(DBS['est'], index=False)
                    st.success(f"Entrada de {total} un confirmada para {p_sel}!")
                    st.rerun()

        st.subheader("Estoque Atualizado")
        df_vis = df_e.copy()
        df_vis['Engradados'] = df_vis['Qtd_Unidades'] // 24
        df_vis['Avulsos'] = df_vis['Qtd_Unidades'] % 24
        st.dataframe(df_vis[['Nome', 'Engradados', 'Avulsos', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: PDV SAÍDAS (COM ESTORNO)
    # =================================================================
    elif menu == "🍻 PDV Saídas":
        st.title("🍻 Saídas PDV")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            est_row = df_e[df_e['Nome'] == item['Nome']]
            if not est_row.empty:
                qtd_total = int(est_row['Qtd_Unidades'].values[0])
                p_v = float(item['Preco_Venda'])
                p_c = float(item['Preco_Custo'])
                
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.markdown(f"**{item['Nome']}**\n\nR$ {p_v:.2f}")
                    c2.metric("Estoque", f"{qtd_total//24} Eng | {qtd_total%24} Un")
                    if c3.button("BAIXAR ENG", key=f"v_e_{item['Nome']}"):
                        if qtd_total >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                            df_e.to_csv(DBS['est'], index=False)
                            v_id = f"V{datetime.now().strftime('%M%S')}"
                            new_v = [[v_id, datetime.now().strftime("%H:%M"), item['Nome'], 24, p_c*24, p_v*24, nome_usuario]]
                            pd.DataFrame(new_v).to_csv(DBS['vendas'], mode='a', header=False, index=False)
                            st.rerun()
                    if c4.button("BAIXAR UN", key=f"v_u_{item['Nome']}"):
                        if qtd_total >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                            df_e.to_csv(DBS['est'], index=False)
                            v_id = f"V{datetime.now().strftime('%M%S')}"
                            new_v = [[v_id, datetime.now().strftime("%H:%M"), item['Nome'], 1, p_c, p_v, nome_usuario]]
                            pd.DataFrame(new_v).to_csv(DBS['vendas'], mode='a', header=False, index=False)
                            st.rerun()
        
        st.markdown("---")
        with st.expander("🕒 Últimas Vendas (Para Estorno)"):
            v_recente = df_v.tail(5).iloc[::-1]
            for idx, row in v_recente.iterrows():
                col_x, col_y = st.columns([4, 1])
                col_x.write(f"{row['Data']} - {row['Produto']} ({row['Qtd']}un) - R$ {row['Venda_Total']}")
                if col_y.button("🚫", key=f"est_{idx}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DBS['est'], index=False)
                    df_v.drop(idx).to_csv(DBS['vendas'], index=False)
                    st.rerun()

    # =================================================================
    # ABA: MAPA DE PILARES
    # =================================================================
    elif menu == "🏗️ Mapa Pilares":
        st.title("🏗️ Gestão de Pilares (3x2 / 2x3)")
        with st.expander("➕ Nova Camada no Pilar"):
            p_sel = st.selectbox("Escolha o Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D"])
            existentes = df_pi[df_pi['Pilar'] == p_sel]
            camada = 1 if existentes.empty else existentes['Camada'].max() + 1
            logica = "3x2" if camada % 2 != 0 else "2x3"
            st.info(f"Lógica da Camada {camada}: {logica}")
            
            novos_itens = []
            c_p1, c_p2 = st.columns(2)
            for i in range(5):
                target = c_p1 if i < 3 else c_p2
                b_p = target.selectbox(f"Pos {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p_{p_sel}_{i}")
                a_p = target.number_input(f"Avulsos {i+1}", 0, key=f"a_{p_sel}_{i}")
                if b_p != "Vazio":
                    novos_itens.append([f"{p_sel}_{camada}_{i}", p_sel, camada, i+1, b_p, a_p])
            
            if st.button("SALVAR CAMADA COMPLETA"):
                pd.concat([df_pi, pd.DataFrame(novos_itens, columns=df_pi.columns)]).to_csv(DBS['pil'], index=False)
                st.rerun()

        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            p_data = df_pi[df_pi['Pilar'] == p]
            for c in sorted(p_data['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                cols = st.columns(5)
                for _, r in p_data[p_data['Camada'] == c].iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.write(f"**{r['Bebida']}**")
                        if st.button("SAÍDA", key=f"p_out_{r['ID']}"):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                            df_e.to_csv(DBS['est'], index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DBS['pil'], index=False)
                            st.rerun()

    # =================================================================
    # ABA: GESTÃO DE CASCOS
    # =================================================================
    elif menu == "🍶 Gestão Cascos":
        st.title("🍶 Controle de Vasilhames")
        m1, m2, m3, m4 = st.columns(4)
        for i, r in df_ec.iterrows():
            [m1, m2, m3, m4][i].metric(r['Tipo'], f"{r['Qtd']} un")
        
        st.markdown("---")
        cl, cr = st.columns([1, 1.5])
        with cl:
            st.subheader("Lançar Pendência")
            with st.form("f_cas"):
                cli, t_c, q_c = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("REGISTRAR DÍVIDA"):
                    new_c = [[f"C{datetime.now().strftime('%H%M')}", datetime.now().strftime("%d/%m"), cli, t_c, q_c, "DEVE", nome_usuario]]
                    pd.concat([df_c, pd.DataFrame(new_c, columns=df_c.columns)]).to_csv(DBS['cascos'], index=False)
                    st.rerun()
        with cr:
            st.subheader("Clientes Devedores")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"{r['Cliente']} - {r['Qtd']}x {r['Tipo']}"):
                    if st.button("📥 RECEBER VASILHAME", key=f"dev_{i}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(DBS['cascos'], index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(DBS['est_cascos'], index=False)
                        st.rerun()

    # =================================================================
    # ABA: CADASTRO ITENS
    # =================================================================
    elif menu == "✨ Cadastro Itens":
        st.title("✨ Cadastro de Produtos")
        with st.form("f_cad"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Refrigerante", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            c3, c4, c5 = st.columns(3)
            pc = c3.number_input("Custo Unitário", 0.0)
            pv = c4.number_input("Venda Unitária", 0.0)
            me = c5.number_input("Mínimo", 24)
            if st.form_submit_button("CADASTRAR"):
                if nom:
                    pd.concat([df_p, pd.DataFrame([[cat, nom, pc, pv, me]], columns=df_p.columns)]).to_csv(DBS['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0, "-"]], columns=df_e.columns)]).to_csv(DBS['est'], index=False)
                    st.rerun()
        st.dataframe(df_p, use_container_width=True, hide_index=True)
