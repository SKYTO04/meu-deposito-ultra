import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. CONFIGURAÇÃO DE AMBIENTE E UI ULTRA DARK
# =================================================================
st.set_page_config(page_title="PACAEMBU G76 ULTRA", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 15px; border-left: 5px solid #58A6FF; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; transition: 0.3s; border: 1px solid #30363D; background-color: #21262D; color: #C9D1D9; }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; background-color: #30363D; transform: scale(1.02); }
    div[data-testid="stExpander"] { background-color: #161B22; border-radius: 10px; border: 1px solid #30363D; }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; letter-spacing: -1px; }
    .status-vazio { color: #FF7B72; font-weight: bold; }
    .status-cheio { color: #7EE787; font-weight: bold; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE BANCO DE DADOS (CSV PERSISTENTE)
# =================================================================
VERSION = "v76"
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
        pd.DataFrame([['admin', 'GERENTE MESTRE', '123', 'SIM', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_USR, index=False)
    
    # Estrutura completa das tabelas
    tabelas = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Venda', 'Estoque_Minimo'], 
        DB_EST: ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        DB_PIL: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação', 'Detalhes'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Total', 'Usuario'],
        DB_EST_CASCOS: ['Tipo', 'Qtd']
    }
    
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            if arq == DB_EST_CASCOS:
                pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=cols).to_csv(arq, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

def registrar_log(u, acao, detalhes=""):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M:%S"), u, acao, detalhes]], 
                 columns=['Data', 'Usuario', 'Ação', 'Detalhes']).to_csv(DB_LOG, mode='a', header=False, index=False)

# =================================================================
# 3. CONTROLE DE SESSÃO E LOGIN
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>PACAEMBU ULTRA G76</h1>", unsafe_allow_html=True)
    with st.form("login_center"):
        u_input = st.text_input("👤 USUÁRIO")
        s_input = st.text_input("🔑 SENHA", type="password")
        if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
            df_usuarios = pd.read_csv(DB_USR)
            check = df_usuarios[(df_usuarios['user'] == u_input) & (df_usuarios['senha'].astype(str) == s_input)]
            if not check.empty:
                st.session_state.update({
                    'auth': True, 'user': u_input, 
                    'nome': check['nome'].values[0], 
                    'adm': (check['is_admin'].values[0] == 'SIM')
                })
                registrar_log(st.session_state['nome'], "LOGIN", "Sucesso")
                st.rerun()
            else: st.error("Acesso negado: Usuário ou senha incorretos.")
else:
    # Carregamento Geral dos DataFrames
    df_p = pd.read_csv(DB_PROD)
    df_e = pd.read_csv(DB_EST)
    df_pi = pd.read_csv(DB_PIL)
    df_c = pd.read_csv(DB_CAS)
    df_u = pd.read_csv(DB_USR)
    df_v = pd.read_csv(DB_VENDAS)
    df_ec = pd.read_csv(DB_EST_CASCOS)
    n_log, u_log, is_adm = st.session_state['nome'], st.session_state['user'], st.session_state['adm']

    # --- NAVEGAÇÃO LATERAL ---
    st.sidebar.markdown(f"<h2 style='text-align:center;'>PACAEMBU</h2>", unsafe_allow_html=True)
    
    u_row = df_u[df_u['user'] == u_log]
    foto_raw = u_row['foto'].values[0] if not u_row.empty and not pd.isna(u_row['foto'].values[0]) else ""
    if foto_raw:
        st.sidebar.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{foto_raw}' style='border-radius:50%; width:110px; height:110px; object-fit:cover; border:2px solid #58A6FF;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<div style='text-align:center'>👤</div>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"<p style='text-align:center;'><b>{n_log}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("MÓDULOS", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Entrada de Estoque", "🍶 Gestão de Cascos", "✨ Cadastro de Itens", "⚙️ Meu Perfil"] + (["📜 Histórico & Logs"] if is_adm else []))
    
    if st.sidebar.button("🚪 LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: PDV ROMARINHO (COMPLETO COM PREÇO DO CADASTRO)
    # =================================================================
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda - Saídas Rápidas")
        
        prods_pdv = df_p[df_p['Categoria'] == "Romarinho"]
        if prods_pdv.empty:
            st.warning("Cadastre itens na categoria 'Romarinho' para visualizar aqui.")
        else:
            for _, item in prods_pdv.iterrows():
                est_data = df_e[df_e['Nome'] == item['Nome']]
                if not est_data.empty:
                    unidades_atuais = int(est_data['Qtd_Unidades'].values[0])
                    preco_un = float(item['Preco_Venda'])
                    
                    with st.container():
                        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                        c1.markdown(f"#### {item['Nome']}\n<small>Valor Unitário: R$ {preco_un:.2f}</small>", unsafe_allow_html=True)
                        
                        # Alerta visual de estoque baixo
                        classe_estoque = "status-cheio" if unidades_atuais > item['Estoque_Minimo'] else "status-vazio"
                        c2.markdown(f"<div style='text-align:center;'><span class='{classe_estoque}'>{unidades_atuais//24} Eng | {unidades_atuais%24} Un</span></div>", unsafe_allow_html=True)
                        
                        if c3.button(f"BAIXAR ENG (24)", key=f"pdv_e_{item['Nome']}"):
                            if unidades_atuais >= 24:
                                df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                                df_e.to_csv(DB_EST, index=False)
                                # Registro de venda com preço do cadastro
                                nova_venda = pd.DataFrame([[f"V{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 24, preco_un * 24, n_log]], columns=df_v.columns)
                                pd.concat([df_v, nova_venda]).to_csv(DB_VENDAS, index=False)
                                registrar_log(n_log, "VENDA", f"Eng {item['Nome']}")
                                st.rerun()
                        
                        if c4.button(f"BAIXAR UN (1)", key=f"pdv_u_{item['Nome']}"):
                            if unidades_atuais >= 1:
                                df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                                df_e.to_csv(DB_EST, index=False)
                                nova_venda = pd.DataFrame([[f"V{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 1, preco_un, n_log]], columns=df_v.columns)
                                pd.concat([df_v, nova_venda]).to_csv(DB_VENDAS, index=False)
                                registrar_log(n_log, "VENDA", f"Un {item['Nome']}")
                                st.rerun()
                st.markdown("---")

            # --- LÓGICA DE ESTORNO DE VENDA ---
            st.subheader("🕒 Estornar Saídas Recentes")
            v_recente = df_v[df_v['Usuario'] == n_log].tail(5).iloc[::-1]
            if not v_recente.empty:
                for idx, row in v_recente.iterrows():
                    h1, h2 = st.columns([7, 2])
                    h1.write(f"Venda: **{row['Produto']}** | Qtd: {row['Qtd']} | Total: R$ {row['Total']:.2f}")
                    if h2.button("🚫 ESTORNAR", key=f"estv_{idx}"):
                        df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                        df_e.to_csv(DB_EST, index=False)
                        df_v.drop(idx).to_csv(DB_VENDAS, index=False)
                        registrar_log(n_log, "ESTORNO VENDA", f"{row['Produto']} ({row['Qtd']}un)")
                        st.rerun()

    # =================================================================
    # ABA: CADASTRO DE ITENS (ONDE DEFINE O PREÇO)
    # =================================================================
    elif menu == "✨ Cadastro de Itens":
        st.title("✨ Gestão de Produtos e Preços")
        
        with st.form("cad_full"):
            st.subheader("Registrar Novo Item no Sistema")
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoria do Produto", ["Romarinho", "Lata", "Refrigerante", "Energético", "Outros"])
            nom = c2.text_input("Nome Completo do Produto").upper()
            
            c3, c4 = st.columns(2)
            pre = c3.number_input("Preço de Venda Unitário (R$)", min_value=0.0, step=0.01)
            min_e = c4.number_input("Alerta de Estoque Mínimo (Un)", 24)
            
            if st.form_submit_button("SALVAR CADASTRO"):
                if nom and not df_p[df_p['Nome'] == nom].empty:
                    st.error("Erro: Este produto já existe!")
                elif nom:
                    # Salva no Cadastro
                    pd.concat([df_p, pd.DataFrame([[cat, nom, pre, min_e]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    # Cria entrada no estoque zerada
                    pd.concat([df_e, pd.DataFrame([[nom, 0, datetime.now().strftime("%d/%m %H:%M")]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                    registrar_log(n_log, "CADASTRO", f"Novo item: {nom} - R$ {pre}")
                    st.success(f"{nom} cadastrado com sucesso!")
                    st.rerun()
        
        st.subheader("Produtos Cadastrados")
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: ENTRADA DE ESTOQUE (MOVIMENTAÇÃO FÍSICA)
    # =================================================================
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Movimentação de Entrada")
        
        with st.form("f_estoque"):
            st.subheader("Dar entrada em mercadoria recebida")
            p_alvo = st.selectbox("Selecione o Produto", df_p['Nome'].tolist())
            q_add = st.number_input("Quantidade de Unidades a somar", min_value=1)
            
            if st.form_submit_button("CONFIRMAR ENTRADA"):
                df_e.loc[df_e['Nome'] == p_alvo, 'Qtd_Unidades'] += q_add
                df_e.loc[df_e['Nome'] == p_alvo, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB_EST, index=False)
                registrar_log(n_log, "ESTOQUE", f"Entrada: {q_add} un em {p_alvo}")
                st.success(f"Estoque de {p_alvo} atualizado!")
                st.rerun()
        
        st.subheader("Status Atual do Estoque")
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: GESTÃO DE CASCOS (SISTEMA DE DÍVIDAS E VAZIOS)
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Controle de Vasilhames e Vazios")
        
        # Painel de Saldo de Vazios
        cols_vazios = st.columns(4)
        for i, row in df_ec.iterrows():
            cols_vazios[i].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        
        col_cad, col_dev = st.columns([1, 1.5])
        
        with col_cad:
            st.subheader("➕ Nova Pendência")
            with st.form("f_casco_divida"):
                cli = st.text_input("Cliente").upper()
                tip = st.selectbox("Tipo de Casco", df_ec['Tipo'].tolist())
                qtd = st.number_input("Qtd Devolvendo", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    if cli:
                        c_id = f"C{datetime.now().strftime('%H%M%S')}"
                        nova_div = pd.DataFrame([[c_id, datetime.now().strftime("%d/%m %H:%M"), cli, tip, qtd, "DEVE", n_log]], columns=df_c.columns)
                        pd.concat([df_c, nova_div]).to_csv(DB_CAS, index=False)
                        registrar_log(n_log, "CASCO", f"{cli} deve {qtd} {tip}")
                        st.rerun()

        with col_dev:
            st.subheader("🔴 Devedores Ativos")
            deve_df = df_c[df_c['Status'] == "DEVE"]
            if deve_df.empty:
                st.info("Nenhuma pendência ativa.")
            else:
                for idx, row in deve_df.iterrows():
                    with st.expander(f"👤 {row['Cliente']} | {row['Qtd']}x {row['Tipo']}"):
                        b_c1, b_c2 = st.columns(2)
                        if b_c1.button("📥 ENTREGOU CASCO", key=f"r_{row['ID']}"):
                            df_c.at[idx, 'Status'] = "DEVOLVEU"
                            df_c.to_csv(DB_CAS, index=False)
                            # Soma no estoque físico de vazios
                            df_ec.loc[df_ec['Tipo'] == row['Tipo'], 'Qtd'] += row['Qtd']
                            df_ec.to_csv(DB_EST_CASCOS, index=False)
                            registrar_log(n_log, "CASCO BAIXA", f"{row['Cliente']} devolveu")
                            st.rerun()
                        if b_c2.button("💰 PAGOU EM DINHEIRO", key=f"p_{row['ID']}"):
                            df_c.at[idx, 'Status'] = "PAGOU $"
                            df_c.to_csv(DB_CAS, index=False)
                            registrar_log(n_log, "CASCO BAIXA $", f"{row['Cliente']} pagou em dinheiro")
                            st.rerun()

        st.markdown("---")
        st.subheader("📜 Estorno de Movimentação de Cascos")
        hist_cascos = df_c[df_c['Status'] != "DEVE"].tail(10).iloc[::-1]
        for idx, row in hist_cascos.iterrows():
            h1, h2 = st.columns([7, 2])
            h1.write(f"**{row['Cliente']}** -> {row['Qtd']} {row['Tipo']} | Status: {row['Status']}")
            if h2.button("🚫 ESTORNAR", key=f"est_cas_{idx}"):
                # Lógica inversa de estoque se ele tinha devolvido o casco
                if row['Status'] == "DEVOLVEU":
                    df_ec.loc[df_ec['Tipo'] == row['Tipo'], 'Qtd'] -= row['Qtd']
                    df_ec.to_csv(DB_EST_CASCOS, index=False)
                # Volta status para devedor
                df_c.at[idx, 'Status'] = "DEVE"
                df_c.to_csv(DB_CAS, index=False)
                registrar_log(n_log, "ESTORNO CASCO", f"Dívida de {row['Cliente']} restaurada")
                st.rerun()

    # =================================================================
    # ABA: MAPA DE PILARES (AMARRAÇÃO 3x2 / 2x3)
    # =================================================================
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Gestão de Pilares e Amarração")
        
        with st.expander("➕ MONTAR NOVA CAMADA DE PILAR"):
            p_lista = ["+ Criar Novo Pilar"] + df_pi['Pilar'].unique().tolist()
            p_escolha = st.selectbox("Selecione o Pilar", p_lista)
            n_pilar = st.text_input("Nome do Pilar").upper() if p_escolha == "+ Criar Novo Pilar" else p_escolha
            
            if n_pilar:
                df_filt = df_pi[df_pi['Pilar'] == n_pilar]
                num_camada = 1 if df_filt.empty else df_filt['Camada'].max() + 1
                
                # Regra de amarração
                atras, frente = (3, 2) if num_camada % 2 != 0 else (2, 3)
                st.info(f"CAMADA {num_camada}: Configuração {atras} Atrás / {frente} Frente")
                
                novas_entradas = []
                col_m1, col_m2 = st.columns(2)
                for i in range(atras + frente):
                    col_alvo = col_m1 if (i+1) <= atras else col_m2
                    bebida = col_alvo.selectbox(f"Posição {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pil_{i}_{num_camada}")
                    avulsos = col_alvo.number_input(f"Avulsos na posição {i+1}", 0, key=f"av_{i}_{num_camada}")
                    if bebida != "Vazio":
                        novas_entradas.append([f"{n_pilar}_{num_camada}_{i+1}", n_pilar, num_camada, i+1, bebida, avulsos])
                
                if st.button("SALVAR CAMADA COMPLETA"):
                    pd.concat([df_pi, pd.DataFrame(novas_entradas, columns=df_pi.columns)]).to_csv(DB_PIL, index=False)
                    registrar_log(n_log, "PILAR MONTAGEM", f"{n_pilar} Camada {num_camada}")
                    st.rerun()

        # Visualização e Retirada
        for pilar_nome in df_pi['Pilar'].unique():
            st.subheader(f"📍 {pilar_nome}")
            df_pilar = df_pi[df_pi['Pilar'] == pilar_nome]
            for cam in sorted(df_pilar['Camada'].unique(), reverse=True):
                st.write(f"Camada {cam}")
                df_camada = df_pilar[df_pilar['Camada'] == cam]
                slots = st.columns(5)
                for _, slot in df_camada.iterrows():
                    with slots[int(slot['Posicao'])-1]:
                        st.markdown(f"<div style='background:#1c2128; padding:5px; border-radius:5px; border:1px solid #30363d; text-align:center;'><b>{slot['Bebida']}</b><br>+{slot['Avulsos']}</div>", unsafe_allow_html=True)
                        if st.button("RETIRAR", key=f"ret_pil_{slot['ID']}"):
                            # Baixa no estoque (Fardo de 6 + avulsos)
                            qtd_retirada = 6 + slot['Avulsos']
                            df_e.loc[df_e['Nome'] == slot['Bebida'], 'Qtd_Unidades'] -= qtd_retirada
                            df_e.to_csv(DB_EST, index=False)
                            # Remove do mapa
                            df_pi[df_pi['ID'] != slot['ID']].to_csv(DB_PIL, index=False)
                            registrar_log(n_log, "PILAR RETIRADA", f"{slot['Bebida']} do {pilar_nome}")
                            st.rerun()

    # =================================================================
    # ABA: HISTÓRICO E AUDITORIA (ADM)
    # =================================================================
    elif menu == "📜 Histórico & Logs" and is_adm:
        st.title("📜 Auditoria Geral")
        t1, t2 = st.tabs(["Logs do Sistema", "Relatório de Vendas"])
        with t1: st.dataframe(pd.read_csv(DB_LOG).iloc[::-1], use_container_width=True)
        with t2: st.dataframe(df_v.iloc[::-1], use_container_width=True)

    # =================================================================
    # ABA: MEU PERFIL
    # =================================================================
    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Gerenciar Perfil")
        upload = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg', 'jpeg'])
        if st.button("SALVAR FOTO"):
            if upload:
                img_proc = Image.open(upload)
                img_proc.thumbnail((150, 150))
                b_io = io.BytesIO()
                img_proc.save(b_io, format="PNG")
                b64_foto = base64.b64encode(b_io.getvalue()).decode()
                df_u.loc[df_u['user'] == u_log, 'foto'] = b64_foto
                df_u.to_csv(DB_USR, index=False)
                st.success("Foto atualizada!")
                st.rerun()
