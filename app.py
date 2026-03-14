import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO DE LUXO (DESIGN DARK PRESTIGE)
# =================================================================
st.set_page_config(page_title="Pacaembu G67 - Ultra", page_icon="🍻", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 15px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; transition: 0.3s; }
    .stButton>button:hover { border-color: #58A6FF; transform: scale(1.02); }
    div[data-testid="stExpander"] { background-color: #161B22; border-radius: 12px; border: 1px solid #30363D; }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; }
    .status-critico { color: #FF7B72; font-weight: bold; }
    .status-ok { color: #7EE787; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (ARQUITETURA COMPLETA)
# =================================================================
DB_P = "prod_v67.csv"
DB_E = "est_v67.csv"
DB_PI = "pil_v67.csv"
DB_U = "usr_v67.csv"
DB_L = "log_v67.csv"
DB_C = "cas_v67.csv"

def init_db():
    if not os.path.exists(DB_U):
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'tel', 'foto']).to_csv(DB_U, index=False)
    
    tabelas = {
        DB_P: ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        DB_E: ['Nome', 'Qtd_Unidades'],
        DB_PI: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_L: ['Data', 'Usuario', 'Ação'],
        DB_C: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel']
    }
    for arq, cols in tabelas.items():
        if not os.path.exists(arq): pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def salvar_log(u, a):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), u, a]], columns=['Data', 'Usuario', 'Ação']).to_csv(DB_L, mode='a', header=False, index=False)

# =================================================================
# 3. LOGIN E SESSÃO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU ULTRA G67</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR"):
            df_u = pd.read_csv(DB_U)
            v = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not v.empty:
                st.session_state.update({'auth': True, 'user': u, 'nome': v['nome'].values[0], 'adm': (v['is_admin'].values[0] == 'SIM')})
                st.rerun()
            else: st.error("Erro de login.")
