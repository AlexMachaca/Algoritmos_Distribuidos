const socket = io();
let nodos = [];
let modoActual = 'BULLY';
let duracionSimulacion = 800; // Valor por defecto en ms

// Listener para el slider de velocidad
document.getElementById('speed-slider').addEventListener('input', (e) => {
    duracionSimulacion = parseInt(e.target.value);
    socket.emit('actualizar_velocidad', { velocidad: duracionSimulacion });
});

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
    actualizarVista(); // Redibujar líneas al cambiar modo
    log(`Modo cambiado a: ${modoActual}`);
}

function agregarNodo() {
    let id;
    do {
        id = Math.floor(Math.random() * 99) + 1;
    } while (nodos.some(n => n.id === id));

    nodos.push({ id: id, estado: 'vivo', esLider: false });
    actualizarVista();
    socket.emit('registrar_nodo', { id: id });
    log(`Nodo ${id} se ha unido a la red.`);
}

function getCoordenadasNodo(index, total) {
    const radio = 250;
    const centroX = 250;
    const centroY = 250;
    const angulo = (index * 2 * Math.PI) / total;
    return {
        x: centroX + radio * Math.cos(angulo),
        y: centroY + radio * Math.sin(angulo)
    };
}

function dibujarConexiones() {
    const svg = document.getElementById('svg-conexiones');
    svg.innerHTML = ''; // Limpiar líneas anteriores
    const total = nodos.length;
    if (total < 2) return;

    if (modoActual === 'RING') {
        // Dibujar anillo: línea entre i e i+1
        nodos.forEach((_, i) => {
            const inicio = getCoordenadasNodo(i, total);
            const fin = getCoordenadasNodo((i + 1) % total, total);
            const linea = document.createElementNS("http://www.w3.org/2000/svg", "line");
            linea.setAttribute("x1", inicio.x);
            linea.setAttribute("y1", inicio.y);
            linea.setAttribute("x2", fin.x);
            linea.setAttribute("y2", fin.y);
            linea.setAttribute("stroke", "#334155"); // slate-700
            linea.setAttribute("stroke-width", "2");
            linea.setAttribute("stroke-dasharray", "5,5"); // Estilo discontinuo para el anillo
            svg.appendChild(linea);
        });
    } else {
        // Dibujar malla (Bully): todos con todos, pero muy tenue
        for (let i = 0; i < total; i++) {
            for (let j = i + 1; j < total; j++) {
                const inicio = getCoordenadasNodo(i, total);
                const fin = getCoordenadasNodo(j, total);
                const linea = document.createElementNS("http://www.w3.org/2000/svg", "line");
                linea.setAttribute("x1", inicio.x);
                linea.setAttribute("y1", inicio.y);
                linea.setAttribute("x2", fin.x);
                linea.setAttribute("y2", fin.y);
                linea.setAttribute("stroke", "rgba(51, 65, 85, 0.3)"); 
                linea.setAttribute("stroke-width", "1");
                svg.appendChild(linea);
            }
        }
    }
}

function actualizarVista() {
    const contenedor = document.getElementById('red-distribuida');
    // Mantener solo el SVG, limpiar los nodos (divs)
    const nodosExistentes = contenedor.querySelectorAll('.nodo');
    nodosExistentes.forEach(n => n.remove());

    dibujarConexiones();

    nodos.forEach((nodo, i) => {
        const pos = getCoordenadasNodo(i, nodos.length);
        const div = document.createElement('div');
        div.id = `nodo-${nodo.id}`;
        const estaMuerto = nodo.estado === 'muerto';
        const esLider = nodo.esLider && !estaMuerto;

        div.className = `nodo absolute w-12 h-12 rounded-full border-4 flex items-center justify-center font-bold cursor-pointer z-10
            ${estaMuerto ? 'border-red-900 bg-gray-800 text-gray-600' : 
              esLider ? 'border-yellow-400 bg-yellow-600 shadow-[0_0_20px_rgba(250,204,21,0.6)]' : 
              'border-blue-500 bg-blue-900 hover:scale-110'}`;
        
        div.style.left = `${pos.x - 24}px`;
        div.style.top = `${pos.y - 24}px`;
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
        const nodosVivos = nodos.filter(n => n.estado === 'vivo');
        if (nodosVivos.length === 0) {
            alert("No hay nodos vivos.");
            return;
        }
        const nodoAleatorio = nodosVivos[Math.floor(Math.random() * nodosVivos.length)];
        log(`🎲 [BULLY] El nodo ${nodoAleatorio.id} inicia.`);
        socket.emit('forzar_eleccion_desde', { id: nodoAleatorio.id });

    } else {
        const indiceMuerto = nodos.findIndex(n => n.estado === 'muerto');
        if (indiceMuerto === -1) {
            alert("Mata un nodo primero.");
            return;
        }
        const total = nodos.length;
        const nodoSig1 = nodos[(indiceMuerto + 1) % total];
        const nodoSig2 = nodos[(indiceMuerto + 2) % total];
        const iniciador = (nodoSig1.id > nodoSig2.id) ? nodoSig1 : nodoSig2;
        log(`⭕ [RING] Detectado fallo. Inicia: ${iniciador.id}`);
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

    const rectO = elOrigen.getBoundingClientRect();
    const rectD = elDestino.getBoundingClientRect();

    const startX = rectO.left + (rectO.width / 2) + window.scrollX;
    const startY = rectO.top + (rectO.height / 2) + window.scrollY;
    const endX = rectD.left + (rectD.width / 2) + window.scrollX;
    const endY = rectD.top + (rectD.height / 2) + window.scrollY;

    const ball = document.createElement('div');
    ball.className = 'mensaje-vuelo';
    
    if (data.tipo === 'ELECTION') ball.style.background = '#f59e0b';
    if (data.tipo === 'OK') ball.style.background = '#10b981';
    if (data.tipo === 'COORDINATOR') ball.style.background = '#8b5cf6';

    ball.style.left = `${startX - 7}px`; 
    ball.style.top = `${startY - 7}px`;
    document.body.appendChild(ball);

    ball.animate([
        { left: `${startX - 7}px`, top: `${startY - 7}px` },
        { left: `${endX - 7}px`, top: `${endY - 7}px` }
    ], { 
        duration: duracionSimulacion, // Sincronizado con el slider
        easing: 'ease-in-out' 
    }).onfinish = () => ball.remove();
});