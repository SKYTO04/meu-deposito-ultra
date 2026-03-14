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
PILAR_ESTRUTURA = "estrutura_pilares.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['Categoria', 'Bebida', 'Qtd', 'Fardo', 'Custo', 'Venda']).to_csv(DB_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(PILAR_ESTRUTURA):
        # Nome do Pilar, Camada (1, 2...), Posicao (1-5), Bebida
        pd.DataFrame(columns=['NomePilar', 'Camada', 'Posicao', 'Bebida']).to_csv(PILAR_ESTRUTURA, index=False)

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
    menu = st.sidebar.radio("Navegação", ["🏗️ Criar/Ver Pilares", "📦 Romarinho", "🔄 Vendas/Cargas", "🍶 Cascos", "📜 Histórico", "⚙️ Configs"])
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CONSTRUTOR DE PILARES VISUAL ---
    if menu == "🏗️ Criar/Ver Pilares":
        st.title("🏗️ Construtor Visual de Pilares")
        
        df_e = pd.read_csv(DB_FILE)
        df_p = pd.read_csv(PILAR_ESTRUTURA)

        with st.expander("➕ Criar Novo Pilar ou Adicionar Camada"):
            nome_novo_pilar = st.text_input("Nome do Pilar (ex: Pilar Coca, Pilar Conquista)").upper()
            
            if nome_novo_pilar:
                # Verifica em qual camada estamos
                camadas_existentes = df_p[df_p['NomePilar'] == nome_novo_pilar]['Camada']
                camada_atual = 1 if camadas_existentes.empty else camadas_existentes.max() + 1
                
                st.subheader(f"Arrumação da {camada_atual}ª Camada")
                st.write("Selecione a bebida e clique no **+** para colocar no lugar:")
                
                bebida_selecionada = st.selectbox("Bebida para esta camada", df_e['Bebida'].unique())
                
                # Interface Visual da Amarração (3 atrás, 2 na frente ou vice-versa)
                # Vamos usar colunas para simular o espaço físico
                col1, col2, col3 = st.columns(3)
                posicoes = {}
                
                st.markdown("### Atrás")
                c1, c2, c3 = st.columns(3)
                posicoes[1] = c1.checkbox("➕ Pos 1", key="p1")
                posicoes[2] = c2.checkbox("➕ Pos 2", key="p2")
                posicoes[3] = c3.checkbox("➕ Pos 3", key="p3")
                
                st.markdown("### Frente")
                f1, f2, f3 = st.columns(3)
                posicoes[4] = f1.checkbox("➕ Pos 4", key="p4")
                posicoes[5] = f2.checkbox("➕ Pos 5", key="p5")

                if st.button("Salvar Camada no Pilar"):
                    novos_registros = []
                    for pos, marcado in posicoes.items():
                        if marcado:
                            novos_registros.append([nome_novo_pilar, camada_atual, pos, bebida_selecionada])
                    
                    if novos_registros:
                        df_novo = pd.DataFrame(novos_registros, columns=df_p.columns)
                        pd.concat([df_p, df_novo]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.success(f"Camada {camada_atual} salva!")
                        st.rerun()

        # --- EXIBIÇÃO DOS PILARES CRIADOS ---
        st.divider()
        if not df_p.empty:
            pilares_nomes = df_p['NomePilar'].unique()
            for p_nome in pilares_nomes:
                st.header(f"📍 {p_nome}")
                # Mostrar da última camada para a primeira (topo para baixo)
                camadas = sorted(df_p[df_p['NomePilar'] == p_nome]['Camada'].unique(), reverse=True)
                
                for c in camadas:
                    st.write(f"**{c}ª Camada**")
                    dados_c = df_p[(df_p['NomePilar'] == p_nome) & (df_p['Camada'] == c)]
                    
                    # Desenho visual da camada
                    grid = st.columns(5)
                    for p_idx in range(1, 6):
                        item = dados_c[dados_c['Posicao'] == p_idx]
                        with grid[p_idx-1]:
                            if not item.empty:
                                st.markdown(f"""<div style="background-color:#1E1E1E; border:1px solid #444; padding:5px; text-align:center; border-radius:5px; font-size:12px;">{item['Bebida'].values[0]}</div>""", unsafe_allow_html=True)
                            else:
                                st.markdown("""<div style="color:#333; text-align:center;">(vazio)</div>""", unsafe_allow_html=True)
                
                if st.button(f"🗑️ Desmanchar {p_nome}", key=f"del_{p_nome}"):
                    df_p = df_p[df_p['NomePilar'] != p_nome]
                    df_p.to_csv(PILAR_ESTRUTURA, index=False)
                    st.rerun()

    # --- ABA: CONFIGS (Cadastro e Nomes) ---
    elif menu == "⚙️ Configs":
        st.title("⚙️ Cadastro")
        cat = st.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante"])
        
        # Lógica automática de nomes e valores que você pediu
        label = "Engradado" if cat == "Romarinho" else "Fardo"
        valor_padrao = 24 if cat in ["Romarinho", "Long Neck"] else (12 if cat == "Cerveja Lata" else 6)
        
        with st.form("cad_bebida"):
            nome_b = st.text_input("Nome da Bebida").upper()
            u_fardo = st.number_input(f"Unidades por {label}", value=valor_padrao)
            if st.form_submit_button("Salvar"):
                df_e = pd.read_csv(DB_FILE)
                pd.concat([df_e, pd.DataFrame([[cat, nome_b, 0, u_fardo, 0.0, 0.0]], columns=df_e.columns)]).to_csv(DB_FILE, index=False)
                st.success("Cadastrado!")
                st.rerun()

    # --- MANTER AS OUTRAS ABAS (CASCOS, HISTORICO, ETC) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Cascos")
        st.dataframe(pd.read_csv(CASCOS_FILE))
    
    elif menu == "📜 Histórico":
        st.title("📜 Histórico")
        st.table(pd.read_csv(LOG_FILE).iloc[::-1])

    elif menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df_r = pd.read_csv(DB_FILE)
        st.dataframe(df_r[df_r['Categoria'] == 'Romarinho'])

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
