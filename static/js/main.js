const socket = io();
let nodos = [];
let modoActual = 'BULLY';

function cambiarModo(nuevoModo) {
    modoActual = nuevoModo;
    const btnB = document.getElementById('btn-bully');
    const btnR = document.getElementById('btn-ring');
    const leyendaContenido = document.getElementById('leyenda-contenido');
    const leyendaTitulo = document.getElementById('leyenda-titulo');

    if(modoActual === 'BULLY') {
        btnB.className = "px-6 py-2 rounded-md font-bold bg-blue-600 text-white";
        btnR.className = "px-6 py-2 rounded-md font-bold text-slate-400 hover:text-white";
        
        leyendaTitulo.innerText = "Leyenda Bully";
        leyendaContenido.innerHTML = `
            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-[#f59e0b]"></div><span>ELECTION (Elección)</span></div>
            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-[#10b981]"></div><span>OK (Respuesta)</span></div>
            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-[#8b5cf6]"></div><span>COORDINATOR (Líder)</span></div>
        `;
    } else {
        btnR.className = "px-6 py-2 rounded-md font-bold bg-purple-600 text-white";
        btnB.className = "px-6 py-2 rounded-md font-bold text-slate-400 hover:text-white";
        
        leyendaTitulo.innerText = "Leyenda Anillo";
        leyendaContenido.innerHTML = `
            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-[#f59e0b]"></div><span>RECOLECCIÓN (Lista IDs)</span></div>
            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-[#8b5cf6]"></div><span>ANUNCIO (Nuevo Líder)</span></div>
        `;
    }
    socket.emit('cambiar_algoritmo', { modo: modoActual });
    log(`Modo cambiado a: ${modoActual}`);
}

function agregarNodo() {
    let id;
    // Generar un ID aleatorio entre 1 y 99 que no exista ya
    do {
        id = Math.floor(Math.random() * 99) + 1;
    } while (nodos.some(n => n.id === id));

    nodos.push({ id: id, estado: 'vivo', esLider: false });
    actualizarVista();
    socket.emit('registrar_nodo', { id: id });
    log(`Nodo ${id} se ha unido a la red.`);
}

function actualizarVista() {
    const contenedor = document.getElementById('red-distribuida');
    contenedor.innerHTML = '';
    const radio = 250;
    const centroX = 250; // Mitad de 500px
    const centroY = 250; // Mitad de 500px

    nodos.forEach((nodo, i) => {
        const angulo = (i * 2 * Math.PI) / nodos.length;
        const x = centroX + radio * Math.cos(angulo) - 24; 
        const y = centroY + radio * Math.sin(angulo) - 24;

        const div = document.createElement('div');
        div.id = `nodo-${nodo.id}`;
        const estaMuerto = nodo.estado === 'muerto';
        const esLider = nodo.esLider && !estaMuerto;

        div.className = `nodo absolute w-12 h-12 rounded-full border-4 flex items-center justify-center font-bold cursor-pointer z-10
            ${estaMuerto ? 'border-red-900 bg-gray-800 text-gray-600' : 
              esLider ? 'border-yellow-400 bg-yellow-600 shadow-[0_0_20px_rgba(250,204,21,0.6)]' : 
              'border-blue-500 bg-blue-900 hover:scale-110'}`;
        
        div.style.left = `${x}px`;
        div.style.top = `${y}px`;
        div.innerText = nodo.id;

        div.onclick = () => {
            if (nodo.estado !== 'muerto') {
                nodo.estado = 'muerto';
                nodo.esLider = false;
                socket.emit('matar_nodo', { id: nodo.id });
                actualizarVista();
            }
        };
        contenedor.appendChild(div);
    });
}

