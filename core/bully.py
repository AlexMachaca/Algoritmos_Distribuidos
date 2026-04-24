class ProcesoBully:
    @staticmethod
    def iniciar_eleccion(nodo_iniciador_id, ctx):
        socketio = ctx['socketio']
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        
        emit_log(f"🕵️ Nodo {nodo_iniciador_id} detectó que el líder no responde.")
        
        # 1. El iniciador envía ELECTION a TODOS los nodos con ID mayor
        nodos_superiores = sorted([n_id for n_id in nodos_db if n_id > nodo_iniciador_id])
        
        if not nodos_superiores:
            # Si no hay nadie por encima, él es el líder
            ProcesoBully.proclamar_lider(nodo_iniciador_id, ctx)
            return

        respuestas_recibidas = False
        
        for m_id in nodos_superiores:
            # Animamos el mensaje de elección hacia todos los superiores
            socketio.emit('animar_mensaje', {'desde': nodo_iniciador_id, 'hasta': m_id, 'tipo': 'ELECTION'})
            emit_log(f"Mensaje ELECTION enviado de {nodo_iniciador_id} a {m_id}")
            
            # Verificamos si el nodo superior está vivo para responder OK
            if nodos_db[m_id]['estado'] == 'vivo':
                socketio.sleep(0.5) # Espera para ver la animación
                socketio.emit('animar_mensaje', {'desde': m_id, 'hasta': nodo_iniciador_id, 'tipo': 'OK'})
                emit_log(f"✅ Nodo {m_id} responde OK a {nodo_iniciador_id}")
                respuestas_recibidas = True

        socketio.sleep(1.0) # Tiempo de espera para recolectar todas las respuestas (Timeout)

        if not respuestas_recibidas:
            # Si nadie respondió OK, el iniciador se proclama líder
            ProcesoBully.proclamar_lider(nodo_iniciador_id, ctx)
        else:
            # Si hubo respuestas, los nodos que dijeron OK ahora deben iniciar su propia elección
            vivos_superiores = [n_id for n_id in nodos_superiores if nodos_db[n_id]['estado'] == 'vivo']
            if vivos_superiores:
                # El proceso se delega al siguiente nodo vivo superior
                ProcesoBully.iniciar_eleccion(min(vivos_superiores), ctx)

    @staticmethod
    def proclamar_lider(nuevo_lider_id, ctx):
        socketio = ctx['socketio']
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        
        emit_log(f"🏆 NODO {nuevo_lider_id} se proclama COORDINADOR")
        
        # Enviar mensaje de COORDINADOR a todos los nodos (inferiores y superiores)
        for n_id in nodos_db:
            if n_id != nuevo_lider_id and nodos_db[n_id]['estado'] == 'vivo':
                socketio.emit('animar_mensaje', {'desde': nuevo_lider_id, 'hasta': n_id, 'tipo': 'COORDINATOR'})
        
        socketio.emit('nuevo_lider', {'id': nuevo_lider_id})
        
        if 'on_lider_proclamado' in ctx:
            ctx['on_lider_proclamado'](nuevo_lider_id)
