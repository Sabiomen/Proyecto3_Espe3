Agente Orquestador MCP con Analítica en MongoDB
PP3 – Orquestador (UFRO)
Integración PP1 (Normativa UFRO) + PP2 (Verificación de Identidad)
Descripción del Proyecto

Este proyecto implementa un Agente Orquestador MCP, capaz de:

Identificar a la persona usando los servicios del PP2 (verificación de identidad).

Responder una consulta utilizando el PP1 (chatbot RAG/Normativa UFRO).

Registrar analítica en MongoDB, almacenando:

usuario reconocido

tipo de consulta

timestamp

respuesta entregada

Exponer un servidor MCP totalmente compatible con FastAPI.

Integrarse con un workflow n8n que orquesta las llamadas entre componentes.

Este proyecto está diseñado para correr en AWS o localmente mediante variables de entorno.

Arquitectura General
      Usuario
         │
   ┌─────▼──────┐
   │ Orquestador │  ← FastAPI + MCP Server
   └─────┬──────┘
         │
         ├────────► PP2 (Verificación de Identidad)
         │
         ├────────► PP1 (Normativa UFRO - RAG)
         │
         └────────► MongoDB (Analítica)

Módulo clave: fuse.py

Archivo que actúa como conector unificado entre:

MCP Server

API del orquestador

Servicios PP2 y PP1

Se encarga de coordinar la lógica completa: identificar usuario, obtener normativa y almacenar actividad.

Funcionalidades
1. Verificación de Identidad (PP2)

Se consulta a múltiples servicios PP2 en paralelo.

Se retorna el mejor match logrado.

2. Consulta de Normativa (PP1)

Se envía la pregunta del usuario al chatbot RAG UFRO.

Se obtiene una respuesta precisa y sustentada.

3. Analítica en MongoDB

Cada interacción se guarda con:

identity

query

answer

timestamp

source

4. MCP Server

Permite al MCP Orchestrator:

Exponer herramientas

Recibir acciones

Procesar solicitudes de manera unificada

Estructura del Proyecto
/project
 ├── app/
 │   ├── main.py        # Endpoint FastAPI
 │   ├── fuse.py        # Integración PP1 + PP2 + MongoDB
 │   ├── mcp_server.py  # Servidor MCP
 │   ├── services/
 │   │   ├── pp1_client.py   # Cliente PP1
 │   │   ├── pp2_client.py   # Cliente PP2
 │   │   └── mongo_client.py # Cliente MongoDB
 │   └── models/
 │       └── schemas.py
 │
 ├── workflow/
 │   └── pp3-n8n-workflow.json   # Versión exportada
 │
 ├── requirements.txt
 ├── README.md
 └── .env.example

Requisitos

Python 3.10+

FastAPI

MCP SDK

MongoDB Atlas o instancia local

n8n (opcional para la demo)

Servicios PP1 / PP2 accesibles desde Internet o localhost

Variables de Entorno

Crea un archivo .env:

MONGO_URI=
MONGO_DB=pp3
PP1_URL=
PP2_URL_1=
PP2_URL_2=
PP2_URL_3=
ORCHESTRATOR_API_KEY=

Cómo ejecutar
1. Instalar dependencias
pip install -r requirements.txt

2. Ejecutar FastAPI
uvicorn app.main:app --reload

3. Iniciar el MCP Server
python app/mcp_server.py

4. Abrir la documentación interactiva
http://localhost:8000/docs

Endpoints principales
 POST /orchestrator/query

Ejemplo:

{
  "usuario": "12345678-9",
  "consulta": "¿Cuál es la normativa sobre apelación de exámenes?"
}


Respuesta:

{
  "identidad": "Juan Pérez",
  "respuesta": "La normativa indica que...",
  "timestamp": "2025-12-07T18:20:03Z"
}

Analítica en MongoDB

Colección: interactions

Ejemplo de documento:

{
  "identity": "Juan Pérez",
  "query": "normativa exámenes",
  "answer": "...",
  "timestamp": { "$date": "2025-12-07T21:00:00Z" }
}

Integración con n8n

El workflow exportado (workflow/pp3-n8n-workflow.json) contiene:

Llamada a PP2

Llamada a PP1

Evaluación paralela

Envío final al Orquestador

Registro en MongoDB

Puede importarse directamente desde el panel de n8n.

Pruebas

Incluye:

Pruebas unitarias (servicios PP1/PP2)

Pruebas de integración (fuse.py)

Pruebas funcionales (FastAPI)

Pruebas MCP (herramientas del servidor)

