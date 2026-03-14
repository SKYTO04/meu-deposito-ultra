import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_v10.csv"
DB_ESTOQUE = "estoque_v10.csv"
PILAR_ESTRUTURA = "pilares_v10.csv"
USERS_FILE = "usuarios_v10.csv"
LOG_FILE = "historico_v10.csv"
CASCOS_FILE = "cascos_v10.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume', 'Custo', 'Venda']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida']).to_csv(PILAR_ESTRUTURA, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Tipo', 'Qtd', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials, 'pacaembu_cookie', 'auth_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_id = st.session_state["username"]
    sou_admin = df_users[df_users['user'] == user_id]['is_admin'].values[0] == 'SIM'

    # --- 4. MENU LATERAL ---
    st.sidebar.title(f"👤 {nome_logado}")
    menu_opcoes = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Novo Produto", "🍶 Cascos"]
    if sou_admin:
        menu_opcoes += ["📜 Histórico (Adm)", "📊 Financeiro", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CADASTRAR PRODUTO ---
    if menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro de Itens")
        with st.form("f_cad"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome = st.text_input("Nome da Bebida").upper()
            padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
            c_unit = st.number_input("Custo Unitário (R$)", format="%.2f")
            v_unit = st.number_input("Venda Unitária (R$)", format="%.2f")
            
            if st.form_submit_button("Cadastrar"):
                df_p = pd.read_csv(DB_PRODUTOS)
                pd.concat([df_p, pd.DataFrame([[cat, nome, padrao, c_unit, v_unit]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                df_e = pd.read_csv(DB_ESTOQUE)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"Cadastrou: {nome}")
                st.success("Cadastrado com sucesso!")
                st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Lançar Fardos/Engradados")
        df_prod = pd.read_csv(DB_PRODUTOS)
        if not df_prod.empty:
            with st.form("f_est"):
                b_sel = st.selectbox("Bebida", df_prod['Nome'].unique())
                info = df_prod[df_prod['Nome'] == b_sel].iloc[0]
                st.write(f"Regra: 1 volume = {info['Un_por_Volume']} unidades.")
                c1, c2 = st.columns(2)
                f = c1.number_input("Fardos/Engradados Fechados", min_value=0)
                s = c2.number_input("Unidades Soltas", min_value=0)
                if st.form_submit_button("Atualizar Estoque"):
                    total = (f * info['Un_por_Volume']) + s
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == b_sel, 'Estoque_Total_Un'] = total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"Estoque {b_sel}: {f} fardos e {s} soltas")
                    st.success("Estoque Atualizado!")
                    st.rerun()
        st.subheader("Estoque Atual")
        st.dataframe(pd.read_csv(DB_ESTOQUE), use_container_width=True)

    # --- ABA: GESTÃO DE PILARES ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        
        # Filtro de trava de estoque
        df_m = pd.merge(df_prod, df_e, on="Nome")
        refri_ok = df_m[(df_m['Categoria'] == "Refrigerante") & (df_m['Estoque_Total_Un'] >= df_m['Un_por_Volume'])]
        lista_refri = ["Vazio"] + refri_ok['Nome'].unique().tolist()

        with st.expander("➕ Nova Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                cam = 1 if df_pilar[df_pilar['NomePilar']==nome_p].empty else df_pilar[df_pilar['NomePilar']==nome_p]['Camada'].max() + 1
                st.write(f"Camada {cam}")
                c_a = st.columns(3); p1=c_a[0].selectbox("P1", lista_refri); p2=c_a[1].selectbox("P2", lista_refri); p3=c_a[2].selectbox("P3", lista_refri)
                c_f = st.columns(2); p4=c_f[0].selectbox("P4", lista_refri); p5=c_f[1].selectbox("P5", lista_refri)
                
                if st.button("💾 Salvar Amarração"):
                    novos = []
                    for pos, beb in {1:p1, 2:p2, 3:p3, 4:p4, 5:p5}.items():
                        if beb != "Vazio":
                            novos.append([nome_p, cam, pos, beb])
                            df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= df_prod[df_prod['Nome']==beb]['Un_por_Volume'].values[0]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        st.rerun()

        # Visualização Visual (Aparece logo abaixo)
        st.divider()
        for np in df_pilar['NomePilar'].unique():
            st.subheader(f"📍 {np}")
            cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
            for c in cms:
                st.write(f"Camada {c}")
                d_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                g_a = st.columns(3); g_f = st.columns(2)
                for i in range(1, 6):
                    it = d_c[d_c['Posicao'] == i]
                    col = g_a[i-1] if i <= 3 else g_f[i-4]
                    if not it.empty:
                        col.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center; font-size:12px;">{it["Bebida"].values[0]}</div>', unsafe_allow_html=True)
            if st.button(f"🗑️ Desmanchar {np}"):
                df_pilar = df_pilar[df_pilar['NomePilar'] != np]
                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                st.rerun()

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        df_c = pd.read_csv(CASCOS_FILE)
        with st.form("f_casco"):
            cli, tipo, q, tel = st.text_input("Cliente"), st.selectbox("Tipo", ["Engradado","Garrafas"]), st.number_input("Qtd",1), st.text_input("Tel")
            if st.form_submit_button("Salvar"):
                pd.concat([df_c, pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"),cli,tipo,q,tel,"PENDENTE"]], columns=df_c.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        st.dataframe(df_c)

    # --- ABAS ADMIN ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Financeiro")
        df_f = pd.merge(pd.read_csv(DB_ESTOQUE), pd.read_csv(DB_PRODUTOS), on="Nome")
        inv = (df_f['Estoque_Total_Un'] * df_f['Custo']).sum()
        st.metric("Total Investido", f"R$ {inv:,.2f}")

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        st.dataframe(df_users[['user', 'nome', 'is_admin']])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
