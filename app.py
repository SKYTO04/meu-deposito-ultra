import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS ---
DB_FILE = "estoque_financeiro.csv"
USERS_FILE = "usuarios_v2.csv"
LOG_FILE = "historico_atividades.csv"
PILAR_FILE = "organizacao_pilares.csv" # Novo arquivo para salvar as pilhas

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['Categoria', 'Bebida', 'Qtd', 'Fardo', 'Custo', 'Venda']).to_csv(DB_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(PILAR_FILE):
        # Armazena: Qual Pilar, Qual Bebida, Quantos Fardos, Ordem (baixo para cima)
        pd.DataFrame(columns=['Pilar', 'Bebida', 'Qtd_Fardo', 'Ordem']).to_csv(PILAR_FILE, index=False)

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
    menu = st.sidebar.radio("Navegação", ["🏗️ Mapa de Pilares", "📦 Romarinho", "🍾 Long Neck", "🔄 Movimentar/Montar Pilar", "⚙️ Configs"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: MOVIMENTAÇÃO E MONTAGEM DE PILAR ---
    if menu == "🔄 Movimentar/Montar Pilar":
        st.title("🏗️ Montagem de Pilar e Carga")
        
        df_p = pd.read_csv(PILAR_FILE)
        df_e = pd.read_csv(DB_FILE)
        
        tab1, tab2 = st.tabs(["🏗️ Montar/Adicionar ao Pilar", "❌ Resetar Pilar"])
        
        with tab1:
            with st.form("form_pilar"):
                pilar_nome = st.selectbox("Qual Pilar (Localização)?", ["Pilar A", "Pilar B", "Pilar C", "Fundo 1", "Fundo 2"])
                bebida_p = st.selectbox("Bebida", df_e['Bebida'].unique())
                qtd_f = st.number_input("Quantos Fardos/Engradados colocar em cima?", min_value=1, step=1)
                
                st.info("💡 Lembre da amarração: 2 atrás/3 frente ou 3 atrás/2 frente!")
                
                if st.form_submit_button("Adicionar ao Topo do Pilar"):
                    # Calcula ordem (pega a maior ordem atual do pilar e soma 1)
                    ordem_atual = df_p[df_p['Pilar'] == pilar_nome]['Ordem'].max()
                    nova_ordem = 1 if pd.isna(ordem_atual) else ordem_atual + 1
                    
                    novo_bloco = pd.DataFrame([[pilar_nome, bebida_p, qtd_f, nova_ordem]], columns=df_p.columns)
                    pd.concat([df_p, novo_bloco]).to_csv(PILAR_FILE, index=False)
                    
                    # Atualiza estoque geral
                    regra = df_e[df_e['Bebida'] == bebida_p].iloc[0]
                    total_un = qtd_f * int(regra['Fardo'])
                    df_e.loc[df_e['Bebida'] == bebida_p, 'Qtd'] += total_un
                    df_e.to_csv(DB_FILE, index=False)
                    
                    st.success(f"Adicionado {qtd_f} fardos de {bebida_p} no topo do {pilar_nome}!")
                    st.rerun()

        with tab2:
            st.warning("Isso remove todos os itens do pilar selecionado no sistema.")
            pilar_del = st.selectbox("Pilar para limpar", df_p['Pilar'].unique())
            if st.button("Limpar Pilar"):
                df_p = df_p[df_p['Pilar'] != pilar_del]
                df_p.to_csv(PILAR_FILE, index=False)
                st.success(f"{pilar_del} esvaziado!")
                st.rerun()

    # --- ABA: MAPA DE PILARES (VISÃO VISUAL) ---
    elif menu == "🏗️ Mapa de Pilares":
        st.title("📊 Visão Real do Estoque (Pilares)")
        df_p = pd.read_csv(PILAR_FILE)
        
        if df_p.empty:
            st.info("Nenhum pilar montado ainda.")
        else:
            pilares = df_p['Pilar'].unique()
            cols = st.columns(len(pilares))
            
            for i, p in enumerate(pilares):
                with cols[i]:
                    st.subheader(p)
                    # Pega itens do pilar e inverte a ordem (para mostrar o topo em cima)
                    itens = df_p[df_p['Pilar'] == p].sort_values(by='Ordem', ascending=False)
                    
                    for _, row in itens.iterrows():
                        # Desenha o bloco físico
                        cor = "#007bff" if "NORMAL" in row['Bebida'] else "#dc3545"
                        st.markdown(f"""
                            <div style="background-color: {cor}; padding: 10px; border: 2px solid white; border-radius: 5px; text-align: center; margin-bottom: 5px; color: white;">
                                <b>{row['Qtd_Fardo']} Fardos</b><br>{row['Bebida']}
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<div style='text-align:center; font-weight:bold;'>⬇️ CHÃO ⬇️</div>", unsafe_allow_html=True)

    # --- DEMAIS ABAS ---
    elif menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df = pd.read_csv(DB_FILE)
        for _, r in df[df['Categoria'] == 'Romarinho'].iterrows():
            st.info(f"**{r['Bebida']}** | Total: {int(r['Qtd'])} un")

    elif menu == "⚙️ Configs":
        st.title("⚙️ Cadastro")
        cat = st.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante"])
        with st.form("cad"):
            nome = st.text_input("Nome (ex: COCA NORMAL)").upper()
            fardo = st.number_input("Unidades por Fardo", value=6 if cat=="Refrigerante" else 24)
            if st.form_submit_button("Salvar"):
                df = pd.read_csv(DB_FILE)
                novo = pd.DataFrame([[cat, nome, 0, fardo, 0.0, 0.0]], columns=df.columns)
                pd.concat([df, novo]).to_csv(DB_FILE, index=False)
                st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
