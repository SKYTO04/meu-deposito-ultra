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
        if cat in ["Alimentos", "Limpeza"]: return 1, "Unidade"
    return 12, "Fardo"

# =================================================================
# 3. SEGURANÇA E LOGIN
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff; margin-top: 50px;'>💎 PACAEMBU ULTRA G66</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in = st.text_input("👤 Usuário")
            s_in = st.text_input("🔑 Senha", type="password")
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
    df_p, df_e, df_pil = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_cas, df_usr = pd.read_csv(DB_CAS), pd.read_csv(DB_USR)

    # --- SIDEBAR COM FOTO ---
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty:
        raw = user_row['foto'].values[0]
        if not pd.isna(raw) and raw != "": f_path = f"data:image/png;base64,{raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='100' style='border-radius: 50%; border: 3px solid #238636; margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 1.2em;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    
    if st.sidebar.button("🚪 SAIR"):
        st.session_state['autenticado'] = False; st.rerun()

    # --- 🍻 PDV ROMARINHO ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV Rápido")
        df_pdv = df_p[df_p['Categoria'].isin(["Romarinho", "Refrigerante", "Cerveja Lata"])]
        for _, item in df_pdv.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 4])
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
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

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🆕 MONTAR NOVA CAMADA"):
            p_alvo = st.selectbox("Pilar", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_filtro = st.selectbox("Categoria", df_p['Categoria'].unique())
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                st.warning(f"Lógica Camada {c_atual}: {at}x{fr}")
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                col_at, col_fr = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1; target = col_at if pos <= at else col_fr
                    beb_dict[pos] = target.selectbox(f"Pos {pos}", lista_beb, key=f"p_{pos}")
                    av_dict[pos] = target.number_input(f"Avulsos {pos}", 0, key=f"a_{pos}")
                if st.button("CONFIRMAR MONTAGEM"):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()

        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            for cam in sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True):
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                cols = st.columns(5)
                for _, r in dados_cam.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1c2128; padding:5px; border-radius:10px; border:1px solid #30363d; text-align:center;'>{r['Bebida']}<br>+{r['Avulsos']}</div>", unsafe_allow_html=True)
                        if st.button("SAÍDA", key=f"out_{r['ID']}"):
                            u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False); df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False); st.rerun()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Inventário")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        st.subheader("⚙️ Movimentação Manual")
        sel_est = st.selectbox("Produto", df_p['Nome'].unique())
        row_p = df_p[df_p['Nome'] == sel_est]
        cat_p = row_p['Categoria'].values[0] if not row_p.empty else ""
        u_b, t_t = get_config_bebida(sel_est, df_p)
        col_m1, col_m2, col_m3 = st.columns(3)
        tipo_mov = col_m1.radio("Operação", ["➕ ENTRADA", "➖ SAÍDA"])
        if cat_p in ["Alimentos", "Limpeza"]:
            qtd_f, qtd_u = 0, col_m2.number_input("Quantidade (Unidades)", 0)
            col_m3.info("Item Unitário")
        else:
            qtd_f, qtd_u = col_m2.number_input(f"Qtd {t_t}s", 0), col_m3.number_input("Qtd Avulsas", 0)
        if st.button("EXECUTAR"):
            total_un = (qtd_f * u_b) + qtd_u
            if "SAÍDA" in tipo_mov: df_e.loc[df_e['Nome'] == sel_est, 'Estoque_Total_Un'] -= total_un
            else: df_e.loc[df_e['Nome'] == sel_est, 'Estoque_Total_Un'] += total_un
            df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Ajuste {sel_est}"); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Catálogo")
        with st.form("f_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Alimentos", "Limpeza", "Outros"])
            fn, fp = c2.text_input("Nome").upper(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("CADASTRAR"):
                if fn and fn not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Cascos")
        with st.form("f_cas"):
            cl, va, qt = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml"]), st.number_input("Qtd", 1)
            if st.form_submit_button("LANÇAR"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            st.error(f"🔴 {r['Cliente']} deve {r['Quantidade']}x {r['Vasilhame']}")
            if st.button("BAIXA", key=f"bx_{r['ID']}"):
                df_cas.at[i, 'Status'] = "PAGO"; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- ⚙️ PERFIL (ATUALIZADO) ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            st.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='180' style='border-radius: 50%; border: 5px solid #238636;'></div>", unsafe_allow_html=True)
        
        with col_p2:
            st.subheader("Dados do Usuário")
            st.info(f"**Nome:** {n_logado}\n\n**Usuário:** {u_logado}\n\n**Cargo:** {'Administrador' if is_adm else 'Colaborador'}")
            
            with st.expander("Atualizar Foto de Perfil"):
                upload = st.file_uploader("Escolha uma imagem", type=['png', 'jpg', 'jpeg'])
                if st.button("SALVAR NOVA FOTO") and upload:
                    img = Image.open(upload)
                    img = img.convert("RGB")
                    img.thumbnail((300, 300))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode()
                    df_usr.loc[df_usr['user'] == u_logado, 'foto'] = img_b64
                    df_usr.to_csv(DB_USR, index=False)
                    st.success("Foto atualizada! Reiniciando...")
                    st.rerun()

    # --- 👥 EQUIPE (ATUALIZADO) ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Equipe")
        
        with st.expander("➕ CADASTRAR NOVO MEMBRO"):
            with st.form("f_equipe"):
                c1, c2, c3, c4 = st.columns(4)
                new_u = c1.text_input("Usuário (Login)")
                new_n = c2.text_input("Nome Completo")
                new_s = c3.text_input("Senha", type="password")
                new_a = c4.selectbox("Admin", ["NÃO", "SIM"])
                if st.form_submit_button("ADICIONAR À EQUIPE"):
                    if new_u and new_n and new_s:
                        if new_u not in df_usr['user'].values:
                            new_row = pd.DataFrame([[new_u, new_n, new_s, new_a, "0000-0000", ""]], columns=df_usr.columns)
                            pd.concat([df_usr, new_row]).to_csv(DB_USR, index=False)
                            registrar_log(n_logado, f"Cadastrou usuário {new_u}")
                            st.success(f"{new_n} adicionado!")
                            st.rerun()
                        else: st.error("Usuário já existe.")

        st.subheader("Membros Ativos")
        for i, r in df_usr.iterrows():
            with st.container():
                ec1, ec2, ec3, ec4 = st.columns([1, 3, 2, 1])
                # Foto pequena
                u_foto = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                if not pd.isna(r['foto']) and r['foto'] != "": u_foto = f"data:image/png;base64,{r['foto']}"
                
                ec1.markdown(f"<img src='{u_foto}' width='50' style='border-radius: 50%;'>", unsafe_allow_html=True)
                ec2.markdown(f"**{r['nome']}** ({r['user']})")
                ec3.markdown(f"🛡️ Admin: `{r['is_admin']}`")
                if r['user'] != 'admin': # Proteção para não deletar o master
                    if ec4.button("❌", key=f"del_{r['user']}"):
                        df_usr[df_usr['user'] != r['user']].to_csv(DB_USR, index=False)
                        st.rerun()
                st.divider()

    # --- 📊 ADMIN/LOGS ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Patrimônio")
        df_fin = pd.merge(df_e, df_p, on='Nome')
        df_fin['Subtotal'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("VALOR EM ESTOQUE", f"R$ {df_fin['Subtotal'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True, hide_index=True)
    
    elif menu == "📜 Logs" and is_adm:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(DB_LOG).sort_values(by='Data', ascending=False), use_container_width=True, hide_index=True)
        if st.button("🗑️ LIMPAR LOGS"):
            pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, index=False); st.rerun()
