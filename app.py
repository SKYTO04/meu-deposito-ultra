import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN DE ALTO PADRÃO (DARK MODE PREMIUM)
# =================================================================
st.set_page_config(page_title="Pacaembu G68 Ultra", page_icon="💎", layout="wide")

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
    hr { border: 0.1px solid #30363D; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. ARQUITETURA DE DADOS (BANCO DE DADOS COMPLETO)
# =================================================================
DB_PROD = "prod_v68.csv"
DB_EST = "est_v68.csv"
DB_PIL = "pil_v68.csv"
DB_USR = "usr_v68.csv"
DB_LOG = "log_v68.csv"
DB_CAS = "cas_v68.csv"
DB_VENDAS = "vendas_v68.csv" # Histórico detalhado de saídas

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
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Tipo', 'Valor', 'Usuario']
    }
    for arq, cols in tabelas.items():
        if not os.path.exists(arq): pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def registrar_movimentacao(u, acao, prod="", qtd=0, tipo="", valor=0.0):
    # Log Geral
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M:%S"), u, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)
    # Histórico de Vendas/Saídas
    if qtd != 0:
        pd.DataFrame([[f"V{datetime.now().strftime('%S%M%H')}", datetime.now().strftime("%d/%m/%Y %H:%M"), prod, qtd, tipo, valor, u]], 
                     columns=['ID', 'Data', 'Produto', 'Qtd', 'Tipo', 'Valor', 'Usuario']).to_csv(DB_VENDAS, mode='a', header=False, index=False)

# =================================================================
# 3. SEGURANÇA E LOGIN
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU ULTRA G68</h1>", unsafe_allow_html=True)
    with st.form("login_prestige"):
        u_in = st.text_input("👤 Usuário")
        s_in = st.text_input("🔑 Senha", type="password")
        if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
            df_u = pd.read_csv(DB_USR)
            v = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
            if not v.empty:
                st.session_state.update({'auth': True, 'user': u_in, 'nome': v['nome'].values[0], 'adm': (v['is_admin'].values[0] == 'SIM')})
                registrar_movimentacao(st.session_state['nome'], "Login no Sistema")
                st.rerun()
            else: st.error("Acesso Negado.")
