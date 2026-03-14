import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. ARQUITETURA DE DESIGN (DARK MODE DE ALTO CONTRASTE)
# =================================================================
st.set_page_config(page_title="PACAEMBU G74 ULTRA", page_icon="🍻", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 15px; border-left: 5px solid #58A6FF; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; transition: 0.3s; border: 1px solid #30363D; background-color: #21262D; color: #C9D1D9; }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; background-color: #30363D; transform: scale(1.01); }
    div[data-testid="stExpander"] { background-color: #161B22; border-radius: 10px; border: 1px solid #30363D; }
    .status-alerta { color: #F0883E; font-weight: bold; }
    .status-critico { color: #FF7B72; font-weight: bold; }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS - ESTRUTURA BRUTA (CSV)
# =================================================================
VERSION = "v74"
DB_PROD = f"prod_{VERSION}.csv"
DB_EST = f"est_{VERSION}.csv"
DB_PIL = f"pil_{VERSION}.csv"
DB_USR = f"usr_{VERSION}.csv"
DB_LOG = f"log_{VERSION}.csv"
DB_CAS = f"cas_{VERSION}.csv"
DB_VENDAS = f"vendas_{VERSION}.csv"
DB_EST_CASCOS = f"est_cascos_{VERSION}.csv"

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'GERENTE MASTER', '123', 'SIM', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_USR, index=False)
    
    # Definição rigorosa de colunas para evitar o erro de 'simplificação'
    tabelas = {
        DB_PROD: ['Categoria', 'Nome', 'Estoque_Minimo'],
        DB_EST: ['Nome', 'Qtd_Unidades', 'Preco_Custo', 'Preco_Venda', 'Ultima_Atualizacao'],
        DB_PIL: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos', 'Data_Montagem'],
        DB_LOG: ['Data', 'Usuario', 'Ação', 'Detalhes'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Preco_Un', 'Total', 'Usuario'],
        DB_EST_CASCOS: ['Tipo', 'Qtd']
    }
    
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            if arq == DB_EST_CASCOS:
                pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=cols).to_csv(arq, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def salvar_log(u, acao, detalhe=""):
    log_data = [[datetime.now().strftime("%d/%m %H:%M:%S"), u, acao, detalhe]]
    pd.DataFrame(log_data).to_csv(DB_LOG, mode='a', header=False, index=False)

# =================================================================
# 3. LÓGICA DE LOGIN
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center;'>PACAEMBU ULTRA G74</h1>", unsafe_allow_html=True)
    with st.form("auth_form"):
        u = st.text_input("👤 USUÁRIO")
        s = st.text_input("🔑 SENHA", type="password")
        if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
            df_u = pd.read_csv(DB_USR)
            valido = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
            if not valido.empty:
                st.session_state.update({'auth': True, 'user': u, 'nome': valido['nome'].values[0], 'adm': (valido['is_admin'].values[0] == 'SIM')})
                salvar_log(st.session_state['nome'], "LOGIN", "Acesso ao sistema")
                st.rerun()
            else: st.error("Credenciais Inválidas")
else:
    # Carregamento de Tabelas em Cache de Sessão
    df_p, df_e, df_pi = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_c, df_u, df_v, df_ec = pd.read_csv(DB_CAS), pd.read_csv(DB_USR), pd.read_csv(DB_VENDAS), pd.read_csv(DB_EST_CASCOS)
    n_log, u_log, is_adm = st.session_state['nome'], st.session_state['user'], st.session_state['adm']

    # --- SIDEBAR PROFISSIONAL ---
    st.sidebar.markdown(f"<h2 style='text-align:center;'>PACAEMBU</h2>", unsafe_allow_html=True)
    user_row = df_u[df_u['user'] == u_log]
    foto_b64 = user_row['foto'].values[0] if not user_row.empty and not pd.isna(user_row['foto'].values[0]) else ""
    if foto_b64:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{foto_b64}' style='border-radius:50%; width:120px; height:120px; object-fit:cover; border:3px solid #58A6FF;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='https://cdn-icons-png.flaticon.com/512/149/149071.png' width='120'></div>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"<p style='text-align:center;'>👤 <b>{n_log}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Estoque & Preços", "🍶 Gestão de Cascos", "✨ Cadastro Geral", "⚙️ Meu Perfil"] + (["📜 Auditoria Total"] if is_adm else []))
    
    if st.sidebar.button("🚪 SAIR"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: PDV ROMARINHO (BAIXA RÁPIDA + ESTORNO IMEDIATO)
    # =================================================================
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda (Saídas)")
        romarinhos = df_p[df_p['Categoria'] == "Romarinho"]
        
        if romarinhos.empty:
            st.info("Nenhum Romarinho cadastrado. Vá em 'Cadastro Geral'.")
        else:
            for _, item in romarinhos.iterrows():
                est_row = df_e[df_e['Nome'] == item['Nome']]
                if not est_row.empty:
                    unidades = int(est_row['Qtd_Unidades'].values[0])
                    v_un = float(est_row['Preco_Venda'].values[0])
                    
                    with st.container():
                        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                        c1.markdown(f"#### {item['Nome']}")
                        
                        # Alertas de cor no estoque
                        cor = "status-ok" if unidades > item['Estoque_Minimo'] else "status-critico"
                        c2.markdown(f"<span class='{cor}'>{unidades//24} Eng | {unidades%24} Un</span>", unsafe_allow_html=True)
                        
                        if c3.button(f"BAIXAR ENG", key=f"eng_{item['Nome']}"):
                            if unidades >= 24:
                                df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                                df_e.to_csv(DB_EST, index=False)
                                # Registrar venda
                                v_id = f"V{datetime.now().strftime('%M%S')}"
                                nova_venda = [[v_id, datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 24, v_un, v_un*24, n_log]]
                                pd.DataFrame(nova_venda).to_csv(DB_VENDAS, mode='a', header=False, index=False)
                                salvar_log(n_log, "VENDA", f"Eng {item['Nome']}")
                                st.rerun()
                        
                        if c4.button(f"BAIXAR UN", key=f"un_{item['Nome']}"):
                            if unidades >= 1:
                                df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                                df_e.to_csv(DB_EST, index=False)
                                v_id = f"V{datetime.now().strftime('%M%S')}"
                                nova_venda = [[v_id, datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 1, v_un, v_un, n_log]]
                                pd.DataFrame(nova_venda).to_csv(DB_VENDAS, mode='a', header=False, index=False)
                                salvar_log(n_log, "VENDA", f"Un {item['Nome']}")
                                st.rerun()
                    st.markdown("---")

            st.subheader("🕒 Estorno de Vendas (Últimas 5)")
            v_recente = df_v[df_v['Usuario'] == n_log].tail(5).iloc[::-1]
            for idx, row in v_recente.iterrows():
                cc1, cc2 = st.columns([7, 2])
                cc1.write(f"ID: {row['ID']} | {row['Produto']} | Qtd: {row['Qtd']} | Total: R${row['Total']:.2f}")
                if cc2.button("🚫 ESTORNAR", key=f"estv_{row['ID']}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB_EST, index=False)
                    # Remover do arquivo de vendas (recriando o csv sem a linha)
                    df_v.drop(idx).to_csv(DB_VENDAS, index=False)
                    salvar_log(n_log, "ESTORNO VENDA", f"ID {row['ID']} - {row['Produto']}")
                    st.rerun()

    # =================================================================
    # ABA: GESTÃO DE CASCOS (ESTOQUE VAZIO + DÍVIDAS + ESTORNO)
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Gestão de Vasilhames")
        
        # Dashboard de Saldo de Vazios
        st.subheader("📦 Saldo Físico (No Depósito)")
        m1, m2, m3, m4 = st.columns(4)
        metrix = [m1, m2, m3, m4]
        for i, r in df_ec.iterrows():
            metrix[i].metric(r['Tipo'], f"{r['Qtd']} un")
        
        st.markdown("---")
        
        c_pend, c_lista = st.columns([1, 1.5])
        
        with c_pend:
            st.subheader("➕ Lançar Devedor")
            with st.form("casco_form"):
                cli = st.text_input("NOME DO CLIENTE").upper()
                tip = st.selectbox("TIPO DE VASILHAME", df_ec['Tipo'].tolist())
                qtd = st.number_input("QUANTIDADE", 1)
                if st.form_submit_button("REGISTRAR DÍVIDA"):
                    if cli:
                        c_id = f"C{datetime.now().strftime('%H%M%S')}"
                        novo_c = [[c_id, datetime.now().strftime("%d/%m %H:%M"), cli, tip, qtd, "DEVE", n_log]]
                        pd.DataFrame(novo_c).to_csv(DB_CAS, mode='a', header=False, index=False)
                        salvar_log(n_log, "DÍVIDA CASCO", f"{cli} deve {qtd} {tip}")
                        st.rerun()

        with c_lista:
            st.subheader("🔴 Pendências Ativas")
            deve_df = df_c[df_c['Status'] == "DEVE"]
            if deve_df.empty:
                st.info("Sem devedores no momento.")
            else:
                for i, r in deve_df.iterrows():
                    with st.expander(f"👤 {r['Cliente']} | {r['Qtd']}x {r['Tipo']}"):
                        b1, b2 = st.columns(2)
                        if b1.button("📥 DEVOLVEU CASCO", key=f"dev_{r['ID']}"):
                            df_c.at[i, 'Status'] = "DEVOLVEU"
                            df_c.to_csv(DB_CAS, index=False)
                            # Soma no estoque de vazios
                            df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                            df_ec.to_csv(DB_EST_CASCOS, index=False)
                            salvar_log(n_log, "BAIXA CASCO", f"{r['Cliente']} entregou")
                            st.rerun()
                        if b2.button("💰 PAGOU DINHEIRO", key=f"pag_{r['ID']}"):
                            df_c.at[i, 'Status'] = "PAGOU $"
                            df_c.to_csv(DB_CAS, index=False)
                            salvar_log(n_log, "BAIXA CASCO $", f"{r['Cliente']} pagou")
                            st.rerun()

        st.markdown("---")
        st.subheader("📜 Histórico de Baixas e Estorno")
        # Histórico de quem não deve mais
        hist_c = df_c[df_c['Status'] != "DEVE"].tail(10).iloc[::-1]
        for i, r in hist_c.iterrows():
            h1, h2 = st.columns([7, 2])
            status_cor = "🟢" if r['Status'] == "DEVOLVEU" else "💰"
            h1.write(f"{status_cor} **{r['Cliente']}** | {r['Qtd']}x {r['Tipo']} | Status: {r['Status']}")
            if h2.button("🚫 ESTORNAR", key=f"estc_{r['ID']}"):
                # Se ele tinha devolvido o casco, ao estornar temos que tirar do estoque de vazios
                if r['Status'] == "DEVOLVEU":
                    df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] -= r['Qtd']
                    df_ec.to_csv(DB_EST_CASCOS, index=False)
                
                # Volta o status para DEVE
                df_c.at[i, 'Status'] = "DEVE"
                df_c.to_csv(DB_CAS, index=False)
                salvar_log(n_log, "ESTORNO CASCO", f"Restaurada dívida de {r['Cliente']}")
                st.rerun()

    # =================================================================
    # ABA: ESTOQUE E PREÇOS (O CORE FINANCEIRO)
    # =================================================================
    elif menu == "📦 Estoque & Preços":
        st.title("📦 Gestão de Mercadoria e Valores")
        with st.form("estoque_update"):
            st.write("Selecione o produto para dar entrada ou ajustar preços.")
            prod_sel = st.selectbox("PRODUTO", df_p['Nome'].unique())
            c1, c2, c3 = st.columns(3)
            add_q = c1.number_input("ADICIONAR QTD (UN)", 0)
            n_custo = c2.number_input("PREÇO DE CUSTO (UN)", 0.0)
            n_venda = c3.number_input("PREÇO DE VENDA (UN)", 0.0)
            
            if st.form_submit_button("SALVAR ALTERAÇÕES"):
                # Atualiza Unidades
                df_e.loc[df_e['Nome'] == prod_sel, 'Qtd_Unidades'] += add_q
                # Atualiza Preços se forem maiores que zero
                if n_custo > 0: df_e.loc[df_e['Nome'] == prod_sel, 'Preco_Custo'] = n_custo
                if n_venda > 0: df_e.loc[df_e['Nome'] == prod_sel, 'Preco_Venda'] = n_venda
                
                df_e.loc[df_e['Nome'] == prod_sel, 'Ultima_Atualizacao'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB_EST, index=False)
                salvar_log(n_log, "ATUALIZAÇÃO ESTOQUE", f"{prod_sel} (+{add_q})")
                st.success("Dados atualizados!")
                st.rerun()
        
        st.subheader("Tabela Geral de Saldo")
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: CADASTRO GERAL (APENAS REGISTRO DE ITEM)
    # =================================================================
    elif menu == "✨ Cadastro Geral":
        st.title("✨ Cadastro de Novos Itens")
        st.write("Registre o nome e a categoria. Valores e estoque são feitos na aba 'Estoque & Preços'.")
        
        with st.form("cad_item"):
            col1, col2, col3 = st.columns([2, 2, 1])
            cat = col1.selectbox("CATEGORIA", ["Romarinho", "Refrigerante", "Cerveja Lata", "Energético", "Outros"])
            nom = col2.text_input("NOME DO PRODUTO (EX: BRAHMA DUPLO MALTE)").upper()
            min_a = col3.number_input("ESTOQUE MÍNIMO", 24)
            
            if st.form_submit_button("CADASTRAR PRODUTO"):
                if nom:
                    if not df_p[df_p['Nome'] == nom].empty:
                        st.error("Este produto já existe no sistema!")
                    else:
                        # Add no Prod
                        nova_p = pd.DataFrame([[cat, nom, min_a]], columns=df_p.columns)
                        pd.concat([df_p, nova_p]).to_csv(DB_PROD, index=False)
                        # Add no Est com valores zerados
                        nova_e = pd.DataFrame([[nom, 0, 0.0, 0.0, datetime.now().strftime("%d/%m")]], columns=df_e.columns)
                        pd.concat([df_e, nova_e]).to_csv(DB_EST, index=False)
                        salvar_log(n_log, "CADASTRO ITEM", f"Novo produto: {nom}")
                        st.success(f"{nom} cadastrado com sucesso!")
                        st.rerun()

    # =================================================================
    # ABA: MAPA DE PILARES (3x2 / 2x3 AMARRAÇÃO)
    # =================================================================
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Controle de Amarração de Pilares")
        
        with st.expander("➕ MONTAR NOVA CAMADA"):
            p_sel = st.selectbox("PILAR", ["+ NOVO PILAR"] + list(df_pi['Pilar'].unique()))
            n_pilar = st.text_input("NOME DO PILAR (EX: PILAR A)").upper() if p_sel == "+ NOVO PILAR" else p_sel
            
            if n_pilar:
                df_filt = df_pi[df_pi['Pilar'] == n_pilar]
                camada_atual = 1 if df_filt.empty else df_filt['Camada'].max() + 1
                
                # Regra de Amarração Pacaembu
                atras, frente = (3, 2) if camada_atual % 2 != 0 else (2, 3)
                st.info(f"CAMADA {camada_atual}: Lógica {atras}x{frente}")
                
                col_at, col_fr = st.columns(2)
                novas_posicoes = []
                
                for i in range(atras + frente):
                    c_target = col_at if (i+1) <= atras else col_fr
                    b_pos = c_target.selectbox(f"Posição {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pos_{i+1}_{camada_atual}")
                    a_pos = c_target.number_input(f"Avulsos {i+1}", 0, key=f"av_{i+1}_{camada_atual}")
                    if b_pos != "Vazio":
                        novas_posicoes.append([f"{n_pilar}_{camada_atual}_{i+1}", n_pilar, camada_atual, i+1, b_pos, a_pos, datetime.now().strftime("%d/%m")])
                
                if st.button("FINALIZAR CAMADA"):
                    pd.concat([df_pi, pd.DataFrame(novas_posicoes, columns=df_pi.columns)]).to_csv(DB_PIL, index=False)
                    salvar_log(n_log, "MONTAGEM PILAR", f"{n_pilar} Camada {camada_atual}")
                    st.rerun()

        # Visualização dos Pilares
        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 {p}")
            p_data = df_pi[df_pi['Pilar'] == p]
            for c in sorted(p_data['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                c_data = p_data[p_data['Camada'] == c]
                cols = st.columns(5)
                for _, r in c_data.iterrows():
                    with cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background:#1c2128; padding:8px; border-radius:5px; border:1px solid #30363d; text-align:center;'><b>{r['Bebida']}</b><br><small>+{r['Avulsos']} un</small></div>", unsafe_allow_html=True)
                        if st.button("RETIRAR", key=f"ret_{r['ID']}"):
                            # Baixa no estoque (Fardo de 6 + avulsos)
                            total_retira = 6 + r['Avulsos']
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total_retira
                            df_e.to_csv(DB_EST, index=False)
                            # Remove do pilar
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            salvar_log(n_log, "RETIRADA PILAR", f"{r['Bebida']} do {p}")
                            st.rerun()

    # =================================================================
    # ABA: AUDITORIA E PERFIL
    # =================================================================
    elif menu == "📜 Auditoria Total" and is_adm:
        st.title("📜 Histórico Geral do Sistema")
        tab1, tab2 = st.tabs(["Logs de Ações", "Relatório de Vendas"])
        with tab1: st.dataframe(pd.read_csv(DB_LOG).iloc[::-1], use_container_width=True)
        with tab2: st.dataframe(df_v.iloc[::-1], use_container_width=True)

    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações de Perfil")
        new_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
        if st.button("ATUALIZAR FOTO"):
            if new_foto:
                img = Image.open(new_foto)
                img.thumbnail((200, 200))
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                df_u.loc[df_u['user'] == u_log, 'foto'] = img_str
                df_u.to_csv(DB_USR, index=False)
                st.success("Foto atualizada!")
                st.rerun()
