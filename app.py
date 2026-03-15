import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE V90 (DEFINITIVO)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Cartões Visuais */
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Estilo para Status */
    .status-badge {
        padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold;
    }
    .badge-verde { background-color: #238636; color: white; }
    .badge-vermelho { background-color: #f85149; color: white; }
    
    /* Fotos e Avatares */
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    
    /* Pilares e Grid */
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 5px solid #58a6ff;
    }
    
    /* Botões */
    .stButton>button {
        border-radius: 8px; font-weight: 600; background-color: #21262d; 
        border: 1px solid #444; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E INFRAESTRUTURA
# =================================================================
DB_FILES = {
    "prod": "produtos_v90.csv", "est": "estoque_v90.csv", "pil": "pilares_v90.csv",
    "usr": "usuarios_v90.csv", "log": "historico_v90.csv", "cas": "cascos_v90.csv",
    "tar": "tarefas_v90.csv", "cat": "categorias_v90.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["log"]: ['Data', 'Usuario', 'Ação'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']
    }
    for f, c in cols.items():
        if not os.path.exists(f): pd.DataFrame(columns=c).to_csv(f, index=False)
        else:
            df = pd.read_csv(f)
            for col in c:
                if col not in df.columns: df[col] = ""; df.to_csv(f, index=False)
    
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '', '']], columns=cols[DB_FILES["usr"]]).to_csv(DB_FILES["usr"], index=False)

init_db()

