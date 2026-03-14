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
CASCOS_FILE = "emprestimo_cascos_v2.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', 'admin123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['Categoria', 'Prateleira', 'Bebida', 'Qtd', 'Fardo', 'Posição', 'Minimo', 'Custo', 'Venda']).to_csv(DB_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, index=False)
    if not os.path.exists(CASCOS_FILE):
        pd.DataFrame(columns=['Data', 'Nome', 'Tipo', 'Quantidade', 'Telefone', 'Status']).to_csv(CASCOS_FILE, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
credentials = {'usernames': {}}
for _, r in df_users.iterrows():
    credentials['usernames'][str(r['user'])] = {'name': str(r['nome']), 'password': str(r['senha']), 'email': ''}

authenticator = stauth.Authenticate(credentials, 'estoque_pacaembu_cookie', 'auth_pacaembu_key', 30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    nome_logado = st.session_state["name"]
    user_id = st.session_state["username"]
    user_info = df_users[df_users['user'] == user_id].iloc[0]
    sou_admin = user_info['is_admin'] == 'SIM'

    st.sidebar.markdown(f"### 👤 {nome_logado}")
    menu_opcoes = ["🏗️ Mapa", "📦 Romarinho", "🍾 Long Neck", "🔄 Vendas/Cargas", "🍶 Cascos"]
    if sou_admin: menu_opcoes += ["📜 Histórico (Adm)", "👥 Equipe", "📊 Financeiro", "⚙️ Configs"]
    menu = st.sidebar.radio("Navegação", menu_opcoes)
    authenticator.logout('Sair', 'sidebar')

    # --- ABA: CONFIGS (CADASTRO COM SOMA AUTOMÁTICA) ---
    if menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Gestão de Produtos")
        tab_cad, tab_edit = st.tabs(["➕ Cadastrar Novo", "✏️ Editar/Excluir"])

        with tab_cad:
            categorias = ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante"]
            
            def atualizar_padrao():
                c = st.session_state['nova_cat']
                if c == "Romarinho":
                    st.session_state['txt_vol'] = "Engradados"
                    st.session_state['un_por_vol'] = 24
                elif c == "Cerveja Lata":
                    st.session_state['txt_vol'] = "Fardos"
                    st.session_state['un_por_vol'] = 12
                elif c == "Refrigerante":
                    st.session_state['txt_vol'] = "Fardos"
                    st.session_state['un_por_vol'] = 6
                elif c == "Long Neck":
                    st.session_state['txt_vol'] = "Fardos (Caixas)"
                    st.session_state['un_por_vol'] = 24

            if 'un_por_vol' not in st.session_state:
                st.session_state['un_por_vol'] = 24
                st.session_state['txt_vol'] = "Engradados"

            cat = st.selectbox("Categoria", categorias, key='nova_cat', on_change=atualizar_padrao)

            with st.form("form_cad_completo"):
                nome = st.text_input("Nome da Bebida").upper()
                
                col1, col2 = st.columns(2)
                qtd_vol = col1.number_input(f"Qtd de {st.session_state['txt_vol']}", min_value=0, step=1)
                qtd_un = col2.number_input("Unidades Avulsas", min_value=0, step=1)
                
                un_fardo = st.number_input(f"Unidades por {st.session_state['txt_vol']} (Padrão)", value=st.session_state['un_por_vol'])
                
                custo = st.number_input("Custo Unitário", format="%.2f")
                venda = st.number_input("Venda Unitária", format="%.2f")
                
                total_inicial = (qtd_vol * un_fardo) + qtd_un
                st.write(f"📊 **Estoque Inicial Total: {total_inicial} unidades**")

                if st.form_submit_button("Salvar Produto"):
                    if nome:
                        df_e = pd.read_csv(DB_FILE)
                        novo = pd.DataFrame([[cat, "GERAL", nome, total_inicial, un_fardo, 1, 12, custo, venda]], columns=df_e.columns)
                        pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"CADASTRO: {nome} ({total_inicial} un)")
                        st.success(f"{nome} salvo com sucesso!")
                        st.rerun()

        with tab_edit:
            df_edit = pd.read_csv(DB_FILE)
            if not df_edit.empty:
                prod = st.selectbox("Selecione o produto", df_edit['Bebida'].tolist())
                dados = df_edit[df_edit['Bebida'] == prod].iloc[0]
                with st.form("edit_form"):
                    n_nome = st.text_input("Nome", value=dados['Bebida']).upper()
                    n_fardo = st.number_input("Unidades por Volume", value=int(dados['Fardo']))
                    if st.form_submit_button("Atualizar"):
                        idx = df_edit[df_edit['Bebida'] == prod].index
                        df_edit.loc[idx, ['Bebida', 'Fardo']] = [n_nome, n_fardo]
                        df_edit.to_csv(DB_FILE, index=False)
                        st.success("Atualizado!")
                        st.rerun()

    # --- ABA: VENDAS/CARGAS (MOVIMENTAÇÃO COM OPÇÃO DE AVULSO) ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Movimentação")
        df_e = pd.read_csv(DB_FILE)
        if not df_e.empty:
            with st.form("mov_form"):
                item = st.selectbox("Bebida", df_e['Bebida'].unique())
                op = st.radio("Ação", ["Venda", "Carga", "Quebra"], horizontal=True)
                
                dados_item = df_e[df_e['Bebida'] == item].iloc[0]
                val_fardo = int(dados_item['Fardo'])
                txt_tipo = "Engradados" if dados_item['Categoria'] == "Romarinho" else "Fardos"

                c1, c2 = st.columns(2)
                m_vol = c1.number_input(f"Qtd de {txt_tipo}", min_value=0, step=1)
                m_un = c2.number_input("Unidades Avulsas", min_value=0, step=1)
                
                total_acao = (m_vol * val_fardo) + m_un
                st.markdown(f"### Total: {total_acao} unidades")

                if st.form_submit_button("Confirmar"):
                    if total_acao > 0:
                        idx = df_e[df_e['Bebida'] == item].index
                        if op == "Venda" or op == "Quebra":
                            df_e.loc[idx, 'Qtd'] -= total_acao
                        else:
                            df_e.loc[idx, 'Qtd'] += total_acao
                        
                        df_e.to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"{op.upper()}: {total_acao} un de {item}")
                        st.success("Estoque Atualizado!")
                        st.rerun()

    # --- VISUALIZAÇÃO ---
    elif menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df_e = pd.read_csv(DB_FILE)
        for _, r in df_e[df_e['Categoria'] == 'Romarinho'].iterrows():
            st.info(f"**{r['Bebida']}** | {int(r['Qtd'])} un | {int(r['Qtd']//r['Fardo'])} Engradados e {int(r['Qtd']%r['Fardo'])} un")

    elif menu == "🍾 Long Neck":
        st.title("🍾 Long Necks")
        df_e = pd.read_csv(DB_FILE)
        for _, r in df_e[df_e['Categoria'] == 'Long Neck'].iterrows():
            st.info(f"**{r['Bebida']}** | {int(r['Qtd'])} un | {int(r['Qtd']//r['Fardo'])} Caixas e {int(r['Qtd']%r['Fardo'])} un")

elif st.session_state["authentication_status"] is False:
    st.error('Login/Senha incorretos.')
