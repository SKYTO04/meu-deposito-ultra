import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import json

# =================================================================
# 1. DESIGN & ESTILO (DARK PRESTIGE V15 - COMPLETO)
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Estilo dos Cards de Produto */
    .product-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-top: 5px solid #58a6ff; transition: 0.3s;
        text-align: center;
    }
    .product-card:hover { border-color: #58a6ff; background: #21262d; transform: translateY(-3px); }
    
    /* Estilo das Tarefas */
    .task-card {
        background: #1c2128; border-left: 5px solid #d29922;
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
    }
    .task-done { border-left-color: #238636; opacity: 0.6; text-decoration: line-through; }
    
    /* Estilo da Equipe */
    .user-card {
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d; border-radius: 15px; padding: 20px;
        text-align: center; height: 100%;
    }
    .avatar-round { border-radius: 50%; border: 3px solid #58a6ff; object-fit: cover; margin-bottom: 10px; }
    
    /* Badges e Labels */
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; display: inline-block; margin-bottom: 8px; }
    .badge-blue { background: #388bfd; color: white; }
    .badge-gold { background: #d29922; color: white; }
    .badge-green { background: #238636; color: white; }
    
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-bottom: 25px; border-top: 4px solid #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. ESTRUTURA DE DADOS E INICIALIZAÇÃO
# =================================================================
DB_FILES = {
    "prod": "prod_v15.csv", "est": "est_v15.csv", "pil": "pil_v15.csv",
    "usr": "usr_v15.csv", "cas": "cas_v15.csv", "tar": "tar_v15.csv", 
    "cat": "cat_v15.csv", "patio": "patio_v15.csv"
}

def init_db():
    cols = {
        DB_FILES["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DB_FILES["est"]: ['Nome', 'Estoque_Total_Un'],
        DB_FILES["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DB_FILES["cas"]: ['ID', 'Data', 'Cliente', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DB_FILES["tar"]: ['ID', 'Tarefa', 'Status', 'Tipo', 'DataProg', 'QuemFez'],
        DB_FILES["cat"]: ['Nome'],
        DB_FILES["usr"]: ['user', 'nome', 'senha', 'is_admin', 'foto'],
        DB_FILES["patio"]: ['Vasilhame', 'Total_Vazio']
    }
    for f, c in cols.items():
        if not os.path.exists(f): 
            df_i = pd.DataFrame(columns=c)
            if f == DB_FILES["patio"]:
                df_i = pd.DataFrame([["Romarinho", 0], ["600ml", 0], ["Coca 1L", 0], ["Coca 2L", 0]], columns=c)
            df_i.to_csv(f, index=False)
    
    df_u = pd.read_csv(DB_FILES["usr"])
    if df_u.empty:
        pd.DataFrame([['admin', 'Gerente', '123', 'SIM', '']], columns=['user', 'nome', 'senha', 'is_admin', 'foto']).to_csv(DB_FILES["usr"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

# =================================================================
# 3. LÓGICA DE ACESSO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>💎 Adega Pacaembu</h1>", unsafe_allow_html=True)
    with st.columns(3)[1]:
        with st.form("login_form"):
            u = st.text_input("Usuário").strip()
            s = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR SISTEMA"):
                df_u = pd.read_csv(DB_FILES["usr"])
                match = df_u[(df_u['user'] == u) & (df_u['senha'].astype(str) == s)]
                if not match.empty:
                    st.session_state.update({'autenticado': True, 'u_l': u, 'u_n': match.iloc[0]['nome'], 'u_a': (match.iloc[0]['is_admin']=='SIM')})
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    # Carregamento de dados
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat, df_patio = [pd.read_csv(f) for f in DB_FILES.values()]

    # Sidebar
    row_user = df_usr[df_usr['user'] == u_logado].iloc[0]
    img_perfil = f"data:image/png;base64,{row_user['foto']}" if row_user['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<center><img src="{img_perfil}" class="avatar-round" width="90" height="90"><br><b>{n_logado}</b></center>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📦 Estoque", "🏗️ Pilares", "🍶 Cascos", "✨ Cadastro", "📋 Tarefas", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title(f"Olá, {n_logado}! 💎")
        df_j = pd.merge(df_e, df_p, on="Nome")
        val_total = (df_j['Estoque_Total_Un'] * df_j['Preco_Unitario']).sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Valor em Estoque", f"R$ {val_total:,.2f}")
        c2.metric("Vasilhames no Pátio", f"{int(df_patio['Total_Vazio'].sum())} un")
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        pendentes = len(df_tar[((df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hoje)) & (df_tar['Status'] == "PENDENTE")])
        c3.metric("Tarefas Pendentes", pendentes)

    # --- 📦 ESTOQUE (CARDS VISUAIS) ---
    elif menu == "📦 Estoque":
        st.title("📦 Controle de Estoque")
        with st.expander("Lançar Entrada/Saída Manual"):
            with st.form("mov_estoque"):
                col_i, col_o, col_q = st.columns([2,1,1])
                item_sel = col_i.selectbox("Produto", df_p['Nome'].unique())
                tipo_mov = col_o.radio("Movimento", ["ENTRADA", "SAÍDA"])
                qtd_mov = col_q.number_input("Quantidade (Unidades)", 1)
                if st.form_submit_button("Registrar"):
                    if tipo_mov == "SAÍDA": df_e.loc[df_e['Nome'] == item_sel, 'Estoque_Total_Un'] -= qtd_mov
                    else: df_e.loc[df_e['Nome'] == item_sel, 'Estoque_Total_Un'] += qtd_mov
                    df_e.to_csv(DB_FILES["est"], index=False); st.success("Estoque atualizado!"); st.rerun()
        
        st.divider()
        df_j = pd.merge(df_e, df_p, on="Nome")
        cols_grid = st.columns(3)
        for i, r in df_j.iterrows():
            ub, t_nome = get_config(r['Nome'], df_p)
            fardos, avulsos = r['Estoque_Total_Un'] // ub, r['Estoque_Total_Un'] % ub
            with cols_grid[i % 3]:
                st.markdown(f"""
                <div class="product-card">
                    <span class="badge badge-blue">{r['Categoria']}</span>
                    <h3>{r['Nome']}</h3>
                    <p style="font-size: 1.3em; margin: 5px 0;"><b>{int(fardos)}</b> {t_nome}(s)</p>
                    <p style="color: #8b949e;">+ {int(avulsos)} unidades avulsas</p>
                    <hr style="border: 0.5px solid #30363d;">
                    <small>Valor Total: R$ {r['Estoque_Total_Un']*r['Preco_Unitario']:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)

    # --- 🏗️ PILARES (LÓGICA 3/2 INTEGRAL) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 Nova Camada (Lógica Zigue-Zague)"):
            p_sel = st.selectbox("Pilar", ["+ CRIAR NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_pilar = st.text_input("Nome do Pilar").upper() if p_sel == "+ CRIAR NOVO" else p_sel
            if n_pilar:
                cat_p = st.selectbox("Categoria da Camada", ["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist())
                lista_prods = df_p[df_p['Categoria'] == cat_p]['Nome'].tolist()
                
                max_cam = 0 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max()
                camada_atual = int(max_cam) + 1
                
                # Definição de layout 3 atravessados / 2 frente ou vice-versa
                atrav, frent = (3, 2) if camada_atual % 2 != 0 else (2, 3)
                st.info(f"Camada {camada_atual}: {atrav} atravessados e {frent} de frente.")
                
                c_pilar = st.columns(5); dados_camada = []
                for i in range(atrav + frent):
                    beb = c_pilar[i].selectbox(f"P{i+1}", ["Vazio"] + lista_prods, key=f"p_{i}")
                    avs = c_pilar[i].number_input("Avs", 0, key=f"a_{i}")
                    if beb != "Vazio":
                        dados_camada.append([f"PIL_{datetime.now().microsecond}_{i}", n_pilar, camada_atual, i+1, beb, avs])
                
                if st.button("SALVAR CAMADA NO PILAR"):
                    pd.concat([df_pil, pd.DataFrame(dados_camada, columns=df_pil.columns)]).to_csv(DB_FILES["pil"], index=False); st.rerun()

        for p in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 {p}</h3>', unsafe_allow_html=True)
            camadas = sorted(df_pil[df_pil['NomePilar']==p]['Camada'].unique(), reverse=True)
            for c in camadas:
                st.caption(f"Camada {c}")
                col_itens = st.columns(5)
                itens_camada = df_pil[(df_pil['NomePilar']==p) & (df_pil['Camada']==c)]
                for _, r in itens_camada.iterrows():
                    idx = int(r['Posicao']) - 1
                    if col_itens[idx].button(f"BAIXA\n{r['Bebida']}", key=r['ID']):
                        cap_caixa, _ = get_config(r['Bebida'], df_p)
                        df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (cap_caixa + r['Avulsos'])
                        df_e.to_csv(DB_FILES["est"], index=False)
                        df_pil[df_pil['ID'] != r['ID']].to_csv(DB_FILES["pil"], index=False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (DEVEDORES E TROCA) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames e Trocas")
        tab1, tab2 = st.tabs(["🔴 Devedores (Clientes)", "🚚 Pátio e Troca Empresa"])
        
        with tab1:
            with st.form("f_deve"):
                c1, c2, c3 = st.columns(3)
                c_cli = c1.text_input("Cliente").upper()
                c_vas = c2.selectbox("Tipo", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
                c_qtd = c3.number_input("Qtd", 1)
                if st.form_submit_button("Lançar Dívida"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), c_cli, c_vas, c_qtd, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                cola, colb = st.columns([4,1])
                cola.warning(f"⚠️ **{r['Cliente']}** está devendo **{r['Quantidade']}** de **{r['Vasilhame']}**")
                if colb.button("PAGO", key=f"bx_{i}"):
                    df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado
                    df_cas.to_csv(DB_FILES["cas"], index=False)
                    df_patio.loc[df_patio['Vasilhame'] == r['Vasilhame'], 'Total_Vazio'] += r['Quantidade']
                    df_patio.to_csv(DB_FILES["patio"], index=False); st.rerun()

        with tab2:
            st.subheader("Registrar Troca com Caminhão")
            with st.form("f_troca"):
                t_vas = st.selectbox("O que a empresa levou?", ["Romarinho", "600ml", "Coca 1L", "Coca 2L"])
                t_qtd = st.number_input("Quantidade de Cascos/Engradados", 1)
                if st.form_submit_button("Confirmar Saída para Troca"):
                    if df_patio.loc[df_patio['Vasilhame'] == t_vas, 'Total_Vazio'].values[0] >= t_qtd:
                        df_patio.loc[df_patio['Vasilhame'] == t_vas, 'Total_Vazio'] -= t_qtd
                        df_patio.to_csv(DB_FILES["patio"], index=False)
                        pd.concat([df_cas, pd.DataFrame([[f"T{datetime.now().microsecond}", datetime.now().strftime("%d/%m"), "EMPRESA (TROCA)", t_vas, t_qtd, "TROCA", n_logado, ""]], columns=df_cas.columns)]).to_csv(DB_FILES["cas"], index=False)
                        st.success("Troca registrada com sucesso!"); st.rerun()
                    else: st.error("Saldo insuficiente no pátio!")
            st.divider()
            for _, r in df_patio.iterrows():
                st.info(f"**Pátio {r['Vasilhame']}:** {int(r['Total_Vazio'])} unidades")

    # --- ✨ CADASTRO (PRODUTOS E CATEGORIAS) ---
    elif menu == "✨ Cadastro":
        st.title("✨ Cadastro do Sistema")
        tc1, tc2 = st.tabs(["📦 Produtos", "📂 Categorias"])
        with tc1:
            with st.form("cad_prod"):
                n_nome = st.text_input("Nome do Produto").upper().strip()
                n_cat = st.selectbox("Categoria", sorted(list(set(["Romarinho", "Refrigerante"] + df_cat['Nome'].tolist()))))
                n_prec = st.number_input("Preço Unitário (Venda)", 0.0)
                if st.form_submit_button("Cadastrar Produto"):
                    if n_nome in df_p['Nome'].values: st.error("Este produto já existe!")
                    else:
                        pd.concat([df_p, pd.DataFrame([[n_cat, n_nome, n_prec]], columns=df_p.columns)]).to_csv(DB_FILES["prod"], index=False)
                        pd.concat([df_e, pd.DataFrame([[n_nome, 0]], columns=df_e.columns)]).to_csv(DB_FILES["est"], index=False); st.rerun()
        with tc2:
            n_cat_nome = st.text_input("Nome da Nova Categoria").strip()
            if st.button("Criar Categoria"):
                if n_cat_nome:
                    pd.concat([df_cat, pd.DataFrame([[n_cat_nome]], columns=df_cat.columns)]).to_csv(DB_FILES["cat"], index=False)
                    st.success("Categoria criada!"); st.rerun()

    # --- 📋 TAREFAS (DIÁRIAS E PROGRAMADAS) ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist")
        if is_adm:
            with st.expander("➕ Adicionar Tarefa"):
                with st.form("cad_task"):
                    t_desc = st.text_input("O que precisa ser feito?")
                    t_tipo = st.selectbox("Recorrência", ["Diária", "Data Específica"])
                    t_data = st.date_input("Data (se for específica)", datetime.now())
                    if st.form_submit_button("Salvar Tarefa"):
                        pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", t_desc, "PENDENTE", t_tipo, str(t_data), ""]], columns=df_tar.columns)]).to_csv(DB_FILES["tar"], index=False); st.rerun()
        
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        df_hoje = df_tar[(df_tar['Tipo'] == "Diária") | (df_tar['DataProg'] == hoje_str)]
        
        for i, r in df_hoje.iterrows():
            estilo = "task-card task-done" if r['Status'] == "OK" else "task-card"
            st.markdown(f"""
            <div class="{estilo}">
                <span class="badge badge-gold">{r['Tipo']}</span>
                <p><b>{r['Tarefa']}</b></p>
                { "✅ Feito por: " + r['QuemFez'] if r['Status'] == "OK" else "⏳ Aguardando" }
            </div>
            """, unsafe_allow_html=True)
            if r['Status'] == "PENDENTE" and st.button("Marcar Concluída", key=f"tk_{i}"):
                df_tar.loc[df_tar['ID'] == r['ID'], 'Status'] = "OK"
                df_tar.loc[df_tar['ID'] == r['ID'], 'QuemFez'] = n_logado
                df_tar.to_csv(DB_FILES["tar"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Nossa Equipe")
        if is_adm:
            with st.expander("➕ Novo Colaborador"):
                with st.form("cad_user"):
                    u_log, u_nom, u_sen, u_adm = st.columns(4)
                    ul, un, us, ua = u_log.text_input("Login"), u_nom.text_input("Nome"), u_sen.text_input("Senha"), u_adm.selectbox("Admin", ["NÃO", "SIM"])
                    if st.form_submit_button("Cadastrar"):
                        pd.concat([df_usr, pd.DataFrame([[ul, un, us, ua, ""]], columns=df_usr.columns)]).to_csv(DB_FILES["usr"], index=False); st.rerun()
        
        st.divider()
        c_eq = st.columns(4)
        for i, r in df_usr.iterrows():
            with c_eq[i % 4]:
                foto = f"data:image/png;base64,{r['foto']}" if r['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                st.markdown(f"""
                    <div class="user-card">
                        <img src="{foto}" class="avatar-round" width="100" height="100">
                        <h4>{r['nome']}</h4>
                        <span class="badge badge-blue">{"ADMIN" if r['is_admin'] == "SIM" else "EQUIPE"}</span>
                    </div>
                """, unsafe_allow_html=True)

    # --- ⚙️ PERFIL E BACKUP ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Configurações")
        tab_p, tab_b = st.tabs(["👤 Meu Perfil", "💾 Backup de Segurança"])
        
        with tab_p:
            file = st.file_uploader("Trocar foto de perfil", type=['png', 'jpg', 'jpeg'])
            if st.button("Salvar Nova Foto") and file:
                img = Image.open(file).convert("RGB")
                img.thumbnail((300, 300))
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                b64 = base64.b64encode(buffer.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64
                df_usr.to_csv(DB_FILES["usr"], index=False); st.success("Foto atualizada!"); st.rerun()
        
        with tab_b:
            st.subheader("💾 Backup dos Dados")
            st.write("Baixe este arquivo para garantir que não perderá os dados se o computador estragar.")
            dict_backup = {k: pd.read_csv(v).to_dict() for k, v in DB_FILES.items()}
            st.download_button("BAIXAR BACKUP COMPLETO (.JSON)", json.dumps(dict_backup), f"backup_adega_{datetime.now().strftime('%d_%m_%Y')}.json")
