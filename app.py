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

# CSS Customizado - Estilo Dark Prestige (Nada simplificado)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Cards de Navegação e Conteúdo */
    div[data-testid="stExpander"] { 
        border: 1px solid #30363d; 
        border-radius: 15px; 
        background-color: #161b22; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    /* Botões de Ação PDV */
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
        height: 3em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #30363d;
        background-color: #21262d;
    }
    .stButton>button:hover {
        border-color: #58a6ff;
        color: #58a6ff;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.6);
    }
    
    /* Métricas Estilizadas */
    div[data-testid="stMetric"] {
        background-color: #1c2128;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #30363d;
        border-left: 6px solid #238636;
    }
    
    /* Scrollbar Chique */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
    
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. INFRAESTRUTURA DE DADOS (BANCO DE DADOS COMPLETO)
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
        DB_CAS: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou']
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
# 3. SEGURANÇA E LOGIN BLINDADO
# =================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff;'>💎 PACAEMBU ULTRA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Gestão de Depósito Profissional v66</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_prestige"):
            u_in = st.text_input("👤 Usuário de Acesso")
            s_in = st.text_input("🔑 Senha Particular", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DB_USR)
                valid = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not valid.empty:
                    st.session_state.update({
                        'autenticado': True, 'u_l': u_in, 
                        'u_n': valid['nome'].values[0], 
                        'u_a': (valid['is_admin'].values[0] == 'SIM')
                    })
                    registrar_log(st.session_state['u_n'], "Login Realizado")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Tente novamente.")
