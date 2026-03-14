import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from PIL import Image
import io
import base64

# =================================================================
# 1. SETUP DE INTERFACE E CSS BRUTALISTA (ULTRA DARK)
# =================================================================
st.set_page_config(page_title="PACAEMBU G86 - OMNI PRESTIGE", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    /* Reset e Fundo */
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    
    /* Sidebar Industrial */
    [data-testid="stSidebar"] { 
        background-color: #161B22; 
        border-right: 1px solid #30363D; 
    }
    
    /* Cards de Métricas */
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #58A6FF;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Botões de Ação Pesada */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 800;
        height: 3.8em;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: 1px solid #30363D;
        background-color: #21262D;
        color: #C9D1D9;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #58A6FF;
        color: #58A6FF;
        background-color: #30363D;
        transform: translateY(-2px);
    }
    
    /* Títulos */
    h1, h2, h3 { color: #58A6FF !important; font-weight: 900 !important; text-transform: uppercase; }
    
    /* Estilo de Perfil */
    .profile-frame {
        text-align: center;
        padding: 10px;
        border-bottom: 1px solid #30363D;
        margin-bottom: 20px;
    }
    .profile-img {
        border-radius: 50%;
        border: 3px solid #58A6FF;
        object-fit: cover;
        box-shadow: 0 0 15px rgba(88, 166, 255, 0.3);
    }
    
    /* Tabelas e Dataframes */
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    
    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #0D1117 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE BANCO DE DADOS (PERSISTÊNCIA V86)
# =================================================================
V = "v86_final"
DB = {
    'prod': f'prod_{V}.csv', 'est': f'est_{V}.csv', 'vendas': f'vendas_{V}.csv',
    'cascos': f'cas_{V}.csv', 'ec': f'ec_{V}.csv', 'pi': f'pi_{V}.csv', 'usr': f'usr_{V}.csv'
}

def init_db():
    structs = {
        'prod': ['Categoria', 'Nome', 'Preco_Custo', 'Preco_Venda', 'Estoque_Minimo'],
        'est': ['Nome', 'Qtd_Unidades', 'Ultima_Entrada'],
        'vendas': ['ID', 'Data', 'Hora', 'Produto', 'Qtd', 'Custo_T', 'Venda_T', 'Usuario'],
        'cascos': ['ID', 'Data', 'Cliente', 'Tipo', 'Qtd', 'Status', 'Resp'],
        'ec': ['Tipo', 'Qtd'],
        'pi': ['ID', 'Pilar', 'Camada', 'Pos', 'Bebida', 'Avulsos'],
        'usr': ['user', 'nome', 'senha', 'foto']
    }
    for key, path in DB.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=structs[key])
            if key == 'ec':
                df = pd.DataFrame([["Coca 1L", 0], ["Coca 2L", 0], ["Engradado", 0], ["Litrinho", 0]], columns=['Tipo', 'Qtd'])
            if key == 'usr':
                df = pd.DataFrame([['admin', 'GERENTE MESTRE', '123', '']], columns=structs[key])
            df.to_csv(path, index=False)

init_db()

# =================================================================
# 3. UTILITÁRIOS (IMAGEM E CONVERSÃO)
# =================================================================
def get_img_64(img_file):
    img = Image.open(img_file).resize((300, 300))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# =================================================================
# 4. CONTROLE DE ACESSO (SESSÃO)
# =================================================================
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'nome': '', 'foto': '', 'user': ''})

