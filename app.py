# --- 🏗️ PILARES (VERSÃO PROFESSIONAL) ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Engenharia de Pilares")
        
        with st.expander("➕ MONTAR NOVA CAMADA (ESTRUTURA AMARRADA)"):
            p_alvo = st.selectbox("Pilar Destino", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Identificação do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            
            cat_filtro = st.selectbox("Filtrar Categoria para Montagem", df_p['Categoria'].unique())
            
            if n_pilar:
                # Lógica para definir a próxima camada
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                
                # Lógica de amarração: alterna entre 3x2 e 2x3 para estabilidade estrutural
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                
                st.info(f"🏗️ **Camada {c_atual}** detectada. Padrão de amarração: **{at}x{fr}**")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                
                # Interface de seleção em Grid (Organiza visualmente as posições antes de salvar)
                cols_grid = st.columns(max(at, fr))
                for i in range(at + fr):
                    pos = i + 1
                    with cols_grid[i % len(cols_grid)]:
                        st.markdown(f"**Posição {pos}**")
                        beb_dict[pos] = st.selectbox(f"Bebida", lista_beb, key=f"p_{pos}", label_visibility="collapsed")
                        av_dict[pos] = st.number_input(f"Avulsos", 0, key=f"a_{pos}")
                
                if st.button("FINALIZAR MONTAGEM E REGISTRAR", use_container_width=True):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        registrar_log(n_logado, f"Montou Camada {c_atual} no Pilar {n_pilar}")
                        st.success("Estrutura integrada ao inventário!")
                        st.rerun()

        st.markdown("---")

        # Visualização dos Pilares Ativos
        if df_pil.empty:
            st.info("Nenhum pilar montado no momento.")
        else:
            for pilar in df_pil['NomePilar'].unique():
                with st.container():
                    st.markdown(f"### 📍 Localização: {pilar}")
                    
                    # Ordenar camadas da maior para a menor (simulando a pilha real do topo para a base)
                    camadas = sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
                    
                    for cam in camadas:
                        dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                        total_un_cam = 0
                        
                        st.markdown(f"**Camada {cam}**")
                        cols = st.columns(5) # Grid de exibição fixo em 5 colunas para os cards
                        
                        for _, r in dados_cam.iterrows():
                            u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                            total_un_cam += (u_padrao + r['Avulsos'])
                            
                            with cols[int(r['Posicao'])-1]:
                                # Card Estilizado em HTML para visual Premium Dark
                                card_html = f"""
                                <div style="background-color:#1c2128; padding:10px; border-radius:12px; border:1px solid #30363d; text-align:center; min-height:90px; margin-bottom:5px;">
                                    <small style="color:#8b949e; font-size:0.7em;">POS {r['Posicao']}</small><br>
                                    <b style="font-size:0.85em; color:#e6edf3;">{r['Bebida']}</b><br>
                                    <span style="color:#238636; font-size:0.8em; font-weight:bold;">+{r['Avulsos']} UN</span>
                                </div>
                                """
                                st.markdown(card_html, unsafe_allow_html=True)
                                
                                # Botão de Saída associado ao ID único
                                if st.button("BAIXA", key=f"out_{r['ID']}", use_container_width=True):
                                    df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                                    df_e.to_csv(DB_EST, index=False)
                                    df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                                    registrar_log(n_logado, f"Saída Pilar {pilar}: {r['Bebida']}")
                                    st.rerun()
                        
                        st.markdown(f"<p style='text-align:right; color:#8b949e; font-size:0.8em; margin-top:-10px;'>Subtotal Camada: {total_un_cam} unidades</p>", unsafe_allow_html=True)
                        st.divider()