else:
    # Carregamento de Tabelas
    df_p, df_e, df_pi = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_c, df_u, df_v = pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_VENDAS)
    n_log, is_adm = st.session_state['nome'], st.session_state['adm']

    # --- SIDEBAR CUSTOM ---
    st.sidebar.markdown(f"<h2 style='text-align:center;'>💎 PACAEMBU</h2>", unsafe_allow_html=True)
    
    user_data = df_u[df_u['user'] == st.session_state['user']]
    f_b64 = user_data['foto'].values[0] if not user_data.empty and not pd.isna(user_data['foto'].values[0]) else ""
    if f_b64:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{f_b64}' style='border-radius:50%; width:110px; height:110px; object-fit:cover; border:3px solid #58A6FF;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='https://cdn-icons-png.flaticon.com/512/149/149071.png' width='110'></div>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"<p style='text-align:center; margin-top:5px;'><b>{n_log}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("SISTEMA", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Estoque Central", "🍶 Gestão de Cascos", "✨ Cadastro Geral", "⚙️ Meu Perfil"] + (["📊 Dash Financeiro", "📜 Histórico Total"] if is_adm else []))
    
    if st.sidebar.button("🚪 DESCONECTAR"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: PDV ROMARINHO (COM ESTORNO E HISTÓRICO LOCAL)
    # =================================================================
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda")
        prods = df_p[df_p['Categoria'] == "Romarinho"]
        
        for _, item in prods.iterrows():
            est_u = int(df_e[df_e['Nome'] == item['Nome']]['Qtd_Unidades'].values[0])
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"#### {item['Nome']}")
                c2.metric("Estoque", f"{est_u//24} Eng | {est_u%24} Un")
                
                if c3.button(f"BAIXAR ENG", key=f"e_{item['Nome']}"):
                    if est_u >= 24:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                        df_e.to_csv(DB_EST, index=False)
                        registrar_movimentacao(n_log, f"Venda Eng {item['Nome']}", item['Nome'], 24, "Engradado", item['Preco_Venda']*24)
                        st.rerun()
                if c4.button(f"BAIXAR UN", key=f"u_{item['Nome']}"):
                    if est_u >= 1:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                        df_e.to_csv(DB_EST, index=False)
                        registrar_movimentacao(n_log, f"Venda Un {item['Nome']}", item['Nome'], 1, "Unidade", item['Preco_Venda'])
                        st.rerun()
            st.markdown("---")
        
        with st.expander("🕒 Últimas Vendas (Para Estorno)"):
            ultimas = df_v[df_v['Usuario'] == n_log].tail(5).iloc[::-1]
            for i, r in ultimas.iterrows():
                l1, l2 = st.columns([7, 2])
                l1.write(f"PRODUTO: {r['Produto']} | QTD: {r['Qtd']} | DATA: {r['Data']}")
                if l2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                    df_e.loc[df_e['Nome'] == r['Produto'], 'Qtd_Unidades'] += r['Qtd']
                    df_e.to_csv(DB_EST, index=False)
                    df_v.drop(i).to_csv(DB_VENDAS, index=False)
                    registrar_movimentacao(n_log, f"ESTORNO: {r['Produto']}")
                    st.rerun()

    # =================================================================
    # ABA: PILARES (LÓGICA AMARRAÇÃO 3x2 / 2x3)
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
                
                bebs = ["Vazio"] + df_p['Nome'].tolist()
                col1, col2 = st.columns(2)
                novos_dados = []
                for i in range(at+fr):
                    col = col1 if (i+1) <= at else col2
                    b = col.selectbox(f"Posição {i+1}", bebs, key=f"b_{i+1}_{cam}")
                    a = col.number_input(f"Avulsos {i+1}", 0, key=f"a_{i+1}_{cam}")
                    if b != "Vazio": novos_dados.append([f"{n_p}_{cam}_{i+1}", n_p, cam, i+1, b, a])
                
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pi, pd.DataFrame(novos_dados, columns=df_pi.columns)]).to_csv(DB_PIL, index=False)
                    st.rerun()

        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            for c in sorted(df_pi[df_pi['Pilar']==p]['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                d = df_pi[(df_pi['Pilar']==p) & (df_pi['Camada']==c)]
                cols = st.columns(5)
                for _, r in d.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background:#1c2128; padding:5px; border-radius:5px; border:1px solid #30363d; text-align:center; font-size:12px;'><b>{r['Bebida']}</b><br>+{r['Avulsos']}un</div>", unsafe_allow_html=True)
                        if st.button("SAÍDA", key=r['ID'], use_container_width=True):
                            total = 6 + r['Avulsos'] # Exemplo Fardo Refri
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total
                            df_e.to_csv(DB_EST, index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            registrar_movimentacao(n_log, f"Saída Pilar: {r['Bebida']}", r['Bebida'], total, "Pilar", 0)
                            st.rerun()

    # =================================================================
    # ABA: GESTÃO DE CASCOS (SISTEMA DE DÍVIDA)
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Vasilhames e Devedores")
        with st.form("add_casco"):
            c1, c2, c3, c4 = st.columns(4)
            cli, tip, qtd = c1.text_input("Cliente"), c2.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c3.number_input("Qtd", 1)
            if c4.form_submit_button("LANÇAR"):
                pd.concat([df_c, pd.DataFrame([[f"C{datetime.now().strftime('%S')}", datetime.now().strftime("%d/%m %H:%M"), cli, tip, qtd, "DEVE", n_log]], columns=df_c.columns)]).to_csv(DB_CAS, index=False)
                st.rerun()
        
        st.subheader("Pendências Ativas")
        for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
            l1, l2 = st.columns([7, 2])
            l1.error(f"👤 {r['Cliente']} -> {r['Qtd']}x {r['Tipo']} (Por: {r['Responsavel']})")
            if l2.button("RECEBER", key=f"pago_{r['ID']}"):
                df_c.at[i, 'Status'] = "PAGO"
                df_c.to_csv(DB_CAS, index=False)
                registrar_movimentacao(n_log, f"Baixa Casco: {r['Cliente']}")
                st.rerun()

    # =================================================================
    # ABA: ESTOQUE (ENTRADAS E ALERTAS)
    # =================================================================
    elif menu == "📦 Estoque Central":
        st.title("📦 Entradas e Balanço")
        if not df_p.empty:
            with st.form("entrada"):
                sel = st.selectbox("Produto", df_p['Nome'].unique())
                ce1, ce2 = st.columns(2)
                f, a = ce1.number_input("Fardos/Eng", 0), ce2.number_input("Avulsos", 0)
                if st.form_submit_button("REGISTRAR"):
                    mult = 24 if df_p[df_p['Nome']==sel]['Categoria'].values[0] == "Romarinho" else 12
                    total = (f * mult) + a
                    df_e.loc[df_e['Nome'] == sel, 'Qtd_Unidades'] += total
                    df_e.to_csv(DB_EST, index=False)
                    registrar_movimentacao(n_log, f"Entrada Estoque: {sel}", sel, total, "Entrada", 0)
                    st.rerun()
        
        st.subheader("Relatório de Estoque")
        for _, r in df_e.iterrows():
            min_e = df_p[df_p['Nome'] == r['Nome']]['Estoque_Minimo'].values[0]
            if r['Qtd_Unidades'] <= min_e:
                st.warning(f"⚠️ REPOSIÇÃO NECESSÁRIA: {r['Nome']} ({r['Qtd_Unidades']} un)")
        st.dataframe(df_e, use_container_width=True)

    # =================================================================
    # ABA: HISTÓRICO TOTAL (COMPLETO)
    # =================================================================
    elif menu == "📜 Histórico Total" and is_adm:
        st.title("📜 Auditoria Geral")
        tab1, tab2, tab3 = st.tabs(["Logs do Sistema", "Vendas Detalhadas", "Movimentação de Pilares"])
        with tab1: st.dataframe(pd.read_csv(DB_LOG).iloc[::-1], use_container_width=True)
        with tab2: st.dataframe(df_v.iloc[::-1], use_container_width=True)
        with tab3: st.dataframe(df_pi, use_container_width=True)

    # =================================================================
    # ABA: FINANCEIRO (LUCRO E PATRIMÔNIO)
    # =================================================================
    elif menu == "📊 Dash Financeiro" and is_adm:
        st.title("📊 Painel Gerencial")
        df_fin = pd.merge(df_e, df_p, on='Nome')
        df_fin['V_Custo'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Custo']
        df_fin['V_Venda'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Venda']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Valor em Estoque (Custo)", f"R$ {df_fin['V_Custo'].sum():,.2f}")
        c2.metric("Potencial de Venda", f"R$ {df_fin['V_Venda'].sum():,.2f}")
        c3.metric("Lucro Previsto", f"R$ {(df_fin['V_Venda'].sum() - df_fin['V_Custo'].sum()):,.2f}")
        
        st.bar_chart(df_fin.set_index('Nome')['Qtd_Unidades'])

    # =================================================================
    # ABA: CADASTRO E PERFIL
    # =================================================================
    elif menu == "✨ Cadastro Geral":
        st.title("✨ Cadastro")
        with st.form("cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat, nom, min_e = c1.selectbox("Cat", ["Romarinho", "Refrigerante", "Lata"]), c2.text_input("Nome").upper(), c3.number_input("Mín", 24)
            c4, c5 = st.columns(2)
            cus, ven = c4.number_input("Custo Un", 0.0), c5.number_input("Venda Un", 0.0)
            if st.form_submit_button("CADASTRAR"):
                pd.concat([df_p, pd.DataFrame([[cat, nom, cus, ven, min_e]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                st.rerun()

    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações")
        upload = st.file_uploader("Trocar Foto", type=['jpg', 'png'])
        if st.button("SALVAR"):
            if upload:
                img = Image.open(upload); img.thumbnail((150, 150))
                buf = io.BytesIO(); img.save(buf, format="PNG")
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = base64.b64encode(buf.getvalue()).decode()
                df_u.to_csv(DB_USR, index=False); st.rerun()
