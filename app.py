import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import random

# =================================================================
# CONFIGURAÇÃO E ESTILO (v68 - PRESERVANDO DADOS)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu v68", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .pilar-container {
        background: #1c2128; border: 2px solid #30363d;
        border-radius: 15px; padding: 20px; margin-bottom: 25px;
    }
    .camada-box {
        background: #21262d; border: 1px dashed #58a6ff;
        border-radius: 10px; padding: 10px; margin: 5px 0;
    }
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 15px; text-align: center;
        border-top: 4px solid #58a6ff;
    }
    .stock-low { border-top: 4px solid #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

# Use a mesma versão que você já está usando para NÃO PERDER os produtos
VERSION = "v67" 
DB = {k: f"{k}_{VERSION}.csv" for k in ["prod", "est", "pil", "usr", "cas", "tar", "cat", "patio"]}

COLS = {
    "prod": ['Categoria', 'Nome', 'Preco_Unitario'],
    "est": ['Nome', 'Estoque_Total_Un'],
    "pil": ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
    "cas": ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
    "tar": ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg'],
    "cat": ['Nome', 'Unidades_Fardo'],
    "usr": ['user', 'nome', 'senha', 'is_admin', 'foto'],
    "patio": ['Vasilhame', 'Total_Vazio']
}

def safe_read(key):
    path = DB[key]
    if not os.path.exists(path):
        df = pd.DataFrame(columns=COLS[key])
        if key == "usr": df = pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=COLS[key])
        if key == "cat": df = pd.DataFrame([["ROMARINHO", 24], ["CERVEJA LATA", 12]], columns=COLS[key])
        if key == "patio": df = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 2L", 0]], columns=COLS[key])
        df.to_csv(path, index=False)
        return df
    return pd.read_csv(path)

# =================================================================
# LÓGICA DE NAVEGAÇÃO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [safe_read(k) for k in ["prod", "est", "pil", "cas", "usr", "tar", "cat", "patio"]]

