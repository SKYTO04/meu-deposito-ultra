import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io

# =================================================================
# 1. DESIGN E CONFIGURAÇÃO PREMIUM
# =================================================================
st.set_page_config(
    page_title="Pacaembu Gestão v64", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para aparência "Chique"
st.markdown("""
    <style>
    /* Estilo do Fundo e Cards */
    .stApp { background-color: #0E1117; }
    div[data-testid="stExpander"] { border: 1px solid #1f2937; border-radius: 12px; background-color: #161b22; }
    
    /* Personalização de Botões */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Estilo das Métricas */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #3b82f6;
    }
    
    /* Títulos e Textos */
    h1, h2, h3 { font-family: 'Segoe UI', Roboto, sans-serif; color: #f9fafb; }
    
    /* Esconder o Menu padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS
# =================================================================
DB_PRODUTOS = "produtos_v64.csv"
DB_ESTOQUE = "estoque_v64.csv"
PILAR_ESTRUTURA = "pilares_v64.csv"
USERS_FILE = "usuarios_v64.csv"
LOG_FILE = "historico_v64.csv"
CASCOS_FILE = "cascos_v64.csv"

def init_db():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '0000-0000', '']], 
                     columns=['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']).to_csv(USERS_FILE, index=False)
    
    arquivos = {
        DB_PRODUTOS: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_ESTOQUE: ['Nome', 'Estoque_Total_Un'],
        PILAR_ESTRUTURA: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        LOG_FILE: ['Data', 'Usuario', 'Ação'],
        CASCOS_FILE: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
    }
    for arq, colunas in arquivos.items():
        if not os.path.exists(arq):
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)
    
    df_u = pd.read_csv(USERS_FILE)
    if 'foto' not in df_u.columns:
        df_u['foto'] = ''
        df_u.to_csv(USERS_FILE, index=False)

init_db()

# --- FUNÇÕES CORE ---
def log_master(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user, acao]], 
                 columns=['Data', 'Usuario', 'Ação']).to_csv(LOG_FILE, mode='a', header=False, index=False)

def conv_foto(file):
    if file:
        img = Image.open(file)
        img.thumbnail((180, 180))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    return ""

def meta_bebida(nome, df_p):
    f = df_p[df_p['Nome'] == nome]
    if not f.empty:
        c = f['Categoria'].values[0]
        if c == "Romarinho": return 24, "Engradado"
        if c == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. SEGURANÇA E LOGIN
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>💎 Depósito Pacaembu</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af;'>Controle de Estoque Profissional</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("login_moderno"):
            u_in = st.text_input("👤 Usuário")
            s_in = st.text_input("🔑 Senha", type="password")
            btn_login = st.form_submit_button("ACESSAR SISTEMA", use_container_width=True)
            if btn_login:
                df_u = pd.read_csv(USERS_FILE)
                v = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not v.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': v['nome'].values[0], 'u_a': (v['is_admin'].values[0] == 'SIM')})
                    log_master(st.session_state['u_n'], "Entrou no app")
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
else:
    # Variáveis de Sessão
    u_logado = st.session_state.get('u_l')
    n_logado = st.session_state.get('u_n')
    is_adm = st.session_state.get('u_a')

    # Carregamento de Dados
    df_p = pd.read_csv(DB_PRODUTOS)
    df_e = pd.read_csv(DB_ESTOQUE)
    df_pil = pd.read_csv(PILAR_ESTRUTURA)
    df_cas = pd.read_csv(CASCOS_FILE)
    df_usr = pd.read_csv(USERS_FILE)

    # --- SIDEBAR PERSONALIZADA ---
    st.sidebar.markdown("<h2 style='text-align: center;'>💎 PACAEMBU</h2>", unsafe_allow_html=True)
    foto_raw = df_usr[df_usr['user'] == u_logado]['foto'].values[0]
    if pd.isna(foto_raw) or foto_raw == "":
        st.sidebar.markdown("<div style='text-align: center;'><img src='https://cdn-icons-png.flaticon.com/512/149/149071.png' width='100' style='border-radius: 50%; border: 3px solid #3b82f6;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{foto_raw}' width='110' style='border-radius: 50%; border: 3px solid #3b82f6; aspect-ratio: 1/1; object-fit: cover;'></div>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"<p style='text-align: center; margin-top: 10px;'>Bem-vindo, <b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("MENU PRINCIPAL", ["🍻 PDV Romarinho", "🏗️ Mapa de Pilares", "📦 Estoque Central", "✨ Gestão de Produtos", "🍶 Vasilhames/Cascos", "⚙️ Meu Perfil"] + (["📊 Dashboards", "📜 Histórico", "👥 Equipe"] if is_adm else []))
    
    if st.sidebar.button("🚪 DESCONECTAR", use_container_width=True):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: ROMARINHO (ESTILO PDV) ---
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda - Romarinhos")
        cols_r = st.columns(2)
        df_rom = df_p[df_p['Categoria'] == "Romarinho"]
        
        for i, item in df_rom.iterrows():
            with cols_r[i % 2]:
                with st.container():
                    st.markdown(f"#### 🏷️ {item['Nome']}")
                    qtd_un = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                    
                    c_m1, c_m2 = st.columns(2)
                    c_m1.metric("Engradados", qtd_un // 24)
                    c_m2.metric("Unidades", qtd_un % 24)
                    
                    b1, b2 = st.columns(2)
                    if b1.button(f"BAIXAR ENGRADADO", key=f"e_{item['Nome']}", use_container_width=True):
                        if qtd_un >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            log_master(n_logado, f"Saída Engradado: {item['Nome']}")
                            st.rerun()
                    if b2.button(f"BAIXAR UNIDADE", key=f"u_{item['Nome']}", use_container_width=True):
                        if qtd_un >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            log_master(n_logado, f"Saída Unidade: {item['Nome']}")
                            st.rerun()
                st.markdown("---")

    # --- ABA: MAPA DE PILARES ---
    elif menu == "🏗️ Mapa de Pilares":
        st.title("🏗️ Controle de Pilares")
        with st.expander("➕ Adicionar Nova Camada de Amarração", expanded=False):
            p_sel = st.selectbox("Selecione o Pilar", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ Criar Novo" else p_sel
            if n_pilar:
                c_n = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                inv = (c_n % 2 == 0)
                at, fr = (3, 2) if not inv else (2, 3)
                st.write(f"Configuração automática: **{at} atrás e {fr} na frente** (Camada {c_n})")
                
                prods_refri = ["Vazio"] + df_p[df_p['Categoria'] == "Refrigerante"]['Nome'].tolist()
                b_dic, a_dic = {}, {}
                col_c1, col_c2 = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1
                    target_col = col_c1 if pos <= at else col_c2
                    b_dic[pos] = target_col.selectbox(f"Posição {pos}", prods_refri, key=f"sel_{pos}_{c_n}")
                    a_dic[pos] = target_col.number_input(f"Avulsos {pos}", 0, key=f"num_{pos}_{c_n}")
                
                if st.button("SALVAR CAMADA NO MAPA"):
                    novos_p = [[f"{n_pilar}_{c_n}_{p}_{datetime.now().strftime('%S')}", n_pilar, c_n, p, b, a_dic[p]] for p, b in b_dic.items() if b != "Vazio"]
                    if novos_p:
                        pd.concat([df_pil, pd.DataFrame(novos_p, columns=df_pil.columns)]).to_csv(PILAR_ESTRUTURA, index=False)
                        st.rerun()

        for pn in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 {pn}")
            for c in sorted(df_pil[df_pil['NomePilar'] == pn]['Camada'].unique(), reverse=True):
                st.markdown(f"**Camada {c}**")
                dados_c = df_pil[(df_pil['NomePilar'] == pn) & (df_pil['Camada'] == c)]
                v_cols = st.columns(5)
                for _, r in dados_c.iterrows():
                    with v_cols[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1e293b; padding:5px; border-radius:5px; text-align:center; font-size:12px;'><b>{r['Bebida']}</b><br>+{r['Avulsos']}un</div>", unsafe_allow_html=True)
                        if st.button("BAIXA", key=f"p_rt_{r['ID']}", use_container_width=True):
                            un_b, _ = meta_bebida(r['Bebida'], df_p)
                            total_s = un_b + r['Avulsos']
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_s
                            df_e.to_csv(DB_ESTOQUE, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(PILAR_ESTRUTURA, index=False)
                            log_master(n_logado, f"Baixa Pilar: {total_s}un de {r['Bebida']}")
                            st.rerun()

    # --- ABA: VASILHAMES/CASCOS ---
    elif menu == "🍶 Vasilhames/Cascos":
        st.title("🍶 Controle de Devedores e Cascos")
        with st.form("casco_moderno"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cl = c1.text_input("Nome do Cliente").upper()
            f_te = c2.text_input("WhatsApp")
            f_ti = c3.selectbox("Tipo de Casco", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "600ml"])
            f_qt = c4.number_input("Qtd", 1)
            if st.form_submit_button("REGISTRAR DÍVIDA DE CASCO"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), f_cl, f_te, f_ti, f_qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(CASCOS_FILE, index=False)
                st.rerun()

        st.subheader("🔴 Pendências em Aberto")
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            with st.container():
                l1, l2 = st.columns([7, 2])
                l1.error(f"👤 {r['Cliente']} | 🍶 {r['Quantidade']}x {r['Vasilhame']} | 📱 {r['Telefone']}")
                if l2.button("BAIXAR DÍVIDA", key=f"pay_{r['ID']}", use_container_width=True):
                    df_cas.at[i, 'Status'] = "PAGO"
                    df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(CASCOS_FILE, index=False)
                    st.rerun()
        
        st.write("---")
        with st.expander("🟢 Histórico de Devoluções (Clique para Estornar)"):
            for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(10).iterrows():
                el1, el2 = st.columns([7, 2])
                el1.success(f"OK: {r['Cliente']} devolveu {r['Quantidade']} {r['Vasilhame']} (Recebido por: {r['QuemBaixou']})")
                if el2.button("ESTORNAR", key=f"est_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "DEVE"
                    df_cas.to_csv(CASCOS_FILE, index=False)
                    st.rerun()

    # --- ABA: MEU PERFIL (FOTO) ---
    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Configurações de Perfil")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            st.markdown("### Foto Atual")
            if pd.isna(foto_raw) or foto_raw == "":
                st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)
            else:
                st.image(f"data:image/png;base64,{foto_raw}", width=150)
        with col_f2:
            st.markdown("### Alterar Foto")
            arq_foto = st.file_uploader("Selecione uma foto da sua Galeria", type=['png', 'jpg', 'jpeg'])
            if st.button("SALVAR NOVA FOTO", use_container_width=True):
                if arq_foto:
                    df_usr.loc[df_usr['user'] == u_logado, 'foto'] = conv_foto(arq_foto)
                    df_usr.to_csv(USERS_FILE, index=False)
                    st.success("Sua foto foi atualizada com sucesso!")
                    st.rerun()

    # --- ABA: ESTOQUE CENTRAL ---
    elif menu == "📦 Estoque Central":
        st.title("📦 Entrada de Mercadoria")
        if not df_p.empty:
            sel_p = st.selectbox("Escolha o Produto para Entrada", df_p['Nome'].unique())
            u_b, t_t = meta_bebida(sel_p, df_p)
            with st.form("entrada_estoque"):
                st.info(f"Configuração: Cada {t_t} contém {u_b} unidades.")
                ce1, ce2 = st.columns(2)
                f_fardos = ce1.number_input(f"Quantidade de {t_t}s", 0)
                f_avulsos = ce2.number_input("Unidades Avulsas", 0)
                if st.form_submit_button("LANÇAR NO ESTOQUE", use_container_width=True):
                    total_in = (f_fardos * u_b) + f_avulsos
                    df_e.loc[df_e['Nome'] == sel_p, 'Estoque_Total_Un'] += total_in
                    df_e.to_csv(DB_ESTOQUE, index=False)
                    log_master(n_logado, f"Entrada: +{total_in}un de {sel_p}")
                    st.rerun()
        
        st.markdown("### 📊 Saldo em Estoque")
        st.dataframe(df_e, use_container_width=True)

    # --- GESTÃO DE PRODUTOS ---
    elif menu == "✨ Gestão de Produtos":
        st.title("✨ Cadastro e Manutenção")
        with st.form("cad_prod"):
            c1, c2, c3 = st.columns([2, 2, 1])
            f_cat = c1.selectbox("Categoria", ["Romarinho", "Cerveja Lata", "Long Neck", "Refrigerante", "Outros"])
            f_nom = c2.text_input("Nome do Produto").upper().strip()
            f_pre = c3.number_input("Preço de Venda", 0.0)
            if st.form_submit_button("CADASTRAR PRODUTO"):
                if f_nom and f_nom not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[f_cat, f_nom, f_pre]], columns=df_p.columns)]).to_csv(DB_PRODUTOS, index=False)
                    pd.concat([df_e, pd.DataFrame([[f_nom, 0]], columns=df_e.columns)]).to_csv(DB_ESTOQUE, index=False)
                    st.rerun()
        
        st.markdown("### 📋 Itens Cadastrados")
        for i, r in df_p.iterrows():
            col1, col2 = st.columns([9, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']}) - R$ {r['Preco_Unitario']}")
            if col2.button("🗑️", key=f"del_{r['Nome']}"):
                df_p[df_p['Nome'] != r['Nome']].to_csv(DB_PRODUTOS, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_ESTOQUE, index=False)
                st.rerun()

    # --- ABAS ADMIN ---
    elif menu == "📊 Dashboards" and is_adm:
        st.title("📊 Painel de Controle Financeiro")
        df_f = pd.merge(df_e, df_p, on='Nome')
        df_f['Patrimônio'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("VALOR TOTAL EM ESTOQUE (VENDA)", f"R$ {df_f['Patrimônio'].sum():,.2f}")
        st.bar_chart(df_f.set_index('Nome')['Estoque_Total_Un'])

    elif menu == "📜 Histórico" and is_adm:
        st.title("📜 Logs de Atividade")
        st.dataframe(pd.read_csv(LOG_FILE).iloc[::-1], use_container_width=True)

    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gestão de Usuários")
        with st.form("eq_add"):
            c1, c2, c3, c4, c5 = st.columns(5)
            nu, nn, ns, nt, na = c1.text_input("Login"), c2.text_input("Nome"), c3.text_input("Senha"), c4.text_input("WhatsApp"), c5.selectbox("Adm?", ["NÃO", "SIM"])
            if st.form_submit_button("ADICIONAR MEMBRO"):
                pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_usr.columns)]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(df_usr[['user', 'nome', 'is_admin', 'telefone']])
