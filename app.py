from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Diccionario para guardar el estado de los nodos: {id: {'id': id, 'estado': 'vivo'}}
nodos_db = {}
lider_actual = None

class ProcesoBully:
    @staticmethod
    def iniciar_eleccion(nodo_iniciador_id):
        global lider_actual
        emit_log(f"🕵️ Nodo {nodo_iniciador_id} detectó que el líder no responde.")
        
        # 1. El iniciador envía ELECTION a TODOS los nodos con ID mayor
        # En ProcesoBully.iniciar_eleccion
        nodos_superiores = sorted([n_id for n_id in nodos_db if n_id > nodo_iniciador_id])
        
        if not nodos_superiores:
            # Si no hay nadie por encima, él es el líder
            ProcesoBully.proclamar_lider(nodo_iniciador_id)
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
            ProcesoBully.proclamar_lider(nodo_iniciador_id)
        else:
            # Si hubo respuestas, los nodos que dijeron OK ahora deben iniciar su propia elección
            # Según el flujo del docente, el siguiente proceso lo toma el mayor de los que respondieron
            vivos_superiores = [n_id for n_id in nodos_superiores if nodos_db[n_id]['estado'] == 'vivo']
            if vivos_superiores:
                # El proceso se delega al siguiente nodo vivo superior
                ProcesoBully.iniciar_eleccion(min(vivos_superiores))

    @staticmethod
    def proclamar_lider(nuevo_lider_id):
        global lider_actual
        lider_actual = nuevo_lider_id
        emit_log(f"🏆 NODO {nuevo_lider_id} se proclama COORDINADOR")
        
        # Enviar mensaje de COORDINADOR a todos los nodos (inferiores y superiores)
        for n_id in nodos_db:
            if n_id != nuevo_lider_id and nodos_db[n_id]['estado'] == 'vivo':
                socketio.emit('animar_mensaje', {'desde': nuevo_lider_id, 'hasta': n_id, 'tipo': 'COORDINATOR'})
        
        socketio.emit('nuevo_lider', {'id': nuevo_lider_id})

class ProcesoRing:
    @staticmethod
    def iniciar_eleccion(nodo_iniciador_id):
        # El orden en el anillo depende de la posición en la lista (como están en pantalla)
        # Obtenemos todos los IDs en el orden en que fueron creados
        orden_anillo = [n_id for n_id in nodos_db.keys()]
        emit_log(f"⭕ RING: Nodo {nodo_iniciador_id} inicia fase de RECOLECCIÓN.")
        
        # Fase 1: Recolección (Naranja)
        lista_ids = [nodo_iniciador_id]
        ProcesoRing.pasar_token(nodo_iniciador_id, lista_ids, orden_anillo, fase="RECOLECCION")

    @staticmethod
    def pasar_token(actual_id, lista_ids, orden_anillo, fase):
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
            # --- MEJORA VISUAL: Animamos el último tramo de vuelta al iniciador ---
            tipo_msg = 'ELECTION' if fase == "RECOLECCION" else 'COORDINATOR'
            socketio.emit('animar_mensaje', {'desde': actual_id, 'hasta': sucesor_id, 'tipo': tipo_msg})
            socketio.sleep(0.8) # Esperamos a que la bolita llegue al iniciador

            if fase == "RECOLECCION":
                nuevo_lider = max(lista_ids)
                emit_log(f"🏁 Ciclo completo. Mayor: {nuevo_lider}. Iniciando ANUNCIO.")
                socketio.sleep(0.5)
                # Iniciar Fase 2
                ProcesoRing.pasar_token(sucesor_id, [sucesor_id, nuevo_lider], orden_anillo, fase="ANUNCIO")
            else:
                lider_final = lista_ids[1]
                socketio.emit('nuevo_lider', {'id': lider_final})
                emit_log(f"🏆 Anuncio completado. Nodo {lider_final} es el líder.")
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
            
            ProcesoRing.pasar_token(sucesor_id, lista_ids, orden_anillo, fase)


def emit_log(msg):
    print(msg)
    socketio.emit('log', {'msg': msg})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('registrar_nodo')
def handle_registro(data):
    n_id = data['id']
    nodos_db[n_id] = {'id': n_id, 'estado': 'vivo'}
    emit_log(f"Nodo {n_id} registrado en el backend.")

@socketio.on('forzar_eleccion')
def handle_force():
    if not nodos_db:
        emit_log("No hay nodos para iniciar elección.")
        return
    
    # Buscamos el nodo vivo con menor ID para que inicie la detección
    vivos = [n_id for n_id in nodos_db if nodos_db[n_id]['estado'] == 'vivo']
    if vivos:
        ProcesoBully.iniciar_eleccion(min(vivos))

@socketio.on('matar_nodo')
def handle_death(data):
    n_id = data['id']
    if n_id in nodos_db:
        nodos_db[n_id]['estado'] = 'muerto'
        emit_log(f"💀 Nodo {n_id} ha fallado (CRASH).")
        
        # Si el que murió era el líder, avisamos para que alguien detecte el fallo
        global lider_actual
        if n_id == lider_actual:
            lider_actual = None
            emit_log("⚠️ ¡El Líder ha muerto! Se requiere nueva elección.")
            socketio.emit('lider_caido')

algoritmo_activo = 'BULLY'

@socketio.on('cambiar_algoritmo')
def handle_algo_change(data):
    global algoritmo_activo
    algoritmo_activo = data['modo']
    print(f"🔄 Algoritmo cambiado a: {algoritmo_activo}")

@socketio.on('forzar_eleccion_desde')
def handle_force_from(data):
    if algoritmo_activo == 'BULLY':
        ProcesoBully.iniciar_eleccion(data['id'])
    else:
        # Iniciamos el proceso de anillo en un hilo separado para no bloquear el socket
        socketio.start_background_task(ProcesoRing.iniciar_eleccion, data['id'])

@socketio.on('connect')
def handle_connect():
    # Opcional: limpiar nodos al conectar o manejar sesiones
    pass

@socketio.on('limpiar_nodos')
def handle_clear():
    global nodos_db, lider_actual
    nodos_db.clear()
    lider_actual = None
    emit_log("Memoria del backend limpiada.")

@socketio.on('reset_backend')
def handle_reset():
    global nodos_db, lider_actual
    nodos_db.clear()
    lider_actual = None
    print("🧹 Backend reiniciado: Nodos borrados.")
    emit_log("Sistema reiniciado. Memoria limpia.")

if __name__ == '__main__':
    socketio.run(app, debug=True)