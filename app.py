import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import json

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO (DARK PRESTIGE V19)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; text-align: center;
    }
    .task-card {
        background: #1c2128; border-left: 5px solid #d29922;
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
    }
    .task-done { border-left-color: #238636; opacity: 0.6; text-decoration: line-through; }
    .user-card {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d; border-radius: 15px; padding: 20px; text-align: center;
    }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; }
    .badge-blue { background: #388bfd; color: white; }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (V19 - COM RESET FORÇADO)
# =================================================================
DB_FILES = {
    "prod": "p_v19.csv", "est": "e_v19.csv", "pil": "pil_v19.csv",
    "usr": "u_v19.csv", "cas": "c_v19.csv", "tar": "t_v19.csv", 
    "cat": "cat_v19.csv", "patio": "pat_v19.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg', 'QuemFez'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    
    for f, c in cols.items():
        # Se o arquivo não existe ou está corrompido (sem a coluna 'user' por exemplo)
        create_new = False
        if not os.path.exists(f):
            create_new = True
        else:
            try:
                temp = pd.read_csv(f)
                if f == DB_FILES["usr"] and 'user' not in temp.columns:
                    create_new = True
                elif f == DB_FILES["prod"] and 'Nome' not in temp.columns:
                    create_new = True
            except:
                create_new = True
        
        if create_new:
            df_empty = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_empty = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            if f == DB_FILES["usr"]:
                df_empty = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            df_empty.to_csv(f, index=False)

init_db()

# =================================================================
# 3. LOGICA DE NAVEGAÇÃO
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login_form"):
            u_in = st.text_input("Usuário").strip()
            s_in = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR"):
                df_usr = pd.read_csv(DB_FILES["usr"])
                # Verificação segura
                match = df_usr[df_usr['user'].astype(str) == str(u_in)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s_in):
                    st.session_state.update({
                        'autenticado': True,
                        'u_l': u_in,
                        'u_n': match.iloc[0]['nome'],
                        'u_a': (match.iloc[0]['is_admin'] == 'SIM')
                    })
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
else:
    # Carregamento dos DataFrames
    df_p = pd.read_csv(DB_FILES["prod"])
    df_e = pd.read_csv(DB_FILES["est"])
    df_pil = pd.read_csv(DB_FILES["pil"])
    df_cas = pd.read_csv(DB_FILES["cas"])
    df_usr = pd.read_csv(DB_FILES["usr"])
    df_tar = pd.read_csv(DB_FILES["tar"])
    df_cat = pd.read_csv(DB_FILES["cat"])
    df_patio = pd.read_csv(DB_FILES["patio"])

    u_logado = st.session_state['u_l']
    n_logado = st.session_state['u_n']
    is_adm = st.session_state['u_a']

    # --- SIDEBAR ---
    # Busca segura da foto para evitar o KeyError
    user_data = df_usr[df_usr['user'] == u_logado]
    foto_b64 = ""
    if not user_data.empty:
        foto_b64 = user_data.iloc[0]['foto'] if not pd.isna(user_data.iloc[0]['foto']) else ""
    
    src = f"data:image/png;base64,{foto_b64}" if foto_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    
    if st.sidebar.button("SAIR"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title(f"Painel Principal")
        if not df_e.empty and not df_p.empty:
            df_j = pd.merge(df_e, df_p, on="Nome")
            val = (df_j['Estoque_Total_Un'] * df_j['Preco_Unitario']).sum()
            c1, c2 = st.columns(2)
            c1.metric("Valor em Estoque", f"R$ {val:,.2f}")
            c2.metric("Pátio (Vazios)", f"{int(df_patio['Total_Vazio'].sum())} un")
        else:
            st.info("Cadastre produtos para ver o resumo.")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Controle de Estoque")
        with st.expander("Lançar Movimento"):
            if not df_p.empty:
                with st.form("m"):
                    sel = st.selectbox("Produto", df_p['Nome'].unique())
                    tp = st.radio("Tipo", ["ENTRADA", "SAÍDA"], horizontal=True)
                    qt = st.number_input("Quantidade", 1)
                    if st.form_submit_button("Gravar"):
                        df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (qt if tp == "ENTRADA" else -qt)
                        df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
            else: st.warning("Cadastre produtos primeiro.")
        
        st.divider()
        if not df_e.empty and not df_p.empty:
            df_full = pd.merge(df_e, df_p, on="Nome")
            cols = st.columns(4)
            for i, r in df_full.iterrows():
                with cols[i % 4]:
                    st.markdown(f'<div class="product-card"><span class="badge badge-blue">{r["Categoria"]}</span><h4>{r["Nome"]}</h4><p>Total: <b>{int(r["Estoque_Total_Un"])}</b> un</p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (3/2) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Layout para Camada {cam_at}: {atrav} atravessados e {frent} de frente.")
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    b = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                    a = cols_p[i].number_input("Avs", 0, key=f"a_{i}")
                    if b != "Vazio":
                        c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    df_pil = pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)])
                    df_pil.to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam}")
                c_grid = st.columns(5)
                it_camada = df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)]
                for _, r in it_camada.iterrows():
                    if c_grid[int(r['Posicao'])-1].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        # Baixa padrão de 12 ou 24 dependendo do tipo poderia entrar aqui
                        df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= 12 
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil = df_pil[df_pil['ID'] != r['ID']]
                        df_pil.to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2 = st.tabs(["🔴 Devedores", "🚚 Pátio"])
        with t1:
            with st.form("d"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    new_c = pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, q, "DEVE", "", ""]], columns=df_cas.columns)
                    pd.concat([df_cas, new_c]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                if st.button(f"BAIXAR: {r['Cliente']} ({r['Quantidade']} {r['Vasilhame']})", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()
        with t2:
            for _, r in df_patio.iterrows():
                st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} unidades no pátio")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro Geral")
        ta1, ta2 = st.tabs(["Produtos", "Categorias"])
        with ta1:
            with st.form("p"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                p = st.number_input("Preço de Venda", 0.0)
                if st.form_submit_button("Salvar"):
                    new_p = pd.DataFrame([[c, n, p]], columns=df_p.columns)
                    new_e = pd.DataFrame([[n, 0]], columns=df_e.columns)
                    pd.concat([df_p, new_p]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, new_e]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            nc = st.text_input("Nome da Nova Categoria")
            if st.button("Criar Categoria"):
                new_cat = pd.DataFrame([[nc]], columns=df_cat.columns)
                pd.concat([df_cat, new_cat]).to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.expander("Adicionar Tarefa"):
                with st.form("t"):
                    d = st.text_input("Descrição")
                    tp = st.selectbox("Tipo", ["Diária", "Data Específica"])
                    dt = st.date_input("Data")
                    if st.form_submit_button("Add"):
                        new_t = pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", tp, str(dt), ""]], columns=df_tar.columns)
                        pd.concat([df_tar, new_t]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        
        hj = datetime.now().strftime("%Y-%m-%d")
        df_hoje = df_tar[(df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hj)]
        for i, r in df_hoje.iterrows():
            st.markdown(f'<div class="task-card {"task-done" if r["Status"]=="OK" else ""}"><b>{r["Tarefa"]}</b></div>', unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("Concluir", key=f"t_{i}"):
                df_tar.loc[df_tar['ID'] == r['ID'], 'Status'] = "OK"
                df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Nossa Equipe")
        if is_adm:
            with st.form("u"):
                li, ni, si, ai = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Adm", ["NÃO", "SIM"])
                if st.form_submit_button("Cadastrar"):
                    new_u = pd.DataFrame([[li, ni, si, ai, ""]], columns=df_usr.columns)
                    pd.concat([df_usr, new_u]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        
        cols_eq = st.columns(4)
        for i, r in df_usr.iterrows():
            with cols_eq[i % 4]:
                st.markdown(f'<div class="user-card"><h4>{r["nome"]}</h4><p>{"Admin" if r["is_admin"]=="SIM" else "Equipe"}</p></div>', unsafe_allow_html=True)

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações de Perfil")
        f_up = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
        if st.button("Salvar Alterações") and f_up:
            img = Image.open(f_up).convert("RGB")
            img.thumbnail((300, 300))
            b = io.BytesIO()
            img.save(b, format="PNG")
            b64 = base64.b64encode(b.getvalue()).decode()
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64
            df_usr.to_csv(DB_FILES["usr"], index=False); st.success("Foto atualizada!"); st.rerun()
        
        st.divider()
        st.subheader("💾 Backup")
        backup = {k: pd.read_csv(v).to_dict() for k, v in DB_FILES.items()}
        st.download_button("Baixar Tudo", json.dumps(backup), "backup.json")
