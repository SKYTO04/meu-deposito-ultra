import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO (DARK PRESTIGE V28 - FULL EDITION)
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
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    .profile-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 20px;
        padding: 30px; text-align: center; border-bottom: 4px solid #58a6ff;
    }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; margin-bottom: 10px; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; background: #388bfd; color: white; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (BLINDAGEM TOTAL)
# =================================================================
DB_FILES = {
    "prod": "p_v28.csv", "est": "e_v28.csv", "pil": "pil_v28.csv",
    "usr": "u_v28.csv", "cas": "c_v28.csv", "tar": "t_v28.csv", 
    "cat": "cat_v28.csv", "patio": "pat_v28.csv"
}

def init_db():
    cols_config = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols_config.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            df_new = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_new = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
            if f == DB_FILES["usr"]:
                df_new = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            df_new.to_csv(f, index=False)
        else:
            df_check = pd.read_csv(f)
            if list(df_check.columns) != c:
                pd.DataFrame(columns=c).to_csv(f, index=False)

init_db()

# =================================================================
# 3. AUTENTICAÇÃO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[df_u['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    # Carregamento de Dados
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB_FILES.values()]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    u_row = df_usr[df_usr['user'] == u_logado]
    f_b64 = u_row.iloc[0]['foto'] if not u_row.empty and not pd.isna(u_row.iloc[0]['foto']) else ""
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO (DASHBOARD) ---
    if menu == "🏠 Início":
        st.title(f"Painel de Controle")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Pendências de Cascos", len(df_cas[df_cas['Status'] == "DEVE"]))
        if is_adm and not df_e.empty and not df_p.empty:
            df_v = pd.merge(df_e, df_p, on="Nome")
            valor = (df_v['Estoque_Total_Un'] * df_v['Preco_Unitario']).sum()
            c3.metric("Patrimônio em Estoque", f"R$ {valor:,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário")
        with st.expander("➕ Movimentação Manual (Entrada/Saída)"):
            with st.form("manual_mov"):
                p_sel = st.selectbox("Produto", df_p['Nome'].unique())
                tipo_m = st.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
                qtd_m = st.number_input("Quantidade", 1)
                if st.form_submit_button("Confirmar"):
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += (qtd_m if tipo_m == "ENTRADA" else -qtd_m)
                    df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        st.divider()
        df_f = pd.merge(df_e, df_p, on="Nome")
        cols = st.columns(4)
        for i, r in df_f.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="product-card"><span class="badge">{r["Categoria"]}</span><h4>{r["Nome"]}</h4><p>Estoque: <b>{int(r["Estoque_Total_Un"])}</b></p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2 INTEGRAL) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Camada {cam_at}: Layout automático {atrav}x{frent}")
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"Pos {i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avulsos", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                st.write(f"**Camada {cam}**")
                c_grid = st.columns(5)
                df_camada = df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)]
                for _, r in df_camada.iterrows():
                    with c_grid[int(r['Posicao'])-1]:
                        if st.button(f"BAIXA\n{r['Bebida']}\n(+{r['Avulsos']})", key=r['ID']):
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (12 + r['Avulsos'])
                            df_e.to_csv(DB_FILES["est"], index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (AÇÃO COMPLETA) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores & Estorno", "📦 Pátio (Vazios)", "🚚 Troca Empresa"])
        
        with t1:
            st.subheader("Nova Dívida")
            with st.form("divida_form"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Quantidade", 1)
                if st.form_submit_button("Registrar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            st.divider()
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"⚠️ **{r['Cliente']}** deve {int(r['Quantidade'])} un de {r['Vasilhame']}")
                if c2.button("BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

            with st.expander("📜 Histórico de Pagamentos (Estorno)"):
                for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Recebido: {r['QuemBaixou']})")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"
                        df_cas.to_csv(DB_FILES["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t2:
            st.subheader("Saldo Físico no Pátio")
            for _, r in df_patio.iterrows():
                st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} vazios")

        with t3:
            st.subheader("🚚 Troca com Caminhão")
            with st.form("troca_emp"):
                emp = st.text_input("Empresa/Transportadora").upper()
                v_tipo = st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"])
                v_qtd = st.number_input("Quantidade Levada", 1)
                if st.form_submit_button("Confirmar Troca"):
                    if df_patio.loc[df_patio['Vasilhame'] == v_tipo, 'Total_Vazio'].values[0] >= v_qtd:
                        df_patio.loc[df_patio['Vasilhame'] == v_tipo, 'Total_Vazio'] -= v_qtd
                        df_patio.to_csv(DB_FILES["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), emp, v_tipo, v_qtd, "TROCA", n_logado]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False)
                        st.success("Saída efetuada com sucesso!"); st.rerun()
                    else: st.error("Não há vazios suficientes no pátio!")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Itens")
        ta1, ta2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with ta1:
            with st.form("add_p"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Categoria", df_cat['Nome'].tolist()), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
            st.divider()
            rem = st.selectbox("Excluir Item", df_p['Nome'].tolist())
            if st.button("REMOVER PRODUTO", type="primary"):
                df_p[df_p['Nome'] != rem].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != rem].to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            nova_cat = st.text_input("Nova Categoria")
            if st.button("Salvar Categoria"):
                pd.concat([df_cat, pd.DataFrame([[nova_cat]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.form("add_t"):
                d, tp, dt = st.text_input("Tarefa"), st.selectbox("Frequência", ["Diária", "Data Única"]), st.date_input("Data")
                if st.form_submit_button("Adicionar"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", tp, str(dt)]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            st.info(f"🔹 {r['Tarefa']}")
            if st.button("CONCLUIR", key=f"t_{i}"):
                df_tar.at[i, 'Status'] = "OK"; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE & PERFIL ---
    elif menu == "👥 Equipe":
        st.title("👥 Gestão de Perfil e Membros")
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.image(src, width=150)
        st.subheader(f"{n_logado}")
        st.write("Cargo: " + ("👑 Administrador" if is_adm else "🚀 Operador"))
        with st.expander("📸 Atualizar Foto / Senha"):
            nova_f = st.file_uploader("Trocar Foto", type=['png', 'jpg', 'jpeg'])
            nova_s = st.text_input("Nova Senha", type="password")
            if st.button("Aplicar Alterações"):
                if nova_f:
                    img = Image.open(nova_f).convert("RGB")
                    img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG")
                    df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(buf.getvalue()).decode()
                if nova_s: df_usr.loc[df_usr['user'] == u_logado, 'senha'] = nova_s
                df_usr.to_csv(DB_FILES["usr"], index=False); st.success("Atualizado!"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        if is_adm:
            st.subheader("Novos Acessos")
            with st.form("new_u"):
                lu, ln, ls, la = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Admin", ["NÃO", "SIM"])
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_usr, pd.DataFrame([[lu, ln, ls, la, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
