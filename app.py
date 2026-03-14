import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO E DESIGN PRESTIGE (DARK MODE ULTRA)
# =================================================================
st.set_page_config(page_title="Pacaembu G72 Ultra", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 15px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 3.2em; transition: 0.3s; border: 1px solid #30363D; }
    .stButton>button:hover { border-color: #58A6FF; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    div[data-testid="stExpander"] { background-color: #161B22; border-radius: 12px; border: 1px solid #30363D; margin-bottom: 10px; }
    .status-critico { color: #FF7B72; font-weight: bold; }
    .status-ok { color: #7EE787; font-weight: bold; }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (ARQUITETURA DE ARQUIVOS)
# =================================================================
DB_PROD = "prod_v72.csv"
DB_EST = "est_v72.csv"
DB_PIL = "pil_v72.csv"
DB_USR = "usr_v72.csv"
DB_LOG = "log_v72.csv"
DB_CAS = "cas_v72.csv"
DB_VENDAS = "vendas_v72.csv"
DB_EST_CASCOS = "est_cascos_v72.csv"

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'tel', 'foto']).to_csv(DB_USR, index=False)
    
    tabelas = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        DB_EST: ['Nome', 'Qtd_Unidades'],
        DB_PIL: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Tipo', 'Valor', 'Usuario'],
        DB_EST_CASCOS: ['Tipo', 'Qtd']
    }
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            if arq == DB_EST_CASCOS:
                pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=cols).to_csv(arq, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def registrar_movimentacao(u, acao, prod="", qtd=0, tipo="", valor=0.0):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M:%S"), u, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)
    if qtd != 0:
        pd.DataFrame([[f"V{datetime.now().strftime('%S%M%H')}", datetime.now().strftime("%d/%m/%Y %H:%M"), prod, qtd, tipo, valor, u]], 
                     columns=['ID', 'Data', 'Produto', 'Qtd', 'Tipo', 'Valor', 'Usuario']).to_csv(DB_VENDAS, mode='a', header=False, index=False)

# =================================================================
# 3. AUTENTICAÇÃO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU ULTRA G72</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR", use_container_width=True):
            df_u = pd.read_csv(DB_USR)
            v = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
            if not v.empty:
                st.session_state.update({'auth': True, 'user': u_in, 'nome': v['nome'].values[0], 'adm': (v['is_admin'].values[0] == 'SIM')})
                st.rerun()
            else: st.error("Acesso Negado.")
else:
    # Carregamento Geral de Dados
    df_p, df_e, df_pi = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_c, df_u, df_v, df_ec = pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_VENDAS), pd.read_csv(DB_EST_CASCOS)
    n_log, is_adm = st.session_state['nome'], st.session_state['adm']

    # --- SIDEBAR ---
    st.sidebar.title("💎 PACAEMBU")
    user_data = df_u[df_u['user'] == st.session_state['user']]
    f_b64 = user_data['foto'].values[0] if not user_data.empty and not pd.isna(user_data['foto'].values[0]) else ""
    if f_b64:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{f_b64}' style='border-radius:50%; width:110px; height:110px; object-fit:cover; border:3px solid #58A6FF;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=110)
    
    st.sidebar.markdown(f"<p style='text-align:center;'><b>{n_log}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("SISTEMA", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Estoque Central", "🍶 Gestão de Cascos", "✨ Cadastro Geral", "⚙️ Meu Perfil"] + (["📊 Dash Financeiro", "📜 Histórico Total"] if is_adm else []))
    
    if st.sidebar.button("🚪 SAIR"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: PDV ROMARINHO
    # =================================================================
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda - Romarinho")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            est_u = int(df_e[df_e['Nome'] == item['Nome']]['Qtd_Unidades'].values[0])
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"#### {item['Nome']}")
                c2.metric("Saldo", f"{est_u//24} Eng | {est_u%24} Un")
                if c3.button(f"➖ ENG", key=f"e_{item['Nome']}"):
                    if est_u >= 24:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                        df_e.to_csv(DB_EST, index=False)
                        registrar_movimentacao(n_log, f"Venda Eng {item['Nome']}", item['Nome'], 24, "Engradado", item['Preco_Venda']*24)
                        st.rerun()
                if c4.button(f"➖ UN", key=f"u_{item['Nome']}"):
                    if est_u >= 1:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                        df_e.to_csv(DB_EST, index=False)
                        registrar_movimentacao(n_log, f"Venda Un {item['Nome']}", item['Nome'], 1, "Unidade", item['Preco_Venda'])
                        st.rerun()
            st.markdown("---")

    # =================================================================
    # ABA: MAPA DE PILARES (LÓGICA 3x2 / 2x3)
    # =================================================================
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Mapa de Amarração")
        with st.expander("➕ MONTAR NOVA CAMADA"):
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
                if st.button("SALVAR"):
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
                        if st.button("SAÍDA", key=r['ID']):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            st.rerun()

    # =================================================================
    # ABA: GESTÃO DE CASCOS (ULTRA INTEGRADO + HISTÓRICO + ESTORNO)
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Gestão de Cascos")
        
        # 1. Painel de Saldo
        st.subheader("📦 Saldo de Vazios no Depósito")
        cols_est = st.columns(4)
        for idx, row in df_ec.iterrows():
            cols_est[idx].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        
        # 2. Cadastro e Devedores
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.subheader("➕ Nova Pendência")
            with st.form("f_casco"):
                f_cli = st.text_input("Cliente").upper()
                f_tip = st.selectbox("Tipo", df_ec['Tipo'].tolist())
                f_qtd = st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_c, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), f_cli, f_tip, f_qtd, "DEVE", n_log]], columns=df_c.columns)]).to_csv(DB_CAS, index=False)
                    st.rerun()
        with c2:
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

        # 3. Histórico e Estorno (O Coração da sua dúvida)
        st.subheader("📜 Histórico e Estornos")
        tab_h, tab_f = st.tabs(["🔄 Baixas Recentes", "🚚 Envio para Fábrica"])
        with tab_h:
            recentes = df_c[df_c['Status'] != "DEVE"].tail(10).iloc[::-1]
            for i, r in recentes.iterrows():
                h1, h2 = st.columns([7, 2])
                h1.write(f"**{r['Cliente']}** entregou {r['Qtd']} {r['Tipo']} ({r['Status']})")
                if h2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                    if r['Status'] == "DEVOLVEU": # Se devolveu o casco, remove do estoque de vazios ao estornar
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] -= r['Qtd']
                        df_ec.to_csv(DB_EST_CASCOS, index=False)
                    df_c.at[i, 'Status'] = "DEVE"
                    df_c.to_csv(DB_CAS, index=False)
                    st.rerun()
        with tab_f:
            with st.form("f_fab"):
                t = st.selectbox("Tipo que saiu", df_ec['Tipo'].tolist())
                q = st.number_input("Qtd", 1)
                if st.form_submit_button("CONFIRMAR SAÍDA"):
                    if df_ec.loc[df_ec['Tipo'] == t, 'Qtd'].values[0] >= q:
                        df_ec.loc[df_ec['Tipo'] == t, 'Qtd'] -= q
                        df_ec.to_csv(DB_EST_CASCOS, index=False)
                        registrar_movimentacao(n_log, f"Saída Fábrica: {q} {t}")
                        st.rerun()
                    else: st.error("Saldo insuficiente!")

    # =================================================================
    # ABAS ADICIONAIS: ESTOQUE, CADASTRO, FINANCEIRO
    # =================================================================
    elif menu == "📦 Estoque Central":
        st.title("📦 Entradas")
        with st.form("ent"):
            p = st.selectbox("Produto", df_p['Nome'].unique())
            f, a = st.columns(2)
            qf = f.number_input("Fardos/Eng", 0)
            qa = a.number_input("Avulsos", 0)
            if st.form_submit_button("LANÇAR"):
                mult = 24 if df_p[df_p['Nome']==p]['Categoria'].values[0] == "Romarinho" else 12
                df_e.loc[df_e['Nome'] == p, 'Qtd_Unidades'] += (qf * mult + qa)
                df_e.to_csv(DB_EST, index=False)
                st.rerun()
        st.dataframe(df_e)

    elif menu == "✨ Cadastro Geral":
        st.title("✨ Novo Item")
        with st.form("cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat, nom, min_e = c1.selectbox("Cat", ["Romarinho", "Refrigerante", "Lata"]), c2.text_input("Nome").upper(), c3.number_input("Mín", 24)
            c4, c5 = st.columns(2)
            cus, ven = c4.number_input("Custo Un", 0.0), c5.number_input("Venda Un", 0.0)
            if st.form_submit_button("SALVAR"):
                pd.concat([df_p, pd.DataFrame([[cat, nom, cus, ven, min_e]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                st.rerun()

    elif menu == "📊 Dash Financeiro" and is_adm:
        st.title("📊 Painel Gerencial")
        df_fin = pd.merge(df_e, df_p, on='Nome')
        df_fin['Custo_Total'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Custo']
        df_fin['Venda_Total'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Venda']
        st.metric("Patrimônio (Custo)", f"R$ {df_fin['Custo_Total'].sum():,.2f}")
        st.metric("Lucro Previsto", f"R$ {df_fin['Venda_Total'].sum() - df_fin['Custo_Total'].sum():,.2f}")
        st.bar_chart(df_fin.set_index('Nome')['Qtd_Unidades'])

    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Perfil")
        u = st.file_uploader("Foto", type=['jpg', 'png'])
        if st.button("SALVAR"):
            if u:
                img = Image.open(u); img.thumbnail((150, 150)); buf = io.BytesIO(); img.save(buf, format="PNG")
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = base64.b64encode(buf.getvalue()).decode()
                df_u.to_csv(DB_USR, index=False); st.rerun()

    elif menu == "📜 Histórico Total":
        st.subheader("Logs do Sistema")
        st.dataframe(pd.read_csv(DB_LOG).iloc[::-1])
        st.subheader("Vendas Detalhadas")
        st.dataframe(df_v.iloc[::-1])
