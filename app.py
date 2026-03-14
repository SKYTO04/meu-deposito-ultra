import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Depósito Pacaembu - Gestão v54", page_icon="🍻", layout="wide")

# --- 2. BANCO DE DADOS (v54) ---
DB_PRODUTOS = "produtos_v54.csv"
DB_ESTOQUE = "estoque_v54.csv"
PILAR_ESTRUTURA = "pilares_v54.csv"
USERS_FILE = "usuarios_v54.csv"
LOG_FILE = "historico_v54.csv"
CASCOS_FILE = "cascos_v54.csv"

def init_files():
    """Garante a existência de todos os arquivos e colunas necessárias"""
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

# --- FUNÇÕES DE APOIO ---
def registrar_log(user, acao):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pd.DataFrame([[data, user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    """Retorna a quantidade de unidades por fardo/engradado conforme a categoria"""
    if df_produtos.empty: return 12, "Fardo"
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# --- 3. SISTEMA DE LOGIN ---
df_users = pd.read_csv(USERS_FILE)
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Login - Depósito Pacaembu")
    with st.form("login_form"):
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            check = df_users[(df_users['user'] == u_in) & (df_users['senha'].astype(str) == s_in)]
            if not check.empty:
                st.session_state['autenticado'] = True
                st.session_state['name'] = check['nome'].values[0]
                st.session_state['is_admin'] = check['is_admin'].values[0] == 'SIM'
                registrar_log(st.session_state['name'], "Login efetuado")
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
else:
    nome_logado = st.session_state['name']
    sou_admin = st.session_state['is_admin']
    
    # --- BARRA LATERAL (MENU) ---
    st.sidebar.title(f"👤 {nome_logado}")
    
    menu_options = ["🏗️ Gestão de Pilares", "🍻 Gestão Romarinho", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if sou_admin:
        menu_options += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    menu = st.sidebar.radio("Navegação", menu_options)

    if st.sidebar.button("Sair / Logout"):
        st.session_state['autenticado'] = False
        st.rerun()

    # Carregamento dos dados
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # --- ABA: GESTÃO DE PILARES (FOCO EM REFRIGERANTE) ---
    if menu == "🏗️ Gestão de Pilares":
        st.title("🏗️ Gestão de Pilares (Foco em Coca/Refri)")
        
        with st.expander("🆕 Criar Novo Pilar ou Camada"):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_alvo = st.selectbox("Selecione o Pilar", pilares_existentes)
            nome_p = st.text_input("Nome do Pilar").upper() if pilar_alvo == "+ NOVO PILAR" else pilar_alvo
            
            if nome_p:
                dados_p = df_pilar[df_pilar['NomePilar'] == nome_p]
                cam_proxima = 1 if dados_p.empty else dados_p['Camada'].max() + 1
                
                # Regra de Amarração
                inverter = (cam_proxima % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter else (2, 3)
                
                # FILTRO: Apenas produtos da categoria Refrigerante aparecem aqui
                lista_bebidas = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                bebidas_selecionadas, avulsos_digitados = {}, {}
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("⬅️ ATRÁS")
                    for i in range(n_atras):
                        pos = i + 1
                        bebidas_selecionadas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp_{nome_p}_{cam_proxima}_{pos}")
                        avulsos_digitados[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap_{nome_p}_{cam_proxima}_{pos}")
                with c2:
                    st.write("➡️ FRENTE")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        bebidas_selecionadas[pos] = st.selectbox(f"Bebida P{pos}", lista_bebidas, key=f"bp_{nome_p}_{cam_proxima}_{pos}")
                        avulsos_digitados[pos] = st.number_input(f"Av P{pos}", 0, key=f"ap_{nome_p}_{cam_proxima}_{pos}")
                
                if st.button(f"💾 Salvar Camada no {nome_p}"):
                    novos_registros = []
                    for p, beb in bebidas_selecionadas.items():
                        if beb != "Vazio":
                            id_u = f"{nome_p}_{cam_proxima}_{p}_{datetime.now().strftime('%S')}"
                            novos_registros.append([id_u, nome_p, cam_proxima, p, beb, avulsos_digitados[p]])
                    
                    if novos_registros:
                        pd.concat([df_pilar, pd.DataFrame(novos_registros, columns=df_pilar.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_logado, f"PILAR: +Camada {cam_proxima} em {nome_p}")
                        st.rerun()

        # Listagem dos Pilares na Tela
        for pilar_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 {pilar_nome}", expanded=True):
                camadas_p = sorted(df_pilar[df_pilar['NomePilar'] == pilar_nome]['Camada'].unique(), reverse=True)
                for cam in camadas_p:
                    st.write(f"**Camada {cam}**")
                    dados_c = df_pilar[(df_pilar['NomePilar'] == pilar_nome) & (df_pilar['Camada'] == cam)]
                    cols_p = st.columns(5)
                    for _, r in dados_c.iterrows():
                        with cols_p[int(r['Posicao'])-1]:
                            st.markdown(f'<div style="background-color:#1E1E1E; border:1px solid #4CAF50; padding:10px; border-radius:10px; text-align:center;"><b>{r["Bebida"]}</b><br><span style="color:#FFD700;">+{r["Avulsos"]} Av</span></div>', unsafe_allow_html=True)
                            if st.button("RETIRAR", key=f"btn_ret_{r['ID']}"):
                                un_por_f, _ = obter_dados_categoria(r['Bebida'], df_prod)
                                total_un = un_por_f + r['Avulsos']
                                
                                # Abate no estoque central
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_un
                                df_e.to_csv(DB_ESTOQUE, index=False)
                                
                                # Remove do pilar
                                df_pilar[df_pilar['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                                
                                registrar_log(nome_logado, f"PILAR: Retirou {total_un} un de {r['Bebida']} ({pilar_nome})")
                                st.rerun()

    # --- ABA: GESTÃO ROMARINHO (NOVA E COMPLETA) ---
    elif menu == "🍻 Gestão Romarinho":
        st.title("🍻 Gestão Rápida de Romarinho")
        st.info("Aqui você visualiza e remove engradados de Romarinho (24 unidades) com um clique.")
        
        df_romarinhos = df_prod[df_prod['Categoria'] == "Romarinho"]
        if not df_romarinhos.empty:
            for _, row in df_romarinhos.iterrows():
                estoque_atual = df_e[df_e['Nome'] == row['Nome']]['Estoque_Total_Un'].values[0]
                engradados = estoque_atual // 24
                sobra = estoque_atual % 24
                
                col_n, col_m, col_b = st.columns([3, 3, 2])
                col_n.subheader(row['Nome'])
                col_m.metric("Estoque", f"{engradados} Eng. | {sobra} un")
                
                if col_b.button(f"➖ REMOVER 1 ENGRADADO", key=f"rom_rem_{row['Nome']}"):
                    if estoque_atual >= 24:
                        df_e.loc[df_e['Nome'] == row['Nome'], 'Estoque_Total_Un'] -= 24
                        df_e.to_csv(DB_ESTOQUE, index=False)
                        registrar_log(nome_logado, f"ROMARINHO: Saiu 1 engradado de {row['Nome']}")
                        st.success(f"Baixa de 24 unidades em {row['Nome']}!")
                        st.rerun()
                    else:
                        st.error("Sem unidades suficientes para 1 engradado completo!")
                st.write("---")
        else:
            st.warning("Cadastre produtos na categoria 'Romarinho' para usar esta aba.")

    # --- ABA: ENTRADA DE ESTOQUE ---
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        if not df_prod.empty:
            p_sel = st.selectbox("Escolha o Produto", df_prod['Nome'].unique())
            un_p_cat, t_cat = obter_dados_categoria(p_sel, df_prod)
            
            with st.form("form_entrada"):
                st.info(f"Categoria detectada: {t_cat} ({un_p_cat} unidades)")
                c1, c2, c3 = st.columns(3)
                f_un = c1.number_input(f"Unidades por {t_cat}", value=un_p_cat)
                f_qtd = c2.number_input(f"Qtd de {t_cat}s", 0)
                f_av = c3.number_input("Avulsos", 0)
                
                if st.form_submit_button("Lançar no Estoque"):
                    total_entrada = (f_qtd * f_un) + f_av
                    df_e.loc[df_e['Nome'] == p_sel, 'Estoque_Total_Un'] += total_entrada
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"ENTRADA: +{total_entrada}un em {p_sel}")
                    st.success(f"Adicionado {total_entrada} unidades!")
                    st.rerun()
        st.subheader("Estoque Atualizado")
        st.dataframe(df_e, use_container_width=True)

    # --- ABA: CADASTRO COM EXCLUSÃO ---
    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro de Produtos")
        with st.form("form_cadastro", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nom = c2.text_input("Nome").upper().strip()
            f_pre = c3.number_input("Preço Unitário", 0.0)
            
            if st.form_submit_button("Cadastrar Produto"):
                if f_nom != "" and f_nom not in df_prod['Nome'].values:
                    pd.concat([df_prod, pd.DataFrame([[f_cat, f_nom, f_pre]], columns=df_prod.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_logado, f"CADASTRO: Criou {f_nom}")
                    st.success(f"Produto {f_nom} cadastrado!")
                    st.rerun()
                elif f_nom in df_prod['Nome'].values:
                    st.warning("Produto já existe no sistema.")

        st.write("---")
        st.subheader("📋 Gestão de Produtos Cadastrados")
        for i, r in df_prod.iterrows():
            col1, col2, col3 = st.columns([7, 2, 1])
            col1.write(f"**{r['Nome']}** | {r['Categoria']}")
            col2.write(f"R$ {r['Preco_Unitario']:.2f}")
            if col3.button("🗑️", key=f"del_prod_{r['Nome']}"):
                df_prod[df_prod['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_logado, f"REMOÇÃO: Excluiu {r['Nome']}")
                st.rerun()

    # --- ABA: CASCOS (VASILHAMES) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames")
        with st.form("form_cascos"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cli, f_tel = c1.text_input("Nome do Cliente").upper(), c2.text_input("Telefone")
            f_vas = c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho"])
            f_qtd = c4.number_input("Qtd", 1)
            
            if st.form_submit_button("Registrar Pendência"):
                nid = f"C{datetime.now().strftime('%M%S')}"
                pd.concat([df_cascos, pd.DataFrame([[nid, datetime.now().strftime("%d/%m %H:%M"), f_cli, f_tel, f_vas, f_qtd, "DEVE", ""]], columns=df_cascos.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("⚠️ Pendentes")
        for i, r in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            lc1, lc2 = st.columns([7, 2])
            lc1.warning(f"🕒 {r['Data']} | **{r['Cliente']}** ({r['Telefone']}) - {r['Quantidade']}x {r['Vasilhame']}")
            if lc2.button("RECEBER", key=f"pay_{r['ID']}"):
                df_cascos.at[i, 'Status'] = "PAGO"
                df_cascos.at[i, 'QuemBaixou'] = nome_logado
                df_cascos.to_csv(CASCOS_FILE, index=False)
                st.rerun()

    # --- ABA: FINANCEIRO (SOMENTE ADMIN) ---
    elif menu == "📊 Financeiro" and sou_admin:
        st.title("📊 Resumo Financeiro")
        df_fin = pd.merge(df_e, df_prod, on='Nome')
        df_fin['Valor_Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
        st.metric("Patrimônio em Estoque", f"R$ {df_fin['Valor_Total'].sum():,.2f}")
        st.dataframe(df_fin, use_container_width=True)

    # --- ABA: HISTÓRICO (SOMENTE ADMIN) ---
    elif menu == "📜 Histórico (Adm)" and sou_admin:
        st.title("📜 Histórico de Atividades")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    # --- ABA: EQUIPE (SOMENTE ADMIN) ---
    elif menu == "👥 Equipe" and sou_admin:
        st.title("👥 Gestão de Equipe")
        with st.form("form_equipe"):
            u, n, s, t, a = st.columns(5)
            nu, nn, ns, nt, na = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha"), t.text_input("Tel"), a.selectbox("Admin?", ["NÃO", "SIM"])
            if st.form_submit_button("Adicionar Membro"):
                pd.concat([df_users, pd.DataFrame([[nu, nn, ns, na, nt]], columns=df_users.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_users)
