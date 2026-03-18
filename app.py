import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO (VISUAL PRESTIGE v40)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu - Sistema Integral", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; text-align: center;
    }
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    .profile-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 20px;
        padding: 30px; text-align: center; border-bottom: 4px solid #58a6ff;
    }
    .avatar-round { border-radius: 50%; border: 4px solid #58a6ff; object-fit: cover; margin-bottom: 15px; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; background: #388bfd; color: white; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (BLINDAGEM TOTAL v40)
# =================================================================
DB = {
    "prod": "p_v40.csv", "est": "e_v40.csv", "pil": "pil_v40.csv",
    "usr": "u_v40.csv", "cas": "c_v40.csv", "tar": "t_v40.csv", 
    "cat": "cat_v40.csv", "patio": "pat_v40.csv"
}

def init_db():
    conf = {
        DB["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB["est"]: ['Nome', 'Estoque_Total_Un'],
        DB["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB["cat"]: ['Nome'],
        DB["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in conf.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            df = pd.DataFrame(columns=c)
            if f == DB["patio"]:
                df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
            if f == DB["usr"]:
                df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            if f == DB["cat"]:
                df = pd.DataFrame([["Romarinho"], ["Cerveja"], ["Refrigerante"]], columns=c)
            df.to_csv(f, index=False)
        else:
            try:
                df_check = pd.read_csv(f)
                if not all(col in df_check.columns for col in c):
                    os.remove(f)
                    pd.DataFrame(columns=c).to_csv(f, index=False)
            except:
                os.remove(f)
                pd.DataFrame(columns=c).to_csv(f, index=False)

init_db()

# =================================================================
# 3. CONTROLE DE SESSÃO E LOGIN
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR"):
                df_u = pd.read_csv(DB["usr"])
                match = df_u[df_u['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    # Carregamento de dados
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB.values()]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    u_row = df_usr[df_usr['user'] == u_logado]
    f_b64 = u_row.iloc[0]['foto'] if not u_row.empty and not pd.isna(u_row.iloc[0]['foto']) else ""
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title("Painel de Controle")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Dívidas de Clientes", len(df_cas[df_cas['Status'] == "DEVE"]))
        if is_adm and not df_e.empty:
            df_v = pd.merge(df_e, df_p, on="Nome")
            c3.metric("Patrimônio Estoque", f"R$ {(df_v['Estoque_Total_Un']*df_v['Preco_Unitario']).sum():,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        df_f = pd.merge(df_e, df_p, on="Nome")
        cols = st.columns(4)
        for i, r in df_f.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="product-card"><h4>{r["Nome"]}</h4><p>Qtd: <b>{int(r["Estoque_Total_Un"])}</b></p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (3x2 e 2x3) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Filtrar Categoria", df_cat['Nome'].tolist())
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Camada {cam_at}: Layout {atrav}x{frent}")
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avs", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB["pil"], index=False); st.rerun()
        
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    with c_grid[int(r['Posicao'])-1]:
                        if st.button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (12 + r['Avulsos'])
                            df_e.to_csv(DB["est"], index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (DEVEDORES, HISTÓRICO/ESTORNO E EMPRESA) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico / Estorno", "🚚 Saída Empresa"])
        with t1:
            with st.form("divida"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Quantidade", 1)
                if st.form_submit_button("Lançar Dívida"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"⚠️ {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                if c2.button("BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t2:
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                ch1, ch2 = st.columns([3, 1])
                ch1.write(f"✅ {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Rec: {r['QuemBaixou']})")
                if ch2.button("ESTORNAR", key=f"est_{i}"):
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t3:
            st.subheader("Saída de Vasilhames para Empresa")
            for _, r in df_patio.iterrows(): st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} no pátio")
            with st.form("saida_emp"):
                emp, v_t, v_q = st.text_input("Nome da Empresa / Caminhão").upper(), st.selectbox("Casco", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"], key="tp_saida"), st.number_input("Qtd Saída", 1)
                if st.form_submit_button("Confirmar Saída"):
                    idx = df_patio[df_patio['Vasilhame'] == v_t].index[0]
                    if df_patio.at[idx, 'Total_Vazio'] >= v_q:
                        df_patio.at[idx, 'Total_Vazio'] -= v_q
                        df_patio.to_csv(DB["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), emp, v_t, v_q, "TROCA", n_logado]], columns=df_cas.columns)]).to_csv(DB["cas"], index=False)
                        st.success("Saída registrada!"); st.rerun()
                    else: st.error("Falta vasilhame no pátio.")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Cadastro")
        with st.form("cad_prod"):
            n, c, pr = st.text_input("Nome do Produto").upper(), st.selectbox("Categoria", df_cat['Nome'].tolist()), st.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB["prod"], index=False)
                pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB["est"], index=False); st.rerun()
        st.divider()
        st.subheader("🗑️ Apagar Produto")
        p_exc = st.selectbox("Produto para excluir", df_p['Nome'].tolist())
        if st.button("EXCLUIR DEFINITIVAMENTE", type="primary"):
            df_p[df_p['Nome'] != p_exc].to_csv(DB["prod"], index=False)
            df_e[df_e['Nome'] != p_exc].to_csv(DB["est"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist de Obrigações")
        if is_adm:
            with st.form("nova_t"):
                txt = st.text_input("O que precisa ser feito?")
                if st.form_submit_button("Adicionar"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", txt, "PENDENTE", "DIÁRIA", ""]], columns=df_tar.columns)]).to_csv(DB["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            st.info(f"🔹 {r['Tarefa']}")
            if st.button("MARCAR COMO CONCLUÍDO", key=f"t_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE / PERFIL ---
    elif menu == "👥 Equipe":
        st.title("👥 Perfil e Gestão de Membros")
        st.markdown(f'<div class="profile-card"><img src="{src}" width="150" class="avatar-round"><h3>{n_logado}</h3><p>Status: {"👑 Administrador" if is_adm else "🚀 Colaborador"}</p></div>', unsafe_allow_html=True)
        
        with st.expander("📸 Atualizar Foto"):
            f = st.file_uploader("Upload da Foto")
            if st.button("Salvar") and f:
                img = Image.open(f).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG")
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(buf.getvalue()).decode()
                df_usr.to_csv(DB["usr"], index=False); st.rerun()
        
        if is_adm:
            st.divider()
            st.subheader("➕ Novo Login de Funcionário")
            with st.form("new_user"):
                lu, ln, ls, la = st.text_input("Username"), st.text_input("Nome Completo"), st.text_input("Senha", type="password"), st.selectbox("Admin?", ["NÃO", "SIM"])
                if st.form_submit_button("CADASTRAR"):
                    if lu and ln and ls:
                        pd.concat([df_usr, pd.DataFrame([[lu, ln, ls, la, ""]], columns=df_usr.columns)]).to_csv(DB["usr"], index=False); st.rerun()
                    else: st.error("Preencha todos os campos.")
            st.subheader("Equipe Ativa")
            st.table(df_usr[['user', 'nome', 'is_admin']])
