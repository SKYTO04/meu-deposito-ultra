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

    # --- ABA: CONFIGS (CADASTRO E EDIÇÃO) ---
    if menu == "⚙️ Configs" and sou_admin:
        st.title("⚙️ Gestão de Produtos")
        tab_cad, tab_edit = st.tabs(["➕ Cadastrar", "✏️ Editar/Excluir"])

        with tab_cad:
            # Removido Cerveja Garrafa conforme solicitado
            categorias = ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante"]
            
            def atualizar_valores():
                c = st.session_state['nova_cat']
                if c == "Romarinho":
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
                fardo_val = st.number_input(st.session_state['txt_un'], value=st.session_state['val_un'], step=1)
                custo = st.number_input("Custo Unitário", format="%.2f")
                venda = st.number_input("Venda Unitária", format="%.2f")
                if st.form_submit_button("Salvar Produto"):
                    if nome:
                        df_e = pd.read_csv(DB_FILE)
                        novo = pd.DataFrame([[cat, "GERAL", nome, 0, fardo_val, 1, 12, custo, venda]], columns=df_e.columns)
                        pd.concat([df_e, novo]).to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"CADASTRO: {nome} ({cat})")
                        st.success(f"{nome} cadastrado!")
                        st.rerun()

        with tab_edit:
            df_edit = pd.read_csv(DB_FILE)
            if not df_edit.empty:
                prod = st.selectbox("Selecionar para Editar", df_edit['Bebida'].tolist())
                dados = df_edit[df_edit['Bebida'] == prod].iloc[0]
                with st.form("ed"):
                    n_nome = st.text_input("Nome", value=dados['Bebida']).upper()
                    n_fardo = st.number_input("Unidades por Volume", value=int(dados['Fardo']))
                    if st.form_submit_button("Atualizar"):
                        idx = df_edit[df_edit['Bebida'] == prod].index
                        df_edit.loc[idx, ['Bebida', 'Fardo']] = [n_nome, n_fardo]
                        df_edit.to_csv(DB_FILE, index=False)
                        st.rerun()

    # --- ABA: VENDAS/CARGAS (LÓGICA DE FARDO SEPARADO) ---
    elif menu == "🔄 Vendas/Cargas":
        st.title("🔄 Movimentação de Estoque")
        df_e = pd.read_csv(DB_FILE)
        if not df_e.empty:
            with st.form("mov_facil"):
                item = st.selectbox("Bebida", df_e['Bebida'].unique())
                op = st.radio("Ação", ["Venda", "Carga", "Quebra"], horizontal=True)
                
                # Pega a info de quanto vale o fardo desse item
                info_item = df_e[df_e['Bebida'] == item].iloc[0]
                val_fardo = int(info_item['Fardo'])
                label_vol = "Engradados" if info_item['Categoria'] == "Romarinho" else "Fardos/Caixas"

                c1, c2 = st.columns(2)
                qtd_vol = c1.number_input(f"Qtd de {label_vol}", min_value=0, step=1)
                qtd_un = c2.number_input("Unidades Avulsas", min_value=0, step=1)
                
                total_mov = (qtd_vol * val_fardo) + qtd_un
                
                st.write(f"➡️ **Total a movimentar: {total_mov} unidades**")

                if st.form_submit_button("Confirmar Movimentação"):
                    if total_mov > 0:
                        idx = df_e[df_e['Bebida'] == item].index
                        if op == "Venda": df_e.loc[idx, 'Qtd'] -= total_mov
                        elif op == "Carga": df_e.loc[idx, 'Qtd'] += total_mov
                        else: df_e.loc[idx, 'Qtd'] -= total_mov
                        
                        df_e.to_csv(DB_FILE, index=False)
                        registrar_log(nome_logado, f"{op.upper()}: {total_mov} un de {item} ({qtd_vol} vol + {qtd_un} un)")
                        st.success("Estoque Atualizado!")
                        st.rerun()
                    else:
                        st.error("Coloque uma quantidade!")

    # --- ABAS DE ESTOQUE ---
    elif menu == "📦 Romarinho":
        st.title("📦 Romarinhos")
        df_r = pd.read_csv(DB_FILE)
        df_r = df_r[df_r['Categoria'] == 'Romarinho']
        for _, r in df_r.iterrows():
            st.info(f"**{r['Bebida']}**\n\nTotal: {int(r['Qtd'])} un | **{int(r['Qtd']//r['Fardo'])} Engradados**")

    elif menu == "🍾 Long Neck":
        st.title("🍾 Long Necks")
        df_l = pd.read_csv(DB_FILE)
        df_l = df_l[df_l['Categoria'] == 'Long Neck']
        for _, r in df_l.iterrows():
            st.info(f"**{r['Bebida']}**\n\nTotal: {int(r['Qtd'])} un | **{int(r['Qtd']//r['Fardo'])} Caixas**")

    elif menu == "🏗️ Mapa":
        st.title("🏗️ Mapa Geral")
        df_m = pd.read_csv(DB_FILE)
        st.table(df_m[['Categoria', 'Bebida', 'Qtd']])

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

elif st.session_state["authentication_status"] is False:
    st.error('Login/Senha incorretos.')
