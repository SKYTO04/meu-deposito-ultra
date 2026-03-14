import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Conveniência Pacaembu", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v44) ---
DB_PRODUTOS = "produtos_v44.csv"
DB_ESTOQUE = "estoque_v44.csv"
PILAR_ESTRUTURA = "pilares_v44.csv"
USERS_FILE = "usuarios_v44.csv"
LOG_FILE = "historico_v44.csv"
CASCOS_FILE = "cascos_v44.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM']], columns=['user', 'nome', 'senha', 'is_admin']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arquivo, colunas in arquivos_padrao.items():
        if not os.path.exists(arquivo):
            pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

init_files()

def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    if df_produtos.empty: return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# --- 3. LOGIN ---
df_users = pd.read_csv(USERS_FILE)
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            user_check = df_users[(df_users['user'] == u_in) & (df_users['senha'].astype(str) == s_in)]
            if not user_check.empty:
                st.session_state.update({'autenticado': True, 'username': u_in, 'name': user_check['nome'].values[0], 'is_admin': user_check['is_admin'].values[0] == 'SIM'})
                registrar_log(st.session_state['name'], "Fez login no sistema")
                st.rerun()
            else: st.error("Erro no login.")
else:
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']
    
    st.sidebar.title(f"👤 {nome_logado}")
    if st.sidebar.button("Sair"):
        registrar_log(nome_logado, "Saiu do sistema")
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Navegação", ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos", "📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"] if sou_admin else ["🏗️ Gestão de Pilares", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"])

    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)

    # --- PILARES (BAIXA AUTOMÁTICA) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares")
        # Parte de montar camada (igual anterior...)
        with st.expander("➕ Montar Nova Camada"):
            nome_p = st.text_input("NOME DO PILAR").upper()
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_atual = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inverter = (cam_atual % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                lista_b = ["Vazio"] + df_prod['Nome'].tolist()
                escolhas, av_in = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    st.write("--- ATRÁS ---")
                    for i in range(n_atras):
                        pos = i+1
                        escolhas[pos] = st.selectbox(f"B{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"A{pos}", 0, key=f"a{pos}{cam_atual}")
                with c2:
                    st.write("--- FRENTE ---")
                    for i in range(n_frente):
                        pos = n_atras+i+1
                        escolhas[pos] = st.selectbox(f"B{pos}", lista_b, key=f"s{pos}{cam_atual}")
                        av_in[pos] = st.number_input(f"A{pos}", 0, key=f"a{pos}{cam_atual}")
                if st.button("💾 Salvar"):
                    novos = [[f"{nome_p}_{cam_atual}_{p}_{datetime.now().strftime('%S')}", nome_p, cam_atual, p, beb, av_in[p]] for p, beb in escolhas.items() if beb != "Vazio"]
                    if novos:
                        pd.concat([df_pilar, pd.DataFrame(novos, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"Montou Camada {cam_atual} no {nome_p}")
                        st.rerun()

        for np in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {np}", expanded=True):
                cms = sorted(df_pilar[df_pilar['NomePilar'] == np]['Camada'].unique(), reverse=True)
                for c in cms:
                    st.write(f"Camada {c}")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == np) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, row in dados_c.iterrows():
                        with cols[int(row['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:5px; border-radius:5px; text-align:center;"><small>{row["Bebida"]}</small><br><b style="color:#FFD700;">+{row["Avulsos"]} Av</b></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"r{row['ID']}"):
                                q_auto, termo = obter_dados_categoria(row['Bebida'], df_prod)
                                total = q_auto + row['Avulsos']
                                # BAIXA NO ESTOQUE
                                df_e.loc[df_e['Nome'] == row['Bebida'], 'Estoque_Total_Un'] -= total
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                # REMOVE DO PILAR
                                df_pilar[df_pilar['ID'] != row['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"RETIRADA: {row['Bebida']} ({total}un) do {np}")
                                st.rerun()

    # --- ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            p_sel = st.selectbox("Produto", df_prod['Nome'].unique())
            un_auto, termo = obter_dados_categoria(p_sel, df_prod)
            with st.form("ent"):
                c1, c2 = st.columns(2)
                u_f = c1.number_input(f"Unidades por {termo.lower()}", value=un_auto)
                n_f = c1.number_input(f"Qtd {termo}s", 0)
                n_s = c2.number_input("Avulsos", 0)
                if st.form_submit_button("Confirmar Entrada"):
                    total = (n_f * u_f) + n_s
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: {total}un de {p_sel}")
                    st.rerun()
        st.dataframe(df_e)

    # --- CASCOS (COM HISTÓRICO DE QUEM RECEBEU) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        df_cascos = pd.read_csv(CASCOS_FILE)
        with st.form("add_casco"):
            c1, c2, c3 = st.columns(3)
            cli = c1.text_input("Cliente").upper()
            vas = c2.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            qtd = c3.number_input("Qtd", 1)
            if st.form_submit_button("Lançar Dívida"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), cli, vas, qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {cli} ficou devendo {qtd} {vas}")
                st.rerun()
        
        st.subheader("Pendentes")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            cc1, cc2, cc3 = st.columns([5, 2, 2])
            cc1.write(f"**{r['Cliente']}** - {r['Quantidade']}x {r['Vasilhame']} ({r['Data']})")
            if cc2.button("RECEBER", key=f"pag_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Recebeu vasilhame de {r['Cliente']}")
                st.rerun()

    # --- HISTÓRICO ADM (O CORAÇÃO DO CONTROLE) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico Geral")
        st.write("Abaixo está tudo o que aconteceu no depósito com data e hora.")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)
        
        st.subheader("Histórico de Vasilhames (Quem recebeu)")
        st.dataframe(df_cascos[df_cascos['Status'] == "PAGO"], use_container_width=True)

    # --- EQUIPE, CADASTRO E FINANCEIRO (Mantidos completos) ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad"):
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nome = c2.text_input("Nome").upper()
            prec = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Cadastrar"):
                pd.concat([df_prod, pd.DataFrame([[cat, nome, prec]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[nome, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"CADASTRO: Criou produto {nome}")
                st.rerun()
        for i, row in df_prod.iterrows():
            cc1, cc2, cc3 = st.columns([4,3,1])
            cc1.write(f"{row['Nome']} ({row['Categoria']})")
            if cc3.button("X", key=f"del_{row['Nome']}"):
                df_prod[df_prod['Nome'] != row['Nome']].to_csv(DB_PRODUTOS, index=False)
                registrar_log(nome_logado, f"EXCLUSÃO: Deletou {row['Nome']}")
                st.rerun()

    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Total em Estoque", f"R$ {df_fin['Valor_Total'].sum():,.2f}")
        st.dataframe(df_fin)

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        with st.form("user"):
            u, n, s, a = st.columns(4)
            nu, nn, ns, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                registrar_log(nome_logado, f"USUÁRIO: Criou conta para {nn}")
                st.rerun()
        st.dataframe(df_users)