function iniciarEleccion() {
    if (nodos.length === 0) {
        alert("No hay nodos en la red.");
        return;
    }

    if (modoActual === 'BULLY') {
        // Algoritmo Bully: Cualquier nodo vivo inicia aleatoriamente
        const nodosVivos = nodos.filter(n => n.estado === 'vivo');
        
        if (nodosVivos.length === 0) {
            alert("No hay nodos vivos para iniciar la elección.");
            return;
        }

        const nodoAleatorio = nodosVivos[Math.floor(Math.random() * nodosVivos.length)];
        log(`🎲 [BULLY] El nodo ${nodoAleatorio.id} ha sido elegido aleatoriamente para iniciar.`);
        socket.emit('forzar_eleccion_desde', { id: nodoAleatorio.id });

    } else {
        // Algoritmo Anillo: Inicia el mayor entre los dos siguientes al nodo muerto
        const indiceMuerto = nodos.findIndex(n => n.estado === 'muerto');

        if (indiceMuerto === -1) {
            alert("Para el simulador de anillo, primero 'mata' un nodo para detectar el fallo.");
            return;
        }

        const total = nodos.length;
        // Obtenemos los dos nodos siguientes en sentido horario
        const nodoSig1 = nodos[(indiceMuerto + 1) % total];
        const nodoSig2 = nodos[(indiceMuerto + 2) % total];

        // Elegimos el que tenga mayor ID de entre esos dos
        const iniciador = (nodoSig1.id > nodoSig2.id) ? nodoSig1 : nodoSig2;

        log(`⭕ [RING] Detectado fallo en nodo ${nodos[indiceMuerto].id}.`);
        log(`🔎 Comparando sucesores: ${nodoSig1.id} vs ${nodoSig2.id}. Inicia el mayor: ${iniciador.id}`);
        
        socket.emit('forzar_eleccion_desde', { id: iniciador.id });
    }
}

function revivirNodos() {
    nodos.forEach(n => { n.estado = 'vivo'; n.esLider = false; socket.emit('registrar_nodo', {id: n.id}); });
    actualizarVista();
    log("Todos los nodos revividos.");
}

function resetCompleto() {
    socket.emit('reset_backend');
    nodos = [];
    actualizarVista();
    document.getElementById('consola').innerHTML = '<p class="text-gray-500">> Sistema reiniciado.</p>';
}

function log(msg) {
    const c = document.getElementById('consola');
    c.innerHTML += `<p>> ${msg}</p>`;
    c.scrollTop = c.scrollHeight;
}

// SOCKET EVENTS
socket.on('log', (data) => log(data.msg));

socket.on('nuevo_lider', (data) => {
    nodos.forEach(n => n.esLider = (n.id === data.id));
    actualizarVista();
});

socket.on('animar_mensaje', (data) => {
    const elOrigen = document.getElementById(`nodo-${data.desde}`);
    const elDestino = document.getElementById(`nodo-${data.hasta}`);
    
    if (!elOrigen || !elDestino) return;

    // Obtenemos la posición exacta respecto a la ventana (viewport)
    const rectO = elOrigen.getBoundingClientRect();
    const rectD = elDestino.getBoundingClientRect();

    // Calculamos el centro exacto del círculo del nodo
    // Sumamos window.scrollX/Y por si moviste la pantalla hacia abajo
    const startX = rectO.left + (rectO.width / 2) + window.scrollX;
    const startY = rectO.top + (rectO.height / 2) + window.scrollY;
    
    const endX = rectD.left + (rectD.width / 2) + window.scrollX;
    const endY = rectD.top + (rectD.height / 2) + window.scrollY;

    const ball = document.createElement('div');
    ball.className = 'mensaje-vuelo';
    
    // Colores según el tipo
    if (data.tipo === 'ELECTION') ball.style.background = '#f59e0b';
    if (data.tipo === 'OK') ball.style.background = '#10b981';
    if (data.tipo === 'COORDINATOR') ball.style.background = '#8b5cf6';

    // Ajustamos la bolita para que su centro coincida con startX/Y
    ball.style.left = `${startX - 7}px`; 
    ball.style.top = `${startY - 7}px`;
    
    document.body.appendChild(ball);

    // Animación corregida
    ball.animate([
        { 
            left: `${startX - 7}px`, 
            top: `${startY - 7}px` 
        },
        { 
            left: `${endX - 7}px`, 
            top: `${endY - 7}px` 
        }
    ], { 
        duration: 800, 
        easing: 'ease-in-out' 
    }).onfinish = () => ball.remove();
});