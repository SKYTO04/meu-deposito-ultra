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
# 2. INFRAESTRUTURA DE DADOS E BACKUP
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

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Central de Comando")
        m1, m2, m3, m4 = st.columns(4)
        total_devedores = len(df_cas[df_cas['Status'] == "DEVE"])
        total_itens = len(df_p)
        baixo_estoque = len(df_e[df_e['Estoque_Total_Un'] < 50])
        total_pilares = len(df_pil['NomePilar'].unique())
        
        m1.metric("Pendências Cascos", f"{total_devedores} Clientes")
        m2.metric("Itens no Catálogo", f"{total_itens} Produtos")
        m3.metric("Pilares Ativos", f"{total_pilares} Estruturas")
        m4.metric("Baixo Estoque", f"{baixo_estoque} Alertas")

        st.markdown("---")
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("📊 Movimentações Recentes")
            df_log_view = pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False).head(8)
            st.table(df_log_view[['Data', 'Usuario', 'Ação']])
        with col_right:
            st.subheader("🔔 Alertas de Estoque")
            critico = df_e[df_e['Estoque_Total_Un'] < 24].head(5)
            if not critico.empty:
                for _, r in critico.iterrows(): st.warning(f"**{r['Nome']}**: {r['Estoque_Total_Un']} un.")
            else: st.success("Estoque em níveis saudáveis.")

    # --- 🍻 PDV ROMARINHO ---
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido - Romarinho")
        df_pdv = df_p[df_p['Categoria'] == "Romarinho"]
        if df_pdv.empty:
            st.info("Nenhum produto da categoria 'Romarinho' cadastrado.")
        else:
            for _, item in df_pdv.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([3, 3, 4])
                    est_u_busca = df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values
                    est_u = int(est_u_busca[0]) if len(est_u_busca) > 0 else 0
                    u_b, t_t = get_config_bebida(item['Nome'], df_p)
                    c1.markdown(f"#### {item['Nome']}")
                    c2.metric("Saldo", f"{est_u//u_b} {t_t} | {est_u%u_b} un")
                    b1, b2 = c3.columns(2)
                    if b1.button(f"➖ {t_t.upper()}", key=f"e_{item['Nome']}"):
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= u_b
                        df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda {t_t} {item['Nome']}"); st.rerun()
                    if b2.button("➖ UNID.", key=f"u_{item['Nome']}"):
                        df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                        df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda Unid {item['Nome']}"); st.rerun()

    # --- 🏗️ PILARES (VERSÃO PILHA VERTICAL) ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Engenharia de Pilares")
        
        with st.expander("➕ MONTAR NOVA CAMADA (ESTRUTURA AMARRADA)"):
            p_alvo = st.selectbox("Pilar Destino", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Identificação do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_filtro = st.selectbox("Filtrar Categoria para Montagem", df_p['Categoria'].unique())
            
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                
                if c_atual == 1: st.success(f"🌟 Iniciando BASE do Pilar: **{n_pilar}**")
                else: st.info(f"⬆️ Montando sobre a Camada {c_atual-1}")
                st.warning(f"📐 Padrão desta Camada: **{at}x{fr}**")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                
                cols_grid = st.columns(max(at, fr))
                for i in range(at + fr):
                    pos = i + 1
                    with cols_grid[i % len(cols_grid)]:
                        st.markdown(f"**Posição {pos}**")
                        beb_dict[pos] = st.selectbox(f"Bebida", lista_beb, key=f"p_{pos}", label_visibility="collapsed")
                        av_dict[pos] = st.number_input(f"Avulsos", 0, key=f"a_{pos}")
                
                if st.button("FINALIZAR CAMADA E EMPILHAR", use_container_width=True):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        registrar_log(n_logado, f"Empilhou Camada {c_atual} no Pilar {n_pilar}")
                        st.rerun()

        st.markdown("---")
        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            # MOSTRA DO TOPO PARA A BASE (Invertido para simular pilha real)
            camadas = sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
            
            for cam in camadas:
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                total_un_cam = 0
                
                with st.container():
                    cor_b = "#58a6ff" if cam == max(camadas) else "#30363d"
                    tag = "🔝 TOPO" if cam == max(camadas) else ("🧱 BASE" if cam == 1 else f"📦 Camada {cam}")
                    st.markdown(f"<small style='color:{cor_b}; font-weight:bold;'>{tag}</small>", unsafe_allow_html=True)
                    
                    cols = st.columns(5)
                    for _, r in dados_cam.iterrows():
                        u_p, _ = get_config_bebida(r['Bebida'], df_p)
                        total_un_cam += (u_p + r['Avulsos'])
                        with cols[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1c2128; padding:8px; border-radius:10px; border:2px solid {cor_b}; text-align:center; margin-bottom:5px;"><b style="font-size:0.8em; color:#e6edf3;">{r["Bebida"]}</b><br><span style="color:#238636; font-size:0.75em;">+{r["Avulsos"]} UN</span></div>', unsafe_allow_html=True)
                            if st.button("BAIXA", key=f"out_{r['ID']}", use_container_width=True):
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                                df_e.to_csv(DB_EST, index=False)
                                df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                                registrar_log(n_logado, f"Saída Pilar {pilar}: {r['Bebida']}"); st.rerun()
                    st.markdown(f"<p style='text-align:right; color:#8b949e; font-size:0.75em; margin-top:-5px;'>Subtotal: {total_un_cam} un</p>", unsafe_allow_html=True)
                    if cam > 1: st.markdown("<div style='text-align:center; color:#30363d; margin-top:-10px; margin-bottom:10px;'>▼ apoiado sobre ▼</div>", unsafe_allow_html=True)
            st.divider()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Inventário")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        st.subheader("⚙️ Movimentação Manual")
        sel_est = st.selectbox("Produto", df_p['Nome'].unique())
        u_b, t_t = get_config_bebida(sel_est, df_p)
        col_m1, col_m2, col_m3 = st.columns(3)
        tipo_mov = col_m1.radio("Operação", ["➕ ENTRADA", "➖ SAÍDA"])
        qtd_f, qtd_u = col_m2.number_input(f"Qtd {t_t}s", 0), col_m3.number_input("Qtd Avulsas", 0)
        if st.button("EXECUTAR"):
            total_un = (qtd_f * u_b) + qtd_u
            if "SAÍDA" in tipo_mov: df_e.loc[df_e['Nome'] == sel_est, 'Estoque_Total_Un'] -= total_un
            else: df_e.loc[df_e['Nome'] == sel_est, 'Estoque_Total_Un'] += total_un
            df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Ajuste {sel_est}"); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Catálogo")
        with st.expander("🆕 CADASTRAR PRODUTO"):
            with st.form("f_cad"):
                c1, c2, c3 = st.columns([2, 2, 1])
                fc = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Alimentos", "Limpeza", "Outros"])
                fn, fp = c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    if fn and fn not in df_p['Nome'].values:
                        pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                        pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()
        st.markdown("---")
        st.subheader("🗑️ Remover do Catálogo")
        p_del = st.selectbox("Selecione o produto para apagar", ["--"] + list(df_p['Nome'].unique()))
        if p_del != "--":
            if st.button(f"APAGAR {p_del}"):
                df_p[df_p['Nome'] != p_del].to_csv(DB_PROD, index=False)
                df_e[df_e['Nome'] != p_del].to_csv(DB_EST, index=False)
                registrar_log(n_logado, f"Removeu {p_del}"); st.rerun()

    # --- 🍶 CONTROLE DE CASCOS ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Controle de Vasilhames")
        tab_deve, tab_hist, tab_vazio = st.tabs(["🔴 Pendentes", "📜 Histórico de Baixas", "📦 Saldo de Vazios"])
        with tab_deve:
            with st.form("f_cas"):
                cl, va, qt = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml"]), st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([4, 2, 2])
                    c1.error(f"🔴 {r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
                    if c3.button("DAR BAIXA ✅", key=f"bx_{r['ID']}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.to_csv(DB_CAS, index=False); st.rerun()
        with tab_hist:
            df_pagos = df_cas[df_cas['Status'] == "PAGO"].sort_index(ascending=False)
            for i, r in df_pagos.iterrows():
                with st.container():
                    h1, h2, h3 = st.columns([4, 2, 2])
                    h1.write(f"🟢 **{r['Cliente']}** trouxe {r['Quantidade']}x {r['Vasilhame']}")
                    h2.caption(f"Baixa por: {r['QuemBaixou']}")
                    if h3.button("VOLTAR P/ LISTA ⏪", key=f"rev_{r['ID']}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB_CAS, index=False); st.rerun()
        with tab_vazio:
            if not df_cas.empty:
                resumo = df_cas[df_cas['Status'] == "PAGO"].groupby('Vasilhame')['Quantidade'].sum().reset_index()
                st.table(resumo)

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1: st.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='180' style='border-radius: 50%; border: 5px solid #238636; height: 180px; object-fit: cover;'></div>", unsafe_allow_html=True)
        with col_p2:
            st.info(f"**Nome:** {n_logado}\n\n**Usuário:** {u_logado}")
            with st.expander("Atualizar Foto"):
                upload = st.file_uploader("Escolha imagem", type=['png', 'jpg', 'jpeg'])
                if st.button("SALVAR") and upload:
                    img = Image.open(upload); img = img.convert("RGB"); img.thumbnail((300, 300))
                    buf = io.BytesIO(); img.save(buf, format="PNG"); img_b64 = base64.b64encode(buf.getvalue()).decode()
                    df_usr.loc[df_usr['user'] == u_logado, 'foto'] = img_b64; df_usr.to_csv(DB_USR, index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Equipe")
        with st.expander("➕ NOVO MEMBRO"):
            with st.form("f_eq_pro"):
                c1, c2 = st.columns(2)
                nu, nn = c1.text_input("Usuário").strip(), c2.text_input("Nome Completo")
                c3, c4 = st.columns(2)
                ns, na = c3.text_input("Senha", type="password").strip(), c4.selectbox("Admin", ["NÃO", "SIM"])
                if st.form_submit_button("CADASTRAR"):
                    if nu and nu not in df_usr['user'].values:
                        pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, "0000-0000", ""]], columns=df_usr.columns)]).to_csv(DB_USR, index=False); st.rerun()
        for i, r in df_usr.iterrows():
            with st.container():
                u_f = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                if not pd.isna(r['foto']) and r['foto'] != "": u_f = f"data:image/png;base64,{r['foto']}"
                st.markdown(f'<div style="background-color: #1c2128; padding: 15px; border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; display: flex; align-items: center;"><img src="{u_f}" style="width: 50px; height: 50px; border-radius: 50%; margin-right: 15px;"><div><b>{r["nome"]}</b><br>@{r["user"]} | Admin: {r["is_admin"]}</div></div>', unsafe_allow_html=True)
                cb1, cb2 = st.columns([4, 1])
                with cb1:
                    with st.expander("Ver Senha"): st.code(r['senha'])
                with cb2:
                    if r['user'] != 'admin' and st.button("❌", key=f"del_
