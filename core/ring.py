class ProcesoRing:
    @staticmethod
    def iniciar_eleccion(nodo_iniciador_id, ctx):
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        
        # El orden en el anillo depende de la posición en la lista (como están en pantalla)
        orden_anillo = [n_id for n_id in nodos_db.keys()]
        emit_log(f"⭕ RING: Nodo {nodo_iniciador_id} inicia fase de RECOLECCIÓN.")
        
        # Fase 1: Recolección (Naranja)
        lista_ids = [nodo_iniciador_id]
        ProcesoRing.pasar_token(nodo_iniciador_id, lista_ids, orden_anillo, "RECOLECCION", ctx)

    @staticmethod
    def pasar_token(actual_id, lista_ids, orden_anillo, fase, ctx):
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        socketio = ctx['socketio']
        
        idx_actual = orden_anillo.index(actual_id)
        
        # Buscar el siguiente nodo vivo en sentido horario (saltando muertos)
        pasos = 1
        sucesor_id = None
        while pasos < len(orden_anillo):
            posible_sucesor = orden_anillo[(idx_actual + pasos) % len(orden_anillo)]
            if nodos_db[posible_sucesor]['estado'] == 'vivo':
                sucesor_id = posible_sucesor
                break
            else:
                emit_log(f"⏭️ Nodo {posible_sucesor} está muerto, saltando...")
                pasos += 1

        if sucesor_id is None: return # Solo hay un nodo vivo

        # ¿El token volvió al que inició la fase?
        if sucesor_id == lista_ids[0]:
            # Animamos el último tramo de vuelta al iniciador
            tipo_msg = 'ELECTION' if fase == "RECOLECCION" else 'COORDINATOR'
            socketio.emit('animar_mensaje', {'desde': actual_id, 'hasta': sucesor_id, 'tipo': tipo_msg})
            socketio.sleep(0.8) # Esperamos a que la bolita llegue al iniciador

            if fase == "RECOLECCION":
                nuevo_lider = max(lista_ids)
                emit_log(f"🏁 Ciclo completo. Mayor: {nuevo_lider}. Iniciando ANUNCIO.")
                socketio.sleep(0.5)
                # Iniciar Fase 2
                ProcesoRing.pasar_token(sucesor_id, [sucesor_id, nuevo_lider], orden_anillo, "ANUNCIO", ctx)
            else:
                lider_final = lista_ids[1]
                socketio.emit('nuevo_lider', {'id': lider_final})
                emit_log(f"🏆 Anuncio completado. Nodo {lider_final} es el líder.")
                if 'on_lider_proclamado' in ctx:
                    ctx['on_lider_proclamado'](lider_final)
        else:
            # Animación y lógica según fase
            tipo_msg = 'ELECTION' if fase == "RECOLECCION" else 'COORDINATOR'
            socketio.emit('animar_mensaje', {'desde': actual_id, 'hasta': sucesor_id, 'tipo': tipo_msg})
            socketio.sleep(0.8)

            if fase == "RECOLECCION":
                lista_ids.append(sucesor_id)
                emit_log(f"📩 Token (Lista: {lista_ids}) -> Nodo {sucesor_id}")
            else:
                emit_log(f"📢 Avisando líder {lista_ids[1]} -> Nodo {sucesor_id}")
            
            ProcesoRing.pasar_token(sucesor_id, lista_ids, orden_anillo, fase, ctx)
