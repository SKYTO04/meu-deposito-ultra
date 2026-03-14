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

    # --- ABA: CONFIGS (AGORA COM LÓGICA DE ATUALIZAÇÃO REAL) ---
    if menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Gestão de Produtos")
        
        tab_cad, tab_edit = st.tabs(["➕ Cadastrar Novo", "✏️ Editar Existente"])

        with tab_cad:
            # Lógica de Automática de Valores usando Session State
            categorias = ["Romarinho", "Cerveja Garrafa", "Cerveja Lata", "Long Neck", "Refrigerante"]
            
            # Quando muda a categoria, essa função roda:
            def atualizar_valores():
                c = st.session_state['nova_cat']
                if c == "Romarinho" or c == "Cerveja Garrafa":
                    st.session_state['txt_un'] = "Unidades por Engradado"
                    st.session_state['val_un'] = 24
                elif c == "Cerveja Lata":
                    st.session_state['txt_un'] = "Unidades por Fardo"
                    st.session_state['val_un'] = 12
                elif c == "Refrigerante":
                    st.session_state['txt_un'] = "Unidades por Fardo"
                    st.session_state['val_un'] = 6
                elif c == "Long Neck":
                    st.session_state['txt_un'] = "Unidades por Caixa (4x6)"
                    st.session_state['val_un'] = 24

            if 'val_un' not in st.session_state:
                st.session_state['val_un'] = 24
                st.session_state['txt_un'] = "Unidades por Engradado"

            cat = st.selectbox("Categoria", categorias, key='nova_cat', on_change=atualizar_valores)

            with st.form("form_cad"):
                nome = st.text_input("Nome da Bebida").upper()
                # O valor padrão agora vem do Session State que muda sozinho
                fardo = st.number_input(st.session_state['txt_un'], value=st.session_state['val_un'], step=1)
                custo = st.number_input("Custo Unitário", format="%.2f")
                venda = st.number_input("Venda Unitária", format="%.2f")
                prat = st.text_input("Localização").upper()
                
                if st.form_submit_button("Salvar Produto"):
                    if nome:
                        df_e = pd.read_csv(DB_FILE)
                        novo = pd.DataFrame([[cat, prat, nome, 0, fardo, 1, 12, custo, venda]], columns=df_e.columns)
                        pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"CADASTRO: {nome} ({cat})")
                        st.success(f"Sucesso! {nome} adicionado.")
                        st.rerun()

        with tab_edit:
            st.subheader("Editar ou Excluir Produto")
            df_edit = pd.read_csv(DB_FILE)
            if not df_edit.empty:
                prod_selecionado = st.selectbox("Selecione o produto para alterar", df_edit['Bebida'].tolist())
                dados_prod = df_edit[df_edit['Bebida'] == prod_selecionado].iloc[0]
                
                with st.form("form_edicao"):
                    e_nome = st.text_input("Nome", value=dados_prod['Bebida']).upper()
                    e_qtd_fardo = st.number_input("Unidades por Volume (Fardo/Engradado)", value=int(dados_prod['Fardo']))
                    e_custo = st.number_input("Custo", value=float(dados_prod['Custo']), format="%.2f")
                    e_venda = st.number_input("Venda", value=float(dados_prod['Venda']), format="%.2f")
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Atualizar Dados"):
                        idx = df_edit[df_edit['Bebida'] == prod_selecionado].index
                        df_edit.loc[idx, ['Bebida', 'Fardo', 'Custo', 'Venda']] = [e_nome, e_qtd_fardo, e_custo, e_venda]
                        df_edit.to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"EDITOU: {prod_selecionado}")
                        st.success("Alterado!")
                        st.rerun()
                    
                    if c2.form_submit_button("❌ EXCLUIR PRODUTO"):
                        df_edit = df_edit[df_edit['Bebida'] != prod_selecionado]
                        df_edit.to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"DELETOU: {prod_selecionado}")
                        st.warning("Excluído!")
                        st.rerun()

    # --- ABAS DE VISUALIZAÇÃO (ROMARINHO E LONG NECK) ---
    elif menu == "📦 Romarinho":
        st.title("📦 Estoque Romarinhos")
        df_e = pd.read_csv(DB_FILE)
        df_r = df_e[df_e['Categoria'] == 'Romarinho']
        for _, r in df_r.iterrows():
            st.info(f"**{r['Bebida']}** | {int(r['Qtd'])} un | {int(r['Qtd']//r['Fardo'])} Engradados")

    elif menu == "🍾 Long Neck":
        st.title("🍾 Estoque Long Necks")
        df_e = pd.read_csv(DB_FILE)
        df_l = df_e[df_e['Categoria'] == 'Long Neck']
        for _, r in df_l.iterrows():
            st.info(f"**{r['Bebida']}** | {int(r['Qtd'])} un | {int(r['Qtd']//r['Fardo'])} Caixas")

    # --- ABA: VENDAS/CARGAS ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Movimentação")
        df_e = pd.read_csv(DB_FILE)
        if not df_e.empty:
            with st.form("mov"):
                item = st.selectbox("Produto", df_e['Bebida'].unique())
                op = st.radio("Ação", ["Venda", "Carga", "Quebra"], horizontal=True)
                qtd = st.number_input("Quantidade (Unidades)", min_value=1)
                if st.form_submit_button("Confirmar"):
                    idx = df_e[df_e['Bebida'] == item].index
                    if op == "Venda": df_e.loc[idx, 'Qtd'] -= qtd
                    elif op == "Carga": df_e.loc[idx, 'Qtd'] += qtd
                    else: df_e.loc[idx, 'Qtd'] -= qtd
                    df_e.to_csv(DB_FILE, index=False)
                    registrar_log(nome_logado, f"{op.upper()}: {qtd} un de {item}")
                    st.success("Estoque atualizado!")
                    st.rerun()

    # --- HISTÓRICO ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- OUTRAS ABAS ---
    elif menu == "🏗️ Mapa":
        st.title("🏗️ Mapa")
        df_m = pd.read_csv(DB_FILE)
        for _, r in df_m.iterrows(): st.write(f"📍 {r['Bebida']}: {int(r['Qtd'])} un")

elif st.session_state["authentication_status"] is False:
    st.error('Login/Senha incorretos.')
