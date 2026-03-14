import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V66
# =================================================================
st.set_page_config(
    page_title="Pacaembu Ultra G66", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="stExpander"] { 
        border: 1px solid #30363d; border-radius: 15px; 
        background-color: #161b22; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .stButton>button {
        border-radius: 10px; font-weight: 700; height: 3em;
        transition: all 0.3s ease; border: 1px solid #30363d; background-color: #21262d;
    }
    .stButton>button:hover {
        border-color: #58a6ff; color: #58a6ff; transform: translateY(-2px);
    }
    div[data-testid="stMetric"] {
        background-color: #1c2128; padding: 20px; border-radius: 15px;
        border: 1px solid #30363d; border-left: 6px solid #238636;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E INFRAESTRUTURA
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(DB_USR, index=False)
    
    arquivos = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_EST: ['Nome', 'Estoque_Total_Un'],
        DB_PIL: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)

init_db()

def registrar_log(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user, acao]], 
                 columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)

def get_config_bebida(nome, df_p):
    busca = df_p[df_p['Nome'] == nome]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. SEGURANÇA E CONTROLE DE SESSÃO
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 PACAEMBU ULTRA</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in, s_in = st.text_input("👤 Usuário"), st.text_input("🔑 Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DB_USR)
                valid = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not valid.empty:
                    st.session_state.update({
                        'autenticado': True, 'u_l': u_in, 
                        'u_n': valid['nome'].values[0], 
                        'u_a': (valid['is_admin'].values[0] == 'SIM')
                    })
                    registrar_log(st.session_state['u_n'], "Login")
                    st.rerun()
                else: st.error("Erro de acesso.")
else:
    # Carregamento Seguro
    u_logado = st.session_state.get('u_l', 'admin')
    n_logado = st.session_state.get('u_n', 'Usuário')
    is_adm = st.session_state.get('u_a', False)

    df_p, df_e, df_pil = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_cas, df_usr = pd.read_csv(DB_CAS), pd.read_csv(DB_USR)

    # --- SIDEBAR ---
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty:
        raw = user_row['foto'].values[0]
        if not pd.isna(raw) and raw != "": f_path = f"data:image/png;base64,{raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='100' style='border-radius: 50%; border: 3px solid #238636;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("MENU", 
        ["🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Perfil"] + 
        (["📊 Admin", "📜 Logs", "👥 Equipe"] if is_adm else []))

    if st.sidebar.button("🚪 SAIR"):
        st.session_state['autenticado'] = False; st.rerun()

    # --- 🍻 PDV ROMARINHO ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido - Romarinhos")
        df_roms = df_p[df_p['Categoria'] == "Romarinho"]
        for _, item in df_roms.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 4])
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                c1.markdown(f"#### {item['Nome']}")
                c2.metric("Estoque", f"{est_u//24} Eng | {est_u%24} un")
                b_eng, b_uni = c3.columns(2)
                if b_eng.button("➖ ENGRADADO", key=f"e_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Eng {item['Nome']}"); st.rerun()
                if b_uni.button("➖ UNIDADE", key=f"u_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Un {item['Nome']}"); st.rerun()

    # --- 🏗️ PILARES (AMARRAÇÃO 3x2/2x3 + FILTRO) ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🆕 MONTAR NOVA CAMADA"):
            p_alvo = st.selectbox("Pilar", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_filtro = st.selectbox("Filtrar por Categoria", df_p['Categoria'].unique())
            
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                st.warning(f"Camada {c_atual}: Amarração automática ({at} atrás / {fr} frente)")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                col_at, col_fr = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1
                    target = col_at if pos <= at else col_fr
                    beb_dict[pos] = target.selectbox(f"Posição {pos}", lista_beb, key=f"p_{pos}")
                    av_dict[pos] = target.number_input(f"Avulsos {pos}", 0, key=f"a_{pos}")
                
                if st.button("CONFIRMAR MONTAGEM"):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()

        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            for cam in sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True):
                st.markdown(f"**Camada {cam}**")
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                cols = st.columns(5)
                for _, r in dados_cam.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1c2128; padding:5px; border-radius:5px; border:1px solid #30363d; text-align:center;'>{r['Bebida']}<br>+{r['Avulsos']}</div>", unsafe_allow_html=True)
                        if st.button("SAÍDA", key=f"out_{r['ID']}"):
                            u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            registrar_log(n_logado, f"Saída Pilar {pilar}"); st.rerun()

    # --- 🍶 CONTROLE DE CASCOS (ESTORNO INTEGRADO) ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Devedores e Vasilhames")
        with st.form("f_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cl, f_te = c1.text_input("Cliente").upper(), c2.text_input("WhatsApp")
            f_ti = c3.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml", "Litrinho"])
            f_qt = c4.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR DÉBITO"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), f_cl, f_te, f_ti, f_qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()

        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            c1, c2 = st.columns([8, 2])
            c1.error(f"🔴 {r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
            if c2.button("RECEBER", key=f"bx_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                df_cas.to_csv(DB_CAS, index=False); registrar_log(n_logado, f"Recebeu Casco {r['Cliente']}"); st.rerun()

        with st.expander("🟢 Histórico / Estorno"):
            for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(5).iterrows():
                c1, c2 = st.columns([8, 2])
                c1.success(f"{r['Cliente']} entregou {r['Vasilhame']}")
                if c2.button("ESTORNAR", key=f"st_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- 📦 ESTOQUE GERAL ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Inventário Real")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        if not df_p.empty:
            sel = st.selectbox("Produto para Entrada", df_p['Nome'].unique())
            u_b, t_t = get_config_bebida(sel, df_p)
            with st.form("f_ent"):
                c1, c2 = st.columns(2)
                f_f, f_a = c1.number_input(f"{t_t}s", 0), c2.number_input("Avulsos", 0)
                if st.form_submit_button("DAR ENTRADA"):
                    df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (f_f * u_b) + f_a
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Entrada {sel}"); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Novo Produto")
        with st.form("f_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Outros"])
            fn, fp = c2.text_input("Nome").upper(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("SALVAR"):
                if fn and fn not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Seu Perfil")
        upload = st.file_uploader("Trocar Foto", type=['png', 'jpg'])
        if st.button("ATUALIZAR FOTO") and upload:
            img = Image.open(upload); img.thumbnail((200, 200))
            buf = io.BytesIO(); img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64
            df_usr.to_csv(DB_USR, index=False); st.rerun()

    # --- 📊 ADMIN / DASHBOARD ---
    elif menu == "📊 Admin" and is_adm:
        st.title("📊 Patrimônio")
        df_f = pd.merge(df_e, df_p, on='Nome')
        df_f['Total'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("VALOR TOTAL EM ESTOQUE", f"R$ {df_f['Total'].sum():,.2f}")
        st.bar_chart(df_f.set_index('Nome')['Estoque_Total_Un'])
