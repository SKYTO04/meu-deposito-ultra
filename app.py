import streamlit as st
import pandas as pd
from datetime import datetime
import os

# =================================================================
# 1. CONFIGURAÇÕES INICIAIS E IDENTIDADE DO SISTEMA
# =================================================================
st.set_page_config(
    page_title="Depósito Pacaembu - Gestão v58 EXTREME", 
    page_icon="🍻", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS para melhorar a visualização dos cards nos pilares
st.markdown("""
    <style>
    .pilar-card {
        background-color: #1E1E1E;
        border: 2px solid #4CAF50;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .pilar-avulso {
        color: #FFD700;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS (ARQUIVOS CSV)
# =================================================================
DB_PRODUTOS = "produtos_v58.csv"
DB_ESTOQUE = "estoque_v58.csv"
PILAR_ESTRUTURA = "pilares_v58.csv"
USERS_FILE = "usuarios_v58.csv"
LOG_FILE = "historico_v58.csv"
CASCOS_FILE = "cascos_v58.csv"

def init_files():
    """Garante que todos os arquivos do sistema existam com suas respectivas colunas"""
    # Criação do usuário Administrador padrão caso o arquivo não exista
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone']).to_csv(USERS_FILE, index=False)
    
    # Dicionário de estruturas de cada tabela
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

# =================================================================
# 3. FUNÇÕES DE LÓGICA DE NEGÓCIO
# =================================================================
def registrar_log(user, acao):
    """Registra data, hora, usuário e a ação exata no histórico"""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    novo_log = pd.DataFrame([[agora, user, acao]], columns=['Data', 'Usuario', 'Ação'])
    novo_log.to_csv(LOG_FILE, mode='a', header=False, index=False)

def obter_dados_categoria(nome_produto, df_produtos):
    """Retorna a regra de unidades por fardo/engradado baseada na categoria"""
    if df_produtos.empty:
        return 12, "Fardo"
    
    busca = df_produtos[df_produtos['Nome'] == nome_produto]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Long Neck": return 24, "Fardo"
        if cat == "Cerveja Lata": return 12, "Fardo"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 4. SISTEMA DE AUTENTICAÇÃO (LOGIN)
# =================================================================
df_users = pd.read_csv(USERS_FILE)

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - Depósito Pacaembu")
    with st.container():
        with st.form("login_form"):
            user_input = st.text_input("Usuário")
            pass_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Sistema"):
                # Verificação de credenciais
                user_data = df_users[(df_users['user'] == user_input) & (df_users['senha'].astype(str) == pass_input)]
                if not user_data.empty:
                    st.session_state['autenticado'] = True
                    st.session_state['user_id'] = user_input
                    st.session_state['name'] = user_data['nome'].values[0]
                    st.session_state['is_admin'] = (user_data['is_admin'].values[0] == 'SIM')
                    registrar_log(st.session_state['name'], "Realizou Login no Sistema")
                    st.rerun()
                else:
                    st.error("Usuário ou Senha inválidos. Tente novamente.")
else:
    # --- VARIÁVEIS DE AMBIENTE DO USUÁRIO ---
    nome_usuario = st.session_state['name']
    eh_admin = st.session_state['is_admin']
    
    # --- MENU LATERAL DE NAVEGAÇÃO ---
    st.sidebar.title(f"👤 {nome_usuario}")
    if eh_admin:
        st.sidebar.warning("Acesso: ADMINISTRADOR")
    
    opcoes_menu = ["🏗️ Gestão de Pilares", "🍻 Gestão Romarinho", "📦 Entrada de Estoque", "✨ Cadastro de Produtos", "🍶 Cascos"]
    if eh_admin:
        opcoes_menu += ["📊 Financeiro", "📜 Histórico (Adm)", "👥 Equipe"]
    
    escolha = st.sidebar.radio("Selecione uma funcionalidade:", opcoes_menu)
    
    if st.sidebar.button("Sair (Logout)"):
        st.session_state['autenticado'] = False
        st.rerun()

    # CARREGAMENTO DOS DADOS PARA AS TELAS
    df_prod = pd.read_csv(DB_PRODUTOS)
    df_estoque = pd.read_csv(DB_ESTOQUE)
    df_pilar = pd.read_csv(PILAR_ESTRUTURA)
    df_cascos = pd.read_csv(CASCOS_FILE)

    # =================================================================
    # ABA: GESTÃO DE PILARES (FOCO EM REFRIGERANTES)
    # =================================================================
    if escolha == "🏗️ Gestão de Pilares":
        st.title("🏗️ Controle de Pilares (Refrigerantes)")
        
        with st.expander("🆕 Criar Novo Pilar ou Adicionar Camada", expanded=False):
            pilares_existentes = ["+ NOVO PILAR"] + list(df_pilar['NomePilar'].unique())
            pilar_selecionado = st.selectbox("Selecione o Pilar de Destino", pilares_existentes)
            
            nome_pilar_final = st.text_input("Nome do Pilar").upper().strip() if pilar_selecionado == "+ NOVO PILAR" else pilar_selecionado
            
            if nome_pilar_final:
                dados_desse_pilar = df_pilar[df_pilar['NomePilar'] == nome_pilar_final]
                camada_atual = 1 if dados_desse_pilar.empty else dados_desse_pilar['Camada'].max() + 1
                
                # Regra de amarração: intercala 3 atrás/2 frente com 2 atrás/3 frente
                inverter_amarracao = (camada_atual % 2 == 0)
                n_atras, n_frente = (3, 2) if not inverter_amarracao else (2, 3)
                
                # TRAVA: Somente produtos cadastrados como 'Refrigerante' aparecem aqui
                lista_refri = ["Vazio"] + df_prod[df_prod['Categoria'] == "Refrigerante"]['Nome'].tolist()
                
                form_bebidas, form_avulsos = {}, {}
                
                st.write(f"### Configurando Camada {camada_atual}")
                col_atras, col_frente = st.columns(2)
                
                with col_atras:
                    st.markdown("🔍 **POSIÇÕES DE TRÁS**")
                    for i in range(n_atras):
                        pos = i + 1
                        form_bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_refri, key=f"beb_{nome_pilar_final}_{camada_atual}_{pos}")
                        form_avulsos[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"avu_{nome_pilar_final}_{camada_atual}_{pos}")
                
                with col_frente:
                    st.markdown("🔍 **POSIÇÕES DE FRENTE**")
                    for i in range(n_frente):
                        pos = n_atras + i + 1
                        form_bebidas[pos] = st.selectbox(f"Bebida P{pos}", lista_refri, key=f"beb_{nome_pilar_final}_{camada_atual}_{pos}")
                        form_avulsos[pos] = st.number_input(f"Avulsos P{pos}", 0, key=f"avu_{nome_pilar_final}_{camada_atual}_{pos}")
                
                if st.button(f"💾 Confirmar Camada {camada_atual}"):
                    registros_novos = []
                    for p, bebida in form_bebidas.items():
                        if bebida != "Vazio":
                            id_unico = f"{nome_pilar_final}_{camada_atual}_{p}_{datetime.now().strftime('%S')}"
                            registros_novos.append([id_unico, nome_pilar_final, camada_atual, p, bebida, form_avulsos[p]])
                    
                    if registros_novos:
                        df_pilar = pd.concat([df_pilar, pd.DataFrame(registros_novos, columns=df_pilar.columns)])
                        df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                        registrar_log(nome_usuario, f"PILAR: Adicionou Camada {camada_atual} no {nome_pilar_final}")
                        st.success("Camada salva com sucesso!")
                        st.rerun()

        # Renderização Visual dos Pilares
        for p_nome in df_pilar['NomePilar'].unique():
            with st.expander(f"📍 PILAR: {p_nome}", expanded=True):
                camadas_pilar = sorted(df_pilar[df_pilar['NomePilar'] == p_nome]['Camada'].unique(), reverse=True)
                for cam in camadas_pilar:
                    st.write(f"--- Camada {cam} ---")
                    dados_camada = df_pilar[(df_pilar['NomePilar'] == p_nome) & (df_pilar['Camada'] == cam)]
                    col_visual = st.columns(5)
                    
                    for _, reg in dados_camada.iterrows():
                        with col_visual[int(reg['Posicao'])-1]:
                            st.markdown(f"""<div class="pilar-card"><b>{reg['Bebida']}</b><br>
                                        <span class="pilar-avulso">+{reg['Avulsos']} Av</span></div>""", unsafe_allow_html=True)
                            
                            if st.button("RETIRAR", key=f"ret_pilar_{reg['ID']}"):
                                q_base, _ = obter_dados_categoria(reg['Bebida'], df_prod)
                                total_unidades = q_base + reg['Avulsos']
                                
                                # Atualiza Estoque Central
                                df_estoque.loc[df_estoque['Nome'] == reg['Bebida'], 'Estoque_Total_Un'] -= total_unidades
                                df_estoque.to_csv(DB_ESTOQUE, index=False)
                                
                                # Remove do Pilar
                                df_pilar = df_pilar[df_pilar['ID'] != reg['ID']]
                                df_pilar.to_csv(PILAR_ESTRUTURA, index=False)
                                
                                registrar_log(nome_usuario, f"SAÍDA PILAR: Retirou {total_unidades}un de {reg['Bebida']} do pilar {p_nome}")
                                st.rerun()

    # =================================================================
    # ABA: GESTÃO ROMARINHO (ENGRADADO E AVULSO)
    # =================================================================
    elif escolha == "🍻 Gestão Romarinho":
        st.title("🍻 Baixa Rápida: Romarinhos")
        st.info("Aqui você controla a saída rápida de engradados (24 un) ou garrafas soltas.")
        
        df_rom_prod = df_prod[df_prod['Categoria'] == "Romarinho"]
        if not df_rom_prod.empty:
            for _, r in df_rom_prod.iterrows():
                estoque_un_total = df_estoque[df_estoque['Nome'] == r['Nome']]['Estoque_Total_Un'].values[0]
                n_engradados = estoque_un_total // 24
                n_avulsos = estoque_un_total % 24
                
                with st.container():
                    c_n, c_est, c_b1, c_b2 = st.columns([3, 3, 2, 2])
                    c_n.subheader(r['Nome'])
                    c_est.metric("Estoque Disponível", f"{n_engradados} Eng | {n_avulsos} un")
                    
                    # Botão para remover engradado cheio
                    if c_b1.button(f"➖ 1 ENGRADADO", key=f"bt_eng_{r['Nome']}"):
                        if estoque_un_total >= 24:
                            df_estoque.loc[df_estoque['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 24
                            df_estoque.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_usuario, f"ROMARINHO: Baixa de 1 Engradado (24un) de {r['Nome']}")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente para 1 engradado!")
                    
                    # Botão para remover apenas 1 unidade solta
                    if c_b2.button(f"➖ 1 UNIDADE", key=f"bt_un_{r['Nome']}"):
                        if estoque_un_total >= 1:
                            df_estoque.loc[df_estoque['Nome'] == r['Nome'], 'Estoque_Total_Un'] -= 1
                            df_estoque.to_csv(DB_ESTOQUE, index=False)
                            registrar_log(nome_usuario, f"ROMARINHO: Baixa de 1 Unidade Avulsa de {r['Nome']}")
                            st.rerun()
                        else:
                            st.error("Estoque zerado!")
                st.write("---")
        else:
            st.warning("Não existem produtos cadastrados na categoria 'Romarinho'.")

    # =================================================================
    # ABA: ENTRADA DE ESTOQUE
    # =================================================================
    elif escolha == "📦 Entrada de Estoque":
        st.title("📦 Lançamento de Entrada")
        if not df_prod.empty:
            prod_selecionado = st.selectbox("Selecione o produto recebido", df_prod['Nome'].unique())
            un_base, termo_base = obter_dados_categoria(prod_selecionado, df_prod)
            
            with st.form("form_entrada"):
                st.write(f"**Padrão Sugerido:** {un_base} unidades por {termo_base}")
                c1, c2, c3 = st.columns(3)
                f_un_por_medida = c1.number_input(f"Unidades por {termo_base}", value=un_base)
                f_qtd_medida = c2.number_input(f"Qtd de {termo_base}s", 0)
                f_avulsos_soltos = c3.number_input("Unidades Soltas", 0)
                
                if st.form_submit_button("Confirmar Entrada"):
                    total_calculado = (f_qtd_medida * f_un_por_medida) + f_avulsos_soltos
                    df_estoque.loc[df_estoque['Nome'] == prod_selecionado, 'Estoque_Total_Un'] += total_calculado
                    df_estoque.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_usuario, f"ENTRADA: +{total_calculado}un em {prod_selecionado}")
                    st.success(f"Adicionado {total_calculado} unidades ao estoque!")
                    st.rerun()
        
        st.subheader("Estoque Atualizado")
        st.dataframe(df_estoque, use_container_width=True)

    # =================================================================
    # ABA: CADASTRO DE PRODUTOS
    # =================================================================
    elif escolha == "✨ Cadastro de Produtos":
        st.title("✨ Cadastro e Manutenção")
        
        with st.form("form_novo_item", clear_on_submit=True):
            st.subheader("Novo Produto")
            col_cat, col_nom, col_pre = st.columns([2, 2, 1])
            cat_n = col_cat.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            nom_n = col_nom.text_input("Nome do Produto").upper().strip()
            pre_n = col_pre.number_input("Preço Unitário", 0.0)
            
            if st.form_submit_button("Cadastrar"):
                if nom_n != "" and nom_n not in df_prod['Nome'].values:
                    # Adiciona ao banco de produtos
                    df_prod = pd.concat([df_prod, pd.DataFrame([[cat_n, nom_n, pre_n]], columns=df_prod.columns)])
                    df_prod.to_csv(DB_PRODUTOS, index=False)
                    # Adiciona ao estoque com zero
                    df_estoque = pd.concat([df_estoque, pd.DataFrame([[nom_n, 0]], columns=df_estoque.columns)])
                    df_estoque.to_csv(DB_ESTOQUE, index=False)
                    registrar_log(nome_usuario, f"CADASTRO: Novo produto {nom_n}")
                    st.rerun()
                elif nom_n in df_prod['Nome'].values:
                    st.error("Produto já existe!")

        st.write("---")
        st.subheader("Lista de Produtos (Excluir/Gerenciar)")
        for idx, item in df_prod.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{item['Nome']}**")
            c2.write(f"*{item['Categoria']}*")
            c3.write(f"R$ {item['Preco_Unitario']:.2f}")
            if c4.button("🗑️", key=f"del_pr_{item['Nome']}"):
                df_prod = df_prod[df_prod['Nome'] != item['Nome']]
                df_prod.to_csv(DB_PRODUTOS, index=False)
                df_estoque = df_estoque[df_estoque['Nome'] != item['Nome']]
                df_estoque.to_csv(DB_ESTOQUE, index=False)
                registrar_log(nome_usuario, f"REMOÇÃO: Excluiu produto {item['Nome']}")
                st.rerun()

    # =================================================================
    # ABA: CASCOS (COM ESTORNO E HISTÓRICO DE BAIXAS)
    # =================================================================
    elif escolha == "🍶 Cascos":
        st.title("🍶 Controle de Vasilhames e Cascos")
        
        with st.form("form_casco_novo"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cli = c1.text_input("Cliente").upper()
            f_tel = c2.text_input("Telefone")
            f_vas = c3.selectbox("Tipo de Casco", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "600ml"])
            f_qtd = c4.number_input("Qtd", 1)
            
            if st.form_submit_button("Lançar Dívida"):
                c_id = f"C{datetime.now().strftime('%M%S')}"
                novo_casco = pd.DataFrame([[c_id, datetime.now().strftime("%d/%m %H:%M"), f_cli, f_tel, f_vas, f_qtd, "DEVE", ""]], columns=df_cascos.columns)
                df_cascos = pd.concat([df_cascos, novo_casco])
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_usuario, f"CASCO: Cliente {f_cli} ficou devendo {f_qtd}x {f_vas}")
                st.rerun()

        st.subheader("⚠️ Pendências (Quem está devendo)")
        for idx, row in df_cascos[df_cascos['Status'] == "DEVE"].iterrows():
            col_d1, col_d2 = st.columns([7, 2])
            col_d1.warning(f"🕒 {row['Data']} | **{row['Cliente']}** - {row['Quantidade']}x {row['Vasilhame']} ({row['Telefone']})")
            if col_d2.button("RECEBER", key=f"rec_{row['ID']}"):
                df_cascos.at[idx, 'Status'] = "PAGO"
                df_cascos.at[idx, 'QuemBaixou'] = nome_usuario
                df_cascos.to_csv(CASCOS_FILE, index=False)
                registrar_log(nome_usuario, f"CASCO: Recebido de {row['Cliente']}")
                st.rerun()

        # ÁREA DE SEGURANÇA PARA ADMIN OU OPERADOR VOLTAR ATRÁS
        st.write("---")
        st.subheader("✅ Baixas Recentes (Estorno)")
        df_pagos_recentes = df_cascos[df_cascos['Status'] == "PAGO"].tail(10)
        
        if not df_pagos_recentes.empty:
            for idx, row in df_pagos_recentes.iloc[::-1].iterrows(): # Mostra os últimos primeiro
                col_p1, col_p2 = st.columns([7, 2])
                col_p1.info(f"OK: {row['Cliente']} entregou {row['Quantidade']} {row['Vasilhame']} | Baixa por: {row['QuemBaixou']}")
                if col_p2.button("🚫 ESTORNAR", key=f"est_{row['ID']}"):
                    df_cascos.at[idx, 'Status'] = "DEVE"
                    df_cascos.at[idx, 'QuemBaixou'] = ""
                    df_cascos.to_csv(CASCOS_FILE, index=False)
                    registrar_log(nome_usuario, f"ESTORNO: Voltou dívida de casco de {row['Cliente']}")
                    st.rerun()
        else:
            st.write("Nenhum histórico de baixa recente.")

    # =================================================================
    # ABAS EXCLUSIVAS DO ADMINISTRADOR
    # =================================================================
    elif eh_admin:
        if escolha == "📊 Financeiro":
            st.title("📊 Resumo de Patrimônio")
            df_fin = pd.merge(df_estoque, df_prod, on='Nome')
            df_fin['Valor_Total'] = df_fin['Estoque_Total_Un'] * df_fin['Preco_Unitario']
            st.metric("Total em Mercadoria", f"R$ {df_fin['Valor_Total'].sum():,.2f}")
            st.dataframe(df_fin, use_container_width=True)

        elif escolha == "📜 Histórico (Adm)":
            st.title("📜 Auditoria Completa")
            st.info("Aqui constam todas as ações com data, hora e responsável.")
            df_log = pd.read_csv(LOG_FILE)
            st.dataframe(df_log.iloc[::-1], use_container_width=True) # Mostra o mais novo no topo

        elif escolha == "👥 Equipe":
            st.title("👥 Gestão de Usuários")
            with st.form("form_equipe"):
                u_id, u_nome, u_senha, u_tel, u_adm = st.columns(5)
                new_id = u_id.text_input("Login")
                new_nom = u_nome.text_input("Nome")
                new_sen = u_senha.text_input("Senha")
                new_tel = u_tel.text_input("Telefone")
                new_adm = u_adm.selectbox("Admin?", ["NÃO", "SIM"])
                if st.form_submit_button("Adicionar"):
                    df_users = pd.concat([df_users, pd.DataFrame([[new_id, new_nom, new_sen, new_adm, new_tel]], columns=df_users.columns)])
                    df_users.to_csv(USERS_FILE, index=False)
                    registrar_log(nome_usuario, f"EQUIPE: Adicionou usuário {new_id}")
                    st.rerun()
            st.dataframe(df_users)
