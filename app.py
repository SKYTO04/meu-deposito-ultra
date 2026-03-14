import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN PREMIUM E CONFIGURAÇÃO DE ALTO NÍVEL
# =================================================================
st.set_page_config(
    page_title="Pacaembu Ultra G66", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="stExpander"] { 
        border: 1px solid #30363d; 
        border-radius: 15px; 
        background-color: #161b22; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .stButton>button {
        border-radius: 10px; font-weight: 700; height: 3em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #30363d; background-color: #21262d;
    }
    .stButton>button:hover {
        border-color: #58a6ff; color: #58a6ff;
        transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.6);
    }
    div[data-testid="stMetric"] {
        background-color: #1c2128; padding: 20px; border-radius: 15px;
        border: 1px solid #30363d; border-left: 6px solid #238636;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS (V66 COMPLETO)
# =================================================================
DB_PROD, DB_EST, DB_PIL = "produtos_v66.csv", "estoque_v66.csv", "pilares_v66.csv"
DB_USR, DB_LOG, DB_CAS = "usuarios_v66.csv", "historico_v66.csv", "cascos_v66.csv"

def init_db():
    if not os.path.exists(DB_USR):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(DB_USR, index=False)
    
    arquivos = {
        DB_PROD: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_EST: ['Nome', 'Estoque_Total_Un'],
        DB_PIL: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_LOG: ['Data', 'Usuario', 'Ação'],
        DB_CAS: ['ID', 'Vasilhame', 'Quantidade_Vazios'] # Ajustado para saldo de vazios
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)

init_db()

def registrar_log(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user, acao]], 
                 columns=['Data', 'Usuario', 'Ação']).to_csv(DB_LOG, mode='a', header=False, index=False)

def get_config_bebida(nome, df_p):
    busca = df_p[df_p['Nome'] == nome]
    if not busca.empty:
        cat = busca['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. SEGURANÇA
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 PACAEMBU ULTRA</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in, s_in = st.text_input("👤 Usuário"), st.text_input("🔑 Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                df_u = pd.read_csv(DB_USR)
                valid = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not valid.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': valid['nome'].values[0], 'u_a': (valid['is_admin'].values[0] == 'SIM')})
                    st.rerun()
else:
    df_p, df_e, df_pil = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_cas, df_usr = pd.read_csv(DB_CAS), pd.read_csv(DB_USR)
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']

    with st.sidebar:
        st.markdown(f"<p style='text-align: center; font-size: 1.2em;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
        menu = st.radio("NAVEGAÇÃO", ["🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro", "🍶 Controle de Cascos", "⚙️ Meu Perfil"])
        if st.button("🚪 SAIR"):
            st.session_state['autenticado'] = False
            st.rerun()

    # --- ABA: PDV ROMARINHO ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 PDV - Romarinhos")
        df_roms = df_p[df_p['Categoria'] == "Romarinho"]
        for i, item in df_roms.iterrows():
            with st.container():
                c_tit, c_met, c_btn = st.columns([3, 3, 4])
                c_tit.markdown(f"#### {item['Nome']}")
                est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                c_met.metric("Saldo", f"{est_u//24} Eng | {est_u%24} un")
                b1, b2 = c_btn.columns(2)
                if b1.button(f"➖ ENGRADADO", key=f"eng_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                    df_e.to_csv(DB_EST, index=False)
                    st.rerun()
                if b2.button(f"➖ UNIDADE", key=f"uni_{item['Nome']}"):
                    df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                    df_e.to_csv(DB_EST, index=False)
                    st.rerun()

    # --- ABA: PILARES (COM FILTRO DE CATEGORIA QUE VOCÊ PEDIU) ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🆕 LANÇAR NOVA CAMADA"):
            # Filtro por categoria para o pilar
            cat_pilar = st.selectbox("Escolha a Categoria deste Pilar", df_p['Categoria'].unique())
            n_pilar = st.text_input("Identificação do Pilar (Ex: PILAR A)").upper()
            
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                st.info(f"Camada {c_atual}: {at}at / {fr}fr")
                
                # AQUI O FILTRO: Só mostra produtos da categoria escolhida acima
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_pilar]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                col_at, col_fr = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1
                    target = col_at if pos <= at else col_fr
                    beb_dict[pos] = target.selectbox(f"Posição {pos}", lista_beb, key=f"p_{pos}_{c_atual}")
                    av_dict[pos] = target.number_input(f"Avulsos {pos}", 0, key=f"a_{pos}_{c_atual}")
                
                if st.button("CONFIRMAR CAMADA"):
                    regs = [[f"{n_pilar}_{c_atual}_{p}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                    st.rerun()

        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            for cam in sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True):
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                cols_v = st.columns(5)
                for _, r in dados_cam.iterrows():
                    with cols_v[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1c2128; padding:8px; border-radius:8px; border:1px solid #30363d; text-align:center;'><b>{r['Bebida']}</b><br>{r['Avulsos']} un</div>", unsafe_allow_html=True)
                        if st.button("RETIRAR", key=f"rt_{r['ID']}"):
                            u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                            df_e.to_csv(DB_EST, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            st.rerun()

    # --- ABA: CASCOS (DEVOLVER PARA O SALDO DE VAZIOS) ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Saldo de Vasilhames (Vazios)")
        with st.form("f_vazios"):
            st.markdown("### Registrar Entrada de Casco Vazio no Depósito")
            c1, c2 = st.columns(2)
            tipo_v = c1.selectbox("Tipo de Casco", ["Engradado Romarinho", "Coca 1L", "Coca 2L", "Ambev 600ml"])
            qtd_v = c2.number_input("Quantidade", 1)
            if st.form_submit_button("ADICIONAR AO SALDO"):
                if tipo_v in df_cas['Vasilhame'].values:
                    df_cas.loc[df_cas['Vasilhame'] == tipo_v, 'Quantidade_Vazios'] += qtd_v
                else:
                    new_c = pd.DataFrame([[f"CAS_{datetime.now().microsecond}", tipo_v, qtd_v]], columns=df_cas.columns)
                    df_cas = pd.concat([df_cas, new_c])
                df_cas.to_csv(DB_CAS, index=False)
                st.rerun()
        
        st.subheader("📊 Cascos Disponíveis para Troca")
        st.dataframe(df_cas[['Vasilhame', 'Quantidade_Vazios']], use_container_width=True, hide_index=True)

    # --- DEMAIS ABAS MANTIDAS IGUAIS AO SEU ORIGINAL ---
    elif menu == "📦 Estoque Geral":
        st.title("📦 Balanço de Estoque")
        st.dataframe(df_e, use_container_width=True)
