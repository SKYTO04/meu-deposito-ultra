import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN E CONFIGURAÇÃO PREMIUM
# =================================================================
st.set_page_config(
    page_title="Pacaembu Gestão v65", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para aparência Dark Luxo
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    div[data-testid="stExpander"] { border: 1px solid #1f2937; border-radius: 12px; background-color: #161b22; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    div[data-testid="stMetric"] { background-color: #1f2937; padding: 15px; border-radius: 15px; border-left: 5px solid #3b82f6; }
    h1, h2, h3 { color: #f9fafb; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS
# =================================================================
DB_PRODUTOS, DB_ESTOQUE, PILAR_ESTRUTURA = "produtos_v65.csv", "estoque_v65.csv", "pilares_v65.csv"
USERS_FILE, LOG_FILE, CASCOS_FILE = "usuarios_v65.csv", "historico_v65.csv", "cascos_v65.csv"

def init_db():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
    tabelas = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, cols in tabelas.items():
        if not os.path.exists(arq): pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def log_master(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user, acao]], 
                 columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# =================================================================
# 3. LÓGICA DE LOGIN (CORREÇÃO DE SEGURANÇA)
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>💎 Depósito Pacaembu</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("login_moderno"):
            u_in = st.text_input("👤 Usuário")
            s_in = st.text_input("🔑 Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(USERS_FILE)
                v = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not v.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': v['nome'].values[0], 'u_a': (v['is_admin'].values[0] == 'SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    u_logado = st.session_state.get('u_l')
    n_logado = st.session_state.get('u_n')
    is_adm = st.session_state.get('u_a')

    # Bairros de dados
    df_p, df_e = pd.read_csv(DB_PRODUTOS), pd.read_csv(DB_ESTOQUE)
    df_pil, df_cas, df_usr = pd.read_csv(PILAR_ESTRUTURA), pd.read_csv(CASCOS_FILE), pd.read_csv(USERS_FILE)

    # --- SIDEBAR (CORREÇÃO DO INDEXERROR) ---
    st.sidebar.markdown("<h2 style='text-align: center;'>💎 PACAEMBU</h2>", unsafe_allow_html=True)
    
    # Busca segura da foto
    user_data = df_usr[df_usr['user'] == u_logado]
    foto_html = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    
    if not user_data.empty:
        foto_raw = user_data['foto'].values[0]
        if not pd.isna(foto_raw) and foto_raw != "":
            foto_html = f"data:image/png;base64,{foto_raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{foto_html}' width='110' style='border-radius: 50%; border: 3px solid #3b82f6; aspect-ratio: 1/1; object-fit: cover;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; margin-top: 10px;'>Olá, <b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("MENU", ["🍻 PDV Romarinho", "🏗️ Pilares", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"] + (["📊 Dashboards", "📜 Logs", "👥 Equipe"] if is_adm else []))
    
    if st.sidebar.button("🚪 SAIR", use_container_width=True):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: ROMARINHO (ESTILO PDV) ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda - Romarinhos")
        df_rom = df_p[df_p['Categoria'] == "Romarinho"]
        cols = st.columns(2)
        for i, item in df_rom.iterrows():
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"### 🏷️ {item['Nome']}")
                    qtd = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                    c1, c2 = st.columns(2)
                    c1.metric("Engradados (24)", qtd // 24)
                    c2.metric("Unidades", qtd % 24)
                    b1, b2 = st.columns(2)
                    if b1.button(f"BAIXAR ENG", key=f"e_{item['Nome']}", use_container_width=True):
                        if qtd >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            log_master(n_logado, f"Venda Engradado: {item['Nome']}")
                            st.rerun()
                    if b2.button(f"BAIXAR UN", key=f"u_{item['Nome']}", use_container_width=True):
                        if qtd >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            log_master(n_logado, f"Venda Unidade: {item['Nome']}")
                            st.rerun()
                st.write("---")

    # --- ABA: PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Mapa de Pilares")
        with st.expander("➕ Adicionar Camada"):
            p_lista = ["+ Novo"] + list(df_pil['NomePilar'].unique())
            p_sel = st.selectbox("Pilar", p_lista)
            n_p = st.text_input("Nome").upper() if p_sel == "+ Novo" else p_sel
            if n_p:
                c_n = 1 if df_pil[df_pil['NomePilar']==n_p].empty else df_pil[df_pil['NomePilar']==n_p]['Camada'].max()+1
                at, fr = (3, 2) if c_n % 2 != 0 else (2, 3)
                st.write(f"Configuração: {at} atrás / {fr} frente")
                beb_list = ["Vazio"] + df_p[df_p['Categoria'] == "Refrigerante"]['Nome'].tolist()
                b_d, a_d = {}, {}
                c1, c2 = st.columns(2)
                for i in range(at+fr):
                    col = c1 if (i+1) <= at else c2
                    b_d[i+1] = col.selectbox(f"Pos {i+1}", beb_list, key=f"b_{i+1}_{c_n}")
                    a_d[i+1] = col.number_input(f"Av {i+1}", 0, key=f"a_{i+1}_{c_n}")
                if st.button("SALVAR"):
                    novos = [[f"{n_p}_{c_n}_{p}_{datetime.now().strftime('%S')}", n_p, c_n, p, b, a_d[p]] for p, b in b_d.items() if b != "Vazio"]
                    if novos:
                        pd.concat([df_pil, pd.DataFrame(novos, columns=df_pil.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        for pn in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 {pn}")
            for c in sorted(df_pil[df_pil['NomePilar'] == pn]['Camada'].unique(), reverse=True):
                st.markdown(f"**Camada {c}**")
                dados = df_pil[(df_pil['NomePilar'] == pn) & (df_pil['Camada'] == c)]
                v_cols = st.columns(5)
                for _, r in dados.iterrows():
                    with v_cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1e293b; padding:5px; border-radius:5px; text-align:center;'><b>{r['Bebida']}</b><br>+{r['Avulsos']}un</div>", unsafe_allow_html=True)
                        if st.button("SAÍDA", key=f"rt_{r['ID']}", use_container_width=True):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (6 + r['Avulsos'])
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                            st.rerun()

    # --- ABA: PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        arq = st.file_uploader("Trocar foto de perfil", type=['png', 'jpg', 'jpeg'])
        if st.button("SALVAR FOTO"):
            if arq:
                img = Image.open(arq)
                img.thumbnail((180, 180))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64
                df_usr.to_csv(USERS_FILE, index=False)
                st.success("Foto atualizada!")
                st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        with st.form("casco_f"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            fcl, fte, fti, fqt = c1.text_input("Cliente").upper(), c2.text_input("Tel"), c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("REGISTRAR"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), fcl, fte, fti, fqt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            l1, l2 = st.columns([7, 2])
            l1.error(f"👤 {r['Cliente']} | {r['Quantidade']}x {r['Vasilhame']}")
            if l2.button("BAIXAR", key=f"p_{r['ID']}", use_container_width=True):
                df_cas.at[i, 'Status'] = "PAGO"
                df_cas.at[i, 'QuemBaixou'] = n_logado
                df_cas.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # --- ABA: ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Entrada")
        if not df_p.empty:
            sel = st.selectbox("Produto", df_p['Nome'].unique())
            with st.form("ent_f"):
                ce1, ce2 = st.columns(2)
                f_f, f_a = ce1.number_input("Qtd Fardos/Eng", 0), ce2.number_input("Avulsos", 0)
                if st.form_submit_button("LANÇAR"):
                    mult = 24 if df_p[df_p['Nome']==sel]['Categoria'].values[0] == "Romarinho" else 12
                    df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (f_f * mult) + f_a
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Produtos")
        with st.form("cad_f"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc, fn, fp = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"]), c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("CADASTRAR") and fn != "" and fn not in df_p['Nome'].values:
                pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                st.rerun()
        for i, r in df_p.iterrows():
            col1, col2 = st.columns([9, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']})")
            if col2.button("🗑️", key=f"d_{r['Nome']}"):
                df_p[df_p['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ADMIN ---
    elif menu == "📊 Dashboards" and is_adm:
        df_f = pd.merge(df_e, df_p, on='Nome')
        st.metric("PATRIMÔNIO TOTAL", f"R$ {(df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']).sum():,.2f}")
        st.bar_chart(df_f.set_index('Nome')['Estoque_Total_Un'])

    elif menu == "📜 Logs" and is_adm:
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "👥 Equipe" and is_adm:
        with st.form("eq_f"):
            c1, c2, c3, c4, c5 = st.columns(5)
            nu, nn, ns, nt, na = c1.text_input("Login"), c2.text_input("Nome"), c3.text_input("Senha"), c4.text_input("Tel"), c5.selectbox("Adm?", ["NÃO", "SIM"])
            if st.form_submit_button("ADD"):
                pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_usr.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_usr[['user', 'nome', 'is_admin']])
