import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO (VISUAL PRESTIGE v58)
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
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (v58 - CÁLCULO DE CAPITAL E UNIDADES)
# =================================================================
DB = {
    "prod": "p_v58.csv", "est": "e_v58.csv", "pil": "pil_v58.csv",
    "usr": "u_v58.csv", "cas": "c_v58.csv", "tar": "t_v58.csv", 
    "cat": "cat_v58.csv", "patio": "pat_v58.csv", "log": "log_v58.csv"
}

COLS = {
    "prod": ['Categoria', 'Nome', 'Preco_Unitario'],
    "est": ['Nome', 'Estoque_Total_Un'],
    "pil": ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
    "cas": ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
    "tar": ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
    "cat": ['Nome'],
    "usr": ['user', 'nome', 'senha', 'is_admin', 'foto'],
    "patio": ['Vasilhame', 'Total_Vazio'],
    "log": ['DataHora', 'Usuario', 'Acao']
}

def safe_read(key):
    path = DB[key]
    c = COLS[key]
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        df = pd.DataFrame(columns=c)
        if key == "patio": df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L Retornável", 0]], columns=c)
        if key == "usr": df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=c)
        if key == "cat": df = pd.DataFrame([["ROMARINHO"], ["CERVEJA"], ["REFRIGERANTE"]], columns=c)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        for col in c:
            if col not in df.columns: df[col] = ""
        return df[c]
    except:
        return pd.DataFrame(columns=c)

def registrar_log(usuario, acao):
    now = datetime.now().strftime("%d/%m/%y %H:%M")
    try:
        df_l = safe_read("log")
        pd.concat([df_l, pd.DataFrame([[now, usuario, acao]], columns=COLS["log"])]).to_csv(DB["log"], index=False)
    except: pass

# =================================================================
# 3. LÓGICA PRINCIPAL
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u, s = st.text_input("Usuário").strip(), st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                df_u = safe_read("usr")
                try:
                    match = df_u[df_u['user'].astype(str) == str(u)]
                    if not match.empty and str(match.iloc[0]['senha']) == str(s):
                        st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                        registrar_log(u, "Entrou.")
                        st.rerun()
                    else: st.error("Acesso negado.")
                except: st.error("Erro no banco.")