def registrar_log(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(DB_FILES["log"], mode='a', header=False, index=False)

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. LÓGICA DE ACESSO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 ADEGA PACAEMBU</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    registrar_log(match.iloc[0]['nome'], "Login"); st.rerun()
                else: st.error("Login Inválido.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat = pd.read_csv(DB_FILES["prod"]), pd.read_csv(DB_FILES["est"]), pd.read_csv(DB_FILES["pil"]), pd.read_csv(DB_FILES["cas"]), pd.read_csv(DB_FILES["usr"]), pd.read_csv(DB_FILES["tar"]), pd.read_csv(DB_FILES["cat"])

    # --- SIDEBAR ---
    row_user = df_usr[df_usr['user'] == u_logado].iloc[0]
    img_b64 = row_user['foto']
    sidebar_src = f"data:image/png;base64,{img_b64}" if img_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{sidebar_src}" class="avatar-round" width="90" height="90"><br><br><b>{n_logado}</b><br><small>{"ADMINISTRADOR" if is_adm else "OPERADOR"}</small></center>', unsafe_allow_html=True)
    st.sidebar.divider()
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "📋 Tarefas", "✨ Cadastro", "🍶 Cascos", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏗️ PILARES (LÓGICA COMPLETA) ---
    if menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 ADICIONAR NOVA CAMADA"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cats_p = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata"] + df_cat['Nome'].tolist())))
                c_escolha = st.selectbox("Filtrar Bebidas por Categoria", cats_p)
                c_num = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else int(df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()) + 1
                at, fr = (3, 2) if c_num % 2 != 0 else (2, 3)
                st.info(f"Pilar {n_pilar} | Camada {c_num} | Estilo {'3+2' if c_num%2!=0 else '2+3'}")
                cols_p = st.columns(5); regs = []
                for i in range(at+fr):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==c_escolha]['Nome'].tolist(), key=f"p{i}")
                    a = cols_p[i].number_input("Av", 0, key=f"a{i}")
                    if b != "Vazio": regs.append([f"{n_pilar}_{c_num}_{i}", n_pilar, c_num, i+1, b, a])
                if st.button("CONFIRMAR E MONTAR"):
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        u_p, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (u_p + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False)
                        registrar_log(n_logado, f"Baixa Pilar {p}: {r['Bebida']}"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- ✨ CADASTRO (COM REMOVER CATEGORIA) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Catálogo")
        t1, t2, t3, t4 = st.tabs(["➕ Novo Item", "📂 Criar Categoria", "🗑️ Remover Categoria", "🛠️ Remover Item"])
        
        with t2:
            nova_cat = st.text_input("Nome da Nova Categoria").upper()
            if st.button("SALVAR CATEGORIA"):
                if nova_cat and nova_cat not in df_cat['Nome'].values:
                    pd.concat([df_cat, pd.DataFrame([[nova_cat]], columns=['Nome'])]).to_csv(DB_FILES["cat"], index=False); st.success("Criada!"); st.rerun()
        
        with t3:
            st.subheader("Remover Categoria Existente")
            if not df_cat.empty:
                c_excluir = st.selectbox("Selecione para remover", df_cat['Nome'].unique())
                if st.button("APAGAR CATEGORIA", type="primary"):
                    df_cat[df_cat['Nome'] != c_excluir].to_csv(DB_FILES["cat"], index=False)
                    st.warning(f"Categoria {c_excluir} apagada!"); st.rerun()
            else: st.write("Nenhuma categoria customizada.")

        with t1:
            with st.form("f_item"):
                cats_all = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata", "Cerveja Garrafa"] + df_cat['Nome'].tolist())))
                c_c = st.selectbox("Categoria", cats_all)
                c_n = st.text_input("Nome da Bebida").upper()
                c_p = st.number_input("Preço", 0.0)
                if st.form_submit_button("CADASTRAR PRODUTO"):
                    pd.concat([df_p, pd.DataFrame([[c_c, c_n, c_p]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[c_n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False)
                    registrar_log(n_logado, f"Cadastrou {c_n}"); st.rerun()
        
        with t4:
            for i, r in df_p.iterrows():
                col_i1, col_i2 = st.columns([5,1])
                col_i1.write(f"**{r['Nome']}** ({r['Categoria']})")
                if col_i2.button("🗑️", key=f"delp_{i}"):
                    df_p.drop(i).to_csv(DB_FILES["prod"], index=False)
                    df_e[df_e['Nome']!=r['Nome']].to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 👥 EQUIPE (CADASTRAR OUTRO USUÁRIO) ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Operadores")
        with st.expander("➕ CADASTRAR NOVO MEMBRO"):
            with st.form("f_equipe"):
                c1, c2, c3, c4 = st.columns(4)
                u_user = c1.text_input("Login")
                u_nome = c2.text_input("Nome Completo")
                u_pass = c3.text_input("Senha")
                u_adm = c4.selectbox("Acesso Admin", ["NÃO", "SIM"])
                if st.form_submit_button("CADASTRAR MEMBRO"):
                    pd.concat([df_usr, pd.DataFrame([[u_user, u_nome, u_pass, u_adm, "", ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False)
                    st.success("Membro adicionado!"); st.rerun()
        
        for i, row in df_usr.iterrows():
            f_eq = f"data:image/png;base64,{row['foto']}" if row['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            st.markdown(f'''
            <div class="card"><div style="display:flex; align-items:center; gap:20px;">
                <img src="{f_eq}" class="avatar-round" width="60" height="60">
                <div style="flex-grow:1"><b>{row['nome']}</b><br><small>{row['user']} | Admin: {row['is_admin']}</small></div>
            </div></div>
            ''', unsafe_allow_html=True)
            if row['user'] != 'admin' and st.button(f"Remover {row['user']}", key=f"rm_u_{i}"):
                df_usr.drop(i).to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações Pessoais")
        col_pf1, col_pf2 = st.columns([1, 2])
        f_perfil = f"data:image/png;base64,{row_user['foto']}" if row_user['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
        col_pf1.image(f_perfil, width=200)
        with col_pf2:
            st.subheader(n_logado)
            st.info(f"Nível de Acesso: {'Administrador' if is_adm else 'Operador'}")
            upload_f = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
            if st.button("SALVAR NOVA FOTO") and upload_f:
                img_o = Image.open(upload_f).convert("RGB"); img_o.thumbnail((300, 300))
                buf_o = io.BytesIO(); img_o.save(buf_o, format="PNG"); b64_o = base64.b64encode(buf_o.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64_o; df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()

    # --- 📦 ESTOQUE (CARTÕES DINÂMICOS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        df_inv = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_inv.iterrows():
            u_b, t_t = get_config(r['Nome'], df_p)
            badge = '<span class="status-badge badge-verde">EM ESTOQUE</span>' if r['Estoque_Total_Un'] > 0 else '<span class="status-badge badge-vermelho">ESGOTADO</span>'
            st.markdown(f'''
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><b>{r['Nome']}</b><br><small>{r['Categoria']}</small></div>
                    <div style="text-align:right"><b>{r['Estoque_Total_Un']} un</b><br>{badge}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        with st.expander("⚙️ AJUSTE MANUAL"):
            with st.form("f_est"):
                sel = st.selectbox("Item", df_p['Nome'].unique())
                op = st.radio("Ação", ["ENTRADA", "SAÍDA"], horizontal=True)
                qtd_un = st.number_input("Quantidade Total em Unidades", 0)
                if st.form_submit_button("ATUALIZAR"):
                    if op == "SAÍDA": df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] -= qtd_un
                    else: df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += qtd_un
                    df_e.to_csv(DB_FILES["est"], index=False); st.rerun()

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        t_c1, t_c2 = st.tabs(["🔴 Pendentes", "📜 Histórico"])
        with t_c1:
            with st.form("f_casco"):
                c_cli, c_tipo, c_qtd = st.columns(3)
                cli_c = c_cli.text_input("Cliente").upper()
                tipo_c = c_tipo.selectbox("Tipo", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"])
                qtd_c = c_qtd.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli_c, "", tipo_c, qtd_c, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                st.warning(f"📍 {r['Cliente']} deve {r['Quantidade']} de {r['Vasilhame']}")
                if st.button(f"RECEBER DE {r['Cliente']}", key=f"bx_c_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                    df_cas.to_csv(DB_FILES["cas"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.form("f_t"):
                t_desc = st.text_input("Nova Tarefa")
                if st.form_submit_button("ADICIONAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_desc, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                col_t, col_b = st.columns([5,1])
                col_t.info(f"⭕ {r['Tarefa']}")
                if col_b.button("FEITO", key=f"ok_t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M")
                    df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()
            else: st.success(f"✅ {r['Tarefa']} (Por: {r['QuemFez']})")

    # --- 🏠 DASHBOARD ---
    elif menu == "🏠 Dashboard":
        st.title("🚀 Painel de Controle")
        c1, c2, c3 = st.columns(3)
        c1.metric("Estoque (Un)", df_e['Estoque_Total_Un'].sum())
        c2.metric("Tarefas Pendentes", len(df_tar[df_tar['Status']=="PENDENTE"]))
        c3.metric("Cascos Devedores", len(df_cas[df_cas['Status']=="DEVE"]))
        st.divider()
        st.subheader("📜 Logs do Sistema")
        st.dataframe(pd.read_csv(DB_FILES["log"]).tail(10), use_container_width=True)
