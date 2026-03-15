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
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @media (max-width: 640px) { .stApp { padding-bottom: 50px; } }
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="stExpander"] { 
        border: 1px solid #30363d; border-radius: 15px; 
        background-color: #161b22; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .stButton>button {
        border-radius: 10px; font-weight: 700; height: 3em;
        transition: all 0.3s ease; border: 1px solid #30363d; background-color: #21262d;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; transform: translateY(-2px); }
    div[data-testid="stMetric"] {
        background-color: #1c2128; padding: 20px; border-radius: 15px;
        border: 1px solid #30363d; border-left: 6px solid #238636;
    }
    [data-testid="stForm"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 20px; }
    .user-card { background-color: #1c2128; border: 1px solid #30363d; border-radius: 15px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #58a6ff; }
    .task-done { background-color: #1b281d; border: 1px solid #238636; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS E AUTO-CORREÇÃO
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"
DB_TAR, DB_CAT = "tarefas_v66.csv", "categorias_v66.csv"
TODOS_DBS = [DB_PROD, DB_EST, DB_PIL, DB_USR, DB_LOG, DB_CAS, DB_TAR, DB_CAT]

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                      columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(DB_USR, index=False)
    
    arquivos = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_EST: ['Nome', 'Estoque_Total_Un'],
        DB_PIL: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_TAR: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DB_CAT: ['Nome']
    }
    
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)
        else:
            df_temp = pd.read_csv(arq)
            for col in colunas:
                if col not in df_temp.columns: df_temp[col] = ""
            df_temp.to_csv(arq, index=False)

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
# 3. LOGIN E SEGURANÇA
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff; margin-top: 50px;'>🍺 ADEGA PACAEMBU </h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login"):
            u_in = st.text_input("👤 Usuário").strip()
            s_in = st.text_input("🔑 Senha", type="password").strip()
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DB_USR)
                valid = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not valid.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': valid['nome'].values[0], 'u_a': (valid['is_admin'].values[0] == 'SIM')})
                    registrar_log(st.session_state['u_n'], "Login"); st.rerun()
                else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL), pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_TAR), pd.read_csv(DB_CAT)

    # --- SIDEBAR ---
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty and not pd.isna(user_row['foto'].values[0]) and user_row['foto'].values[0] != "":
        f_path = f"data:image/png;base64,{user_row['foto'].values[0]}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='100' style='border-radius: 50%; border: 3px solid #238636; height: 100px; object-fit: cover;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🏠 Dashboard", "📋 Tarefas", "🍻 PDV Romarinho", "🏗️ Pilares", "📦 Estoque", "✨ Cadastro", "🍶 Cascos", "⚙️ Perfil"] + (["📊 Admin Financeiro", "📜 Logs", "👥 Equipe"] if is_adm else []))
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title("🚀 Painel de Controle")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pendências Cascos", f"{len(df_cas[df_cas['Status'] == 'DEVE'])} un")
        c2.metric("Tarefas Ativas", f"{len(df_tar[df_tar['Status'] == 'PENDENTE'])}")
        c3.metric("Pilares Ativos", len(df_pil['NomePilar'].unique()))
        st.table(pd.read_csv(DB_LOG).tail(5))

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Quadro de Tarefas")
        if is_adm:
            with st.form("f_tar"):
                t_desc = st.text_input("Nova Tarefa")
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_desc, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_TAR, index=False); st.rerun()
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                col1, col2 = st.columns([4,1])
                col1.info(f"⭕ {r['Tarefa']}")
                if col2.button("FEITO 👍", key=f"t_{r['ID']}"):
                    df_tar.at[i, 'Status'] = "CONCLUÍDO"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M")
                    df_tar.to_csv(DB_TAR, index=False); st.rerun()
            else:
                st.markdown(f'<div class="task-done">✅ <b>{r["Tarefa"]}</b> (Por: {r["QuemFez"]} às {r["Horario"]})</div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("➕ NOVA CAMADA"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_p = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_p:
                cats_all = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata"] + df_cat['Nome'].tolist())))
                cat_p = st.selectbox("Categoria do Pilar", cats_all)
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_p].empty else int(df_pil[df_pil['NomePilar']==n_p]['Camada'].max()) + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                cols = st.columns(5); regs = []
                for i in range(at+fr):
                    b = cols[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==cat_p]['Nome'].tolist(), key=f"p{i}")
                    a = cols[i].number_input("Av", 0, key=f"a{i}")
                    if b != "Vazio": regs.append([f"{n_p}_{c_atual}_{i}", n_p, c_atual, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False); st.rerun()
        for p in df_pil['NomePilar'].unique():
            st.subheader(f"📍 {p}")
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                cols = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if cols[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_p, _ = get_config_bebida(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                        df_e.to_csv(DB_EST, index=False); df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False); st.rerun()

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Estoque Geral")
        st.dataframe(df_e, use_container_width=True)
        st.subheader("⚙️ Ajuste Manual")
        sel_e = st.selectbox("Produto", df_p['Nome'].unique())
        u_b, t_t = get_config_bebida(sel_e, df_p)
        c_m1, c_m2, c_m3 = st.columns(3)
        tipo_m = c_m1.radio("Operação", ["➕ ENTRADA", "➖ SAÍDA"])
        qtd_f, qtd_u = c_m2.number_input(f"Qtd {t_t}s", 0), c_m3.number_input("Qtd Unid", 0)
        if st.button("EXECUTAR AJUSTE"):
            total = (qtd_f * u_b) + qtd_u
            if "SAÍDA" in tipo_m: df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] -= total
            else: df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] += total
            df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Ajuste {sel_e}"); st.rerun()

    # --- ✨ CADASTRO (CATEGORIAS DINÂMICAS E EXCLUSÃO) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Itens")
        t_c1, t_c2, t_c3 = st.tabs(["➕ Novo Item", "📂 Criar Categoria", "🗑️ Gerenciar Itens"])
        with t_c2:
            with st.form("f_cat"):
                n_cat = st.text_input("Nome da Nova Categoria").upper()
                if st.form_submit_button("CRIAR"):
                    if n_cat and n_cat not in df_cat['Nome'].values:
                        pd.concat([df_cat, pd.DataFrame([[n_cat]], columns=['Nome'])]).to_csv(DB_CAT, index=False); st.success("Criada!"); st.rerun()
        with t_c1:
            with st.form("f_cad"):
                cats_all = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata", "Cerveja Garrafa", "Outros"] + df_cat['Nome'].tolist())))
                c1, c2, c3 = st.columns(3); cat = c1.selectbox("Cat", cats_all); nome = c2.text_input("Nome").upper(); preco = c3.number_input("Preço", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    pd.concat([df_p, pd.DataFrame([[cat, nome, preco]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False); st.rerun()
        with t_c3:
            busca = st.text_input("🔍 Buscar para remover").upper()
            df_v = df_p[df_p['Nome'].str.contains(busca)] if busca else df_p
            for i, r in df_v.iterrows():
                col_n, col_b = st.columns([5,1])
                col_n.write(f"**{r['Nome']}** ({r['Categoria']})")
                if col_b.button("❌", key=f"del_{i}"):
                    df_p.drop(i).to_csv(DB_PROD, index=False); df_e[df_e['Nome'] != r['Nome']].to_csv(DB_EST, index=False); st.rerun()

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3, t4 = st.tabs(["🔴 Pendentes", "🚚 Saída Empresa", "📦 Saldo", "📜 Histórico"])
        with t1:
            with st.form("f_cas"):
                c1, v, q = st.columns(3); cli, vas, qtd = c1.text_input("Cliente").upper(), v.selectbox("Tipo", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"]), q.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, "", vas, qtd, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                if st.button(f"RECEBER de {r['Cliente']} ({r['Quantidade']}x {r['Vasilhame']})", key=r['ID']):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                    df_cas.to_csv(DB_CAS, index=False); st.rerun()
        with t4:
            for i, r in df_cas[df_cas['Status'] == "PAGO"].iterrows():
                h1, h2 = st.columns([4,1])
                h1.success(f"✔️ {r['Cliente']} | {r['Quantidade']} un | Por: {r.get('QuemBaixou','-')} às {r.get('HoraBaixa','-')}")
                if h2.button("ESTORNAR ↩️", key=f"est_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.at[i, 'QuemBaixou'] = ""; df_cas.at[i, 'HoraBaixa'] = ""; df_cas.to_csv(DB_CAS, index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gerenciar Equipe")
        with st.expander("➕ ADICIONAR"):
            with st.form("f_eq"):
                u, n, s, a = st.columns(4); nu = u.text_input("User"); nn = n.text_input("Nome"); ns = s.text_input("Senha"); na = a.selectbox("Admin", ["NÃO", "SIM"])
                if st.form_submit_button("OK"):
                    pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, "0000", ""]], columns=df_usr.columns)]).to_csv(DB_USR, index=False); st.rerun()
        for i, row in df_usr.iterrows():
            c_img, c_txt, c_btn = st.columns([1, 4, 1])
            f_m = f"data:image/png;base64,{row['foto']}" if not pd.isna(row['foto']) and row['foto'] != "" else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            c_img.markdown(f'<img src="{f_m}" style="width:60px; height:60px; border-radius:50%; object-fit: cover;">', unsafe_allow_html=True)
            c_txt.write(f"**{row['nome']}** - {'Admin' if row['is_admin']=='SIM' else 'Operador'}")
            if row['user'] != 'admin' and c_btn.button("X", key=f"rem_u_{i}"):
                df_usr.drop(i).to_csv(DB_USR, index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Perfil")
        upload = st.file_uploader("Foto", type=['png', 'jpg'])
        if st.button("SALVAR") and upload:
            img = Image.open(upload).convert("RGB"); img.thumbnail((300, 300))
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64; df_usr.to_csv(DB_USR, index=False); st.rerun()

    # --- 📊 ADMIN ---
    elif menu == "📊 Admin Financeiro" and is_adm:
        st.title("📊 Gestão")
        if st.button("💾 BACKUP ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as z:
                for f in TODOS_DBS:
                    if os.path.exists(f): z.write(f)
            st.download_button("⬇️ BAIXAR", buf.getvalue(), "backup.zip")

    # --- 🍻 PDV ---
    elif menu == "🍻 PDV Romarinho":
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            if st.button(f"VENDER {item['Nome']}"):
                df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                df_e.to_csv(DB_EST, index=False); registrar_log(n_logado, f"Venda {item['Nome']}"); st.rerun()
