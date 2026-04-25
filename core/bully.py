class ProcesoBully:
    @staticmethod
    def iniciar_eleccion(nodo_iniciador_id, ctx):
        socketio = ctx['socketio']
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        delay = ctx['delay']
        
        emit_log(f"🕵️ Nodo {nodo_iniciador_id} detectó que el líder no responde.")
        
        nodos_superiores = sorted([n_id for n_id in nodos_db if n_id > nodo_iniciador_id])
        
        if not nodos_superiores:
            ProcesoBully.proclamar_lider(nodo_iniciador_id, ctx)
            return

        respuestas_recibidas = False
        
        for m_id in nodos_superiores:
            socketio.emit('animar_mensaje', {'desde': nodo_iniciador_id, 'hasta': m_id, 'tipo': 'ELECTION'})
            emit_log(f"Mensaje ELECTION enviado de {nodo_iniciador_id} a {m_id}")
            
            if nodos_db[m_id]['estado'] == 'vivo':
                socketio.sleep(delay) # Usar delay dinámico
                socketio.emit('animar_mensaje', {'desde': m_id, 'hasta': nodo_iniciador_id, 'tipo': 'OK'})
                emit_log(f"✅ Nodo {m_id} responde OK a {nodo_iniciador_id}")
                respuestas_recibidas = True

        socketio.sleep(delay * 1.5) # Timeout proporcional a la velocidad

        if not respuestas_recibidas:
            ProcesoBully.proclamar_lider(nodo_iniciador_id, ctx)
        else:
            vivos_superiores = [n_id for n_id in nodos_superiores if nodos_db[n_id]['estado'] == 'vivo']
            if vivos_superiores:
                ProcesoBully.iniciar_eleccion(min(vivos_superiores), ctx)

    @staticmethod
    def proclamar_lider(nuevo_lider_id, ctx):
        socketio = ctx['socketio']
        nodos_db = ctx['nodos_db']
        emit_log = ctx['emit_log']
        
        emit_log(f"🏆 NODO {nuevo_lider_id} se proclama COORDINADOR")
        
        for n_id in nodos_db:
            if n_id != nuevo_lider_id and nodos_db[n_id]['estado'] == 'vivo':
                socketio.emit('animar_mensaje', {'desde': nuevo_lider_id, 'hasta': n_id, 'tipo': 'COORDINATOR'})
        
        socketio.emit('nuevo_lider', {'id': nuevo_lider_id})
        
        if 'on_lider_proclamado' in ctx:
            ctx['on_lider_proclamado'](nuevo_lider_id)
