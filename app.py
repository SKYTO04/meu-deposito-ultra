import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
import base64
from PIL import Image
import io

# =================================================================
# 1. SETUP DE INTERFACE (DARK PRESTIGE TOTAL - SEM SIMPLIFICAR)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

# Inicialização de variáveis de estado
for key, val in {'auth': False, 'nome': '', 'foto': '', 'user': '', 'role': 'OPERADOR'}.items():
    if key not in st.session_state: st.session_state[key] = val

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; min-width: 300px; }
    div[data-testid="metric-container"] {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: 20px; border-left: 5px solid #58A6FF; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 800; height: 3.8em;
        text-transform: uppercase; border: 1px solid #30363D;
        background-color: #21262D; color: #C9D1D9; transition: 0.2s;
    }
    .stButton>button:hover { border-color: #58A6FF !important; color: #58A6FF !important; transform: scale(1.02); }
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; letter-spacing: -1px; }
    .profile-img { border-radius: 50%; border: 3px solid #58A6FF; object-fit: cover; margin-bottom: 15px; box-shadow: 0 0 15px rgba(88,166,255,0.4); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161B22; border-radius: 8px 8px 0 0; padding: 12px 25px; color: #C9D1D9; font-weight: 700;
    }
    .pilar-card { background: #1C2128; border: 1px solid #30363D; border-radius: 10px; padding: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS (V86 COMPLETA)
# =================================================================
V = "v86_final_prestige"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv', 'log_cad': f'log_cad_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'foto', 'cargo'],
        'log_cad': ['Data', 'Hora', 'Acao', 'Item', 'Usuario']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'usr': 
                df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '', 'ADMIN']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

# =================================================================
# 3. SISTEMA DE LOGIN COM FOTO
# =================================================================
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>PACAEMBU OMNI PRESTIGE</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("USUÁRIO MASTER")
            s = st.text_input("SENHA ACESSO", type="password")
            if st.form_submit_button("DESBLOQUEAR SISTEMA"):
                df_u = pd.read_csv(DB['usr'])
                res = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not res.empty:
                    st.session_state.update({
                        'auth': True, 'nome': res['nome'].values[0], 'user': u,
                        'role': res['cargo'].values[0],
                        'foto': str(res['foto'].values[0]) if pd.notna(res['foto'].values[0]) else ''
                    })
                    st.rerun()
                else: st.error("CREDENCIAIS INVÁLIDAS")