else:
    # Carregamento Geral
    df_p, df_e, df_pi = pd.read_csv(DB_P), pd.read_csv(DB_E), pd.read_csv(DB_PI)
    df_c, df_u = pd.read_csv(DB_C), pd.read_csv(DB_U)
    u_log, n_log, is_adm = st.session_state['user'], st.session_state['nome'], st.session_state['adm']

    # --- SIDEBAR PROFISSIONAL ---
    st.sidebar.title("💎 MENU")
    user_data = df_u[df_u['user'] == u_log]
    img_b64 = user_data['foto'].values[0] if not user_data.empty and not pd.isna(user_data['foto'].values[0]) else ""
    
    if img_b64:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{img_b64}' style='border-radius:50%; width:120px; border:3px solid #58A6FF;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.sidebar.markdown(f"<p style='text-align:center'><b>{n_log}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Navegar:", ["🍻 Romarinhos (PDV)", "🏗️ Pilares (Mapa)", "📦 Estoque & Entradas", "🍶 Gestão de Cascos", "✨ Cadastro", "⚙️ Perfil"] + (["📊 Financeiro", "📜 Logs"] if is_adm else []))
    
    if st.sidebar.button("Sair"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: ROMARINHOS (BAIXA REAL E ALERTA)
    # =================================================================
    if menu == "🍻 Romarinhos (PDV)":
        st.title("🍻 PDV Romarinhos")
        prods = df_p[df_p['Categoria'] == "Romarinho"]
        
        for _, item in prods.iterrows():
            est_atual = int(df_e[df_e['Nome'] == item['Nome']]['Qtd_Unidades'].values[0])
            min_est = item['Estoque_Minimo']
            
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"#### {item['Nome']}")
                
                status_cor = "status-ok" if est_atual > min_est else "status-critico"
                c2.markdown(f"<span class='{status_cor}'>{est_atual//24} Eng | {est_atual%24} Un</span>", unsafe_allow_html=True)
                
                if c3.button("➖ ENG", key=f"e_{item['Nome']}"):
                    if est_atual >= 24:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                        df_e.to_csv(DB_E, index=False)
                        salvar_log(n_log, f"Venda Eng: {item['Nome']}")
                        st.rerun()
                if c4.button("➖ UN", key=f"u_{item['Nome']}"):
                    if est_atual >= 1:
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                        df_e.to_csv(DB_E, index=False)
                        salvar_log(n_log, f"Venda Un: {item['Nome']}")
                        st.rerun()
            st.markdown("---")

    # =================================================================
    # ABA: PILARES (LÓGICA 3x2 / 2x3 COMPLETA)
    # =================================================================
    elif menu == "🏗️ Pilares (Mapa)":
        st.title("🏗️ Controle de Amarração")
        with st.expander("➕ Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ Novo"] + list(df_pi['Pilar'].unique()))
            n_p = st.text_input("Nome").upper() if p_sel == "+ Novo" else p_sel
            if n_p:
                cam = 1 if df_pi[df_pi['Pilar']==n_p].empty else df_pi[df_pi['Pilar']==n_p]['Camada'].max() + 1
                at, fr = (3, 2) if cam % 2 != 0 else (2, 3)
                st.info(f"Configuração {at}x{fr} (Camada {cam})")
                
                bebs = ["Vazio"] + df_p['Nome'].tolist()
                b_d, a_d = {}, {}
                col_at, col_fr = st.columns(2)
                for i in range(at + fr):
                    target = col_at if (i+1) <= at else col_fr
                    b_d[i+1] = target.selectbox(f"Pos {i+1}", bebs, key=f"b{i+1}{cam}")
                    a_d[i+1] = target.number_input(f"Avulso {i+1}", 0, key=f"a{i+1}{cam}")
                
                if st.button("SALVAR"):
                    novos = [[f"{n_p}_{cam}_{p}", n_p, cam, p, b, a_d[p]] for p, b in b_d.items() if b != "Vazio"]
                    pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB_PI, index=False)
                    st.rerun()

        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            for cam in sorted(df_pi[df_pi['Pilar']==p]['Camada'].unique(), reverse=True):
                st.write(f"Camada {cam}")
                d_c = df_pi[(df_pi['Pilar']==p) & (df_pi['Camada']==cam)]
                cols = st.columns(5)
                for _, r in d_c.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background:#21262D; padding:10px; border-radius:5px;'>{r['Bebida']}<br>+{r['Avulsos']}</div>", unsafe_allow_html=True)
                        if st.button("RETIRAR", key=r['ID']):
                            total = 6 + r['Avulsos'] # Exemplo refri fardo de 6
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total
                            df_e.to_csv(DB_E, index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PI, index=False)
                            st.rerun()

    # =================================================================
    # ABA: ESTOQUE (COM ALERTA DE REPOSIÇÃO)
    # =================================================================
    elif menu == "📦 Estoque & Entradas":
        st.title("📦 Gestão de Estoque")
        if not df_p.empty:
            with st.form("entrada"):
                sel = st.selectbox("Produto", df_p['Nome'].unique())
                c1, c2 = st.columns(2)
                qtd_f = c1.number_input("Fardos/Eng", 0)
                qtd_a = c2.number_input("Avulsos", 0)
                if st.form_submit_button("REGISTRAR ENTRADA"):
                    mult = 24 if df_p[df_p['Nome']==sel]['Categoria'].values[0] == "Romarinho" else 12
                    total = (qtd_f * mult) + qtd_a
                    df_e.loc[df_e['Nome'] == sel, 'Qtd_Unidades'] += total
                    df_e.to_csv(DB_E, index=False)
                    st.rerun()
        
        st.subheader("Situação do Estoque")
        for i, r in df_e.iterrows():
            p_info = df_p[df_p['Nome'] == r['Nome']].iloc[0]
            if r['Qtd_Unidades'] <= p_info['Estoque_Minimo']:
                st.warning(f"⚠️ {r['Nome']}: APENAS {r['Qtd_Unidades']} UNIDADES RESTANTES!")
        st.dataframe(df_e, use_container_width=True)

    # =================================================================
    # ABA: FINANCEIRO (LUCRO REAL)
    # =================================================================
    elif menu == "📊 Financeiro" and is_adm:
        st.title("📊 Relatório de Lucratividade")
        df_fin = pd.merge(df_e, df_p, on='Nome')
        df_fin['Vlr_Custo'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Custo']
        df_fin['Vlr_Venda'] = df_fin['Qtd_Unidades'] * df_fin['Preco_Venda']
        df_fin['Lucro_Estimado'] = df_fin['Vlr_Venda'] - df_fin['Vlr_Custo']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Investido (Custo)", f"R$ {df_fin['Vlr_Custo'].sum():,.2f}")
        c2.metric("Potencial de Venda", f"R$ {df_fin['Vlr_Venda'].sum():,.2f}")
        c3.metric("Lucro Bruto Previsto", f"R$ {df_fin['Lucro_Estimado'].sum():,.2f}")
        
        st.bar_chart(df_fin.set_index('Nome')['Lucro_Estimado'])

    # =================================================================
    # ABA: GESTÃO DE CASCOS
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("cascos"):
            c1, c2, c3, c4 = st.columns(4)
            cli, tip, qtd = c1.text_input("Cliente"), c2.selectbox("Casco", ["Coca 1L", "Litrinho", "Engradado", "600ml"]), c3.number_input("Qtd", 1)
            if c4.form_submit_button("LANÇAR"):
                pd.concat([df_c, pd.DataFrame([[f"C{datetime.now().strftime('%S')}", datetime.now().strftime("%d/%m"), cli, tip, qtd, "DEVE", n_log]], columns=df_c.columns)]).to_csv(DB_C, index=False)
                st.rerun()
        
        for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
            cols = st.columns([6, 2])
            cols[0].error(f"🔴 {r['Cliente']} deve {r['Qtd']}x {r['Tipo']}")
            if cols[1].button("RECEBER", key=r['ID']):
                df_c.at[i, 'Status'] = "PAGO"
                df_c.to_csv(DB_C, index=False)
                st.rerun()

    # =================================================================
    # ABA: CADASTRO (PREÇO DE CUSTO E ESTOQUE MÍNIMO)
    # =================================================================
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Itens")
        with st.form("cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            min_est = c3.number_input("Estoque Mínimo", 24)
            c4, c5 = st.columns(2)
            cus = c4.number_input("Preço de Custo (Un)", 0.0)
            ven = c5.number_input("Preço de Venda (Un)", 0.0)
            if st.form_submit_button("CADASTRAR"):
                pd.concat([df_p, pd.DataFrame([[cat, nom, cus, ven, min_est]], columns=df_p.columns)]).to_csv(DB_P, index=False)
                pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_E, index=False)
                st.rerun()

    # =================================================================
    # ABA: PERFIL (FOTO)
    # =================================================================
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações")
        arq = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png'])
        if st.button("SALVAR FOTO"):
            if arq:
                img = Image.open(arq)
                img.thumbnail((150, 150))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                df_u.loc[df_u['user'] == u_log, 'foto'] = b64
                df_u.to_csv(DB_U, index=False)
                st.success("Foto atualizada!")
                st.rerun()

    elif menu == "📜 Logs":
        st.dataframe(pd.read_csv(DB_L).iloc[::-1])
