# --- 🏗️ PILARES (VERSÃO PILHA VERTICAL AMARRADA) ---
    elif menu == "🏗️ Pilares (Amarração)":
        st.title("🏗️ Engenharia de Pilares")
        
        with st.expander("➕ MONTAR NOVA CAMADA (ESTRUTURA AMARRADA)"):
            p_alvo = st.selectbox("Pilar Destino", ["+ Criar Novo"] + list(df_pil['NomePilar'].unique()))
            n_pilar = st.text_input("Identificação do Pilar").upper() if p_alvo == "+ Criar Novo" else p_alvo
            cat_filtro = st.selectbox("Filtrar Categoria para Montagem", df_p['Categoria'].unique())
            
            if n_pilar:
                # Lógica para identificar a próxima camada
                c_atual = 1 if df_pil[df_pil['NomePilar']==n_pilar].empty else df_pil[df_pil['NomePilar']==n_pilar]['Camada'].max() + 1
                
                # Padrão de amarração 3x2 ou 2x3 para travar o pilar
                at, fr = (3, 2) if c_atual % 2 != 0 else (2, 3)
                
                if c_atual == 1:
                    st.success(f"🌟 Iniciando BASE do Pilar: **{n_pilar}**")
                else:
                    st.info(f"⬆️ Montando sobre a Camada {c_atual-1}")

                st.warning(f"📐 Padrão desta Camada: **{at}x{fr}** (Total: {at+fr} fardos/caixas)")
                
                lista_beb = ["Vazio"] + df_p[df_p['Categoria'] == cat_filtro]['Nome'].tolist()
                beb_dict, av_dict = {}, {}
                
                # Grid de montagem dinâmico
                cols_grid = st.columns(max(at, fr))
                for i in range(at + fr):
                    pos = i + 1
                    with cols_grid[i % len(cols_grid)]:
                        st.markdown(f"**Posição {pos}**")
                        beb_dict[pos] = st.selectbox(f"Bebida", lista_beb, key=f"p_{pos}", label_visibility="collapsed")
                        av_dict[pos] = st.number_input(f"Avulsos", 0, key=f"a_{pos}")
                
                if st.button("FINALIZAR CAMADA E EMPILHAR", use_container_width=True):
                    regs = [[f"{n_pilar}_{c_atual}_{p}_{datetime.now().second}", n_pilar, c_atual, p, b, av_dict[p]] for p, b in beb_dict.items() if b != "Vazio"]
                    if regs:
                        pd.concat([df_pil, pd.DataFrame(regs, columns=df_pil.columns)]).to_csv(DB_PIL, index=False)
                        registrar_log(n_logado, f"Empilhou Camada {c_atual} no Pilar {n_pilar}")
                        st.success("Camada adicionada ao topo!")
                        st.rerun()

        st.markdown("---")

        # --- VISUALIZAÇÃO DOS PILARES (DE BAIXO PARA CIMA) ---
        for pilar in df_pil['NomePilar'].unique():
            st.markdown(f"### 📍 Pilar: {pilar}")
            
            # Invertemos a ordem (reverse=True) para que a maior camada apareça no TOPO da tela
            camadas = sorted(df_pil[df_pil['NomePilar'] == pilar]['Camada'].unique(), reverse=True)
            
            for cam in camadas:
                dados_cam = df_pil[(df_pil['NomePilar'] == pilar) & (df_pil['Camada'] == cam)]
                total_un_cam = 0
                
                with st.container():
                    # Estilização para identificar o que é topo e o que é base
                    cor_borda = "#58a6ff" if cam == max(camadas) else "#30363d"
                    label_camada = "🔝 TOPO" if cam == max(camadas) else ("🧱 BASE" if cam == 1 else f"📦 Camada {cam}")
                    
                    st.markdown(f"<small style='color:{cor_borda}; font-weight:bold;'>{label_camada}</small>", unsafe_allow_html=True)
                    
                    cols = st.columns(5)
                    for _, r in dados_cam.iterrows():
                        u_padrao, _ = get_config_bebida(r['Bebida'], df_p)
                        total_un_cam += (u_padrao + r['Avulsos'])
                        
                        with cols[int(r['Posicao'])-1]:
                            # Card visual do fardo/refri
                            card_html = f"""
                            <div style="background-color:#1c2128; padding:8px; border-radius:10px; border:2px solid {cor_borda}; text-align:center; margin-bottom:5px;">
                                <b style="font-size:0.8em; color:#e6edf3;">{r['Bebida']}</b><br>
                                <span style="color:#238636; font-size:0.75em;">+{r['Avulsos']} UN</span>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # Botão de Baixa (só faz sentido tirar do topo, mas deixei em todos por flexibilidade)
                            if st.button("BAIXA", key=f"out_{r['ID']}", use_container_width=True):
                                df_e.loc[df_e['Nome'] == r['Bebida'], 'Estoque_Total_Un'] -= (u_padrao + r['Avulsos'])
                                df_e.to_csv(DB_EST, index=False)
                                df_pil[df_pil['ID'] != r['ID']].to_csv(DB_PIL, index=False)
                                registrar_log(n_logado, f"Saída Pilar {pilar}: {r['Bebida']}")
                                st.rerun()
                    
                    st.markdown(f"<p style='text-align:right; color:#8b949e; font-size:0.75em; margin-top:-5px;'>Total na camada: {total_un_cam} un</p>", unsafe_allow_html=True)
                    
                    # Indicador visual de empilhamento
                    if cam > 1:
                        st.markdown("<div style='text-align:center; color:#30363d; margin-top:-10px; margin-bottom:10px;'>▼ APOIADO SOBRE ▼</div>", unsafe_allow_html=True)
            st.divider()
