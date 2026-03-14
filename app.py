import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V66 (TOTAL)
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
# 2. INFRAESTRUTURA DE DADOS
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
# 3. SEGURANÇA E LOGIN (BLINDADO)
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 PACAEMBU ULTRA</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in = st.text_input("👤 Usuário")
            s_in = st.text_input("🔑 Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
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
                else: st.error("Acesso negado.")
else:
    # Acesso seguro às variáveis
    u_logado = st.session_state.get('u_l')
    n_logado = st.session_state.get('u_n')
    is_adm = st.session_state.get('u_a')

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
    
    menu = st.sidebar.radio("NAVEGAÇÃO", 
        ["🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Perfil"] + 
        (["📊 Admin", "📜 Logs do Sistema", "👥 Equipe"] if is_adm else []))

    if st.sidebar.button("🚪 SAIR"):
        st.session_state['autenticado'] = False; st.rerun()

    # --- ABA: PDV ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Venda Rápida")
        df_roms = df_p[df_p['Categoria'] == "Romarinho"]
        for _, item in df_roms.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 4])
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                c1.markdown(f"#### {item['Nome']}")
                c2.metric("Saldo", f"{est_u//24} Eng")
                b1, b2 = c3.columns(2)
                if b1.button(f"➖ ENG", key=f"e_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Saiu Eng {item['Nome']}"); st.rerun()
                if b2.button(f"➖ UN", key=f"u_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Saiu Un {item['Nome']}"); st.rerun()

    # --- ABA: PILARES ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Controle de Pilares")
        with st.expander("🆕 NOVA CAMADA"):
            p_alvo = st.selectbox("Pilar", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_f = st.selectbox("Categoria", df_p['Categoria'].unique())
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_f]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                c_at, c_fr = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1; target = c_at if pos <= at else c_fr
                    beb_dict[pos] = target.selectbox(f"Pos {pos}", lista_beb, key=f"p_{pos}")
                    av_dict[pos] = target.number_input(f"Avul {pos}", 0, key=f"a_{pos}")
                if st.button("MONTAR"):
                    regs = [[f"{n_pilar}_{c_atual}_{p}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()

        for pilar in df_pil['NomePilar'].unique():
            st.subheader(f"Pilar {pilar}")
            for cam in sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True):
                dados = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                cols = st.columns(5)
                for _, r in dados.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.write(f"**{r['Bebida']}**")
                        if st.button("RETIRAR", key=f"r_{r['ID']}"):
                            u_p, _ = get_config_bebida(r['Bebida'], df_p)
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            registrar_log(n_logado, f"Retirada Pilar {pilar}"); st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Devedores")
        with st.form("f_c"):
            c1, c2, c3 = st.columns([3, 3, 1])
            cl, va, qt = c1.text_input("Cliente").upper(), c2.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Romarinho", "600ml"]), c3.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            col1, col2 = st.columns([8, 2])
            col1.error(f"🔴 {r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
            if col2.button("RECEBER", key=f"bx_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                df_cas.to_csv(DB_CAS, index=False); registrar_log(n_logado, f"Recebeu de {r['Cliente']}"); st.rerun()

    # --- ABA: LOGS ---
    elif menu == "📜 Logs do Sistema":
        st.title("📜 Histórico Geral")
        st.dataframe(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False), use_container_width=True)

    # --- ABA: EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Time Pacaembu")
        with st.expander("➕ NOVO MEMBRO"):
            with st.form("f_e"):
                u, n, s, a = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Adm", ["NÃO", "SIM"])
                if st.form_submit_button("CADASTRAR"):
                    pd.concat([df_usr, pd.DataFrame([[u, n, s, a, "", ""]], columns=df_usr.columns)]).to_csv(DB_USR, index=False); st.rerun()
        for i, r in df_usr.iterrows():
            st.write(f"**{r['nome']}** | Nível: {r['is_admin']}")

    # --- ABA: ESTOQUE ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Inventário")
        st.dataframe(df_e, use_container_width=True)
        sel = st.selectbox("Produto", df_p['Nome'].unique())
        u_b, t_t = get_config_bebida(sel, df_p)
        f_f = st.number_input(f"Qtd {t_t}", 0)
        if st.button("ENTRADA"):
            df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (f_f * u_b)
            df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Entrada {sel}"); st.rerun()

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        with st.form("f_cad"):
            fc, fn, fp = st.selectbox("Cat", ["Romarinho", "Refrigerante", "Outros"]), st.text_input("Nome").upper(), st.number_input("Preço", 0.0)
            if st.form_submit_button("SALVAR"):
                pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- ABA: PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        upload = st.file_uploader("Foto", type=['png', 'jpg'])
        if st.button("SALVAR") and upload:
            img = Image.open(upload); img.thumbnail((200, 200))
            buf = io.BytesIO(); img.save(buf, format="PNG")
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(buf.getvalue()).decode()
            df_usr.to_csv(DB_USR, index=False); st.rerun()
