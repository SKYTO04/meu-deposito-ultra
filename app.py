import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v31) ---
DB_PRODUTOS = "produtos_v31.csv"
DB_ESTOQUE = "estoque_v31.csv"
PILAR_ESTRUTURA = "pilares_v31.csv"
USERS_FILE = "usuarios_v31.csv"
LOG_FILE = "historico_v31.csv"
CASCOS_FILE = "cascos_v31.csv"
CASCOS_HISTORICO = "cascos_historico_v31.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou'],
        CASCOS_HISTORICO: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

# --- 3. AUTENTICAÇÃO ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials, 'pacaembu_cookie', 'auth_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_logado = st.session_state["username"]
    sou_admin = df_users[df_users['user'] == user_logado]['is_admin'].values[0] == 'SIM'

    st.sidebar.title(f"👤 {nome_logado}")
    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"])
    authenticator.logout('Sair', 'sidebar')

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- ABA: GESTÃO DE PILARES (A VERSÃO QUE VOCÊ GOSTOU) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares Profissional")
        
        with st.expander("➕ Montar Nova Camada no Pilar", expanded=False):
            nome_p = st.text_input("NOME DO PILAR (Ex: Pilar A)").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Lógica de Layout (3/2 ou 2/3)
                if cam_atual == 1:
                    st.session_state[f"layout_{nome_p}"] = st.radio("Configuração de Base:", ["3 Atrás / 2 Frente", "2 Atrás / 3 Frente"], horizontal=True)
                
                layout_base = st.session_state.get(f"layout_{nome_p}", "3 Atrás / 2 Frente")
                inverter = (cam_atual % 2 == 0) if layout_base == "3 Atrás / 2 Frente" else (cam_atual % 2 != 0)
                
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                n_atras = 3 if not inverter else 2
                n_frente = 2 if not inverter else 3
                
                escolhas, av_in = {}, {}
                st.write(f"### Montando Camada **{cam_atual}**")
                
                c_atras, c_frente = st.columns(2)
                with c_atras:
                    st.markdown("--- **ATRÁS** ---")
                    for i in range(n_atras):
                        pos = i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}{nome_p}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}{nome_p}")
                
                with c_frente:
                    st.markdown("--- **FRENTE** ---")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        escolhas[pos] = st.selectbox(f"Bebida P{pos}", lista_b, key=f"s{pos}{cam_atual}{nome_p}")
                        av_in[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"a{pos}{cam_atual}{nome_p}")

                if st.button("💾 Salvar Camada no Pilar"):
                    novos_dados = []
                    for pos, beb in escolhas.items():
                        if beb != "Vazio":
                            f_id = f"{nome_p}_{cam_atual}_{pos}_{datetime.now().strftime('%H%M%S')}"
                            novos_dados.append([f_id, nome_p, cam_atual, pos, beb, av_in[pos]])
                    if novos_dados:
                        pd.concat([df_pilar, pd.DataFrame(novos_dados, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.success("Camada salva com sucesso!")
                        st.rerun()

        # Visualização dos Pilares (Cards Profissionais)
        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.markdown(f"**Camada {c}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    
                    for _, row in dados_c.iterrows():
                        p = int(row['Posicao'])
                        with cols[p-1]:
                            st.markdown(f"""
                            <div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:8px; text-align:center;">
                                <b style="color:white; font-size:13px;">{row['Bebida']}</b><br>
                                <small style="color:#FFD700;">+{row['Avulsos']} Avulsos</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("RETIRAR", key=f"btn_{row['ID']}"):
                                st.session_state[f"ask_{row['ID']}"] = True
                            
                            if st.session_state.get(f"ask_{row['ID']}", False):
                                with st.form(f"form_bx_{row['ID']}"):
                                    qtd_f = st.number_input("Unidades no Fardo?", 12)
                                    if st.form_submit_button("Confirmar Baixa"):
                                        total_baixa = qtd_f + row['Avulsos']
                                        df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total_baixa
                                        df_e.to_csv(DB_ESTOQUE, index=False)
                                        df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                        st.session_state[f"ask_{row['ID']}"] = False
                                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (FARDOS E SOLTAS) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("entrada_estoque"):
            p_sel = st.selectbox("Selecione o Produto", df_prod['Nome'].unique() if not df_prod.empty else [])
            c1, c2 = st.columns(2)
            u_fardo = c1.number_input("Unidades por Fardo", 12)
            n_fardos = c1.number_input("Quantidade de Fardos", 0)
            n_soltas = c2.number_input("Unidades Soltas (Avulsas)", 0)
            
            if st.form_submit_button("Confirmar Entrada"):
                total = (n_fardos * u_fardo) + n_soltas
                df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                df_e.to_csv(DB_ESTOQUE, index=False)
                st.success(f"Estoque de {p_sel} atualizado em +{total} un.")
                st.rerun()
        st.subheader("Saldo Atual")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO DE PRODUTOS ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro de Itens")
        with st.form("cad_novo"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox("Categoria", ["Cerveja", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome do Produto").upper()
            preco = c3.number_input("Preço Unitário (R$)", 0.0)
            if st.form_submit_button("Cadastrar"):
                if nome and nome not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[cat, nome, preco]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        st.divider()
        st.subheader("Produtos Cadastrados")
        st.dataframe(df_prod, use_container_width=True)

    # --- ABA: CASCOS ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        with st.form("novo_casco"):
            cli = st.text_input("NOME DO CLIENTE").upper()
            tipo = st.selectbox("VASILHAME", ["Coca-Cola 1L", "Coca-Cola 2L", "Engradado", "Litrinho"])
            qtd = st.number_input("QUANTIDADE", 1)
            if st.form_submit_button("Registrar Pendência"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, tipo, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()
        st.write("### 🔴 Pendências Ativas")
        st.dataframe(df_cascos[df_cascos['Status'] == "DEVE"], use_container_width=True)

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
