import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import random

# =================================================================
# 1. ESTILO E CONFIGURAÇÃO
# =================================================================
st.set_page_config(page_title="Adega Pacaembu - Sistema Integral", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .product-card, .team-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; text-align: center;
    }
    .stock-low { border: 2px solid #ff4b4b !important; border-top: 5px solid #ff4b4b !important; }
    .profile-card {
        background: #1c2128; border: 1px solid #30363d; border-radius: 20px;
        padding: 30px; text-align: center; border-bottom: 4px solid #58a6ff;
    }
    .avatar-round { border-radius: 50%; border: 4px solid #58a6ff; object-fit: cover; margin-bottom: 15px; }
    .avatar-team { border-radius: 50%; border: 2px solid #ab7ffb; object-fit: cover; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# MANTENDO A VERSÃO QUE VOCÊ JÁ ESTÁ USANDO PARA NÃO PERDER DADOS
VERSION = "v67" 
DB = {k: f"{k}_{VERSION}.csv" for k in ["prod", "est", "pil", "usr", "cas", "tar", "cat", "patio", "log"]}

COLS = {
    "prod": ['Categoria', 'Nome', 'Preco_Unitario'],
    "est": ['Nome', 'Estoque_Total_Un'],
    "pil": ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
    "cas": ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
    "tar": ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
    "cat": ['Nome', 'Unidades_Fardo'],
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
        if key == "cat": df = pd.DataFrame([["ROMARINHO", 24], ["CERVEJA LATA", 12], ["REFRI 2L", 6]], columns=c)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        for col in c:
            if col not in df.columns: df[col] = 12 if col == 'Unidades_Fardo' else ""
        return df[c]
    except: return pd.DataFrame(columns=c)

# --- LOGIN E CARREGAMENTO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio, df_log = [safe_read(k) for k in ["prod", "est", "pil", "cas", "usr", "tar", "cat", "patio", "log"]]

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login"):
            u, s = st.text_input("Usuário").strip(), st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR"):
                match = df_usr[df_usr['user'].astype(str) == str(u)]
                if not match.empty and str(match.iloc[0]['senha']) == str(s):
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Acesso negado.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])
    
    def get_units_by_cat(nome_cat):
        row = df_cat[df_cat['Nome'] == nome_cat]
        return int(row.iloc[0]['Unidades_Fardo']) if not row.empty else 12

    # --- 🏗️ PILARES (AMARRAÇÃO CORRIGIDA) ---
    if menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Adicionar Nova Camada"):
            p_sel = st.selectbox("Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D", "Pilar E"])
            ultima = df_pil[df_pil['NomePilar'] == p_sel]['Camada'].max()
            cam_at = 1 if pd.isna(ultima) else int(ultima + 1)
            
            # Lógica de Amarração Real
            layout = [3, 2] if cam_at % 2 != 0 else [2, 3]
            st.info(f"Camada {cam_at}: {'3 Frente / 2 Trás' if cam_at % 2 != 0 else '2 Frente / 3 Trás (Amarração)'}")
            
            prods = ["Vazio"] + df_p['Nome'].tolist()
            c_data = []
            col1, col2 = st.columns(2)
            with col1:
                st.write("🚚 Frente")
                for i in range(layout[0]):
                    b = st.selectbox(f"Posição F{i+1}", prods, key=f"f_{i}")
                    av = st.number_input(f"Avulsos F{i+1}", 0, key=f"af_{i}")
                    if b != "Vazio": c_data.append([f"P_{random.randint(0,99999)}", p_sel, cam_at, f"F{i+1}", b, av])
            with col2:
                st.write("📦 Trás")
                for i in range(layout[1]):
                    b = st.selectbox(f"Posição T{i+1}", prods, key=f"t_{i}")
                    av = st.number_input(f"Avulsos T{i+1}", 0, key=f"at_{i}")
                    if b != "Vazio": c_data.append([f"P_{random.randint(0,99999)}", p_sel, cam_at, f"T{i+1}", b, av])
            
            if st.button("SALVAR CAMADA"):
                pd.concat([df_pil, pd.DataFrame(c_data, columns=COLS["pil"])]).to_csv(DB["pil"], index=False); st.rerun()

        for p in sorted(df_pil['NomePilar'].unique()):
            st.subheader(f"📍 {p}")
            for cam in sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True):
                with st.container():
                    st.write(f"**Camada {cam}**")
                    itens = df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==cam)]
                    cols = st.columns(len(itens))
                    for idx, (i, r) in enumerate(itens.iterrows()):
                        if cols[idx].button(f"BAIXA\n{r['Bebida']}\n({r['Posicao']})", key=r['ID']):
                            cat_p = df_p[df_p['Nome'] == r['Bebida']]['Categoria'].iloc[0]
                            fator = get_units_by_cat(cat_p)
                            df_e.loc[df_e['Nome']==r['Bebida'], 'Estoque_Total_Un'] -= (fator + int(r['Avulsos']))
                            df_e.to_csv(DB["est"], index=False); df_pil.drop(i).to_csv(DB["pil"], index=False); st.rerun()

    # --- 🍶 CASCOS (HISTÓRICO VOLTOU) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico", "🚚 Pátio"])
        with t1:
            with st.form("div"):
                cli, v, q = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_patio['Vasilhame'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{random.randint(0,999)}", datetime.now().strftime("%d/%m"), cli, v, q, "DEVE", ""]], columns=COLS["cas"])]).to_csv(DB["cas"], index=False); st.rerun()
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                c1, c2 = st.columns([3, 1]); c1.warning(f"⚠️ {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                if c2.button("BAIXA", key=f"bx_{i}"):
                    df_cas.loc[i, 'Status'] = "PAGO"; df_cas.loc[i, 'QuemBaixou'] = n_logado
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_cas.to_csv(DB["cas"], index=False); df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t2:
            st.write("Últimos Pagamentos:")
            for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(10).iterrows():
                c1, c2 = st.columns([3, 1]); c1.success(f"✔️ {r['Cliente']} pagou {int(r['Quantidade'])} {r['Vasilhame']} ({r['QuemBaixou']})")
                if c2.button("ESTORNAR", key=f"es_{i}"):
                    df_cas.loc[i, 'Status'] = "DEVE"; df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_cas.to_csv(DB["cas"], index=False); df_patio.to_csv(DB["patio"], index=False); st.rerun()
        with t3:
            st.write("Vazios no Pátio:"); st.table(df_patio)

    # --- TODO O RESTO IGUAL À SUA VERSÃO ---
    elif menu == "🏠 Início":
        st.title("Painel Geral")
        c1, c2 = st.columns(2)
        c1.metric("Vazios", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Dívidas", len(df_cas[df_cas['Status'] == 'DEVE']))

    elif menu == "📦 Estoque":
        st.title("📦 Estoque")
        cat_sel = st.selectbox("Categoria", [""] + df_cat['Nome'].tolist())
        if cat_sel:
            un = get_units_by_cat(cat_sel)
            df_lista = pd.merge(df_p[df_p['Categoria'] == cat_sel], df_e, on="Nome")
            with st.expander("Lançar"):
                with st.form("m"):
                    p = st.selectbox("Produto", df_lista['Nome'].tolist())
                    t = st.radio("Tipo", ["ENTRADA", "SAÍDA"])
                    modo = st.radio("Modo", [f"Fardo ({un})", "Unidade"])
                    q = st.number_input("Qtd", 1)
                    if st.form_submit_button("OK"):
                        fator = un if "Fardo" in modo else 1
                        df_e.loc[df_e['Nome']==p, 'Estoque_Total_Un'] += (q*fator if t=="ENTRADA" else -(q*fator))
                        df_e.to_csv(DB["est"], index=False); st.rerun()
            for i, r in df_lista.iterrows():
                st.write(f"**{r['Nome']}**: {int(r['Estoque_Total_Un']//un)} fardos | {int(r['Estoque_Total_Un']%un)} un")

    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("p"):
                n, c, pr = st.text_input("Produto").upper(), st.selectbox("Cat", df_cat['Nome'].tolist()), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, pr]], columns=COLS["prod"])]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=COLS["est"])]).to_csv(DB["est"], index=False); st.rerun()
        with c2:
            with st.form("ct"):
                nc, unf = st.text_input("Categoria").upper(), st.number_input("Un/Fardo", 1, 100, 12)
                if st.form_submit_button("Salvar Cat"):
                    pd.concat([df_cat, pd.DataFrame([[nc, unf]], columns=COLS["cat"])]).to_csv(DB["cat"], index=False); st.rerun()

    elif menu == "📋 Tarefas":
        st.title("📋 Tarefas")
        nt = st.text_input("Nova")
        if st.button("Add"): pd.concat([df_tar, pd.DataFrame([[f"T{random.randint(0,99)}", nt, "PENDENTE", "", ""]], columns=COLS["tar"])]).to_csv(DB["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            if st.button(f"OK: {r['Tarefa']}", key=f"tk_{i}"): df_tar.loc[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()

    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        if is_adm: st.dataframe(df_usr[['nome', 'user', 'senha']])
        if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()
