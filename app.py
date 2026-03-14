import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_lista_v7.csv"
DB_ESTOQUE = "estoque_movimentacao_v7.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v7.csv"
USERS_FILE = "usuarios_v7.csv"
LOG_FILE = "historico_v7.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        pd.DataFrame(columns=['Categoria', 'Nome', 'Un_por_Volume']).to_csv(DB_PRODUTOS, index=False)
    if not os.path.exists(DB_ESTOQUE):
        pd.DataFrame(columns=['Nome', 'Estoque_Total_Un']).to_csv(DB_ESTOQUE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida']).to_csv(PILAR_ESTRUTURA, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)

init_files()

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha'])}

authenticator = stauth.Authenticate(credentials, 'pacaembu_cookie', 'auth_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    sou_admin = df_users[df_users['user'] == st.session_state["username"]]['is_admin'].values[0] == 'SIM'

    st.sidebar.title(f"👤 {nome_logado}")
    menu_opcoes = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Nova Bebida"]
    if sou_admin:
        menu_opcoes += ["📜 Histórico (Adm)", "🍶 Cascos", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CADASTRAR NOVA BEBIDA (Lugar Diferente) ---
    if menu == "✨ Cadastrar Nova Bebida":
        st.title("✨ Cadastro de Produtos")
        st.info("Cadastre aqui o nome da bebida e a categoria apenas UMA vez.")
        
        with st.form("form_novo_produto"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck"])
            nome_novo = st.text_input("Nome da Bebida (Ex: COCA COLA 2L)").upper()
            
            # Unidades padrão por volume
            padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
            u_vol = st.number_input("Unidades por Fardo/Engradado", value=padrao)
            
            if st.form_submit_button("Cadastrar"):
                if nome_novo:
                    df_p = pd.read_csv(DB_PRODUTOS)
                    if nome_novo in df_p['Nome'].values:
                        st.error("Esta bebida já está cadastrada!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[cat, nome_novo, u_vol]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                        # Inicia estoque com zero
                        df_e = pd.read_csv(DB_ESTOQUE)
                        pd.concat([df_e, pd.DataFrame([[nome_novo, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                        st.success(f"{nome_novo} cadastrado com sucesso!")
                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (Onde coloca fardos e unidades) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        df_prod = pd.read_csv(DB_PRODUTOS)
        
        if df_prod.empty:
            st.warning("⚠️ Cadastre primeiro as bebidas na aba 'Cadastrar Nova Bebida'.")
        else:
            with st.form("form_entrada"):
                bebida_sel = st.selectbox("Escolha a Bebida", df_prod['Nome'].unique())
                info_bebida = df_prod[df_prod['Nome'] == bebida_sel].iloc[0]
                
                st.write(f"Categoria: **{info_bebida['Categoria']}** | Fardo de: **{info_bebida['Un_por_Volume']} un**")
                
                c1, c2 = st.columns(2)
                fardos = c1.number_input("Qtd de Fardos/Engradados FECHADOS", min_value=0, step=1)
                soltas = c2.number_input("Unidades SOLTAS", min_value=0, step=1)
                
                total_entrada = (fardos * info_bebida['Un_por_Volume']) + soltas
                
                if st.form_submit_button("Atualizar Estoque"):
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == bebida_sel, 'Estoque_Total_Un'] = total_entrada
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success(f"Estoque de {bebida_sel} atualizado para {total_entrada} unidades!")
                    st.rerun()
            
            st.subheader("Resumo do Estoque Atual")
            df_e_ver = pd.read_csv(DB_ESTOQUE)
            df_final = pd.merge(df_e_ver, df_prod, on="Nome")
            st.dataframe(df_final[['Categoria', 'Nome', 'Estoque_Total_Un']], use_container_width=True)

    # --- ABA: GESTÃO DE PILARES (CONSTRUTOR VISUAL) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        
        # Unir dados para saber quem tem fardo disponível
        df_master = pd.merge(df_prod, df_e, on="Nome")
        refri_disponivel = df_master[(df_master['Categoria'] == "Refrigerante") & (df_master['Estoque_Total_Un'] >= df_master['Un_por_Volume'])]
        
        lista_refri = ["Vazio"] + refri_disponivel['Nome'].unique().tolist()
        
        nome_pilar = st.text_input("NOME DO PILAR").upper()
        if nome_pilar:
            camada = 1 if df_pilar[df_pilar['NomePilar']==nome_pilar].empty else df_pilar[df_pilar['NomePilar']==nome_pilar]['Camada'].max() + 1
            
            st.subheader(f"Arrumação da {camada}ª Camada")
            escolhas = {}
            st.write("**Atrás (3)**")
            c1, c2, c3 = st.columns(3)
            escolhas[1], escolhas[2], escolhas[3] = c1.selectbox("P1", lista_refri), c2.selectbox("P2", lista_refri), c3.selectbox("P3", lista_refri)
            
            st.write("**Frente (2)**")
            f1, f2 = st.columns(2)
            escolhas[4], escolhas[5] = f1.selectbox("P4", lista_refri), f2.selectbox("P5", lista_refri)

            if st.button("Salvar e Abater Estoque"):
                # Validação e Baixa (mesma lógica anterior)
                novos = []
                for pos, beb in escolhas.items():
                    if beb != "Vazio":
                        novos.append([nome_pilar, camada, pos, beb])
                        un_fardo = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                        df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= un_fardo
                
                if novos:
                    pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Salvo!")
                    st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