if not st.session_state['autenticado']:
    with st.columns(3)[1]:
        st.title("💎 Login")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user_match = df_usr[(df_usr['user'] == u) & (df_usr['senha'].astype(str) == s)]
            if not user_match.empty:
                st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': user_match.iloc[0]['nome'], 'u_a': (user_match.iloc[0]['is_admin'] == 'SIM')})
                st.rerun()
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    menu = st.sidebar.radio("Menu", ["🏠 Início", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe"])

    def get_un_fardo(produto):
        try:
            categoria = df_p[df_p['Nome'] == produto]['Categoria'].iloc[0]
            return int(df_cat[df_cat['Nome'] == categoria]['Unidades_Fardo'].iloc[0])
        except: return 12

    # --- 🏗️ PILARES (AMARRAÇÃO CORRIGIDA) ---
    if menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares (Amarração)")
        
        with st.expander("🧱 Montar Nova Camada"):
            nome_p = st.selectbox("Escolha o Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D", "Pilar E"])
            # Descobrir qual a próxima camada (Amarração)
            ultima_camada = df_pil[df_pil['NomePilar'] == nome_p]['Camada'].max()
            camada_atual = 1 if pd.isna(ultima_camada) else int(ultima_camada + 1)
            
            # Lógica de Amarração: 1ª (3 frente, 2 trás), 2ª (2 frente, 3 trás)
            if camada_atual % 2 != 0:
                st.info(f"Camada {camada_atual}: Configuração 3 na frente / 2 atrás")
                layout = [3, 2]
            else:
                st.info(f"Camada {camada_atual}: Configuração 2 na frente / 3 atrás (AMARRAÇÃO)")
                layout = [2, 3]
            
            c_data = []
            prods = ["Vazio"] + df_p['Nome'].tolist()
            
            col_f, col_t = st.columns(2)
            with col_f:
                st.write("🚚 Frente")
                for i in range(layout[0]):
                    b = st.selectbox(f"Frente {i+1}", prods, key=f"f_{i}")
                    a = st.number_input(f"Avulsos F{i+1}", 0, key=f"af_{i}")
                    if b != "Vazio": c_data.append([f"PIL_{random.randint(0,999)}", nome_p, camada_atual, f"F{i+1}", b, a])
            with col_t:
                st.write("📦 Trás")
                for i in range(layout[1]):
                    b = st.selectbox(f"Trás {i+1}", prods, key=f"t_{i}")
                    a = st.number_input(f"Avulsos T{i+1}", 0, key=f"at_{i}")
                    if b != "Vazio": c_data.append([f"PIL_{random.randint(0,999)}", nome_p, camada_atual, f"T{i+1}", b, a])
            
            if st.button("✅ Confirmar Camada e Salvar"):
                df_pil = pd.concat([df_pil, pd.DataFrame(c_data, columns=COLS["pil"])])
                df_pil.to_csv(DB["pil"], index=False); st.rerun()

        # Visualização dos Pilares
        for p in sorted(df_pil['NomePilar'].unique()):
            st.markdown(f'<div class="pilar-container"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            camadas_do_pilar = sorted(df_pil[df_pil['NomePilar'] == p]['Camada'].unique(), reverse=True)
            for c in camadas_do_pilar:
                st.markdown(f'<div class="camada-box"><b>Camada {c}</b>', unsafe_allow_html=True)
                itens = df_pil[(df_pil['NomePilar'] == p) & (df_pil['Camada'] == c)]
                cols = st.columns(len(itens))
                for idx, (i, r) in enumerate(itens.iterrows()):
                    with cols[idx]:
                        if st.button(f"BAIXA\n{r['Bebida']}\n({r['Posicao']})", key=f"btn_{r['ID']}"):
                            un = get_un_fardo(r['Bebida'])
                            total_sair = un + int(r['Avulsos'])
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_sair
                            df_e.to_csv(DB["est"], index=False)
                            df_pil.drop(i).to_csv(DB["pil"], index=False); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (HISTÓRICO ATUALIZADO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Gestão de Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Devedores", "📜 Histórico de Pagos", "🚚 Saída Pátio"])
        
        with t1:
            with st.form("divida"):
                cli, vas, qtd = st.text_input("Nome do Cliente").upper(), st.selectbox("Tipo", df_patio['Vasilhame'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("Lançar Dívida"):
                    new = pd.DataFrame([[f"C{random.randint(0,999)}", datetime.now().strftime("%d/%m"), cli, vas, qtd, "DEVE", ""]], columns=COLS["cas"])
                    pd.concat([df_cas, new]).to_csv(DB["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
                c1, c2 = st.columns([4, 1])
                c1.warning(f"⚠️ {r['Cliente']} deve {int(r['Quantidade'])} {r['Vasilhame']}")
                if c2.button("RECEBER", key=f"pg_{i}"):
                    df_cas.loc[i, 'Status'] = "PAGO"
                    df_cas.loc[i, 'QuemBaixou'] = n_logado
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_cas.to_csv(DB["cas"], index=False); df_patio.to_csv(DB["patio"], index=False); st.rerun()

        with t2:
            st.write("Últimos pagamentos recebidos:")
            df_pagos = df_cas[df_cas['Status'] == "PAGO"].tail(10)
            for i, r in df_pagos.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.success(f"✔️ {r['Cliente']} entregou {int(r['Quantidade'])} {r['Vasilhame']} (Recebido por: {r['QuemBaixou']})")
                if c2.button("ESTORNAR", key=f"est_{i}"):
                    df_cas.loc[i, 'Status'] = "DEVE"
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] -= r['Quantidade']
                    df_cas.to_csv(DB["cas"], index=False); df_patio.to_csv(DB["patio"], index=False); st.rerun()

        with t3:
            st.subheader("Vazios no Pátio")
            st.table(df_patio)
            v_sai = st.selectbox("Vasilhame saindo para empresa", df_patio['Vasilhame'].tolist())
            q_sai = st.number_input("Quantidade que o caminhão levou", 1)
            if st.button("Confirmar Saída do Pátio"):
                df_patio.loc[df_patio['Vasilhame'] == v_sai, 'Total_Vazio'] -= q_sai
                df_patio.to_csv(DB["patio"], index=False); st.rerun()

    # --- (AS OUTRAS ABAS CONTINUAM IGUAIS PARA NÃO PERDER SEUS DADOS) ---
    elif menu == "🏠 Início":
        st.title(f"Bem-vindo, {n_logado}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pátio (Vazios)", f"{int(df_patio['Total_Vazio'].sum())} un")
        c2.metric("Clientes Devendo", len(df_cas[df_cas['Status'] == "DEVE"]))
        st.divider()
        st.write("Resumo de Estoque Baixo:")
        df_merged = pd.merge(df_e, df_p, on="Nome")
        for _, r in df_merged.iterrows():
            fardo = get_un_fardo(r['Nome'])
            if r['Estoque_Total_Un'] < (fardo * 2):
                st.error(f"⚠️ {r['Nome']} está com apenas {int(r['Estoque_Total_Un'])} unidades!")

    elif menu == "📦 Estoque":
        st.title("📦 Controle de Estoque")
        cat = st.selectbox("Filtrar Categoria", [""] + df_cat['Nome'].tolist())
        if cat:
            un = int(df_cat[df_cat['Nome'] == cat]['Unidades_Fardo'].iloc[0])
            prods_cat = df_p[df_p['Categoria'] == cat]
            df_exibir = pd.merge(prods_cat, df_e, on="Nome")
            
            with st.expander("➕ Entrada / ➖ Saída"):
                with st.form("mov"):
                    p_sel = st.selectbox("Produto", df_exibir['Nome'].tolist())
                    tipo = st.radio("Operação", ["Entrada (+)", "Saída (-)"])
                    modo = st.radio("Lançar como", [f"Fardo ({un}un)", "Unidade Avulsa"])
                    qtd = st.number_input("Quantidade", 1)
                    if st.form_submit_button("Lançar"):
                        fator = un if "Fardo" in modo else 1
                        val = qtd * fator if "Entrada" in tipo else -(qtd * fator)
                        df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += val
                        df_e.to_csv(DB["est"], index=False); st.rerun()
            
            grid = st.columns(4)
            for idx, r in df_exibir.iterrows():
                total = int(r['Estoque_Total_Un'])
                fds, av = total // un, total % un
                with grid[idx % 4]:
                    st.markdown(f'<div class="product-card"><b>{r["Nome"]}</b><br><h3>{fds} fds</h3><p>{av} un avulsas</p></div>', unsafe_allow_html=True)

    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro de Itens")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Novo Produto")
            with st.form("f_prod"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Categoria", df_cat['Nome'].tolist())
                p = st.number_input("Preço Unitário", 0.0)
                if st.form_submit_button("Cadastrar"):
                    pd.concat([df_p, pd.DataFrame([[c, n, p]], columns=COLS["prod"])]).to_csv(DB["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[n, 0]], columns=COLS["est"])]).to_csv(DB["est"], index=False); st.rerun()
        with c2:
            st.subheader("Nova Categoria")
            with st.form("f_cat"):
                nc = st.text_input("Nome Categoria").upper()
                unf = st.number_input("Unidades no Fardo", 1, 100, 12)
                if st.form_submit_button("Cadastrar Categoria"):
                    pd.concat([df_cat, pd.DataFrame([[nc, unf]], columns=COLS["cat"])]).to_csv(DB["cat"], index=False); st.rerun()

    elif menu == "👥 Equipe":
        st.title("👥 Equipe")
        if is_adm:
            st.write("Ver Logins/Senhas:")
            st.dataframe(df_usr[['nome', 'user', 'senha', 'is_admin']])
            with st.expander("Adicionar Membro"):
                with st.form("add_u"):
                    u_n, u_u, u_s, u_a = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha"), st.selectbox("Admin", ["NÃO", "SIM"])
                    if st.form_submit_button("Criar"):
                        pd.concat([df_usr, pd.DataFrame([[u_u, u_n, u_s, u_a, ""]], columns=COLS["usr"])]).to_csv(DB["usr"], index=False); st.rerun()

    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        nt = st.text_input("Nova Tarefa")
        if st.button("Add"):
            pd.concat([df_tar, pd.DataFrame([[f"T{random.randint(0,99)}", nt, "PENDENTE", "DIA", ""]], columns=COLS["tar"])]).to_csv(DB["tar"], index=False); st.rerun()
        for i, r in df_tar[df_tar['Status'] == "PENDENTE"].iterrows():
            if st.button(f"Concluir: {r['Tarefa']}", key=f"t_{i}"):
                df_tar.loc[i, 'Status'] = "OK"; df_tar.to_csv(DB["tar"], index=False); st.rerun()