else:
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio, df_log = [safe_read(k) for k in DB.keys()]
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    # --- SIDEBAR ---
    f_b64 = ""
    try:
        u_row = df_usr[df_usr['user'] == u_logado]
        if not u_row.empty: f_b64 = u_row.iloc[0]['foto'] if not pd.isna(u_row.iloc[0]['foto']) else ""
    except: pass
    src = f"data:image/png;base64,{f_b64}" if f_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{src}" class="avatar-round" width="80" height="80"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"] + (["📜 Log Geral"] if is_adm else []))
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 INÍCIO ---
    if menu == "🏠 Início":
        st.title("Painel Geral")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vazios no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        
        try: d_at = len(df_cas[df_cas['Status'] == "DEVE"])
        except: d_at = 0
        c2.metric("Dívidas Ativas", f"{d_at} un")
        
        # CÁLCULO DE DINHEIRO NO ESTOQUE
        total_dinheiro = 0
        try:
            df_merged = pd.merge(df_e, df_p, on="Nome")
            total_dinheiro = (df_merged['Estoque_Total_Un'] * df_merged['Preco_Unitario']).sum()
        except: pass
        c3.metric("Capital em Estoque", f"R$ {total_dinheiro:,.2f}")

    # --- 📦 ESTOQUE (FARDOS E AVULSOS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário Detalhado")
        cat_sel = st.selectbox("Categoria", [""] + df_cat['Nome'].tolist())
        if cat_sel:
            # Pega produtos da categoria e junta com estoque e preço
            df_lista = pd.merge(df_p[df_p['Categoria'] == cat_sel], df_e, on="Nome")
            
            with st.expander("🔄 Lançar Movimento"):
                with st.form("mov"):
                    p = st.selectbox("Produto", df_lista['Nome'].tolist())
                    t = st.radio("Tipo", ["ENTRADA (+)", "SAÍDA (-)"], horizontal=True)
                    # Lógica de lançamento por fardo ou un
                    un_ou_fardo = st.radio("Lançar em:", ["Unidades", "Fardos/Caixas"], horizontal=True)
                    q = st.number_input("Quantidade", 1)
                    
                    if st.form_submit_button("Lançar"):
                        fator = 1
                        if un_ou_fardo == "Fardos/Caixas":
                            fator = 24 if "ROMARINHO" in cat_sel.upper() else 12
                        
                        qtd_final = q * fator
                        df_e.loc[df_e['Nome'] == p, 'Estoque_Total_Un'] += (qtd_final if "ENTRADA" in t else -qtd_final)
                        df_e.to_csv(DB["est"], index=False); registrar_log(u_logado, f"Estoque {p}: {t} {qtd_final} un"); st.rerun()

            cols = st.columns(4)
            for i, r in df_lista.reset_index().iterrows():
                total_un = int(r['Estoque_Total_Un'])
                divisor = 24 if "ROMARINHO" in cat_sel.upper() else 12
                nome_caixa = "Engradados" if divisor == 24 else "Fardos"
                
                fardos = total_un // divisor
                avulsos = total_un % divisor
                
                with cols[i % 4]: 
                    st.markdown(f"""
                    <div class="product-card">
                        <h4>{r["Nome"]}</h4>
                        <p style='font-size: 18px;'><b>{fardos}</b> {nome_caixa}</p>
                        <p style='font-size: 14px;'>+ <b>{avulsos}</b> avulsos</p>
                        <hr>
                        <p style='color: #58a6ff;'>Total: {total_un} un</p>
                    </div>
                    """, unsafe_allow_html=True)

    # --- 🏗️ PILARES ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada"):
            p_sel = st.selectbox("Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_pilar:
                prods = df_p['Nome'].tolist()
                max_c = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                cam_at = int(max_c) + 1
                atrav, frent = (3, 2) if cam_at % 2 != 0 else (2, 3)
                cols_p = st.columns(5); c_data = []
                for i in range(atrav + frent):
                    with cols_p[i]:
                        b = st.selectbox(f"P{i+1}", ["Vazio"] + prods, key=f"p_{i}")
                        a = st.number_input("Avs", 0, key=f"a_{i}")
                        if b != "Vazio": c_data.append([f"P_{datetime.now().microsecond}_{i}", n_pilar, cam_at, i+1, b, a])
                if st.button("CONFIRMAR"):
                    pd.concat([df_pil, pd.DataFrame(c_data, columns=COLS["pil"])]).to_csv(DB["pil"], index=False); st.rerun()
        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                c_grid = st.columns(5)
                for _, r in df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)].iterrows():
                    with c_grid[int(r['Posicao'])-1]:
                        if st.button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                            # Baixa automática de um fardo/engradado completo
                            divisor = 24 if "ROMARINHO" in r['Bebida'].upper() else 12
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (divisor + r['Avulsos'])
                            df_e.to_csv(DB["est"], index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico", "🚚 Saída Empresa"])
        agora = datetime.now().strftime("%d/%m %H:%M")
        with t1:
            with st.form("div"):
                cli, vas, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", agora, cli, vas, q, "DEVE", ""]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()
            try:
                for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.warning(f"⚠️ **{r['Data']}** - {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                    if c2.button("BAIXA", key=f"bx_{i}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'Data'] = agora
                        df_cas.to_csv(DB["cas"], index=False); df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']; df_patio.to_csv(DB["patio"], index=False); st.rerun()
            except: pass
        with t2:
            try:
                for i, r in df_cas[df_cas['Status'] == "PAGO"].iterrows():
                    ch1, ch2 = st.columns([3, 1])
                    ch1.write(f"✅ **{r['Data']}** | {r['Cliente']} devolveu {int(r['Quantidade'])} {r['Vasilhame']} (Rec: {r['QuemBaixou']})")
                    if ch2.button("ESTORNAR", key=f"est_{i}"):
                        df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DB["cas"], index=False); df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']; df_patio.to_csv(DB["patio"], index=False); st.rerun()
            except: pass
        with t3:
            for _, r in df_patio.iterrows(): st.info(f"**{r['Vasilhame']}:** {int(r['Total_Vazio'])} no pátio")
            with st.form("saida_emp"):
                emp, v_t, v_q = st.text_input("Caminhão").upper(), st.selectbox("Vasilhame", ["Romarinho", "600ml", "Coca 1L", "Coca 2L Retornável"]), st.number_input("Qtd", 1)
                if st.form_submit_button("Confirmar Saída"):
                    idx = df_patio[df_patio['Vasilhame'] == v_t].index[0]
                    if df_patio.at[idx, 'Total_Vazio'] >= v_q:
                        df_patio.at[idx, 'Total_Vazio'] -= v_q; df_patio.to_csv(DB["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", agora, emp, v_t, v_q, "TROCA", n_logado]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()

    # --- ✨ CADASTRO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão")
        tab1, tab2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with tab1:
            with st.form("cp"):
                n, c, pr = st.text_input("Nome").upper(), st.selectbox("Categoria", df_cat['Nome'].tolist()), st.number_input("Preço Unitário", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=COLS["prod"])]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=COLS["est"])]).to_csv(DB["est"], index=False); st.rerun()
            p_exc = st.selectbox("Apagar Produto", df_p['Nome'].tolist())
            if st.button("EXCLUIR PRODUTO", type="primary"):
                df_p[df_p['Nome'] != p_exc].to_csv(DB["prod"], index=False); df_e[df_e['Nome'] != p_exc].to_csv(DB["est"], index=False); st.rerun()
        with tab2:
            nova = st.text_input("Nova Categoria").upper()
            if st.button("Criar"): pd.concat([df_cat, pd.DataFrame([[nova]], columns=COLS["cat"])]).to_csv(DB["cat"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        aba_pend, aba_conc = st.tabs(["📝 Pendentes", "✅ Concluídas"])
        with aba_pend:
            if is_adm:
                with st.form("nt"):
                    txt = st.text_input("Tarefa")
                    if st.form_submit_button("Add"): pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", txt, "PENDENTE", "DIÁRIA", ""]], columns=COLS["tar"])]).to_csv(DB["tar"], index=False); st.rerun()
            for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
                if st.button(f"OK: {r['Tarefa']}", key=f"t_{i}"):
                    df_tar.at[i, 'Status'] = "OK"; df_tar.at[i, 'DataProg'] = datetime.now().strftime("%d/%m %H:%M")
                    df_tar.to_csv(DB["tar"], index=False); registrar_log(u_logado, f"Fez: {r['Tarefa']}"); st.rerun()
        with aba_conc:
            for i, r in df_tar[df_tar['Status'] == "OK"].sort_values(by="DataProg", ascending=False).iterrows():
                st.success(f"✔️ {r['DataProg']} - {r['Tarefa']}")

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Perfil")
        st.markdown(f'<div class="profile-card"><img src="{src}" width="150" class="avatar-round"><h3>{n_logado}</h3></div>', unsafe_allow_html=True)
        f = st.file_uploader("Trocar foto")
        if st.button("Salvar") and f:
            img = Image.open(f).convert("RGB"); img.thumbnail((300, 300)); buf = io.BytesIO(); img.save(buf, format="PNG")
            df_usr_fix = safe_read("usr") 
            df_usr_fix.loc[df_usr_fix['user'] == u_logado, 'foto'] = base64.b64encode(buf.getvalue()).decode()
            df_usr_fix.to_csv(DB["usr"], index=False); st.rerun()
        if is_adm:
            st.divider(); st.subheader("Membros")
            with st.form("nu"):
                lu, ln, ls, la = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Admin?", ["NÃO", "SIM"])
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_usr, pd.DataFrame([[lu, ln, ls, la, ""]], columns=COLS["usr"])]).to_csv(DB["usr"], index=False); st.rerun()
            st.table(df_usr[['user', 'nome', 'is_admin']])

    # --- 📜 LOG GERAL ---
    elif menu == "📜 Log Geral" and is_adm:
        st.title("📜 Log")
        st.dataframe(safe_read("log").sort_values(by="DataHora", ascending=False), use_container_width=True)