else:
    # Carregamento Bruto de Dados
    df_p = pd.read_csv(DB['prod'])
    df_e = pd.read_csv(DB['est'])
    df_v = pd.read_csv(DB['vendas'])
    df_pi = pd.read_csv(DB['pi'])
    df_u = pd.read_csv(DB['usr'])
    df_log = pd.read_csv(DB['log_cad'])

    with st.sidebar:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if len(st.session_state['foto']) > 100:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" class="profile-img" width="180">', unsafe_allow_html=True)
        st.markdown(f"## {st.session_state['nome']}")
        st.markdown(f"<span style='color: #58A6FF;'>{st.session_state['role']}</span>", unsafe_allow_html=True)
        st.markdown('</div><br>', unsafe_allow_html=True)
        
        menu = st.radio("SISTEMA OMNI", ["📊 DASHBOARD", "📦 ESTOQUE DINÂMICO", "🏗️ MAPA DE PILARES", "🍻 PDV RÁPIDO", "🕒 HISTÓRICO BRUTO", "⚙️ CONFIGS"])
        
        if st.button("🔴 ENCERRAR SESSÃO"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # 4. MAPA DE PILARES (LÓGICA DE AMARRAÇÃO COMPLETA - BRUTA)
    # =================================================================
    if menu == "🏗️ MAPA DE PILARES":
        st.title("🏗️ Gestão de Amarração e Pilares")
        
        t_p1, t_p2 = st.tabs(["🏛️ VISUALIZAR MAPA", "🛠️ CONFIGURAR AMARRAÇÃO"])
        
        with t_p2:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_amarre"):
                    st.markdown("### Montar Nova Camada de Pilar")
                    c1, c2 = st.columns(2)
                    nome_p = c1.text_input("NOME DO PILAR (Ex: COCA 2L, BRAHMA, SKOL)").upper()
                    nivel_c = c2.number_input("NÍVEL DA CAMADA (Altura)", 1)
                    
                    st.markdown("---")
                    st.write("Defina os 5 produtos que compõem a amarração desta camada:")
                    cols = st.columns(5)
                    novos_v86 = []
                    for i in range(1, 6):
                        with cols[i-1]:
                            st.markdown(f"**POSIÇÃO {i}**")
                            p_escolha = st.selectbox(f"Produto {i}", ["Vazio"] + df_p['Nome'].tolist(), key=f"p_v86_{i}")
                            a_escolha = st.number_input(f"Avulsos {i}", 0, key=f"a_v86_{i}")
                            if p_escolha != "Vazio" and nome_p != "":
                                novos_v86.append([f"PI{datetime.now().microsecond}{i}", nome_p, nivel_c, i, p_escolha, a_escolha])
                    
                    if st.form_submit_button("💾 SALVAR AMARRAÇÃO NO BANCO"):
                        if novos_v86:
                            pd.concat([df_pi, pd.DataFrame(novos_v86, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                            st.success("Configuração de Amarração Salva!")
                            st.rerun()
            else:
                st.warning("Apenas Administradores podem configurar amarrações.")

        with t_p1:
            pilares_disponiveis = sorted(df_pi['Pilar'].unique())
            if pilares_disponiveis:
                col_sel, col_filtro = st.columns([2, 2])
                p_atual = col_sel.selectbox("Selecione o Pilar:", pilares_disponiveis)
                
                # FILTRO DE CATEGORIA (O que você pediu: só mostra Refri e Outros no Mapa)
                df_m = pd.merge(df_pi, df_p[['Nome', 'Categoria']], left_on='Bebida', right_on='Nome', how='left')
                df_show = df_m[(df_m['Pilar'] == p_atual) & (df_m['Categoria'].isin(["Refrigerante", "Outros"]))]
                
                camadas = sorted(df_show['Camada'].unique(), reverse=True)
                for cam in camadas:
                    st.markdown(f"#### Camada Nível {cam}")
                    grade = st.columns(5)
                    itens_cam = df_show[df_show['Camada'] == cam]
                    for _, r in itens_cam.iterrows():
                        with grade[int(r['Pos'])-1]:
                            st.markdown(f"""
                            <div class="pilar-card">
                                <b>{r['Bebida']}</b><br>
                                <small>+{r['Avulsos']} Avulsos</small>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("BAIXAR CARGA", key=f"bx_v86_{r['ID']}"):
                                f_baixa = 6 if r['Categoria'] == "Refrigerante" else 1
                                total_desconto = f_baixa + int(r['Avulsos'])
                                # Desconto no estoque
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= total_desconto
                                df_e.to_csv(DB['est'], index=False)
                                # Remove a posição do mapa
                                df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                                st.rerun()
            else:
                st.info("Nenhum pilar com amarrações de Refrigerante/Outros configurado.")

    # =================================================================
    # 5. ESTOQUE DINÂMICO (COM REGRAS BRUTAS)
    # =================================================================
    elif menu == "📦 ESTOQUE DINÂMICO":
        st.title("📦 Gestão de Estoque Reativo")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### Entrada Manual")
            p_ent = st.selectbox("Produto alvo", df_p['Nome'].tolist())
            cat_ent = df_p[df_p['Nome'] == p_ent]['Categoria'].values[0]
            
            # Multiplicadores Exatos
            if cat_ent in ["Romarinho", "Litrinho", "Long Neck"]: f, t = 24, "Engradado (24u)"
            elif cat_ent == "Cerveja Lata": f, t = 12, "Fardo (12u)"
            elif cat_ent == "Refrigerante": f, t = 6, "Fardo 2L (6u)"
            else: f, t = 1, "Unidade Individual"
            
            st.write(f"Categoria: **{cat_ent}**")
            with st.form("ent_v86"):
                fardos = st.number_input(f"Qtd de {t}", 0)
                avulsos = st.number_input("Unidades Avulsas", 0)
                if st.form_submit_button("CONFIRMAR ENTRADA"):
                    total = (fardos * f) + avulsos
                    df_e.loc[df_e['Nome'] == p_ent, 'Qtd_Unidades'] += total
                    df_e.to_csv(DB['est'], index=False)
                    st.success(f"Adicionado: {total} un.")
                    st.rerun()
        
        with c2:
            st.markdown("### Status do Inventário")
            st.dataframe(df_e, use_container_width=True, hide_index=True)

    # =================================================================
    # 6. PDV RÁPIDO E AUDITORIA
    # =================================================================
    elif menu == "🍻 PDV RÁPIDO":
        st.title("🍻 Venda Expressa Omni")
        for _, r in df_p.iterrows():
            q_atual = df_e[df_e['Nome'] == r['Nome']]['Qtd_Unidades'].values[0]
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 2])
            c1.markdown(f"### {r['Nome']}")
            c2.metric("Preço", f"R$ {r['Preco_Venda']:.2f}")
            c3.metric("Estoque", f"{q_atual} un")
            if c4.button("VENDER UNIDADE", key=f"vd_{r['Nome']}"):
                df_e.loc[df_e['Nome'] == r['Nome'], 'Qtd_Unidades'] -= 1
                df_e.to_csv(DB['est'], index=False)
                # Log de Venda
                pd.DataFrame([[f"V{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), r['Nome'], 1, r['Preco_Custo'], r['Preco_Venda'], st.session_state['nome']]]).to_csv(DB['vendas'], mode='a', header=False, index=False)
                st.rerun()

    elif menu == "⚙️ CONFIGS":
        st.title("⚙️ Painel de Controle e Auditoria")
        tab_p, tab_u, tab_l = st.tabs(["📦 PRODUTOS", "👥 USUÁRIOS", "📜 LOG DE AUDITORIA"])
        
        with tab_p:
            with st.form("cad_prod_v86"):
                st.markdown("### Cadastrar Novo Item")
                cp1, cp2 = st.columns(2)
                nome_n = cp1.text_input("NOME DO PRODUTO").upper()
                cat_n = cp1.selectbox("CATEGORIA", ["Romarinho", "Litrinho", "Long Neck", "Cerveja Lata", "Refrigerante", "Outros"])
                pc_n = cp2.number_input("PREÇO DE CUSTO", 0.0)
                pv_n = cp2.number_input("PREÇO DE VENDA", 0.0)
                if st.form_submit_button("REGISTRAR PRODUTO"):
                    pd.concat([df_p, pd.DataFrame([[cat_n, nome_n, pc_n, pv_n, 12]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                    pd.concat([df_e, pd.DataFrame([[nome_n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                    st.rerun()
        
        with tab_u:
            if st.session_state['role'] == "ADMIN":
                with st.form("cad_user_v86"):
                    cu1, cu2 = st.columns(2)
                    un, nn, sn = cu1.text_input("User Login"), cu1.text_input("Nome Real"), cu2.text_input("Senha")
                    cargo = cu2.selectbox("Cargo", ["OPERADOR", "ADMIN"])
                    arq = st.file_uploader("Foto de Perfil")
                    if st.form_submit_button("CRIAR CONTA"):
                        img_str = ""
                        if arq:
                            img_str = base64.b64encode(arq.read()).decode()
                        pd.concat([df_u, pd.DataFrame([[un, nn, sn, img_str, cargo]], columns=df_u.columns)]).to_csv(DB['usr'], index=False)
                        st.success("Usuário Criado!")
            st.dataframe(df_u[['user', 'nome', 'cargo']], use_container_width=True)

        with tab_l:
            st.dataframe(df_log.iloc[::-1], use_container_width=True)

    elif menu == "📊 DASHBOARD":
        if st.session_state['role'] == "ADMIN":
            df_dash = pd.merge(df_e, df_p, on="Nome")
            df_dash['Lucro_Unit'] = df_dash['Preco_Venda'] - df_dash['Preco_Custo']
            df_dash['Total_Est_Venda'] = df_dash['Preco_Venda'] * df_dash['Qtd_Unidades']
            df_dash['Lucro_Potencial'] = df_dash['Lucro_Unit'] * df_dash['Qtd_Unidades']
            
            c_d1, c_d2, c_d3 = st.columns(3)
            c_d1.metric("ESTOQUE TOTAL (VALOR)", f"R$ {df_dash['Total_Est_Venda'].sum():,.2f}")
            c_d2.metric("LUCRO POTENCIAL", f"R$ {df_dash['Lucro_Potencial'].sum():,.2f}")
            c_d3.metric("ITENS CADASTRADOS", len(df_p))
            
            st.plotly_chart(px.bar(df_dash, x='Nome', y='Qtd_Unidades', color='Categoria', title="Saldos por Categoria", template="plotly_dark"), use_container_width=True)

    elif menu == "🕒 HISTÓRICO BRUTO":
        st.title("🕒 Registro de Saídas e Vendas")
        st.dataframe(df_v.iloc[::-1], use_container_width=True, hide_index=True)
