# --- 🍶 CASCOS (ATUALIZADO COM SALDO E HISTÓRICO) ---
    elif menu == "🍶 Controle de Cascos":
        st.title("🍶 Gestão de Cascos e Vasilhames")
        
        tab1, tab2, tab3 = st.tabs(["🔴 Pendências", "🟢 Histórico de Baixas", "📦 Saldo de Vazios"])

        with tab1:
            with st.form("f_cas"):
                c1, c2, c3 = st.columns([2, 2, 1])
                cl = c1.text_input("Cliente").upper()
                va = c2.selectbox("Vasilhame", ["Coca 1L", "Coca 2L", "Romarinho", "600ml", "Litrão"])
                qt = c3.number_input("Qtd", 1)
                if st.form_submit_button("LANÇAR DÉBITO"):
                    novo_id = f"C{datetime.now().strftime('%M%S')}"
                    nova_linha = pd.DataFrame([[novo_id, datetime.now().strftime("%d/%m"), cl, "", va, qt, "DEVE", n_logado]], columns=df_cas.columns)
                    pd.concat([df_cas, nova_linha]).to_csv(DB_CAS, index=False)
                    st.rerun()

            st.markdown("### ⚠️ Clientes em Débito")
            pendentes = df_cas[df_cas['Status'] == "DEVE"]
            if pendentes.empty:
                st.success("Tudo em dia! Nenhum casco pendente.")
            else:
                for i, r in pendentes.iterrows():
                    with st.container():
                        col_r1, col_r2, col_r3 = st.columns([4, 2, 2])
                        col_r1.warning(f"👤 **{r['Cliente']}**")
                        col_r2.write(f"{r['Quantidade']}x {r['Vasilhame']} ({r['Data']})")
                        if col_r3.button("DAR BAIXA", key=f"bx_{r['ID']}", use_container_width=True):
                            df_cas.at[i, 'Status'] = "PAGO"
                            df_cas.at[i, 'QuemBaixou'] = n_logado
                            df_cas.to_csv(DB_CAS, index=False)
                            registrar_log(n_logado, f"Baixa casco: {r['Cliente']}")
                            st.rerun()

        with tab2:
            st.markdown("### ✅ Últimos Recebimentos")
            pagos = df_cas[df_cas['Status'] == "PAGO"].sort_index(ascending=False)
            if pagos.empty:
                st.info("Nenhuma baixa registrada ainda.")
            else:
                for i, r in pagos.iterrows():
                    with st.container():
                        col_h1, col_h2, col_h3 = st.columns([4, 2, 2])
                        col_h1.write(f"🟢 **{r['Cliente']}**")
                        col_h2.write(f"{r['Quantidade']}x {r['Vasilhame']}")
                        if col_h3.button("ESTORNAR", key=f"est_{r['ID']}", help="Volta para lista de deve", use_container_width=True):
                            df_cas.at[i, 'Status'] = "DEVE"
                            df_cas.to_csv(DB_CAS, index=False)
                            st.rerun()
                if st.button("🗑️ LIMPAR HISTÓRICO DE PAGOS"):
                    df_cas[df_cas['Status'] == "DEVE"].to_csv(DB_CAS, index=False)
                    st.rerun()

        with tab3:
            st.markdown("### 📦 Cascos Vazios em Loja")
            # Cálculo automático baseado nas baixas e vendas (opcional) ou manual
            # Aqui faremos um resumo das baixas para controle de estoque físico
            resumo_vazios = df_cas[df_cas['Status'] == "PAGO"].groupby('Vasilhame')['Quantidade'].sum().reset_index()
            if resumo_vazios.empty:
                st.info("Sem cascos vazios registrados no momento.")
            else:
                st.table(resumo_vazios)
                st.metric("TOTAL DE GARRAFAS NO FUNDO", resumo_vazios['Quantidade'].sum())
