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

    # --- ABA: CONFIGS (CORREÇÃO DA SINCRONIZAÇÃO) ---
    if menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Gestão de Produtos")
        tab_cad, tab_edit = st.tabs(["➕ Cadastrar Novo", "✏️ Editar/Excluir"])

        with tab_cad:
            # FUNÇÃO QUE FORÇA A TROCA DOS VALORES
            def reset_campos():
                c = st.session_state['cat_selector']
                if c == "Romarinho":
                    st.session_state['label_vol'] = "Engradados"
                    st.session_state['un_fixo'] = 24
                elif c == "Cerveja Lata":
                    st.session_state['label_vol'] = "Fardos"
                    st.session_state['un_fixo'] = 12
                elif c == "Refrigerante":
                    st.session_state['label_vol'] = "Fardos"
                    st.session_state['un_fixo'] = 6
                elif c == "Long Neck":
                    st.session_state['label_vol'] = "Fardos (Caixas)"
                    st.session_state['un_fixo'] = 24

            # Inicializa os estados se não existirem
            if 'label_vol' not in st.session_state:
                st.session_state['label_vol'] = "Engradados"
                st.session_state['un_fixo'] = 24

            # Seletor de Categoria com a função de reset
            cat = st.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante"], 
                               key='cat_selector', on_change=reset_campos)

            with st.form("form_cadastro_v3"):
                nome = st.text_input("Nome da Bebida").upper()
                
                col1, col2 = st.columns(2)
                # Agora o 'value' desses campos está amarrado ao session_state
                q_vol = col1.number_input(f"Qtd Inicial ({st.session_state['label_vol']})", min_value=0, step=1)
                q_un = col2.number_input("Qtd Inicial (Unidades Avulsas)", min_value=0, step=1)
                
                u_por_fardo = st.number_input(f"Unidades por {st.session_state['label_vol']}", 
                                             value=st.session_state['un_fixo'])
                
                custo = st.number_input("Custo Unitário", format="%.2f")
                venda = st.number_input("Venda Unitária", format="%.2f")
                
                total_calc = (q_vol * u_por_fardo) + q_un
                st.info(f"💡 O estoque começará com: **{total_calc} unidades**")

                if st.form_submit_button("Salvar Produto"):
                    if nome:
                        df_db = pd.read_csv(DB_FILE)
                        novo_p = pd.DataFrame([[cat, "GERAL", nome, total_calc, u_por_fardo, 1, 12, custo, venda]], columns=df_db.columns)
                        pd.concat([df_db, novo_p]).to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"CADASTRO: {nome} ({total_calc} un)")
                        st.success("Cadastrado!")
                        st.rerun()

        with tab_edit:
            df_ed = pd.read_csv(DB_FILE)
            if not df_ed.empty:
                escolha = st.selectbox("Escolha o produto", df_ed['Bebida'].tolist())
                d = df_ed[df_ed['Bebida'] == escolha].iloc[0]
                with st.form("ed_rapida"):
                    novo_n = st.text_input("Nome", value=d['Bebida']).upper()
                    novo_f = st.number_input("Unidades no Volume", value=int(d['Fardo']))
                    if st.form_submit_button("Salvar Alterações"):
                        df_ed.loc[df_ed['Bebida'] == escolha, ['Bebida', 'Fardo']] = [novo_n, novo_f]
                        df_ed.to_csv(DB_FILE, index=False)
                        st.success("Atualizado!")
                        st.rerun()

    # --- ABA: VENDAS/CARGAS (SOMA CRUZADA DE FARDO + UNIDADE) ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Movimentar Estoque")
        df_v = pd.read_csv(DB_FILE)
        if not df_v.empty:
            with st.form("mov_cruzada"):
                item_v = st.selectbox("Selecione a Bebida", df_v['Bebida'].unique())
                acao_v = st.radio("Operação", ["Venda", "Carga", "Quebra"], horizontal=True)
                
                # Busca as regras desse item
                regra = df_v[df_v['Bebida'] == item_v].iloc[0]
                v_fardo = int(regra['Fardo'])
                t_vol = "Engradado" if regra['Categoria'] == "Romarinho" else "Fardo"

                col_a, col_b = st.columns(2)
                in_vol = col_a.number_input(f"Qtd de {t_vol}s", min_value=0, step=1)
                in_un = col_b.number_input("Unidades Avulsas", min_value=0, step=1)
                
                soma_total = (in_vol * v_fardo) + in_un
                st.warning(f"Total da operação: {soma_total} unidades")

                if st.form_submit_button("Confirmar"):
                    if soma_total > 0:
                        idx = df_v[df_v['Bebida'] == item_v].index
                        if acao_v == "Carga": df_v.loc[idx, 'Qtd'] += soma_total
                        else: df_v.loc[idx, 'Qtd'] -= soma_total
                        
                        df_v.to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"{acao_v.upper()}: {soma_total} un de {item_v}")
                        st.success("Estoque atualizado!")
                        st.rerun()

    # --- VISUALIZAÇÃO ---
    elif menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df_e = pd.read_csv(DB_FILE)
        for _, r in df_e[df_e['Categoria'] == 'Romarinho'].iterrows():
            st.info(f"**{r['Bebida']}** | Total: {int(r['Qtd'])} un ({int(r['Qtd']//r['Fardo'])} Eng. e {int(r['Qtd']%r['Fardo'])} un)")

    elif menu == "🍾 Long Neck":
        st.title("🍾 Long Necks")
        df_e = pd.read_csv(DB_FILE)
        for _, r in df_e[df_e['Categoria'] == 'Long Neck'].iterrows():
            st.info(f"**{r['Bebida']}** | Total: {int(r['Qtd'])} un ({int(r['Qtd']//r['Fardo'])} Caixas e {int(r['Qtd']%r['Fardo'])} un)")

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

elif st.session_state["authentication_status"] is False:
    st.error('Login incorreto.')