else:
    # Carregamento Seguro dos Bancos
    u_logado = st.session_state.get('u_l')
    n_logado = st.session_state.get('u_n')
    is_adm = st.session_state.get('u_a')

    df_p, df_e, df_pil = pd.read_csv(DB_PROD), pd.read_csv(DB_EST), pd.read_csv(DB_PIL)
    df_cas, df_usr = pd.read_csv(DB_CAS), pd.read_csv(DB_USR)

    # --- SIDEBAR ULTRA ---
    st.sidebar.markdown("<h2 style='text-align: center; color: #58a6ff;'>PACAEMBU</h2>", unsafe_allow_html=True)
    
    # Foto de Perfil com Trava de Erro
    user_row = df_usr[df_usr['user'] == u_logado]
    f_path = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    if not user_row.empty:
        raw = user_row['foto'].values[0]
        if not pd.isna(raw) and raw != "":
            f_path = f"data:image/png;base64,{raw}"

    st.sidebar.markdown(f"<div style='text-align: center;'><img src='{f_path}' width='120' style='border-radius: 50%; border: 4px solid #238636; aspect-ratio: 1/1; object-fit: cover;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 1.2em;'><b>{n_logado}</b></p>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("NAVEGAÇÃO", 
        ["🍻 PDV Romarinho", "🏗️ Pilares (Amarração)", "📦 Estoque Geral", "✨ Cadastro de Produtos", "🍶 Controle de Cascos", "⚙️ Meu Perfil"] + 
        (["📊 Dashboard Financeiro", "📜 Logs do Sistema", "👥 Gerenciar Equipe"] if is_adm else []))

    if st.sidebar.button("🚪 ENCERRAR SESSÃO", use_container_width=True):
        st.session_state['autenticado'] = False
        st.rerun()

    # =================================================================
    # ABA: PDV ROMARINHO (COMPLETO E FUNCIONAL)
    # =================================================================
    if menu == "🍻 PDV Romarinho":
        st.title("🍻 Ponto de Venda - Romarinhos")
        st.markdown("### Baixa Instantânea de Estoque")
        
        df_roms = df_p[df_p['Categoria'] == "Romarinho"]
        if df_roms.empty:
            st.warning("Nenhum Romarinho cadastrado.")
        else:
            for i, item in df_roms.iterrows():
                with st.container():
                    c_tit, c_met, c_btn = st.columns([3, 3, 4])
                    c_tit.markdown(f"#### {item['Nome']}")
                    
                    # Cálculo de Estoque Real
                    est_u = int(df_e[df_e['Nome'] == item['Nome']]['Estoque_Total_Un'].values[0])
                    c_met.metric("Saldo", f"{est_u//24} Eng | {est_u%24} un")
                    
                    # Botões de Baixa
                    b1, b2 = c_btn.columns(2)
                    if b1.button(f"➖ ENGRADADO", key=f"eng_{item['Nome']}", use_container_width=True):
                        if est_u >= 24:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 24
                            df_e.to_csv(DB_EST, index=False)
                            registrar_log(n_logado, f"BAIXA PDV: -1 Eng {item['Nome']}")
                            st.rerun()
                        else: st.error("Sem estoque!")
                    
                    if b2.button(f"➖ UNIDADE", key=f"uni_{item['Nome']}", use_container_width=True):
                        if est_u >= 1:
                            df_e.loc[df_e['Nome'] == item['Nome'], 'Estoque_Total_Un'] -= 1
                            df_e.to_csv(DB_EST, index=False)
                            registrar_log(n_logado, f"BAIXA PDV: -1 Un {item['Nome']}")
                            st.rerun()
                        else: st.error("Sem estoque!")
                st.markdown("---")

    # =================================================================
    # ABA: PILARES (LÓGICA 3x2 e 2x3 INTEGRADA)
    # =================================================================
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Gestão de Pilares e Camadas")
        
        with st.expander("🆕 LANÇAR NOVA CAMADA", expanded=False):
            p_alvo = st.selectbox("Selecione o Pilar", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            
            if n_pilar:
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                # Lógica de Amarração: Impar = 3at/2fr | Par = 2at/3fr
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                st.info(f"Camada {c_atual}: Estrutura de amarração automática (**{at} atrás / {fr} na frente**)")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == "Refrigerante"]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                
                col_at, col_fr = st.columns(2)
                for i in range(at + fr):
                    pos = i + 1
                    target = col_at if pos <= at else col_fr
                    beb_dict[pos] = target.selectbox(f"Posição {pos}", lista_beb, key=f"p_{pos}_{c_atual}")
                    av_dict[pos] = target.number_input(f"Avulsos {pos}", 0, key=f"a_{pos}_{c_atual}")
                
                if st.button("CONFIRMAR E MONTAR CAMADA", use_container_width=True):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().strftime('%S')}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        st.success("Camada montada!")
                        st.rerun()

        # Exibição do Mapa de Pilares
        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            for cam in sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True):
                st.markdown(f"**Camada {cam}**")
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                cols_v = st.columns(5)
                for _, r in dados_cam.iterrows():
                    with cols_v[int(r['Posicao'])-1]:
                        st.markdown(f"<div style='background-color:#1c2128; padding:8px; border-radius:8px; border:1px solid #30363d; text-align:center;'><b>{r['Bebida']}</b><br><small>+{r['Avulsos']} un</small></div>", unsafe_allow_html=True)
                        if st.button("RETIRAR", key=f"rt_{r['ID']}", use_container_width=True):
                            u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                            total_sair = u_padrao + r['Avulsos']
                            df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= total_sair
                            df_e.to_csv(DB_EST, index=False)
                            df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                            registrar_log(n_logado, f"RETIRADA PILAR: {total_sair}un {r['Bebida']}")
                            st.rerun()

    # =================================================================
    # ABA: CONTROLE DE CASCOS (ESTORNO REAL)
    # =================================================================
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Registro de Vasilhames e Devedores")
        with st.form("f_casco"):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            f_cl, f_te = c1.text_input("Nome do Cliente").upper(), c2.text_input("WhatsApp")
            f_ti = c3.selectbox("Tipo", ["Coca 1L", "Coca 2L", "Engradado", "Litrinho", "600ml"])
            f_qt = c4.number_input("Qtd", 1)
            if st.form_submit_button("REGISTRAR PENDÊNCIA"):
                pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().strftime('%M%S')}", datetime.now().strftime("%d/%m %H:%M"), f_cl, f_te, f_ti, f_qt, "DEVE", ""]], columns=df_cas.columns)]).to_csv(DB_CAS, index=False)
                st.rerun()

        st.subheader("🔴 Devedores Atuais")
        for i, r in df_cas[df_cas['Status'] == "DEVE"].iterrows():
            with st.container():
                l1, l2 = st.columns([7, 2])
                l1.error(f"👤 {r['Cliente']} | {r['Quantidade']}x {r['Vasilhame']} | 📱 {r['Telefone']}")
                if l2.button("RECEBER", key=f"bx_{r['ID']}", use_container_width=True):
                    df_cas.at[i, 'Status'] = "PAGO"
                    df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_CAS, index=False)
                    st.rerun()
        
        st.write("---")
        with st.expander("🟢 Histórico de Devoluções (Possibilidade de Estorno)"):
            for i, r in df_cas[df_cas['Status'] == "PAGO"].tail(10).iterrows():
                el1, el2 = st.columns([7, 2])
                el1.success(f"OK: {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']} (Baixa: {r['QuemBaixou']})")
                if el2.button("🚫 ESTORNAR", key=f"est_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "DEVE"
                    df_cas.to_csv(DB_CAS, index=False)
                    st.rerun()

    # =================================================================
    # ABA: PERFIL (FOTO DA GALERIA - NÃO SIMPLIFICADO)
    # =================================================================
    elif menu == "⚙️ Meu Perfil":
        st.title("⚙️ Gestão de Perfil")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            if not user_row.empty and not pd.isna(user_row['foto'].values[0]):
                st.image(f"data:image/png;base64,{user_row['foto'].values[0]}", width=200)
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=200)
        
        with col_f2:
            st.subheader("Alterar Foto de Perfil")
            upload = st.file_uploader("Selecione sua foto da Galeria", type=['png', 'jpg', 'jpeg'])
            if st.button("SALVAR ALTERAÇÕES", use_container_width=True):
                if upload:
                    img = Image.open(upload)
                    img.thumbnail((200, 200))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64
                    df_usr.to_csv(DB_USR, index=False)
                    st.success("Foto atualizada!")
                    st.rerun()

    # =================================================================
    # DEMAIS ABAS (ESTOQUE, CADASTRO, ADMIN)
    # =================================================================
    elif menu == "📦 Estoque Geral":
        st.title("📦 Entrada de Mercadorias")
        if not df_p.empty:
            sel_e = st.selectbox("Produto", df_p['Nome'].unique())
            u_b, t_t = get_config_bebida(sel_e, df_p)
            with st.form("f_entrada"):
                st.info(f"Padrão: {u_b} unidades por {t_t}")
                ce1, ce2 = st.columns(2)
                f_f, f_a = ce1.number_input(f"Qtd {t_t}s", 0), ce2.number_input("Avulsos", 0)
                if st.form_submit_button("LANÇAR ENTRADA"):
                    total = (f_f * u_b) + f_a
                    df_e.loc[df_e['Nome'] == sel_e, 'Estoque_Total_Un'] += total
                    df_e.to_csv(DB_EST, index=False)
                    registrar_log(n_logado, f"ENTRADA: +{total}un {sel_e}")
                    st.rerun()
        st.markdown("### 📊 Saldo Atual em Tempo Real")
        st.dataframe(df_e, use_container_width=True)

    elif menu == "✨ Cadastro de Produtos":
        st.title("✨ Gestão de Catálogo")
        with st.form("f_cad"):
            c1, c2, c3 = st.columns([2, 2, 1])
            fc, fn, fp = c1.selectbox("Categoria", ["Romarinho", "Refrigerante", "Cerveja Lata", "Outros"]), c2.text_input("Nome").upper().strip(), c3.number_input("Preço", 0.0)
            if st.form_submit_button("SALVAR PRODUTO"):
                if fn and fn not in df_p['Nome'].values:
                    pd.concat([df_p, pd.DataFrame([[fc, fn, fp]], columns=df_p.columns)]).to_csv(DB_PROD, index=False)
                    pd.concat([df_e, pd.DataFrame([[fn, 0]], columns=df_e.columns)]).to_csv(DB_EST, index=False)
                    st.rerun()
        st.write("---")
        for i, r in df_p.iterrows():
            col1, col2 = st.columns([9, 1])
            col1.write(f"**{r['Nome']}** ({r['Categoria']}) - R$ {r['Preco_Unitario']}")
            if col2.button("🗑️", key=f"del_{r['Nome']}"):
                df_p[df_p['Nome'] != r['Nome']].to_csv(DB_PROD, index=False)
                df_e[df_e['Nome'] != r['Nome']].to_csv(DB_EST, index=False)
                st.rerun()

    elif menu == "📊 Dashboard Financeiro" and is_adm:
        st.title("📊 Visão Geral de Valor")
        df_f = pd.merge(df_e, df_p, on='Nome')
        df_f['Patrimônio'] = df_f['Estoque_Total_Un'] * df_f['Preco_Unitario']
        st.metric("TOTAL EM MERCADORIA (PREÇO VENDA)", f"R$ {df_f['Patrimônio'].sum():,.2f}")
        st.bar_chart(df_f.set_index('Nome')['Estoque_Total_Un'])

    elif menu == "📜 Logs do Sistema" and is_adm:
        st.title("📜 Histórico de Atividade")
        st.dataframe(pd.read_csv(DB_LOG).iloc[::-1], use_container_width=True)

    elif menu == "👥 Gerenciar Equipe" and is_adm:
        st.title("👥 Controle de Acesso")
        with st.form("f_equipe"):
            c1, c2, c3, c4, c5 = st.columns(5)
            nu, nn, ns, nt, na = c1.text_input("Login"), c2.text_input("Nome"), c3.text_input("Senha"), c4.text_input("WhatsApp"), c5.selectbox("Adm?", ["NÃO", "SIM"])
            if st.form_submit_button("ADD FUNCIONÁRIO"):
                pd.concat([df_usr, pd.DataFrame([[nu, nn, ns, na, nt, ""]], columns=df_usr.columns)]).to_csv(DB_USR, index=False)
                st.rerun()
        st.dataframe(df_usr[['user', 'nome', 'is_admin', 'telefone']])
