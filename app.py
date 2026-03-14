import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import zipfile

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V66 (TOTAL)
# =================================================================
st.set_page_config(
    page_title="Adega Pacaembu", 
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
    [data-testid="stForm"] {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"
TODOS_DBS = [DB_PROD, DB_EST, DB_PIL, DB_USR, DB_LOG, DB_CAS]

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

def gerar_backup_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in TODOS_DBS:
            if os.path.exists(f):
                z.write(f)
    return buf.getvalue()

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
        if cat in ["Alimentos", "Limpeza"]: return 1, "Unidade"
    return 12, "Fardo"

# =================================================================
# 3. SEGURANÇA E LOGIN
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff; margin-top: 50px;'>🍺 ADEGA PACAEMBU </h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in = st.text_input("👤 Usuário").strip()
            s_in = st.text_input("🔑 Senha", type="password").strip()
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
                else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    
    df_p = pd.read_csv(DB_PROD)
    df_e = pd.read_csv(DB_EST)
    df_pil = pd.read_csv(DB_PIL)
    df_cas = pd.read_csv(DB_CAS)
    df_usr = pd.read_csv(DB_USR)

    # --- SIDEBAR ---
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty:
        raw = user_row['foto'].values[0]
        if not pd.isna(raw) and raw != "": f_path = f"data:image/png;base64,{raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='100' style='border-radius: 50%; border: 3px solid #238636; margin-bottom: 10px; object-fit: cover; height: 100px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 1.2em;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🏠 Dashboard", "🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    
    if st.sidebar.button("🚪 SAIR"):
        st.session_state['autenticado'] = False; st.rerun()

    # --- 🏗️ PILARES (DINÂMICOS POR NOME E CRESCENTES) ---
    if menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Engenharia de Pilares")
        
        with st.expander("🏗️ MONTAR / EMPILHAR CAMADA", expanded=True):
            pilares_existentes = sorted(df_pil['NomePilar'].unique().tolist())
            
            # Seleção ou Criação de Pilar
            col_sel1, col_sel2 = st.columns([1, 1])
            p_opcao = col_sel1.selectbox("Escolha um pilar existente", ["NOVO PILAR..."] + pilares_existentes)
            
            if p_opcao == "NOVO PILAR...":
                n_pilar = col_sel2.text_input("Digite o nome do NOVO pilar (Ex: FANTA)").upper().strip()
            else:
                n_pilar = p_opcao
                col_sel2.info(f"Adicionando ao pilar: **{n_pilar}**")

            st.divider()
            
            if n_pilar:
                cat_filtro = st.selectbox("Categoria da Bebida", df_p['Categoria'].unique())
                
                # Cálculo de camada: Começa na 1, se já existe, pega a próxima.
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                
                st.subheader(f"{'🧱 BASE' if c_atual == 1 else '📦 Camada '+str(c_atual)} (Padrão {at}x{fr})")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                
                cols_grid = st.columns(5)
                for i in range(at + fr):
                    pos = i + 1
                    with cols_grid[i]:
                        st.markdown(f"**Pos {pos}**")
                        beb_dict[pos] = st.selectbox(f"Ref", lista_beb, key=f"p_{pos}", label_visibility="collapsed")
                        av_dict[pos] = st.number_input(f"Unid", 0, key=f"a_{pos}")
                
                if st.button(f"CONSOLIDAR CAMADA {c_atual} NO PILAR {n_pilar}", use_container_width=True):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().microsecond}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        registrar_log(n_logado, f"Nova camada no pilar {n_pilar}")
                        st.success(f"Camada {c_atual} empilhada!")
                        st.rerun()

        # EXIBIÇÃO DOS PILARES (REVERSA: TOPO EM CIMA)
        st.markdown("---")
        for pilar in sorted(df_pil['NomePilar'].unique()):
            with st.container():
                st.markdown(f"### 📍 Pilar: {pilar}")
                # reverse=True faz o maior número (topo) aparecer primeiro visualmente
                camadas = sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
                
                for cam in camadas:
                    dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                    cor_b = "#58a6ff" if cam == max(camadas) else "#30363d"
                    tag = "🔝 TOPO" if cam == max(camadas) else ("🧱 BASE" if cam == 1 else f"📦 Camada {cam}")
                    
                    st.markdown(f"<small style='color:{cor_b}; font-weight:bold;'>{tag}</small>", unsafe_allow_html=True)
                    cols_view = st.columns(5)
                    
                    for _, r in dados_cam.iterrows():
                        u_p, _ = get_config_bebida(r['Bebida'], df_p)
                        with cols_view[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1c2128; padding:5px; border-radius:8px; border:1px solid {cor_b}; text-align:center; min-height:60px;"><b style="font-size:0.75em;">{r["Bebida"]}</b><br><span style="color:#238636; font-size:0.7em;">+{r["Avulsos"]}</span></div>', unsafe_allow_html=True)
                            if st.button("SAÍDA", key=f"bx_{r['ID']}", use_container_width=True):
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                                df_e.to_csv(DB_EST, index=False)
                                df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                                registrar_log(n_logado, f"Baixa {pilar}: {r['Bebida']}"); st.rerun()
                    
                    if cam > 1: st.markdown("<div style='text-align:center; color:#30363d; margin-top:-10px; margin-bottom:10px;'>▼ sobreposta ▼</div>", unsafe_allow_html=True)
                
                if is_adm:
                    if st.button(f"🗑️ DESMONTAR PILAR {pilar}", key=f"del_{pilar}"):
                        df_pil[df_pil['NomePilar'] != pilar].to_csv(DB_PIL, index=False)
                        st.rerun()
            st.divider()

    # --- ABA DASHBOARD ---
    elif menu == "🏠 Dashboard":
        st.title("🚀 Central de Comando")
        m1, m2, m3 = st.columns(3)
        m1.metric("Pendências Cascos", f"{len(df_cas[df_cas['Status'] == 'DEVE'])}")
        m2.metric("Itens no Catálogo", f"{len(df_p)}")
        m3.metric("Pilares Ativos", f"{len(df_pil['NomePilar'].unique())}")
        st.markdown("---")
        st.subheader("📊 Movimentações Recentes")
        st.table(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False).head(5))

    # --- ABA PDV ---
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido - Romarinho")
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            c1, c2, c3 = st.columns([3, 3, 4])
            u_b, t_t = get_config_bebida(item['Nome'], df_p)
            c1.markdown(f"#### {item['Nome']}")
            if c3.button(f"➖ VENDER {t_t.upper()}", key=f"v_{item['Nome']}"):
                df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= u_b
                df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda {item['Nome']}"); st.rerun()

    # --- ESTOQUE GERAL ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Inventário")
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # --- CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Catálogo")
        with st.form("f_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Alimentos", "Limpeza", "Outros"])
            fn, fp = c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("CADASTRAR"):
                if fn and fn not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- CASCOS ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("f_cas"):
            cl, va, qt = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml"]), st.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            st.error(f"🔴 {r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
            if st.button("DAR BAIXA ✅", key=f"bx_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        st.info(f"**Nome:** {n_logado}\n\n**Usuário:** {u_logado}")

    # --- ADMIN ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Gestão Patrimonial")
        backup_zip = gerar_backup_zip()
        st.download_button(label="📥 BAIXAR BACKUP COMPLETO", data=backup_zip, file_name=f"backup_adega.zip", mime="application/zip")

    elif menu == "📜 Logs" and is_adm:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False), use_container_width=True)

    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Equipe")
        st.dataframe(df_usr[['user', 'nome', 'is_admin']], use_container_width=True)
