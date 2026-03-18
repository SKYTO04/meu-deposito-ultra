import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO E ESTILO (DARK PRESTIGE V26 - FINAL)
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
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; background: #388bfd; color: white; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (ESTRUTURA COMPLETA V26)
# =================================================================
DB_FILES = {
    "prod": "p_v26.csv", "est": "e_v26.csv", "pil": "pil_v26.csv",
    "usr": "u_v26.csv", "cas": "c_v26.csv", "tar": "t_v26.csv", 
    "cat": "cat_v26.csv", "patio": "pat_v26.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            df_i = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_i = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
            if f == DB_FILES["usr"]:
                df_i = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
            df_i.to_csv(f, index=False)

init_db()

# =================================================================
# 3. SISTEMA DE AUTENTICAÇÃO
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
                if 'user' in df_u.columns:
                    match = df_u[df_u['user'].astype(str) == str(u)]
                    if not match.empty and str(match.iloc[0]['senha']) == str(s):
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                        st.rerun()
                    else: st.error("Acesso negado.")
                else: st.error("Erro no banco de dados. Apague os arquivos CSV.")
else:
    # Carregamento Geral
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB_FILES.values()]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    try:
        u_row = df_usr[df_usr['user'] == u_logado]
        f_b64 = u_row.iloc[0]['foto'] if not u_row.empty and not pd.isna(u_row.iloc[0]['foto']) else ""
        src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    except: src = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title(f"Painel Adega Pacaembu")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Clientes Devedores", len(df_cas[df_cas['Status'] == "DEVE"]))
        if is_adm and not df_e.empty and not df_p.empty:
            df_full = pd.merge(df_e, df_p, on="Nome")
            valor = (df_full['Estoque_Total_Un'] * df_full['Preco_Unitario']).sum()
            c3.metric("Valor em Estoque", f"R$ {valor:,.2f}")

    # --- 📦 ESTOQUE ---
    elif menu == "📦 Estoque":
        st.title("📦 Controle de Estoque")
        with st.expander("Lançar Movimento Manual"):
            with st.form("mov"):
                sel = st.selectbox("Produto", df_p['Nome'].unique())
                tp = st.radio("Tipo", ["ENTRADA", "SAÍDA"], horizontal=True)
                qt = st.number_input("Quantidade", 1)
                if st.form_submit_button("Lançar"):
                    df_e.loc[df_e['Nome'] == sel, 'Estoque_Total_Un'] += (qt if tp == "ENTRADA" else -qt)
                    df_e.to_csv(DB_FILES["est"], index=False); st.rerun()
        st.divider()
        df_f = pd.merge(df_e, df_p, on="Nome")
        cols = st.columns(4)
        for i, r in df_f.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="product-card"><span class="badge">{r["Categoria"]}</span><h4>{r["Nome"]}</h4><p>Estoque: <b>{int(r["Estoque_Total_Un"])}</b> un</p></div>', unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2 INTEGRAL) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Escolha o Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria da Bebida", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                st.info(f"Camada {cam_at} detectada. Layout automático: {atrav} atravessados e {frent} de frente.")
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
                        if st.button(f"BAIXA\n{r['Bebida']}\n(+{r['Avulsos']} avs)", key=r['ID']):
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (12 + r['Avulsos'])
                            df_e.to_csv(DB_FILES["est"], index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (ROMARINHO, COCA 1L, COCA 2L, TROCA EMPRESA E ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores & Estorno", "📦 Pátio (Vazios)", "🚚 Troca Empresa"])
        
        with t1:
            st.subheader("Registrar Nova Dívida")
            with st.form("divida"):
                cli, vas, q = st.text_input("Nome do Cliente").upper(), st.selectbox("Tipo de Casco", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Quantidade", 1)
                if st.form_submit_button("Salvar Dívida"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, vas, q, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            st.divider()
            st.subheader("Lista de Pendentes")
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"⚠️ **{r['Cliente']}** deve {int(r['Quantidade'])} un de {r['Vasilhame']}")
                if c2.button("BAIXA", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

            with st.expander("📜 Histórico de Baixas (Botão de Estorno)"):
                for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Recebido por: {r['QuemBaixou']})")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.at[i, 'QuemBaixou'] = ""
                        df_cas.to_csv(DB_FILES["cas"], index=False)
                        df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                        df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with t2:
            st.subheader("Controle Físico do Pátio")
            for _, r in df_patio.iterrows():
                st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} vazios disponíveis")

        with t3:
            st.subheader("🚚 Troca com Empresa (Saída do Pátio)")
            with st.form("troca_emp"):
                emp = st.text_input("Nome da Empresa / Caminhão").upper()
                v_tipo = st.selectbox("Vasilhame Levado", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"])
                v_qtd = st.number_input("Qtd de Engradados/Cascos", 1)
                if st.form_submit_button("Confirmar Saída"):
                    if df_patio.loc[df_patio['Vasilhame'] == v_tipo, 'Total_Vazio'].values[0] >= v_qtd:
                        df_patio.loc[df_patio['Vasilhame'] == v_tipo, 'Total_Vazio'] -= v_qtd
                        df_patio.to_csv(DB_FILES["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), emp, v_tipo, v_qtd, "TROCA_EMPRESA", n_logado]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False)
                        st.success(f"Saída de {v_qtd} {v_tipo} para {emp} registrada!"); st.rerun()
                    else: st.error("Saldo insuficiente no pátio.")

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Itens")
        ta1, ta2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with ta1:
            with st.form("p"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())))), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar Produto"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
            st.divider()
            p_rem = st.selectbox("Excluir Produto", df_p['Nome'].tolist())
            if st.button("REMOVER DEFINITIVAMENTE", type="primary"):
                df_p[df_p['Nome'] != p_rem].to_csv(DB_FILES["prod"], index=False)
                df_e[df_e['Nome'] != p_rem].to_csv(DB_FILES["est"], index=False); st.rerun()
        with ta2:
            nc = st.text_input("Nova Categoria")
            if st.button("Salvar Categoria"):
                pd.concat([df_cat, pd.DataFrame([[nc]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist Operacional")
        if is_adm:
            with st.form("t"):
                d, tp, dt = st.text_input("Descrição da Tarefa"), st.selectbox("Tipo", ["Diária", "Data Específica"]), st.date_input("Data")
                if st.form_submit_button("Agendar"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", d, "PENDENTE", tp, str(dt)]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        hj = datetime.now().strftime("%Y-%m-%d")
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            if r['Tipo'] == "Diária" or r['DataProg'] == hj:
                st.info(f"🔹 {r['Tarefa']}")
                if st.button("FEITO", key=f"t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Gestão de Equipe")
        if is_adm:
            with st.form("u"):
                li, ni, si, ai = st.text_input("Usuário de Login"), st.text_input("Nome Completo"), st.text_input("Senha"), st.selectbox("Administrador?", ["NÃO", "SIM"])
                if st.form_submit_button("Adicionar"):
                    pd.concat([df_usr, pd.DataFrame([[li, ni, si, ai, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        st.divider()
        st.subheader("Trocar Foto de Perfil")
        f = st.file_uploader("Subir Foto")
        if st.button("Salvar Minha Foto") and f:
            img = Image.open(f).convert("RGB"); img.thumbnail((300, 300)); b = io.BytesIO(); img.save(b, format="PNG")
            df_usr.loc[df_usr['user'] == u_logado, 'foto'] = base64.b64encode(b.getvalue()).decode()
            df_usr.to_csv(DB_FILES["usr"], index=False); st.rerun()
