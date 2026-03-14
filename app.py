import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO E DESIGN PRESTIGE
# =================================================================
st.set_page_config(page_title="Pacaembu G73 Ultra", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 15px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; transition: 0.3s; border: 1px solid #30363D; }
    .stButton>button:hover { border-color: #58A6FF; transform: translateY(-2px); }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS
# =================================================================
DB_PROD = "prod_v73.csv"
DB_EST = "est_v73.csv"
DB_PIL = "pil_v73.csv"
DB_USR = "usr_v73.csv"
DB_LOG = "log_v73.csv"
DB_CAS = "cas_v73.csv"
DB_VENDAS = "vendas_v73.csv"
DB_EST_CASCOS = "est_cascos_v73.csv"

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_USR, index=False)
    
    tabelas = {
        DB_PROD: ['Categoria', 'Nome', 'Estoque_Minimo'],
        DB_EST: ['Nome', 'Qtd_Unidades', 'Preco_Custo', 'Preco_Venda'],
        DB_PIL: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Valor', 'Usuario'],
        DB_EST_CASCOS: ['Tipo', 'Qtd']
    }
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            if arq == DB_EST_CASCOS:
                pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=cols).to_csv(arq, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def registrar_movimentacao(u, acao, prod="", qtd=0, valor=0.0):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M:%S"), u, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)
    if qtd != 0:
        pd.DataFrame([[f"V{datetime.now().strftime('%S%M%H')}", datetime.now().strftime("%d/%m/%Y %H:%M"), prod, qtd, valor, u]], 
                     columns=['ID', 'Data', 'Produto', 'Qtd', 'Valor', 'Usuario']).to_csv(DB_VENDAS, mode='a', header=False, index=False)

# =================================================================
# 3. INTERFACE PRINCIPAL
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU G73</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR"):
            df_u = pd.read_csv(DB_USR)
            v = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
            if not v.empty:
                st.session_state.update({'auth': True, 'user': u_in, 'nome': v['nome'].values[0], 'adm': (v['is_admin'].values[0] == 'SIM')})
                st.rerun()
else:
    df_p, df_e, df_pi = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_c, df_u, df_v, df_ec = pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_VENDAS), pd.read_csv(DB_EST_CASCOS)
    n_log, is_adm = st.session_state['nome'], st.session_state['adm']

    menu = st.sidebar.radio("SISTEMA", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Estoque & Preços", "🍶 Gestão de Cascos", "✨ Cadastro de Itens", "⚙️ Meu Perfil"] + (["📜 Histórico Total"] if is_adm else []))

    # --- PDV ROMARINHO (COM ESTORNO) ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Romarinho")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            dados_est = df_e[df_e['Nome'] == item['Nome']]
            if not dados_est.empty:
                est_u = int(dados_est['Qtd_Unidades'].values[0])
                venda_un = float(dados_est['Preco_Venda'].values[0])
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.markdown(f"#### {item['Nome']}")
                    c2.metric("Estoque", f"{est_u//24} Eng | {est_u%24} Un")
                    if c3.button(f"➖ ENG (24)", key=f"e_{item['Nome']}"):
                        if est_u >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                            df_e.to_csv(DB_EST, index=False)
                            registrar_movimentacao(n_log, f"Venda Eng: {item['Nome']}", item['Nome'], 24, venda_un*24)
                            st.rerun()
                    if c4.button(f"➖ UN (1)", key=f"u_{item['Nome']}"):
                        if est_u >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                            df_e.to_csv(DB_EST, index=False)
                            registrar_movimentacao(n_log, f"Venda Un: {item['Nome']}", item['Nome'], 1, venda_un)
                            st.rerun()
        
        st.markdown("---")
        with st.expander("🕒 Estornar Últimas Vendas"):
            ultimas = df_v[df_v['Usuario'] == n_log].tail(5).iloc[::-1]
            for i, r in ultimas.iterrows():
                h1, h2 = st.columns([7, 2])
                h1.write(f"Venda: {r['Produto']} | Qtd: {r['Qtd']} | Total: R${r['Valor']:.2f}")
                if h2.button("🚫 ESTORNAR", key=f"estv_{r['ID']}"):
                    df_e.loc[df_e['Nome'] == r['Produto'], 'Qtd_Unidades'] += r['Qtd']
                    df_e.to_csv(DB_EST, index=False)
                    df_v.drop(i).to_csv(DB_VENDAS, index=False)
                    registrar_movimentacao(n_log, f"ESTORNO VENDA: {r['Produto']}")
                    st.rerun()

    # --- ESTOQUE E PREÇOS (CENTRALIZADO) ---
    elif menu == "📦 Estoque & Preços":
        st.title("📦 Gestão de Estoque e Valores")
        with st.form("entrada"):
            st.subheader("Entrada de Mercadoria / Ajuste de Preço")
            p_sel = st.selectbox("Produto", df_p['Nome'].unique())
            c1, c2, c3 = st.columns(3)
            qtd_e = c1.number_input("Adicionar Qtd (Unidades)", 0)
            pc = c2.number_input("Novo Preço Custo", 0.0)
            pv = c3.number_input("Novo Preço Venda", 0.0)
            if st.form_submit_button("ATUALIZAR"):
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += qtd_e
                if pc > 0: df_e.loc[df_e['Nome'] == p_sel, 'Preco_Custo'] = pc
                if pv > 0: df_e.loc[df_e['Nome'] == p_sel, 'Preco_Venda'] = pv
                df_e.to_csv(DB_EST, index=False)
                registrar_movimentacao(n_log, f"Ajuste Estoque/Preço: {p_sel}")
                st.rerun()
        st.dataframe(df_e, use_container_width=True)

    # --- CADASTRO DE ITENS (SIMPLIFICADO) ---
    elif menu == "✨ Cadastro de Itens":
        st.title("✨ Cadastro de Novos Produtos")
        with st.form("novo_p"):
            st.write("Aqui você apenas registra o nome. Preços e quantidades são feitos na aba 'Estoque'.")
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Lata", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            min_e = c3.number_input("Mínimo Alerta", 24)
            if st.form_submit_button("CADASTRAR"):
                if nom and not df_p[df_p['Nome'] == nom].empty:
                    st.error("Produto já existe!")
                elif nom:
                    pd.concat([df_p, pd.DataFrame([[cat, nom, min_e]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0, 0.0, 0.0]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                    registrar_movimentacao(n_log, f"Cadastrou Item: {nom}")
                    st.success(f"{nom} cadastrado!")
                    st.rerun()

    # --- GESTÃO DE CASCOS (INTEGRADO COM ESTORNO) ---
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Vasilhames")
        # Painel de Saldo
        cols_ec = st.columns(4)
        for idx, row in df_ec.iterrows():
            cols_ec[idx].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        c_cad, c_dev = st.columns([1, 1.5])
        with c_cad:
            st.subheader("➕ Nova Pendência")
            with st.form("f_cas"):
                cli, tip, qtd = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("GERAR DÍVIDA"):
                    pd.concat([df_c, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), cli, tip, qtd, "DEVE", n_log]], columns=df_c.columns)]).to_csv(DB_CAS, index=False)
                    st.rerun()
        with c_dev:
            st.subheader("🔴 Devedores")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"⚠️ {r['Cliente']} - {r['Qtd']}x {r['Tipo']}"):
                    b1, b2 = st.columns(2)
                    if b1.button("📥 RECEBEU CASCO", key=f"r{r['ID']}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(DB_CAS, index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(DB_EST_CASCOS, index=False)
                        st.rerun()
                    if b2.button("💰 PAGO EM $", key=f"m{r['ID']}"):
                        df_c.at[i, 'Status'] = "PAGOU $"
                        df_c.to_csv(DB_CAS, index=False)
                        st.rerun()
        
        st.markdown("---")
        st.subheader("📜 Histórico e Estornos de Cascos")
        recentes_c = df_c[df_c['Status'] != "DEVE"].tail(10).iloc[::-1]
        for i, r in recentes_c.iterrows():
            h1, h2 = st.columns([7, 2])
            h1.write(f"**{r['Cliente']}** -> {r['Qtd']} {r['Tipo']} ({r['Status']})")
            if h2.button("🚫 ESTORNAR", key=f"estc_{r['ID']}"):
                if r['Status'] == "DEVOLVEU":
                    df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] -= r['Qtd']
                    df_ec.to_csv(DB_EST_CASCOS, index=False)
                df_c.at[i, 'Status'] = "DEVE"
                df_c.to_csv(DB_CAS, index=False)
                st.rerun()

    # --- MAPA DE PILARES (MANTIDO) ---
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Mapa de Amarração")
        with st.expander("➕ NOVA CAMADA"):
            p_sel = st.selectbox("Pilar", ["+ Criar"] + list(df_pi['Pilar'].unique()))
            n_p = st.text_input("Nome").upper() if p_sel == "+ Criar" else p_sel
            if n_p:
                cam = 1 if df_pi[df_pi['Pilar']==n_p].empty else df_pi[df_pi['Pilar']==n_p]['Camada'].max() + 1
                at, fr = (3, 2) if cam % 2 != 0 else (2, 3)
                st.info(f"MODO: {'Impar (3 Atrás / 2 Frente)' if cam % 2 != 0 else 'Par (2 Atrás / 3 Frente)'}")
                col1, col2 = st.columns(2)
                novos = []
                for i in range(at+fr):
                    col = col1 if (i+1) <= at else col2
                    b = col.selectbox(f"Posição {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p{i+1}{cam}")
                    a = col.number_input(f"Avulsos {i+1}", 0, key=f"a{i+1}{cam}")
                    if b != "Vazio": novos.append([f"{n_p}_{cam}_{i+1}", n_p, cam, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB_PIL, index=False)
                    st.rerun()
        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            for c in sorted(df_pi[df_pi['Pilar']==p]['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                d = df_pi[(df_pi['Pilar']==p) & (df_pi['Camada']==c)]
                cols = st.columns(5)
                for _, r in d.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background:#1c2128; padding:5px; border-radius:5px; border:1px solid #30363d; text-align:center;'><b>{r['Bebida']}</b><br>+{r['Avulsos']}</div>", unsafe_allow_html=True)
                        if st.button("SAÍDA", key=f"pil_{r['ID']}"):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            st.rerun()

    # --- HISTÓRICO TOTAL ---
    elif menu == "📜 Histórico Total":
        st.subheader("Logs e Auditoria")
        st.dataframe(pd.read_csv(DB_LOG).iloc[::-1], use_container_width=True)
        st.subheader("Histórico de Vendas Realizadas")
        st.dataframe(df_v.iloc[::-1], use_container_width=True)

    # --- MEU PERFIL ---
    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações de Perfil")
        u_file = st.file_uploader("Trocar Foto", type=['jpg', 'png'])
        if st.button("SALVAR"):
            if u_file:
                img = Image.open(u_file); img.thumbnail((150, 150)); buf = io.BytesIO(); img.save(buf, format="PNG")
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = base64.b64encode(buf.getvalue()).decode()
                df_u.to_csv(DB_USR, index=False); st.rerun()
