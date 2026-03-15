import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from PIL import Image
import io
import zipfile

# =================================================================
# 1. DESIGN PREMIUM - DARK PRESTIGE "EVOLUTION" V70
# =================================================================
st.set_page_config(page_title="Adega Pacaembu", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Cartões de Conteúdo */
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    
    /* Indicadores de Status */
    .status-bom { color: #238636; font-weight: bold; border-left: 4px solid #238636; padding-left: 10px; }
    .status-alerta { color: #d29922; font-weight: bold; border-left: 4px solid #d29922; padding-left: 10px; }
    .status-critico { color: #f85149; font-weight: bold; border-left: 4px solid #f85149; padding-left: 10px; }
    
    /* Avatares */
    .avatar-round { border-radius: 50%; border: 2px solid #58a6ff; object-fit: cover; }
    
    /* Botões Customizados */
    .stButton>button {
        border-radius: 8px; font-weight: 600; transition: 0.3s;
        background-color: #21262d; border: 1px solid #30363d; height: 2.8em;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; background-color: #30363d; }
    
    /* Pilares Visuais */
    .pilar-frame {
        background: #1c2128; border: 1px solid #30363d; border-radius: 15px;
        padding: 20px; margin-top: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BANCO DE DADOS E INFRAESTRUTURA
# =================================================================
DBS = {
    "prod": "produtos_v70.csv", "est": "estoque_v70.csv", "pil": "pilares_v70.csv",
    "usr": "usuarios_v70.csv", "log": "historico_v70.csv", "cas": "cascos_v70.csv",
    "tar": "tarefas_v70.csv", "cat": "categorias_v70.csv"
}

def init_db():
    cols = {
        DBS["prod"]: ['Categoria', 'Nome', 'Preco_Unitario'],
        DBS["est"]: ['Nome', 'Estoque_Total_Un'],
        DBS["pil"]: ['ID', 'NomePilar', 'Camada', 'Posicao', 'Bebida', 'Avulsos'],
        DBS["log"]: ['Data', 'Usuario', 'Ação'],
        DBS["cas"]: ['ID', 'Data', 'Cliente', 'Telefone', 'Vasilhame', 'Quantidade', 'Status', 'QuemBaixou', 'HoraBaixa'],
        DBS["tar"]: ['ID', 'Tarefa', 'Status', 'QuemFez', 'Horario'],
        DBS["cat"]: ['Nome'],
        DBS["usr"]: ['user', 'nome', 'senha', 'is_admin', 'telefone', 'foto']
    }
    for arq, colunas in cols.items():
        if not os.path.exists(arq): pd.DataFrame(columns=colunas).to_csv(arq, index=False)
        else:
            df_check = pd.read_csv(arq)
            for c in colunas:
                if c not in df_check.columns: df_check[c] = ""; df_check.to_csv(arq, index=False)
    
    # Criar Admin Padrão
    df_u = pd.read_csv(DBS["usr"])
    if df_u.empty:
        pd.DataFrame([['admin', 'Gerente Mestre', '123', 'SIM', '', '']], columns=cols[DBS["usr"]]).to_csv(DBS["usr"], index=False)

init_db()

def get_config(nome, df_p):
    item = df_p[df_p['Nome'] == nome]
    if not item.empty:
        cat = item['Categoria'].values[0]
        if cat == "Romarinho": return 24, "Engradado"
        if cat == "Refrigerante": return 6, "Fardo"
    return 12, "Fardo"

def registrar_log(user, acao):
    pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), user, acao]], columns=['Data', 'Usuario', 'Ação']).to_csv(DBS["log"], mode='a', header=False, index=False)

# =================================================================
# 3. CONTROLE DE ACESSO
# =================================================================
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #58a6ff; margin-top: 50px;'>💎 ADEGA PACAEMBU</h1>", unsafe_allow_html=True)
    col_login, _ = st.columns([1, 1.5])
    with col_login:
        with st.form("f_login"):
            u_in = st.text_input("Usuário")
            s_in = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                df_u = pd.read_csv(DBS["usr"])
                match = df_u[(df_u['user'] == u_in) & (df_u['senha'].astype(str) == s_in)]
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.update({'autenticado': True, 'u_l': u_in, 'u_n': row['nome'], 'u_a': (row['is_admin']=='SIM')})
                    registrar_log(row['nome'], "Login"); st.rerun()
                else: st.error("Incorreto.")
else:
    u_logado, n_logado, is_adm = st.session_state['u_l'], st.session_state['u_n'], st.session_state['u_a']
    df_p, df_e, df_pil, df_cas, df_usr, df_tar, df_cat = pd.read_csv(DBS["prod"]), pd.read_csv(DBS["est"]), pd.read_csv(DBS["pil"]), pd.read_csv(DBS["cas"]), pd.read_csv(DBS["usr"]), pd.read_csv(DBS["tar"]), pd.read_csv(DBS["cat"])

    # --- SIDEBAR PROFISSIONAL ---
    user_row = df_usr[df_usr['user'] == u_logado].iloc[0]
    foto_b64 = user_row['foto']
    img_sidebar = f"data:image/png;base64,{foto_b64}" if foto_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    
    st.sidebar.markdown(f'<div style="text-align:center"><img src="{img_sidebar}" class="avatar-round" width="90" height="90"><br><br><b>{n_logado}</b><br><small>{"ADMIN" if is_adm else "OPERADOR"}</small></div>', unsafe_allow_html=True)
    st.sidebar.divider()
    menu = st.sidebar.radio("NAVEGAÇÃO", ["🏠 Home", "📦 Estoque", "🏗️ Pilares", "📋 Tarefas", "✨ Cadastro", "🍶 Cascos", "👥 Equipe", "⚙️ Perfil"])
    if st.sidebar.button("🚪 SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- 🏠 HOME / DASHBOARD ---
    if menu == "🏠 Home":
        st.title("🚀 Painel Geral")
        c1, c2, c3 = st.columns(3)
        c1.metric("Itens no Estoque", df_e['Estoque_Total_Un'].sum())
        c2.metric("Tarefas Ativas", len(df_tar[df_tar['Status']=='PENDENTE']))
        c3.metric("Dívidas Cascos", len(df_cas[df_cas['Status']=='DEVE']))
        st.divider()
        st.subheader("📜 Atividade Recente")
        st.table(pd.read_csv(DBS["log"]).tail(5))

    # --- 📦 ESTOQUE PROFISSIONAL ---
    elif menu == "📦 Estoque":
        st.title("📦 Inventário e Ajustes")
        df_join = pd.merge(df_e, df_p, on="Nome")
        
        c_search, c_cat_f = st.columns([2,1])
        s_term = c_search.text_input("🔍 Buscar Produto...").upper()
        f_cat = c_cat_f.selectbox("Filtrar Categoria", ["Todas"] + sorted(df_p['Categoria'].unique().tolist()))
        
        if s_term: df_join = df_join[df_join['Nome'].str.contains(s_term)]
        if f_cat != "Todas": df_join = df_join[df_join['Categoria'] == f_cat]

        for _, r in df_join.iterrows():
            u_b, t_t = get_config(r['Nome'], df_p)
            fardos = r['Estoque_Total_Un'] // u_b
            un_avulsa = r['Estoque_Total_Un'] % u_b
            
            # Lógica de cor
            cor_classe = "status-bom" if r['Estoque_Total_Un'] > 24 else "status-alerta" if r['Estoque_Total_Un'] > 0 else "status-critico"
            
            st.markdown(f'''
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex:2"><b>{r['Nome']}</b><br><small>{r['Categoria']}</small></div>
                    <div style="flex:1" class="{cor_classe}">{r['Estoque_Total_Un']} un</div>
                    <div style="flex:1">{fardos} {t_t}s + {un_avulsa} un</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        with st.expander("➕ LANÇAR ENTRADA / SAÍDA MANUAL"):
            with st.form("f_ajuste"):
                sel_item = st.selectbox("Produto", df_p['Nome'].unique())
                tipo_aj = st.radio("Operação", ["ENTRADA", "SAÍDA"], horizontal=True)
                col_a1, col_a2 = st.columns(2)
                f_aj = col_a1.number_input("Fardos/Engradados", 0)
                u_aj = col_a2.number_input("Unidades Avulsas", 0)
                if st.form_submit_button("ATUALIZAR ESTOQUE"):
                    u_base, _ = get_config(sel_item, df_p)
                    total_aj = (f_aj * u_base) + u_aj
                    if tipo_aj == "SAÍDA": df_e.loc[df_e['Nome'] == sel_item, 'Estoque_Total_Un'] -= total_aj
                    else: df_e.loc[df_e['Nome'] == sel_item, 'Estoque_Total_Un'] += total_aj
                    df_e.to_csv(DBS["est"], index=False)
                    registrar_log(n_logado, f"Ajuste {tipo_aj}: {sel_item} ({total_aj}un)"); st.rerun()

    # --- 🏗️ PILARES (LÓGICA COMPLETA) ---
    elif menu == "🏗️ Pilares":
        st.title("🏗️ Gestão de Pilares")
        with st.expander("🧱 ADICIONAR NOVA CAMADA"):
            p_sel = st.selectbox("Escolha o Pilar", ["+ NOVO"] + sorted(df_pil['NomePilar'].unique().tolist()))
            n_p = st.text_input("Nome").upper() if p_sel == "+ NOVO" else p_sel
            if n_p:
                all_cats = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata"] + df_cat['Nome'].tolist())))
                c_pilar = st.selectbox("Filtrar Bebidas por Categoria", all_cats)
                c_idx = 1 if df_pil[df_pil['NomePilar']==n_p].empty else int(df_pil[df_pil['NomePilar']==n_p]['Camada'].max()) + 1
                # Lógica de posições Zig-Zag (3+2 / 2+3)
                at, fr = (3, 2) if c_idx % 2 != 0 else (2, 3)
                st.info(f"Camada {c_idx}: {at+fr} posições disponíveis.")
                cols_p = st.columns(5); data_p = []
                for i in range(at+fr):
                    beb = cols_p[i].selectbox(f"Pos {i+1}", ["Vazio"] + df_p[df_p['Categoria']==c_pilar]['Nome'].tolist(), key=f"p{i}")
                    avul = cols_p[i].number_input("Av", 0, key=f"av{i}")
                    if beb != "Vazio": data_p.append([f"{n_p}_{c_idx}_{i}", n_p, c_idx, i+1, beb, avul])
                if st.button("SALVAR CAMADA NO PILAR"):
                    pd.concat([df_pil, pd.DataFrame(data_p, columns=df_pil.columns)]).to_csv(DBS["pil"], index=False); st.rerun()

        for pilar_nome in df_pil['NomePilar'].unique():
            st.markdown(f'<div class="pilar-frame"><h3>📍 Pilar {pilar_nome}</h3>', unsafe_allow_html=True)
            # Mostrar da camada mais alta para a mais baixa
            for cam_num in sorted(df_pil[df_pil['NomePilar']==pilar_nome]['Camada'].unique(), reverse=True):
                st.caption(f"Camada {cam_num}")
                c_grid = st.columns(5)
                for _, row_p in df_pil[(df_pil['NomePilar']==pilar_nome) & (df_pil['Camada']==cam_num)].iterrows():
                    if c_grid[int(row_p['Posicao'])-1].button(f"BAIXA\n{row_p['Bebida']}", key=row_p['ID'], use_container_width=True):
                        u_p, _ = get_config(row_p['Bebida'], df_p)
                        # Baixa = 1 fardo completo + os avulsos configurados
                        df_e.loc[df_e['Nome']==row_p['Bebida'], 'Estoque_Total_Un'] -= (u_p + row_p['Avulsos'])
                        df_e.to_csv(DBS["est"], index=False)
                        # Remove a posição do pilar (foi consumida)
                        df_pil[df_pil['ID'] != row_p['ID']].to_csv(DBS["pil"], index=False)
                        registrar_log(n_logado, f"Baixa Pilar {pilar_nome}: {row_p['Bebida']}"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 🍶 CASCOS (COMPLETO COM ESTORNO) ---
    elif menu == "🍶 Cascos":
        st.title("🍶 Vasilhames")
        t1, t2, t3 = st.tabs(["🔴 Pendentes", "📊 Saldo Pátio", "📜 Histórico/Estorno"])
        with t1:
            with st.form("f_casco"):
                c1, c2, c3 = st.columns(3)
                cli = c1.text_input("Cliente").upper()
                tipo_v = c2.selectbox("Tipo", ["Romarinho", "Coca 1L", "Coca 2L", "600ml"])
                q_v = c3.number_input("Quantidade", 1)
                if st.form_submit_button("LANÇAR DÍVIDA"):
                    pd.concat([df_cas, pd.DataFrame([[f"C{datetime.now().microsecond}", datetime.now().strftime("%d/%m %H:%M"), cli, "", tipo_v, q_v, "DEVE", "", ""]], columns=df_cas.columns)]).to_csv(DBS["cas"], index=False); st.rerun()
            
            for i, r in df_cas[df_cas['Status']=="DEVE"].iterrows():
                with st.container():
                    st.markdown(f'<div class="card"><b style="color:#f85149">DÍVIDA:</b> {r["Cliente"]} | {r["Quantidade"]}x {r["Vasilhame"]}</div>', unsafe_allow_html=True)
                    if st.button(f"DAR BAIXA EM {r['Cliente']}", key=f"bx_{r['ID']}"):
                        df_cas.at[i, 'Status'] = "PAGO"; df_cas.at[i, 'QuemBaixou'] = n_logado; df_cas.at[i, 'HoraBaixa'] = datetime.now().strftime("%H:%M")
                        df_cas.to_csv(DBS["cas"], index=False); st.rerun()
        with t2:
            st.subheader("Total no Pátio (Pagos)")
            st.table(df_cas[df_cas['Status']=="PAGO"].groupby('Vasilhame')['Quantidade'].sum())
        with t3:
            for i, r in df_cas[df_cas['Status']=="PAGO"].iterrows():
                st.write(f"✅ {r['Cliente']} entregou {r['Quantidade']} {r['Vasilhame']} (Recebido por {r['QuemBaixou']})")
                if st.button("ESTORNAR", key=f"est_{r['ID']}"):
                    df_cas.at[i, 'Status'] = "DEVE"; df_cas.to_csv(DBS["cas"], index=False); st.rerun()

    # --- 📋 TAREFAS ---
    elif menu == "📋 Tarefas":
        st.title("📋 Checklist da Equipe")
        if is_adm:
            with st.form("f_tar"):
                nova_t = st.text_input("Nova Tarefa")
                if st.form_submit_button("PUBLICAR"):
                    pd.concat([df_tar, pd.DataFrame([[f"T{datetime.now().microsecond}", nova_t, "PENDENTE", "", ""]], columns=df_tar.columns)]).to_csv(DBS["tar"], index=False); st.rerun()
        
        for i, r in df_tar.iterrows():
            if r['Status'] == "PENDENTE":
                col_t1, col_t2 = st.columns([4,1])
                col_t1.warning(f"🔔 {r['Tarefa']}")
                if col_t2.button("FEITO", key=f"ok_{i}"):
                    df_tar.at[i, 'Status'] = "CONCLUÍDO"; df_tar.at[i, 'QuemFez'] = n_logado; df_tar.at[i, 'Horario'] = datetime.now().strftime("%H:%M")
                    df_tar.to_csv(DBS["tar"], index=False); st.rerun()
            else:
                st.markdown(f'<div style="color:gray; text-decoration:line-through">✅ {r["Tarefa"]} (Por {r["QuemFez"]} às {r["Horario"]})</div>', unsafe_allow_html=True)

    # --- ✨ CADASTRO DINÂMICO ---
    elif menu == "✨ Cadastro":
        st.title("✨ Gestão de Produtos")
        tab_p1, tab_p2, tab_p3 = st.tabs(["➕ Novo Item", "📂 Nova Categoria", "🗑️ Gerenciar"])
        
        with tab_p2:
            cat_nome = st.text_input("Nome da Categoria").upper()
            if st.button("CRIAR CATEGORIA"):
                if cat_nome and cat_nome not in df_cat['Nome'].values:
                    pd.concat([df_cat, pd.DataFrame([[cat_nome]], columns=['Nome'])]).to_csv(DBS["cat"], index=False); st.success("Criada!"); st.rerun()
        
        with tab_p1:
            with st.form("f_item"):
                cats_all = sorted(list(set(["Romarinho", "Refrigerante", "Cerveja Lata", "Outros"] + df_cat['Nome'].tolist())))
                c_c = st.selectbox("Categoria", cats_all)
                c_n = st.text_input("Nome do Produto").upper()
                c_p = st.number_input("Preço", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    pd.concat([df_p, pd.DataFrame([[c_c, c_n, c_p]], columns=df_p.columns)]).to_csv(DBS["prod"], index=False)
                    pd.concat([df_e, pd.DataFrame([[c_n, 0]], columns=df_e.columns)]).to_csv(DBS["est"], index=False); st.rerun()
        
        with tab_p3:
            for i, r in df_p.iterrows():
                col_r1, col_r2 = st.columns([4,1])
                col_r1.write(f"**{r['Nome']}** ({r['Categoria']})")
                if col_r2.button("Excluir", key=f"rm_p_{i}"):
                    df_p.drop(i).to_csv(DBS["prod"], index=False)
                    df_e[df_e['Nome'] != r['Nome']].to_csv(DBS["est"], index=False); st.rerun()

    # --- 👥 EQUIPE ---
    elif menu == "👥 Equipe" and is_adm:
        st.title("👥 Gerenciar Equipe")
        with st.expander("➕ Adicionar Operador"):
            with st.form("f_add_u"):
                u, n, s, a = st.columns(4)
                f_u, f_n, f_s = u.text_input("User"), n.text_input("Nome"), s.text_input("Senha")
                f_a = a.selectbox("Admin", ["NÃO", "SIM"])
                if st.form_submit_button("SALVAR"):
                    pd.concat([df_usr, pd.DataFrame([[f_u, f_n, f_s, f_a, "", ""]], columns=df_usr.columns)]).to_csv(DBS["usr"], index=False); st.rerun()
        
        for i, row in df_usr.iterrows():
            f_img = f"data:image/png;base64,{row['foto']}" if row['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            st.markdown(f'''
            <div class="card">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="{f_img}" class="avatar-round" width="50" height="50">
                    <div><b>{row['nome']}</b> ({row['user']})<br><small>{'ADMIN' if row['is_admin']=='SIM' else 'OPERADOR'}</small></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            if row['user'] != 'admin' and st.button("Remover", key=f"ru_{i}"):
                df_usr.drop(i).to_csv(DBS["usr"], index=False); st.rerun()

    # --- ⚙️ PERFIL ---
    elif menu == "⚙️ Perfil":
        st.title("⚙️ Meu Perfil")
        col_pf1, col_pf2 = st.columns([1, 2])
        f_perfil = f"data:image/png;base64,{user_row['foto']}" if user_row['foto'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
        col_pf1.image(f_perfil, width=200)
        with col_pf2:
            st.write(f"### {n_logado}")
            up = st.file_uploader("Trocar Foto de Perfil", type=['png', 'jpg'])
            if st.button("SALVAR ALTERAÇÕES") and up:
                img_p = Image.open(up).convert("RGB"); img_p.thumbnail((300, 300))
                buf_p = io.BytesIO(); img_p.save(buf_p, format="PNG")
                b64_p = base64.b64encode(buf_p.getvalue()).decode()
                df_usr.loc[df_usr['user'] == u_logado, 'foto'] = b64_p; df_usr.to_csv(DBS["usr"], index=False); st.rerun()
