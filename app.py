# --- 🍶 CASCOS (ATUALIZADO COM HISTÓRICO E SALDO) ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Gestão de Cascos e Vasilhames")
        
        tab1, tab2, tab3 = st.tabs(["🔴 Pendências", "📜 Histórico de Baixas", "📦 Saldo de Vazios"])

        with tab1:
            with st.form("f_cas"):
                c1, col_v, c3 = st.columns([2, 2, 1])
                cl = c1.text_input("Cliente").upper()
                va = col_v.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml", "Litrão"])
                qt = c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÉBITO"):
                    if cl:
                        novo_id = f"C{datetime.now().strftime('%M%S')}"
                        nova_linha = pd.DataFrame([[novo_id, datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", ""]], columns=df_cas.columns)
                        pd.concat([df_cas, nova_linha]).to_csv(DB_CAS, index=False)
                        registrar_log(n_logado, f"Lançou débito de casco: {cl} ({va})")
                        st.rerun()

            st.markdown("### ⚠️ Clientes em Débito")
            pendentes = df_cas[df_cas['Status'] == "DEVE"]
            if pendentes.empty:
                st.success("Nenhum casco pendente no momento!")
            else:
                for i, r in pendentes.iterrows():
                    with st.container():
                        col_r1, col_r2, col_r3 = st.columns([4, 2, 2])
                        col_r1.error(f"👤 **{r['Cliente']}**")
                        col_r2.write(f"{r['Quantidade']}x {r['Vasilhame']} ({r['Data']})")
                        if col_r3.button("BAIXA ✅", key=f"bx_{r['ID']}", use_container_width=True):
                            df_cas.at[i, 'Status'] = "PAGO"
                            df_cas.at[i, 'QuemBaixou'] = n_logado
                            df_cas.to_csv(DB_CAS, index=False)
                            registrar_log(n_logado, f"Baixa de casco: {r['Cliente']}")
                            st.rerun()

        with tab2:
            st.markdown("### ✅ Baixas Recentes")
            # Mostra apenas os que já foram pagos
            pagos = df_cas[df_cas['Status'] == "PAGO"].sort_index(ascending=False)
            if pagos.empty:
                st.info("O histórico de baixas está vazio.")
            else:
                for i, r in pagos.iterrows():
                    with st.container():
                        col_h1, col_h2, col_h3, col_h4 = st.columns([3, 2, 2, 1])
                        col_h1.write(f"🟢 **{r['Cliente']}**")
                        col_h2.write(f"{r['Quantidade']}x {r['Vasilhame']}")
                        col_h3.caption(f"Recebido por: {r['QuemBaixou']}")
                        if col_h4.button("⏪", key=f"est_{r['ID']}", help="Estornar (Voltar para lista de deve)"):
                            df_cas.at[i, 'Status'] = "DEVE"
                            df_cas.at[i, 'QuemBaixou'] = ""
                            df_cas.to_csv(DB_CAS, index=False)
                            st.rerun()
                
                st.divider()
                if st.button("🗑️ LIMPAR HISTÓRICO DE PAGOS"):
                    df_cas[df_cas['Status'] == "DEVE"].to_csv(DB_CAS, index=False)
                    st.rerun()

        with tab3:
            st.markdown("### 📦 Saldo de Cascos Vazios")
            # Calcula o total de cascos que entraram (foram pagos)
            if not df_cas.empty:
                saldo_vazios = df_cas[df_cas['Status'] == "PAGO"].groupby('Vasilhame')['Quantidade'].sum().reset_index()
                if saldo_vazios.empty:
                    st.info("Nenhum casco vazio em estoque.")
                else:
                    st.table(saldo_vazios)
                    total_geral = saldo_vazios['Quantidade'].sum()
                    st.metric("Total de Garrafas Físicas", f"{total_geral} un")
            else:
                st.info("Nenhum dado registrado.")
