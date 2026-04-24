from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from core.bully import ProcesoBully
from core.ring import ProcesoRing

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Diccionario para guardar el estado de los nodos: {id: {'id': id, 'estado': 'vivo'}}
nodos_db = {}
lider_actual = None
algoritmo_activo = 'BULLY'

def emit_log(msg):
    print(msg)
    socketio.emit('log', {'msg': msg})

def update_lider(nuevo_id):
    global lider_actual
    lider_actual = nuevo_id

def get_context():
    return {
        'socketio': socketio,
        'nodos_db': nodos_db,
        'emit_log': emit_log,
        'on_lider_proclamado': update_lider
    }

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('registrar_nodo')
def handle_registro(data):
    n_id = data['id']
    nodos_db[n_id] = {'id': n_id, 'estado': 'vivo'}
    emit_log(f"Nodo {n_id} registrado en el backend.")

@socketio.on('matar_nodo')
def handle_death(data):
    n_id = data['id']
    if n_id in nodos_db:
        nodos_db[n_id]['estado'] = 'muerto'
        emit_log(f"💀 Nodo {n_id} ha fallado (CRASH).")
        
        global lider_actual
        if n_id == lider_actual:
            lider_actual = None
            emit_log("⚠️ ¡El Líder ha muerto! Se requiere nueva elección.")
            socketio.emit('lider_caido')

@socketio.on('cambiar_algoritmo')
def handle_algo_change(data):
    global algoritmo_activo
    algoritmo_activo = data['modo']
    print(f"🔄 Algoritmo cambiado a: {algoritmo_activo}")

@socketio.on('forzar_eleccion_desde')
def handle_force_from(data):
    ctx = get_context()
    if algoritmo_activo == 'BULLY':
        ProcesoBully.iniciar_eleccion(data['id'], ctx)
    else:
        # Iniciamos el proceso de anillo en un hilo separado para no bloquear el socket
        socketio.start_background_task(ProcesoRing.iniciar_eleccion, data['id'], ctx)

@socketio.on('reset_backend')
def handle_reset():
    global nodos_db, lider_actual
    nodos_db.clear()
    lider_actual = None
    print("🧹 Backend reiniciado: Nodos borrados.")
    emit_log("Sistema reiniciado. Memoria limpia.")

if __name__ == '__main__':
    socketio.run(app, debug=True)
