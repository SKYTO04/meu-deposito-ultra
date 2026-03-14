import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão v57", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v57) ---
DB_PRODUTOS = "produtos_v57.csv"
DB_ESTOQUE = "estoque_v57.csv"
PILAR_ESTRUTURA = "pilares_v57.csv"
USERS_FILE = "usuarios_v57.csv"
LOG_FILE = "historico_v57.csv"
CASCOS_FILE = "cascos_v57.csv"

def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone']).to_csv(USERS_FILE, index=False)
    
    arquivos_padrao = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
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
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login"):
        u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            check = df_users[(df_users['user'] == u) & (df_users['senha'].astype(str) == s)]
            if not check.empty:
                st.session_state.update({'autenticado': True, 'name': check['nome'].values[0], 'is_admin': check['is_admin'].values[0] == 'SIM'})
                registrar_log(st.session_state['name'], "Login Realizado")
                st.rerun()
            else: st.error("Acesso Negado")
else:
    nome_logado, sou_admin = st.session_state['name'], st.session_state['is_admin']
    
    menu_options = ["🏗️ Gestão de Pilares", "🍻 Gestão Romarinho", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin: menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    menu = st.sidebar.radio("Navegação", menu_options)
    
    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()

    df_prod, df_e, df_pilar, df_cascos = pd.read_csv(DB_PRODUTOS), pd.read_csv(DB_ESTOQUE), pd.read_csv(PILAR_ESTRUTURA), pd.read_csv(CASCOS_FILE)

    # --- ABA: PILARES ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Pilares (Refrigerantes)")
        with st.expander("🆕 Nova Camada"):
            pilares = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            alvo = st.selectbox("Pilar", pilares)
            np = st.text_input("Nome").upper() if alvo == "+ NOVO PILAR" else alvo
            if np:
                dados_p = df_pilar[df_pilar['NomePilar'] == np]
                cam = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                inv = (cam % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                bebidas_lista = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                b, a = {}, {}
                c1, c2 = st.columns(2)
                with c1:
                    for i in range(at):
                        pos = i+1
                        b[pos] = st.selectbox(f"Bebida P{pos}", bebidas_lista, key=f"b{pos}{np}{cam}")
                        a[pos] = st.number_input(f"Av P{pos}", 0, key=f"a{pos}{np}{cam}")
                with c2:
                    for i in range(fr):
                        pos = at+i+1
                        b[pos] = st.selectbox(f"Bebida P{pos}", bebidas_lista, key=f"b{pos}{np}{cam}")
                        a[pos] = st.number_input(f"Av P{pos}", 0, key=f"a{pos}{np}{cam}")
                if st.button("💾 Salvar Camada"):
                    regs = [[f"{np}_{cam}_{p}_{datetime.now().strftime('%S')}", np, cam, p, beb, a[p]] for p, beb in b.items() if beb != "Vazio"]
                    if regs:
                        pd.concat([df_pilar, pd.DataFrame(regs, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: Criou Camada {cam} no {np}")
                        st.rerun()

        for p_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {p_nome}", expanded=True):
                for c in sorted(df_pilar[df_pilar['NomePilar'] == p_nome]['Camada'].unique(), reverse=True):
                    st.write(f"**Camada {c}**")
                    d_c = df_pilar[(df_pilar['NomePilar'] == p_nome) & (df_pilar['Camada'] == c)]
                    cols = st.columns(5)
                    for _, r in d_c.iterrows():
                        with cols[int(r['Posicao'])-1]:
                            st.info(f"{r['Bebida']}\n+{r['Avulsos']} Av")
                            if st.button("RETIRAR", key=f"rt_{r['ID']}"):
                                q, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (q + r['Avulsos'])
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                registrar_log(nome_logado, f"RETIRADA: Pilar {p_nome} - {r['Bebida']}")
                                st.rerun()

    # --- ABA: ROMARINHO ---
    elif menu == "🍻 Gestão Romarinho":
        st.title("🍻 Romarinhos")
        df_r = df_prod[df_prod['Categoria'] == "Romarinho"]
        for _, row in df_r.iterrows():
            est = df_e[df_e['Nome'] == row['Nome']]['Estoque_Total_Un'].values[0]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.subheader(row['Nome'])
            c2.metric("Estoque", f"{est//24} Eng | {est%24} un")
            if c3.button(f"➖ ENGRADADO", key=f"e_{row['Nome']}"):
                if est >= 24:
                    df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"SAÍDA: 1 Engradado {row['Nome']}")
                    st.rerun()
            if c4.button(f"➖ UNIDADE", key=f"u_{row['Nome']}"):
                if est >= 1:
                    df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"SAÍDA: 1 Avulso {row['Nome']}")
                    st.rerun()
        st.write("---")

    # --- ABA: ENTRADA ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada")
        if not df_prod.empty:
            p_s = st.selectbox("Produto", df_prod['Nome'].unique())
            un, t = obter_dados_categoria(p_s, df_prod)
            with st.form("ent"):
                st.info(f"Padrão: {un} por {t}")
                c1, c2 = st.columns(2)
                qf, qa = c1.number_input(f"Qtd {t}", 0), c2.number_input("Avulsos", 0)
                if st.form_submit_button("Lançar"):
                    tot = (qf * un) + qa
                    df_e.loc[df_e['Nome'] == p_s, 'Estoque_Total_Un'] += tot
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: +{tot}un {p_s}")
                    st.rerun()
        st.dataframe(df_e)

    # --- ABA: CADASTRO ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro")
        with st.form("cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc, fn, fp = c1.selectbox("Cat", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"]), c2.text_input("Nome").upper(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar") and fn != "" and fn not in df_prod['Nome'].values:
                pd.concat([df_prod, pd.DataFrame([[fc, fn, fp]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"CADASTRO: {fn}")
                st.rerun()
        for i, r in df_prod.iterrows():
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']})")
            if col2.button("🗑️", key=f"dl_{r['Nome']}"):
                df_prod[df_prod['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"REMOÇÃO: {r['Nome']}")
                st.rerun()

    # --- ABA: CASCOS (COM ESTORNO E HISTÓRICO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Cascos")
        with st.form("cas"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            fcl, fte, fva, fqt = c1.text_input("Cliente").upper(), c2.text_input("Tel"), c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "600ml"]), c4.number_input("Qtd", 1)
            if st.form_submit_button("Salvar"):
                cid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[cid, datetime.now().strftime("%d/%m %H:%M"), fcl, fte, fva, fqt, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: {fcl} deve {fqt} {fva}")
                st.rerun()

        st.subheader("⚠️ Pendentes (Quem deve)")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"**{r['Cliente']}** - {r['Quantidade']}x {r['Vasilhame']} ({r['Data']})")
            if lc2.button("RECEBER", key=f"rc_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_logado, f"CASCO: Recebido de {r['Cliente']}")
                st.rerun()

        # ÁREA DE SEGURANÇA: ESTORNO
        st.write("---")
        st.subheader("✅ Recebidos Recentemente (Para Estorno)")
        df_pagos = df_cascos[df_cascos['Status'] == "PAGO"].tail(10) # Mostra os últimos 10
        if not df_pagos.empty:
            for i, r in df_pagos.iterrows():
                ec1, ec2 = st.columns([7, 2])
                ec1.info(f"OK: {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']} (Baixa por: {r['QuemBaixou']})")
                if ec2.button("🚫 ESTORNAR", key=f"es_{r['ID']}"):
                    df_cascos.at[i, 'Status'] = "DEVE"
                    df_cascos.at[i, 'QuemBaixou'] = ""
                    df_cascos.to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_logado, f"ESTORNO: Casco de {r['Cliente']} voltou para pendente")
                    st.rerun()
        else:
            st.write("Nenhum recebimento registrado ainda.")

    # --- ADM ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Financeiro")
        df_f = pd.merge(df_e, df_prod, on='Nome')
        df_f['Total'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("Total Patrimônio", f"R$ {df_f['Total'].sum():,.2f}")
        st.dataframe(df_f)

    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico Geral (Data, Hora e Responsável)")
        st.info("Aqui você vê exatamente quem fez o quê e quando.")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Equipe")
        with st.form("eq"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Criar"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                registrar_log(nome_logado, f"EQUIPE: Criou usuário {nu}")
                st.rerun()
        st.dataframe(df_users)
