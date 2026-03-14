import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_PRODUTOS = "produtos_lista_v8.csv"
DB_ESTOQUE = "estoque_movimentacao_v8.csv"
PILAR_ESTRUTURA = "estrutura_pilares_v8.csv"
USERS_FILE = "usuarios_v8.csv"
LOG_FILE = "historico_v8.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_PRODUTOS):
        # Aqui não guardamos mais quantidades, apenas a regra do produto
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
    menu_opcoes = ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastrar Novo Produto"]
    if sou_admin:
        menu_opcoes += ["📜 Histórico (Adm)", "🍶 Cascos", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CADASTRAR NOVO PRODUTO (SÓ NOME E CATEGORIA) ---
    if menu == "✨ Cadastrar Novo Produto":
        st.title("✨ Cadastro de Produtos")
        st.info("Apenas registre o nome e a categoria. A contagem de fardos é feita na aba 'Entrada de Estoque'.")
        
        with st.form("form_novo_produto"):
            cat = st.selectbox("Categoria", ["Refrigerante", "Romarinho", "Cerveja Lata", "Long Neck", "Outros"])
            nome_novo = st.text_input("Nome da Bebida (Ex: COCA COLA 2L)").upper()
            
            # Unidades padrão por volume (oculto na interface de estoque, mas salvo como regra)
            if cat == "Romarinho": padrao = 24
            elif cat == "Long Neck": padrao = 24
            elif cat == "Cerveja Lata": padrao = 12
            else: padrao = 6 # Refrigerante
            
            if st.form_submit_button("Cadastrar Produto"):
                if nome_novo:
                    df_p = pd.read_csv(DB_PRODUTOS)
                    if nome_novo in df_p['Nome'].values:
                        st.error("Esta bebida já está cadastrada!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[cat, nome_novo, padrao]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                        # Inicia o saldo de estoque zerado para esse novo nome
                        df_e = pd.read_csv(DB_ESTOQUE)
                        pd.concat([df_e, pd.DataFrame([[nome_novo, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                        st.success(f"O produto {nome_novo} foi criado! Agora vá em 'Entrada de Estoque' para colocar as quantidades.")
                        st.rerun()

    # --- ABA: ENTRADA DE ESTOQUE (ONDE DEFINE QUANTOS FARDOS/ENGRADADOS TEM) ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Lançar Quantidades em Estoque")
        df_prod = pd.read_csv(DB_PRODUTOS)
        
        if df_prod.empty:
            st.warning("⚠️ Você precisa cadastrar o nome da bebida primeiro na aba 'Cadastrar Novo Produto'.")
        else:
            with st.form("form_entrada"):
                # Filtro por categoria para facilitar a busca
                filtro_cat = st.selectbox("Filtrar por Categoria", ["Todas"] + df_prod['Categoria'].unique().tolist())
                
                if filtro_cat == "Todas":
                    lista_nomes = df_prod['Nome'].unique()
                else:
                    lista_nomes = df_prod[df_prod['Categoria'] == filtro_cat]['Nome'].unique()
                
                bebida_sel = st.selectbox("Selecione o Produto", lista_nomes)
                info = df_prod[df_prod['Nome'] == bebida_sel].iloc[0]
                
                label_vol = "Engradado" if info['Categoria'] == "Romarinho" else "Fardo"
                st.write(f"Regra: 1 {label_vol} de {bebida_sel} contém **{info['Un_por_Volume']} unidades**.")
                
                c1, c2 = st.columns(2)
                fardos = c1.number_input(f"Qtd de {label_vol}s FECHADOS", min_value=0, step=1)
                soltas = c2.number_input("Unidades SOLTAS", min_value=0, step=1)
                
                if st.form_submit_button("Atualizar Saldo de Estoque"):
                    total_un = (fardos * info['Un_por_Volume']) + soltas
                    df_e = pd.read_csv(DB_ESTOQUE)
                    df_e.loc[df_e['Nome'] == bebida_sel, 'Estoque_Total_Un'] = total_un
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success(f"Estoque de {bebida_sel} atualizado com sucesso!")
                    st.rerun()
            
            st.subheader("📋 Saldo Geral no Sistema")
            df_e_ver = pd.read_csv(DB_ESTOQUE)
            df_resumo = pd.merge(df_e_ver, df_prod, on="Nome")
            st.dataframe(df_resumo[['Categoria', 'Nome', 'Estoque_Total_Un']], use_container_width=True)

    # --- ABA: GESTÃO DE PILARES (TRAVA AUTOMÁTICA) ---
    elif menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Montagem de Pilares")
        df_prod = pd.read_csv(DB_PRODUTOS)
        df_e = pd.read_csv(DB_ESTOQUE)
        df_pilar = pd.read_csv(PILAR_ESTRUTURA)
        
        # Só mostra no pilar o que é Refrigerante e tem pelo menos 1 fardo
        df_m = pd.merge(df_prod, df_e, on="Nome")
        refri_ok = df_m[(df_m['Categoria'] == "Refrigerante") & (df_m['Estoque_Total_Un'] >= df_m['Un_por_Volume'])]
        lista_refri = ["Vazio"] + refri_ok['Nome'].unique().tolist()
        
        nome_p = st.text_input("NOME DO PILAR").upper()
        if nome_p:
            camada = 1 if df_pilar[df_pilar['NomePilar']==nome_p].empty else df_pilar[df_pilar['NomePilar']==nome_p]['Camada'].max() + 1
            st.subheader(f"Camada {camada}")
            
            col_atras = st.columns(3)
            p1 = col_atras[0].selectbox("Pos 1", lista_refri)
            p2 = col_atras[1].selectbox("Pos 2", lista_refri)
            p3 = col_atras[2].selectbox("Pos 3", lista_refri)
            
            col_frente = st.columns(2)
            p4 = col_frente[0].selectbox("Pos 4", lista_refri)
            p5 = col_frente[1].selectbox("Pos 5", lista_refri)

            if st.button("💾 Salvar Arrumação"):
                escolhas = {1:p1, 2:p2, 3:p3, 4:p4, 5:p5}
                novos = []
                for pos, beb in escolhas.items():
                    if beb != "Vazio":
                        novos.append([nome_p, camada, pos, beb])
                        # Baixa automática
                        un_f = df_prod[df_prod['Nome'] == beb]['Un_por_Volume'].values[0]
                        df_e.loc[df_e['Nome'] == beb, 'Estoque_Total_Un'] -= un_f
                
                if novos:
                    pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    st.success("Arrumação salva e fardos retirados do estoque!")
                    st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