if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>PACAEMBU OMNI</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("USUÁRIO")
            s = st.text_input("SENHA", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                df_u = pd.read_csv(DB['usr'])
                user_match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not user_match.empty:
                    st.session_state.update({
                        'auth': True, 'nome': user_match['nome'].values[0],
                        'foto': user_match['foto'].values[0], 'user': u
                    })
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas.")
else:
    # Carregamento Global das Tabelas
    df_p, df_e, df_v = pd.read_csv(DB['prod']), pd.read_csv(DB['est']), pd.read_csv(DB['vendas'])
    df_ec, df_c, df_pi = pd.read_csv(DB['ec']), pd.read_csv(DB['cascos']), pd.read_csv(DB['pi'])
    u_logado = st.session_state['nome']

    # --- SIDEBAR PROFISSIONAL ---
    with st.sidebar:
        st.markdown('<div class="profile-frame">', unsafe_allow_html=True)
        if st.session_state['foto']:
            st.markdown(f'<img src="data:image/png;base64,{st.session_state["foto"]}" class="profile-img" width="160">', unsafe_allow_html=True)
        else:
            st.info("Sem Foto")
        st.markdown(f'<h3>{st.session_state["nome"]}</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        menu = st.radio("NAVEGAÇÃO MESTRE", [
            "📊 DASHBOARD", "📦 ENTRADA BRUTA", "🍻 PDV ROMARINHO", 
            "🏗️ MAPA DE PILARES", "🍶 GESTÃO DE CASCOS", "🕒 HISTÓRICO", "⚙️ CONFIGURAÇÕES"
        ])
        
        if st.button("DESCONECTAR"):
            st.session_state['auth'] = False
            st.rerun()

    # =================================================================
    # MÓDULO 1: DASHBOARD (FINANCEIRO REAL)
    # =================================================================
    if menu == "📊 DASHBOARD":
        st.title("📊 Painel de Patrimônio")
        if not df_e.empty and not df_p.empty:
            df_f = pd.merge(df_e, df_p, on="Nome")
            df_f['Pat_Custo'] = df_f['Qtd_Unidades'] * df_f['Preco_Custo']
            df_f['Pat_Venda'] = df_f['Qtd_Unidades'] * df_f['Preco_Venda']
            df_f['Lucro'] = df_f['Pat_Venda'] - df_f['Pat_Custo']

            c1, c2, c3 = st.columns(3)
            c1.metric("Investimento Atual", f"R$ {df_f['Pat_Custo'].sum():,.2f}")
            c2.metric("Venda Potencial", f"R$ {df_f['Pat_Venda'].sum():,.2f}")
            c3.metric("Lucro Estimado", f"R$ {df_f['Lucro'].sum():,.2f}")

            st.markdown("---")
            col_left, col_right = st.columns(2)
            with col_left:
                fig_pie = px.pie(df_f, values='Pat_Venda', names='Categoria', hole=0.4, title="Distribuição por Categoria", template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_right:
                fig_bar = px.bar(df_f.nlargest(8, 'Lucro'), x='Nome', y='Lucro', title="Top 8 Produtos mais Lucrativos", template="plotly_dark", color_discrete_sequence=['#58A6FF'])
                st.plotly_chart(fig_bar, use_container_width=True)

    # =================================================================
    # MÓDULO 2: ENTRADA BRUTA (ENG + AVU)
    # =================================================================
    elif menu == "📦 ENTRADA BRUTA":
        st.title("📦 Entrada de Mercadoria")
        with st.form("entrada_form"):
            item_sel = st.selectbox("Selecione o Item", df_p['Nome'].tolist())
            col_1, col_2 = st.columns(2)
            e_qtd = col_1.number_input("Engradados Fechados (x24)", 0, step=1)
            a_qtd = col_2.number_input("Unidades Soltas", 0, step=1)
            total_u = (e_qtd * 24) + a_qtd
            
            if st.form_submit_button("CONFIRMAR ENTRADA NA BASE"):
                if total_u > 0:
                    df_e.loc[df_e['Nome'] == item_sel, 'Qtd_Unidades'] += total_u
                    df_e.loc[df_e['Nome'] == item_sel, 'Ultima_Entrada'] = datetime.now().strftime("%d/%m %H:%M")
                    df_e.to_csv(DB['est'], index=False)
                    st.success(f"Carga de {total_u} un registrada para {item_sel}!")
                    st.rerun()

        st.subheader("Situação Atual do Estoque")
        df_view = df_e.copy()
        df_view['Eng'] = df_view['Qtd_Unidades'] // 24
        df_view['Un'] = df_view['Qtd_Unidades'] % 24
        st.dataframe(df_view[['Nome', 'Eng', 'Un', 'Qtd_Unidades', 'Ultima_Entrada']], use_container_width=True, hide_index=True)

    # =================================================================
    # MÓDULO 3: PDV RÁPIDO ROMARINHO
    # =================================================================
    elif menu == "🍻 PDV ROMARINHO":
        st.title("🍻 Ponto de Venda")
        romas = df_p[df_p['Categoria'] == "Romarinho"]
        
        for _, it in romas.iterrows():
            st_data = df_e[df_e['Nome'] == it['Nome']]
            if not st_data.empty:
                q = int(st_data['Qtd_Unidades'].values[0])
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.markdown(f"### {it['Nome']}\n**R$ {it['Preco_Venda']:.2f}**")
                    c2.metric("Estoque", f"{q//24}E | {q%24}U")
                    
                    if c3.button("VENDER ENG", key=f"v_e_{it['Nome']}") and q >= 24:
                        df_e.loc[df_e['Nome'] == it['Nome'], 'Qtd_Unidades'] -= 24
                        df_e.to_csv(DB['est'], index=False)
                        new_v = [[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), it['Nome'], 24, it['Preco_Custo']*24, it['Preco_Venda']*24, u_logado]]
                        pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                        st.rerun()
                        
                    if c4.button("VENDER UN", key=f"v_u_{it['Nome']}") and q >= 1:
                        df_e.loc[df_e['Nome'] == it['Nome'], 'Qtd_Unidades'] -= 1
                        df_e.to_csv(DB['est'], index=False)
                        new_v = [[f"V{datetime.now().second}", datetime.now().strftime("%d/%m"), datetime.now().strftime("%H:%M"), it['Nome'], 1, it['Preco_Custo'], it['Preco_Venda'], u_logado]]
                        pd.DataFrame(new_v).to_csv(DB['vendas'], mode='a', header=False, index=False)
                        st.rerun()
                st.markdown("---")

    # =================================================================
    # MÓDULO 4: MAPA DE PILARES (LOGÍSTICA)
    # =================================================================
    elif menu == "🏗️ MAPA DE PILARES":
        st.title("🏗️ Gestão de Pilares e Amarração")
        p_sel = st.selectbox("Escolha o Pilar", ["Pilar A", "Pilar B", "Pilar C", "Pilar D"])
        
        with st.expander("➕ Adicionar Nova Camada"):
            existente = df_pi[df_pi['Pilar'] == p_sel]
            cam = 1 if existente.empty else existente['Camada'].max() + 1
            st.info(f"Montando Camada {cam}")
            
            p_novos = []
            cols_p = st.columns(5)
            for i in range(5):
                with cols_p[i]:
                    b = st.selectbox(f"Posição {i+1}", ["Vazio"] + df_p['Nome'].tolist(), key=f"pi_b_{i}")
                    a = st.number_input(f"Avulsos {i+1}", 0, key=f"pi_a_{i}")
                    if b != "Vazio":
                        p_novos.append([f"{p_sel}_{cam}_{i}", p_sel, cam, i+1, b, a])
            
            if st.button("SALVAR CAMADA NO PILAR"):
                pd.concat([df_pi, pd.DataFrame(p_novos, columns=df_pi.columns)]).to_csv(DB['pi'], index=False)
                st.rerun()

        # Visualização e Baixa
        for c in sorted(df_pi[df_pi['Pilar'] == p_sel]['Camada'].unique(), reverse=True):
            st.subheader(f"Camada {c}")
            slots = st.columns(5)
            for _, r in df_pi[(df_pi['Pilar'] == p_sel) & (df_pi['Camada'] == c)].iterrows():
                with slots[int(r['Pos'])-1]:
                    st.write(f"**{r['Bebida']}**")
                    if st.button("BAIXA", key=f"baixa_{r['ID']}"):
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Qtd_Unidades'] -= (6 + r['Avulsos'])
                        df_e.to_csv(DB['est'], index=False)
                        df_pi[df_pi['ID'] != r['ID']].to_csv(DB['pi'], index=False)
                        st.rerun()

    # =================================================================
    # MÓDULO 5: GESTÃO DE CASCOS
    # =================================================================
    elif menu == "🍶 GESTÃO DE CASCOS":
        st.title("🍶 Controle de Vasilhames")
        m_c = st.columns(4)
        for i, row in df_ec.iterrows():
            m_c[i].metric(row['Tipo'], f"{row['Qtd']} un")

        st.markdown("---")
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("Registrar Dívida")
            with st.form("f_casco"):
                cli, tip, q_c = st.text_input("Cliente").upper(), st.selectbox("Tipo", df_ec['Tipo'].tolist()), st.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR PENDÊNCIA"):
                    if cli:
                        new_c = [[f"C{datetime.now().second}", datetime.now().strftime("%d/%m"), cli, tip, q_c, "DEVE", u_logado]]
                        pd.concat([df_c, pd.DataFrame(new_c, columns=df_c.columns)]).to_csv(DB['cascos'], index=False)
                        st.rerun()
        with cl2:
            st.subheader("Pendências Ativas")
            for i, r in df_c[df_c['Status'] == "DEVE"].iterrows():
                with st.expander(f"⚠️ {r['Cliente']} deve {r['Qtd']} {r['Tipo']}"):
                    if st.button("RECEBER CASCO", key=f"rec_{i}"):
                        df_c.at[i, 'Status'] = "DEVOLVEU"
                        df_c.to_csv(DB['cascos'], index=False)
                        df_ec.loc[df_ec['Tipo'] == r['Tipo'], 'Qtd'] += r['Qtd']
                        df_ec.to_csv(DB['ec'], index=False)
                        st.rerun()

    # =================================================================
    # MÓDULO 6: HISTÓRICO E ESTORNO
    # =================================================================
    elif menu == "🕒 HISTÓRICO":
        st.title("🕒 Histórico de Transações")
        busca = st.text_input("Buscar por Produto ou Operador").upper()
        df_h = df_v[df_v['Produto'].str.contains(busca) | df_v['Usuario'].str.contains(busca)]
        st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("Anular Operação")
        if not df_v.empty:
            last_v = df_v.tail(5).iloc[::-1]
            for idx, row in last_v.iterrows():
                cc1, cc2 = st.columns([5, 1])
                cc1.warning(f"{row['Data']} {row['Hora']} - {row['Produto']} - {row['Qtd']}un - Total: R${row['Venda_T']}")
                if cc2.button("ESTORNAR", key=f"estorno_{idx}"):
                    df_e.loc[df_e['Nome'] == row['Produto'], 'Qtd_Unidades'] += row['Qtd']
                    df_e.to_csv(DB['est'], index=False)
                    df_v.drop(idx).to_csv(DB['vendas'], index=False)
                    st.rerun()

    # =================================================================
    # MÓDULO 7: CONFIGURAÇÕES E PERFIL
    # =================================================================
    elif menu == "⚙️ CONFIGURAÇÕES":
        st.title("⚙️ Painel de Controle")
        t1, t2 = st.tabs(["Gerenciar Perfil", "Cadastrar Produtos"])
        
        with t1:
            st.subheader("Dados do Operador")
            up = st.file_uploader("Sua Foto de Perfil", type=['png', 'jpg', 'jpeg'])
            if up:
                b64 = get_img_64(up)
                df_u = pd.read_csv(DB['usr'])
                df_u.loc[df_u['user'] == st.session_state['user'], 'foto'] = b64
                df_u.to_csv(DB['usr'], index=False)
                st.session_state['foto'] = b64
                st.success("Foto atualizada! Reinicie para aplicar.")
                
        with t2:
            with st.form("cad_prod"):
                n = st.text_input("Nome").upper()
                c = st.selectbox("Categoria", ["Romarinho", "Lata", "Garrafa", "Litro", "Refrigerante", "Outros"])
                col_c, col_v, col_m = st.columns(3)
                pc = col_c.number_input("Preço de Custo")
                pv = col_v.number_input("Preço de Venda")
                em = col_m.number_input("Estoque Mínimo", 24)
                if st.form_submit_button("SALVAR PRODUTO"):
                    if n:
                        pd.concat([df_p, pd.DataFrame([[c, n, pc, pv, em]], columns=df_p.columns)]).to_csv(DB['prod'], index=False)
                        pd.concat([df_e, pd.DataFrame([[n, 0, "-"]], columns=df_e.columns)]).to_csv(DB['est'], index=False)
                        st.rerun()
            st.dataframe(df_p, use_container_width=True)
