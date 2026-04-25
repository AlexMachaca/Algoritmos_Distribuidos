# 🚀 Simulador de Algoritmos de Elección (Bully & Ring)

Este proyecto es una herramienta interactiva y visual diseñada para entender el funcionamiento de los algoritmos de elección en **Sistemas Distribuidos**. Permite simular fallos en una red de nodos y observar en tiempo real cómo el sistema se auto-organiza para elegir un nuevo líder (coordinador).

![Tecnologías](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Framework](https://img.shields.io/badge/Flask-3.x-lightgrey?style=flat-square&logo=flask)
![Realtime](https://img.shields.io/badge/Socket.io-Realtime-black?style=flat-square&logo=socket.dot-io)
![Styling](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=flat-square&logo=tailwind-css)

---

## 🛠️ Algoritmos Implementados

### 1. Algoritmo de Bully (El Abusón)
Basado en la jerarquía por ID. 
- Cuando un nodo detecta que el líder ha fallado, envía un mensaje `ELECTION` a todos los nodos con un ID superior.
- Si no recibe respuesta, se proclama líder.
- Si recibe un `OK`, espera a que el nodo superior tome el mando.

### 2. Algoritmo de Ring (Anillo)
Basado en una estructura circular lógica.
- Los nodos se organizan en un anillo. 
- Al detectar un fallo, se inicia un mensaje de elección que circula por el anillo recolectando los IDs de los nodos vivos.
- Una vez el mensaje completa el círculo, el nodo con el ID más alto es proclamado líder y se notifica a todos.

---

## 🚀 Instalación y Ejecución Local

Sigue estos pasos para levantar el proyecto en tu máquina:

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd bully_web_viz
```

### 2. Crear un entorno virtual (Recomendado)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Iniciar la aplicación
```bash
python app.py
```

### 5. Acceder al navegador
Abre tu navegador y entra en: `http://127.0.0.1:5000`

---

## 🎮 Guía de Uso

1. **Añadir Nodos:** Haz clic en "Añadir Nodo" para poblar la red con IDs aleatorios.
2. **Seleccionar Algoritmo:** Cambia entre el modo **BULLY** o **RING** usando los botones superiores.
3. **Simular Fallo:** Haz clic sobre cualquier nodo (especialmente el líder, marcado en amarillo) para "matarlo" (simular un CRASH).
4. **Iniciar Elección:** Presiona el botón "Iniciar Elección" para que un nodo vivo detecte el fallo y comience el proceso.
5. **Control de Velocidad:** Usa el deslizador (slider) para ralentizar o acelerar las animaciones de los mensajes.

---

## 📂 Estructura del Proyecto

- `app.py`: Servidor Flask y manejo de eventos Socket.io.
- `core/`: Lógica pura de los algoritmos (Python).
- `static/`: Estilos CSS y lógica del frontend (JavaScript/Tailwind).
- `templates/`: Interfaz de usuario (HTML).

---

## 📝 Notas del Proyecto
Este simulador utiliza **Socket.io** para garantizar que la comunicación entre el "backend" (la lógica de elección) y el "frontend" (la visualización) sea instantánea y sincronizada.
