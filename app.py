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
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': valid['nome'].values[0], 'u_a': (valid['is_admin'].values[0] == 'SIM')})
                    registrar_log(st.session_state['u_n'], "Login")
                    st.rerun()
                else: st.error("Erro de acesso.")
else:
    u_logado, n_logado, is_adm = st.session_state.get('u_l'), st.session_state.get('u_n'), st.session_state.get('u_a')
    df_p, df_e, df_pil = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_cas, df_usr = pd.read_csv(DB_CAS), pd.read_csv(DB_USR)

    # --- SIDEBAR ---
    menu = st.sidebar.radio("MENU", ["🍻 PDV", "🏗️ Pilares", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- ABA: ADMIN FINANCEIRO ---
    if menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Painel de Patrimônio")
        df_inv = pd.merge(df_e, df_p, on='Nome')
        df_inv['Subtotal'] = df_inv['Estoque_Total_Un'] * df_inv['Preco_Unitario']
        st.metric("VALOR TOTAL EM ESTOQUE", f"R$ {df_inv['Subtotal'].sum():,.2f}")
        st.dataframe(df_inv[['Nome', 'Categoria', 'Estoque_Total_Un', 'Subtotal']], use_container_width=True, hide_index=True)

    # --- ABA: ESTOQUE (COM ENTRADA E SAÍDA MANUAL) ---
    elif menu == "📦 Estoque":
        st.title("📦 Gestão de Estoque")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        
        with st.expander("⚙️ AJUSTE MANUAL (ENTRADA / SAÍDA)"):
            sel_e = st.selectbox("Produto", df_p['Nome'].unique())
            u_b, t_t = get_config_bebida(sel_e, df_p)
            col_m1, col_m2, col_m3 = st.columns(3)
            tipo = col_m1.radio("Operação", ["➕ ENTRADA", "➖ SAÍDA"])
            qtd_f = col_m2.number_input(f"Qtd {t_t}s", 0)
            qtd_u = col_m3.number_input("Qtd Unidades", 0)
            
            if st.button("CONFIRMAR AJUSTE"):
                total_un = (qtd_f * u_b) + qtd_u
                if "SAÍDA" in tipo:
                    df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] -= total_un
                    registrar_log(n_logado, f"Saída Manual: {sel_e} (-{total_un} un)")
                else:
                    df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] += total_un
                    registrar_log(n_logado, f"Entrada Manual: {sel_e} (+{total_un} un)")
                df_e.to_csv(DB_EST, index=False); st.success("Ajustado!"); st.rerun()

    # --- ABA: CADASTRO (COM REMOVER) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Produtos")
        with st.form("cad_prod"):
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Cat", ["Romarinho", "Refrigerante", "Cerveja Lata", "Outros"])
            nom, pre = c2.text_input("Nome").upper(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("SALVAR NOVO PRODUTO"):
                if nom and nom not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[cat, nom, pre]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[nom, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()
        
        st.divider()
        st.subheader("🗑️ Remover Produto do Sistema")
        rem = st.selectbox("Escolha para excluir", df_p['Nome'].unique())
        if st.button("❌ EXCLUIR DEFINITIVAMENTE"):
            df_p[df_p['Nome'] != rem].to_csv(DB_PROD, index=False)
            df_e[df_e['Nome'] != rem].to_csv(DB_EST, index=False)
            registrar_log(n_logado, f"Removeu produto {rem}"); st.rerun()

    # --- ABA: PDV ---
    elif menu == "🍻 PDV":
        st.title("🍻 Venda Rápida")
        for _, r in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            c1, c2, c3 = st.columns([4, 2, 4])
            c1.markdown(f"### {r['Nome']}")
            saldo = int(df_e[df_e['Nome'] == r['Nome']]['Estoque_Total_Un'].values[0])
            c2.metric("Saldo", f"{saldo//24} Eng")
            b1, b2 = c3.columns(2)
            if b1.button("➖ ENG", key=f"e{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 24
                df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Eng {r['Nome']}"); st.rerun()
            if b2.button("➖ UN", key=f"u{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 1
                df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Un {r['Nome']}"); st.rerun()

    # --- ABA: PILARES (AMARRAÇÃO 3x2/2x3) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Controle de Pilares")
        with st.expander("🆕 MONTAR CAMADA"):
            p_alvo = st.selectbox("Pilar", ["Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome").upper() if p_alvo == "Novo" else p_alvo
            if n_pilar:
                cam = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if cam % 2 != 0 else (2, 3)
                st.info(f"Camada {cam}: Lógica {at}x{fr}")
                regs = []
                for i in range(at+fr):
                    p = i+1
                    beb = st.selectbox(f"Posição {p}", ["Vazio"]+df_p['Nome'].tolist(), key=f"pos{p}")
                    if beb != "Vazio": regs.append([f"{n_pilar}_{cam}_{p}", n_pilar, cam, p, beb, 0])
                if st.button("SALVAR"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()

        for pil in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 {pil}")
            dados_p = df_pil[df_pil['NomePilar'] == pil]
            for c in sorted(dados_p['Camada'].unique(), reverse=True):
                cols = st.columns(5)
                for _, r in dados_p[dados_p['Camada'] == c].iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.write(r['Bebida'])
                        if st.button("BAIXA", key=r['ID']):
                            u_p, _ = get_config_bebida(r['Bebida'], df_p)
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= u_p
                            df_e.to_csv(DB_EST, index=False); df_pil[df_pil['ID']!=r['ID']].to_csv(DB_PIL, index=False); st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        with st.form("cas_form"):
            cl, va, qt = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho"]), st.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR DEVEDOR"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
        for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
            st.error(f"{r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
            if st.button("DAR BAIXA", key=r['ID']):
                df_cas.at[i, 'Status'] = "PAGO"; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- ABAS ADMIN (LOGS/EQUIPE) ---
    elif menu == "📜 Logs":
        st.title("📜 Logs")
        st.dataframe(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False), use_container_width=True)

    elif menu == "👥 Equipe":
        st.title("👥 Time")
        with st.form("add_equipe"):
            u, n, s, a = st.text_input("User"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Adm", ["NÃO", "SIM"])
            if st.form_submit_button("ADICIONAR"):
                pd.concat([df_usr, pd.DataFrame([[u, n, s, a, "0", ""]], columns=df_usr.columns)]).to_csv(DB_USR, index=False); st.rerun()
        st.dataframe(df_usr[['nome', 'user', 'is_admin']])
