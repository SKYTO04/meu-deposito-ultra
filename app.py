import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import plotly.express as px

# =================================================================
# 1. ARQUITETURA DE DESIGN E UI (BRUTALIST DARK)
# =================================================================
st.set_page_config(page_title="PACAEMBU G78 OMNI", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 20px; border-left: 5px solid #58A6FF; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; transition: 0.3s; border: 1px solid #30363D; background-color: #21262D; color: #C9D1D9; }
    .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; background-color: #30363D; transform: scale(1.02); }
    h1, h2, h3 { color: #58A6FF; font-weight: 800; letter-spacing: -1px; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    div[data-testid="stExpander"] { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE DADOS (DATABASE CSV)
# =================================================================
VERSION = "v78"
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
    
    tabelas = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'], 
        DB_EST: ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        DB_PIL: ['ID', 'Pilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação', 'Detalhes'],
        DB_CAS: ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Responsavel'],
        DB_VENDAS: ['ID', 'Data', 'Produto', 'Qtd', 'Custo_Total', 'Venda_Total', 'Usuario'],
        DB_EST_CASCOS: ['Tipo', 'Qtd']
    }
    
    for arq, cols in tabelas.items():
        if not os.path.exists(arq):
            if arq == DB_EST_CASCOS:
                pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=cols).to_csv(arq, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(arq, index=False)

init_db()

# =================================================================
# 3. AUTENTICAÇÃO
# =================================================================
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>PACAEMBU OMNI G78</h1>", unsafe_allow_html=True)
    with st.container():
        _, center, _ = st.columns([1, 1, 1])
        with center:
            with st.form("login"):
                u = st.text_input("👤 USUÁRIO")
                s = st.text_input("🔑 SENHA", type="password")
                if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                    df_u = pd.read_csv(DB_USR)
                    v = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                    if not v.empty:
                        st.session_state.update({'auth': True, 'user': u, 'nome': v['nome'].values[0], 'adm': (v['is_admin'].values[0] == 'SIM')})
                        st.rerun()
                    else: st.error("Incorreto.")
else:
    # Carga de Dados
    df_p, df_e, df_pi = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_c, df_v, df_ec = pd.read_csv(DB_CAS), pd.read_csv(DB_VENDAS), pd.read_csv(DB_EST_CASCOS)
    n_log, is_adm = st.session_state['nome'], st.session_state['adm']

    # --- MENU LATERAL ---
    st.sidebar.title("PACAEMBU")
    menu = st.sidebar.radio("MÓDULOS", ["📊 Dashboard Financeiro", "🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Entrada de Estoque", "🍶 Gestão de Cascos", "✨ Cadastro de Itens", "⚙️ Perfil"])
    
    if st.sidebar.button("🚪 SAIR"):
        st.session_state['auth'] = False
        st.rerun()

    # =================================================================
    # ABA: DASHBOARD FINANCEIRO (DINHEIRO EM PRODUTO + ESTIMATIVAS)
    # =================================================================
    if menu == "📊 Dashboard Financeiro":
        st.title("📊 Saúde Financeira do Estoque")
        
        # Merge para cálculos
        df_f = pd.merge(df_e, df_p, on="Nome")
        df_f['Patrimonio_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
        df_f['Estimativa_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
        df_f['Lucro_Projetado'] = df_f['Estimativa_Venda'] - df_f['Patrimonio_Custo']

        c1, c2, c3 = st.columns(3)
        v_custo = df_f['Patrimonio_Custo'].sum()
        v_venda = df_f['Estimativa_Venda'].sum()
        v_lucro = df_f['Lucro_Projetado'].sum()

        c1.metric("Dinheiro Imobilizado (Custo)", f"R$ {v_custo:,.2f}")
        c2.metric("Estimativa de Retorno (Venda)", f"R$ {v_venda:,.2f}")
        c3.metric("Lucro Bruto Projetado", f"R$ {v_lucro:,.2f}", 
                  delta=f"{((v_lucro/v_custo)*100 if v_custo > 0 else 0):.1f}%")

        st.markdown("---")
        
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.subheader("Patrimônio por Categoria")
            fig1 = px.pie(df_f, values='Estimativa_Venda', names='Categoria', hole=.4, template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_dir:
            st.subheader("Top 10 Produtos em Valor")
            fig2 = px.bar(df_f.nlargest(10, 'Estimativa_Venda'), x='Nome', y='Estimativa_Venda', color='Lucro_Projetado', template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

    # =================================================================
    # ABA: PDV ROMARINHO (SAÍDAS + ESTORNO)
    # =================================================================
    elif menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV - Romarinho")
        
        for _, item in df_p[df_p['Categoria'] == "Romarinho"].iterrows():
            est_data = df_e[df_e['Nome'] == item['Nome']]
            if not est_data.empty:
                qtd = int(est_data['Qtd_Unidades'].values[0])
                v_un = float(item['Preco_Venda'])
                v_ct = float(item['Preco_Custo'])
                
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.markdown(f"#### {item['Nome']}\n<small>Venda: R$ {v_un:.2f}</small>", unsafe_allow_html=True)
                    c2.metric("Estoque", f"{qtd//24} Eng | {qtd%24} Un")
                    
                    if c3.button(f"BAIXAR ENG", key=f"pdv_e_{item['Nome']}"):
                        if qtd >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 24
                            df_e.to_csv(DB_EST, index=False)
                            # Registro com Custo e Venda para o histórico
                            v_id = f"V{datetime.now().strftime('%M%S')}"
                            nova_v = [[v_id, datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 24, v_ct*24, v_un*24, n_log]]
                            pd.DataFrame(nova_v).to_csv(DB_VENDAS, mode='a', header=False, index=False)
                            st.rerun()
                            
                    if c4.button(f"BAIXAR UN", key=f"pdv_u_{item['Nome']}"):
                        if qtd >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Qtd_Unidades'] -= 1
                            df_e.to_csv(DB_EST, index=False)
                            v_id = f"V{datetime.now().strftime('%M%S')}"
                            nova_v = [[v_id, datetime.now().strftime("%d/%m %H:%M"), item['Nome'], 1, v_ct, v_un, n_log]]
                            pd.DataFrame(nova_v).to_csv(DB_VENDAS, mode='a', header=False, index=False)
                            st.rerun()
                st.markdown("---")

        with st.expander("🕒 Estornar Vendas Recentes"):
            v_hist = df_v[df_v['Usuario'] == n_log].tail(5).iloc[::-1]
            for idx, row in v_hist.iterrows():
                cc1, cc2 = st.columns([7, 2])
                cc1.write(f"ID: {row['ID']} | {row['Produto']} | {row['Qtd']}un | Total R$ {row['Venda_Total']}")
                if cc2.button("🚫 ESTORNAR", key=f"estv_{idx}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB_EST, index=False)
                    # Recria o arquivo sem a linha estornada
                    df_v.drop(idx).to_csv(DB_VENDAS, index=False)
                    st.rerun()

    # =================================================================
    # ABA: CADASTRO DE ITENS (CUSTO + VENDA)
    # =================================================================
    elif menu == "✨ Cadastro de Itens":
        st.title("✨ Cadastro de Itens e Preços")
        with st.form("cad_bruto"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Refrigerante", "Outros"])
            nom = c2.text_input("Nome do Produto").upper()
            
            c3, c4, c5 = st.columns(3)
            cto = c3.number_input("Preço de Custo (Un)", 0.0, step=0.01)
            vda = c4.number_input("Preço de Venda (Un)", 0.0, step=0.01)
            mie = c5.number_input("Mínimo para Alerta", 24)
            
            if st.form_submit_button("CADASTRAR PRODUTO NOVO"):
                if nom:
                    if not df_p[df_p['Nome'] == nom].empty:
                        st.error("Produto já existe!")
                    else:
                        # Salva no Cadastro
                        pd.concat([df_p, pd.DataFrame([[cat, nom, cto, vda, mie]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                        # Salva no Estoque (Zerar)
                        pd.concat([df_e, pd.DataFrame([[nom, 0, datetime.now().strftime("%d/%m")]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                        st.success(f"{nom} cadastrado!")
                        st.rerun()
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: ENTRADA DE ESTOQUE (QUANTIDADE PURA)
    # =================================================================
    elif menu == "📦 Entrada de Estoque":
        st.title("📦 Entrada de Mercadoria")
        with st.form("ent_est"):
            p_sel = st.selectbox("Selecione o Item", df_p['Nome'].tolist())
            q_add = st.number_input("Quantidade de Unidades Recebidas", 1)
            if st.form_submit_button("REGISTRAR ENTRADA"):
                df_e.loc[df_e['Nome'] == p_sel, 'Qtd_Unidades'] += q_add
                df_e.loc[df_e['Nome'] == p_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                df_e.to_csv(DB_EST, index=False)
                st.success("Estoque Atualizado!")
                st.rerun()
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # ABA: GESTÃO DE CASCOS (ESTOQUE VAZIOS + DÍVIDAS)
    # =================================================================
    elif menu == "🍶 Gestão de Cascos":
        st.title("🍶 Vasilhames e Cascos")
        
        # Métricas de Vazios no Depósito
        cols_ec = st.columns(4)
        for i, row in df_ec.iterrows():
            cols_ec[i].metric(row['Tipo'], f"{row['Qtd']} un")
        
        st.markdown("---")
        col_l, col_r = st.columns([1, 1.5])
        
        with col_l:
            st.subheader("➕ Lançar Dívida")
            with st.form("f_casco"):
                cli = st.text_input("Nome do Cliente").upper()
                tip = st.selectbox("Vasilhame", df_ec['Tipo'].tolist())
                qtd = st.number_input("Quantidade", 1)
                if st.form_submit_button("REGISTRAR"):
                    if cli:
                        c_id = f"C{datetime.now().strftime('%H%M%S')}"
                        pd.concat([df_c, pd.DataFrame([[c_id, datetime.now().strftime("%d/%m %H:%M"), cli, tip, qtd, "DEVE", n_log]], columns=df_c.columns)]).to_csv(DB_CAS, index=False)
                        st.rerun()

        with col_r:
            st.subheader("🔴 Pendências Ativas")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"{r['Cliente']} | {r['Qtd']}x {r['Tipo']}"):
                    bc1, bc2 = st.columns(2)
                    if bc1.button("📥 DEVOLVEU CASCO", key=f"dev_{r['ID']}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(DB_CAS, index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(DB_EST_CASCOS, index=False)
                        st.rerun()
                    if bc2.button("💰 PAGOU DINHEIRO", key=f"pag_{r['ID']}"):
                        df_c.at[i, 'Status'] = "PAGOU $"
                        df_c.to_csv(DB_CAS, index=False)
                        st.rerun()

    # =================================================================
    # ABA: MAPA DE PILARES (AMARRAÇÃO 3x2 / 2x3)
    # =================================================================
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("➕ MONTAR CAMADA"):
            p_sel = st.selectbox("Pilar", ["+ Novo"] + df_pi['Pilar'].unique().tolist())
            n_p = st.text_input("Nome").upper() if p_sel == "+ Novo" else p_sel
            if n_p:
                df_f = df_pi[df_pi['Pilar'] == n_p]
                cam = 1 if df_f.empty else df_f['Camada'].max() + 1
                at, fr = (3, 2) if cam % 2 != 0 else (2, 3)
                st.info(f"Camada {cam}: Lógica {at}x{fr}")
                
                novos = []
                c_m1, c_m2 = st.columns(2)
                for i in range(at+fr):
                    col_target = c_m1 if (i+1) <= at else c_m2
                    beb = col_target.selectbox(f"Posição {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pil_{i}_{cam}")
                    avu = col_target.number_input(f"Avulsos {i+1}", 0, key=f"av_{i}_{cam}")
                    if beb != "Vazio":
                        novos.append([f"{n_p}_{cam}_{i+1}", n_p, cam, i+1, beb, avu])
                
                if st.button("SALVAR CAMADA"):
                    pd.concat([df_pi, pd.DataFrame(novos, columns=df_pi.columns)]).to_csv(DB_PIL, index=False)
                    st.rerun()

        for p in df_pi['Pilar'].unique():
            st.subheader(f"📍 Pilar {p}")
            p_data = df_pi[df_pi['Pilar'] == p]
            for c in sorted(p_data['Camada'].unique(), reverse=True):
                st.write(f"Camada {c}")
                slots = st.columns(5)
                for _, r in p_data[p_data['Camada'] == c].iterrows():
                    with slots[int(r['Posicao'])-1]:
                        st.write(f"**{r['Bebida']}**\n+{r['Avulsos']}")
                        if st.button("SAÍDA", key=f"ret_{r['ID']}"):
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pi[df_pi['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            st.rerun()

    # =================================================================
    # ABA: PERFIL
    # =================================================================
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações")
        f = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
        if st.button("ATUALIZAR"):
            if f:
                img = Image.open(f); img.thumbnail((150, 150)); buf = io.BytesIO(); img.save(buf, format="PNG")
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = base64.b64encode(buf.getvalue()).decode()
                df_u.to_csv(DB_USR, index=False); st.rerun()
