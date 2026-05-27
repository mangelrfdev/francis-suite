# Francis Suite — Documento Operativo Definitivo

> **Cómo convertir `Francis Suite` en un sistema de automatización de datos confiable, online y observable, conectado a Supabase, con manejo de errores, reintentos y despliegue cloud.**

---

## Tabla de contenidos

- [Francis Suite — Documento Operativo Definitivo](#francis-suite--documento-operativo-definitivo)
  - [Tabla de contenidos](#tabla-de-contenidos)
  - [1. Visión](#1-visión)
  - [2. Filosofía operativa](#2-filosofía-operativa)
  - [3. Arquitectura en una imagen](#3-arquitectura-en-una-imagen)
  - [4. Los 3 contratos clave](#4-los-3-contratos-clave)
  - [5. Modelo de datos en Supabase](#5-modelo-de-datos-en-supabase)
  - [6. Paso 0 — Preparación](#6-paso-0--preparación)
  - [7. Paso 1 — Trigger: iniciar una ejecución](#7-paso-1--trigger-iniciar-una-ejecución)
  - [8. Paso 2 — Ejecutar Francis Suite](#8-paso-2--ejecutar-francis-suite)
  - [9. Paso 3 — Éxito: identificar el archivo generado](#9-paso-3--éxito-identificar-el-archivo-generado)
  - [10. Paso 4 — Fallo: clasificar y reintentar](#10-paso-4--fallo-clasificar-y-reintentar)
  - [11. Paso 5 — Cargar datos a Supabase de forma segura](#11-paso-5--cargar-datos-a-supabase-de-forma-segura)
  - [12. Paso 6 — Observabilidad: endpoints y logs](#12-paso-6--observabilidad-endpoints-y-logs)
  - [13. Paso 7 — Despliegue en la nube](#13-paso-7--despliegue-en-la-nube)
  - [14. Ideas de vanguardia (roadmap)](#14-ideas-de-vanguardia-roadmap)
  - [15. Checklist de implementación](#15-checklist-de-implementación)
  - [16. Qué poner en el CV cuando esté listo](#16-qué-poner-en-el-cv-cuando-esté-listo)

---

## 1. Visión

`Francis Suite` ya es un **motor ejecutable local** que procesa workflows XML y genera archivos de datos. Este documento define **cómo operarlo de forma profesional**:

- Correrlo **online** 24/7.
- **Disparar ejecuciones** vía API desde cualquier lado.
- Saber en tiempo real si una corrida está **running, failed o completed**.
- Manejar **errores con reintentos inteligentes**.
- **Identificar el archivo generado** sin ambigüedad.
- **Refrescar una tabla Supabase** sin dejarla nunca vacía por error.

---

## 2. Filosofía operativa

Cuatro principios que guían todo el diseño:

- **Idempotencia**: una misma ejecución debe poder repetirse sin corromper datos.
- **Atomicidad práctica**: nunca borrar la tabla destino antes de validar el nuevo output.
- **Observabilidad por defecto**: cada paso debe dejar rastro en Supabase.
- **Separación de responsabilidades**: una capa ejecuta, otra valida, otra carga, otra reporta.

---

## 3. Arquitectura en una imagen

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Cliente   │───▶│  API FastAPI │───▶│  Background job  │
│ (curl, n8n, │     │  POST /run   │     │ Francis Suite CLI│
│  cron, UI)  │     └──────┬───────┘     └────────┬─────────┘
└─────────────┘            │                      │
                           ▼                      ▼
                    ┌────────────────────────────────┐
                    │       Supabase                 │
                    │  ┌──────────────────────────┐  │
                    │  │ francis_runs (estado)    │  │
                    │  └──────────────────────────┘  │
                    │  ┌──────────────────────────┐  │
                    │  │ tu_tabla (datos finales) │  │
                    │  └──────────────────────────┘  │
                    └────────────────────────────────┘
                           ▲                      ▲
                           │                      │
                    ┌──────┴───────┐     ┌───────┴────────┐
                    │  Status API  │     │ Loader Python  │
                    │ GET /status  │     │ (refresh total)│
                    └──────────────┘     └────────────────┘
```

---

## 4. Los 3 contratos clave

Todo el sistema se reduce a definir bien tres contratos:

| Contrato | Qué define | Cómo se expresa |
|---|---|---|
| **Ejecución** | Cómo se dispara un run | `POST /run` con `workflow` y `params` |
| **Estado** | Cómo se reporta progreso/error/éxito | Fila en `francis_runs` con `status` + campos |
| **Salida** | Qué archivo representa el resultado final | Carpeta única `runs/{session_id}/` + `output_path` registrado |

Si estos tres contratos son sólidos, todo lo demás encaja.

---

## 5. Modelo de datos en Supabase

### Tabla `francis_runs` (estado de cada ejecución)

```sql
CREATE TABLE francis_runs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_name    TEXT NOT NULL,
  params           JSONB DEFAULT '{}'::jsonb,
  status           TEXT NOT NULL DEFAULT 'CREATED',
  -- CREATED | RUNNING | RETRYING | COMPLETED | FAILED | CANCELLED
  started_at       TIMESTAMPTZ DEFAULT NOW(),
  ended_at         TIMESTAMPTZ,
  duration_ms      INTEGER,
  retry_count      INTEGER DEFAULT 0,
  max_retries      INTEGER DEFAULT 3,
  error_type       TEXT,         -- RECOVERABLE | FATAL
  error_message    TEXT,
  output_path      TEXT,
  output_format    TEXT,         -- json | csv | ndjson | xlsx | parquet
  output_row_count INTEGER,
  load_status      TEXT DEFAULT 'PENDING',
  -- PENDING | LOADING | LOADED | LOAD_FAILED | SKIPPED
  loaded_rows      INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_runs_status ON francis_runs(status);
CREATE INDEX idx_runs_workflow ON francis_runs(workflow_name);
CREATE INDEX idx_runs_created ON francis_runs(created_at DESC);
```

### Tabla `tu_tabla_de_datos`

La que ya tienes. Solo necesita una clave natural estable para poder ser borrada y repoblada de forma segura.

---

## 6. Paso 0 — Preparación

### Tecnologías

| Tecnología | Rol |
|---|---|
| Python 3.11+ | Lenguaje base |
| Francis Suite | Motor de workflows |
| FastAPI + Uvicorn | API de control |
| `supabase-py` | Cliente oficial de Supabase |
| `python-dotenv` | Leer `.env` |
| Docker | Contenedor para deploy |
| Railway / Render / Fly.io | Entorno cloud |

### Archivo `.env` (nunca subir a git)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
TARGET_TABLE=tu_tabla_de_datos
FRANCIS_RUNS_DIR=./runs
MAX_CONCURRENT_RUNS=2
EXECUTION_TIMEOUT_SEC=600
```

### Estructura del proyecto

```
francis-operator/
├── api.py                 # FastAPI app
├── executor.py            # Ejecución + retries
├── loader.py              # Carga a Supabase
├── errors.py              # Clasificación de errores
├── db.py                  # Cliente Supabase
├── config.py              # Lectura de .env
├── requirements.txt
├── Dockerfile
├── .env
└── workflows/
    └── topPropiedades.xml
```

---

## 7. Paso 1 — Trigger: iniciar una ejecución

### Qué pasa
El cliente llama `POST /run` con el workflow y parámetros. La API crea un `session_id`, registra el run en `CREATED` y lanza la ejecución en background. Responde inmediatamente.

### Código: `api.py`

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from pathlib import Path
import uuid

from db import supabase
from executor import execute_francis
from config import settings

app = FastAPI(title="Francis Suite Operator")

class RunRequest(BaseModel):
    workflow: str
    params: dict = {}

@app.post("/run")
async def run_workflow(req: RunRequest, background_tasks: BackgroundTasks):
    # Validar que el workflow existe
    workflow_path = Path(req.workflow)
    if not workflow_path.exists():
        raise HTTPException(400, f"Workflow no encontrado: {req.workflow}")

    session_id = str(uuid.uuid4())

    supabase.table("francis_runs").insert({
        "id": session_id,
        "workflow_name": req.workflow,
        "params": req.params,
        "status": "CREATED",
        "started_at": datetime.now(timezone.utc).isoformat()
    }).execute()

    background_tasks.add_task(
        execute_francis, session_id, req.workflow, req.params
    )

    return {
        "session_id": session_id,
        "status": "CREATED",
        "status_url": f"/status/{session_id}"
    }
```

### Errores controlados aquí

| Caso | Respuesta |
|---|---|
| Workflow no existe | HTTP 400 |
| Body mal formado | HTTP 422 (FastAPI auto) |
| Supabase caído | HTTP 503 |

---

## 8. Paso 2 — Ejecutar Francis Suite

### Qué pasa
Un worker en background corre `francis-suite run` dentro de una carpeta única para esa sesión. Captura stdout, stderr y returncode. Impone un timeout para evitar ejecuciones colgadas.

### Código: `executor.py`

```python
import subprocess, time
from pathlib import Path
from datetime import datetime, timezone

from db import supabase
from config import settings
from errors import classify_error

def execute_francis(session_id: str, workflow: str, params: dict):
    # Marcar RUNNING
    supabase.table("francis_runs").update({
        "status": "RUNNING"
    }).eq("id", session_id).execute()

    output_dir = Path(settings.FRANCIS_RUNS_DIR) / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["francis-suite", "run", workflow]
    for k, v in params.items():
        cmd.extend(["--param", f"{k}={v}"])

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.EXECUTION_TIMEOUT_SEC,
            cwd=output_dir,
        )
        duration_ms = int((time.time() - start) * 1000)

        if result.returncode == 0:
            _handle_success(session_id, output_dir, duration_ms)
        else:
            _handle_failure(
                session_id, result.stderr, workflow, params, duration_ms
            )

    except subprocess.TimeoutExpired:
        _handle_failure(
            session_id,
            "TIMEOUT: excedido tiempo máximo de ejecución",
            workflow, params,
            int((time.time() - start) * 1000),
        )
    except Exception as e:
        _mark_fatal(session_id, f"Error inesperado: {e}")
```

### Errores controlados aquí

| Error | Tipo | Acción |
|---|---|---|
| `returncode != 0` | Depende | Clasificar con `classify_error()` |
| Timeout | RECOVERABLE | Retry con backoff |
| Excepción Python | FATAL | Marcar FAILED sin retry |

---

## 9. Paso 3 — Éxito: identificar el archivo generado

### Qué pasa
Se busca el archivo principal dentro de `runs/{session_id}/`, se cuenta sus filas y se registra en la fila del run. Luego se dispara la carga a Supabase.

### Regla de identificación del archivo principal

1. Solo extensiones de datos: `.json .csv .ndjson .xlsx .parquet`.
2. Se descartan archivos que contengan `metadata`, `log`, `debug` en el nombre.
3. De los restantes, se toma el **más grande**.
4. Si no hay ninguno → FAILED (FATAL).

### Código

```python
DATA_EXTENSIONS = {".json", ".csv", ".ndjson", ".xlsx", ".parquet"}
EXCLUDE_KEYWORDS = ("metadata", "log", "debug")

def _find_main_file(output_dir: Path) -> Path | None:
    candidates = [
        f for f in output_dir.rglob("*")
        if f.is_file()
        and f.suffix.lower() in DATA_EXTENSIONS
        and not any(kw in f.name.lower() for kw in EXCLUDE_KEYWORDS)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_size)

def _handle_success(session_id: str, output_dir: Path, duration_ms: int):
    main_file = _find_main_file(output_dir)

    if main_file is None:
        supabase.table("francis_runs").update({
            "status": "FAILED",
            "error_type": "FATAL",
            "error_message": "Workflow completó pero no generó archivos de datos",
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
        }).eq("id", session_id).execute()
        return

    row_count = _count_rows(main_file)

    supabase.table("francis_runs").update({
        "status": "COMPLETED",
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "output_path": str(main_file),
        "output_format": main_file.suffix.lstrip("."),
        "output_row_count": row_count,
        "load_status": "PENDING",
    }).eq("id", session_id).execute()

    # Disparar carga
    from loader import load_to_supabase
    load_to_supabase(session_id, main_file)
```

### Contador de filas genérico

```python
import json, csv

def _count_rows(f: Path) -> int:
    try:
        suf = f.suffix.lower()
        if suf == ".json":
            data = json.loads(f.read_text(encoding="utf-8"))
            return len(data) if isinstance(data, list) else 1
        if suf == ".csv":
            with open(f, encoding="utf-8") as fh:
                return max(0, sum(1 for _ in csv.reader(fh)) - 1)
        if suf == ".ndjson":
            return sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip())
        return -1
    except Exception:
        return -1
```

---

## 10. Paso 4 — Fallo: clasificar y reintentar

### Qué pasa
Se analiza `stderr`. Si es un error temporal (red, timeout, rate limit), se reintenta con backoff exponencial. Si es lógico (XML inválido, bug), se marca FAILED inmediatamente.

### Código: `errors.py`

```python
RECOVERABLE_PATTERNS = (
    "timeout", "timed out",
    "connection refused", "connection reset", "connection aborted",
    "temporary failure", "name resolution", "dns",
    "429", "too many requests", "rate limit",
    "502", "503", "504",
    "blocked", "try again", "retry",
)

def classify_error(stderr: str) -> str:
    s = (stderr or "").lower()
    return "RECOVERABLE" if any(p in s for p in RECOVERABLE_PATTERNS) else "FATAL"
```

### Código: política de retry con backoff

```python
import time

def _handle_failure(session_id, stderr, workflow, params, duration_ms):
    err_type = classify_error(stderr)
    msg = (stderr or "")[-1000:]

    row = supabase.table("francis_runs").select(
        "retry_count,max_retries"
    ).eq("id", session_id).single().execute().data

    retries = row["retry_count"]
    maximum = row["max_retries"]

    if err_type == "RECOVERABLE" and retries < maximum:
        supabase.table("francis_runs").update({
            "status": "RETRYING",
            "retry_count": retries + 1,
            "error_type": "RECOVERABLE",
            "error_message": msg,
        }).eq("id", session_id).execute()

        wait = 30 * (2 ** retries)  # 30s, 60s, 120s
        time.sleep(wait)
        execute_francis(session_id, workflow, params)
    else:
        supabase.table("francis_runs").update({
            "status": "FAILED",
            "error_type": err_type,
            "error_message": msg,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
        }).eq("id", session_id).execute()

def _mark_fatal(session_id: str, msg: str):
    supabase.table("francis_runs").update({
        "status": "FAILED",
        "error_type": "FATAL",
        "error_message": msg[-1000:],
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", session_id).execute()
```

### Matriz de decisión

| Situación | retry_count | Acción |
|---|---|---|
| RECOVERABLE + `retries < max` | aumenta +1 | Backoff + re-ejecutar |
| RECOVERABLE + `retries >= max` | queda igual | FAILED |
| FATAL | — | FAILED inmediato |
| Excepción inesperada | — | FAILED FATAL |

---

## 11. Paso 5 — Cargar datos a Supabase de forma segura

### Qué pasa
Se lee el archivo, se valida que tenga filas, y **solo entonces** se borra la tabla destino y se insertan los nuevos datos en lotes. Si algo falla, se marca `LOAD_FAILED` sin tocar la tabla.

### Patrón seguro: **validar → borrar → insertar**

```
Leer archivo  ✔
      │
      ▼
Validar >0 filas  ✔
      │
      ▼  (solo aquí empieza la escritura destructiva)
BEGIN transacción lógica
  DELETE destino
  INSERT por lotes
COMMIT
      │
      ▼
Marcar LOADED
```

### Código: `loader.py`

```python
import json, csv
from pathlib import Path
from db import supabase
from config import settings

BATCH_SIZE = 500

def _read_rows(filepath: Path) -> list[dict]:
    suf = filepath.suffix.lower()
    if suf == ".json":
        data = json.loads(filepath.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON debe ser un array de objetos")
        return data
    if suf == ".csv":
        with open(filepath, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if suf == ".ndjson":
        return [
            json.loads(line) for line in
            filepath.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    raise ValueError(f"Formato no soportado: {suf}")

def load_to_supabase(session_id: str, filepath: Path):
    supabase.table("francis_runs").update({
        "load_status": "LOADING"
    }).eq("id", session_id).execute()

    try:
        rows = _read_rows(filepath)
        if not rows:
            raise ValueError("Archivo sin filas")

        # Borrar tabla destino (solo después de validar)
        supabase.table(settings.TARGET_TABLE).delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        # Insertar en lotes
        inserted = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            supabase.table(settings.TARGET_TABLE).insert(batch).execute()
            inserted += len(batch)

        supabase.table("francis_runs").update({
            "load_status": "LOADED",
            "loaded_rows": inserted,
        }).eq("id", session_id).execute()

    except Exception as e:
        supabase.table("francis_runs").update({
            "load_status": "LOAD_FAILED",
            "error_message": f"Carga fallida: {str(e)[:500]}",
        }).eq("id", session_id).execute()
```

### Errores controlados aquí

| Error | Acción | Tabla destino |
|---|---|---|
| Archivo vacío | LOAD_FAILED | Intacta |
| Formato no soportado | LOAD_FAILED | Intacta |
| Falla al borrar | LOAD_FAILED | Intacta |
| Falla al insertar (mitad) | LOAD_FAILED | **Parcial** — requiere alerta |

### Mejora opcional: staging + swap

Para total seguridad en producción:

1. Insertar a `tu_tabla_staging`.
2. Validar conteo.
3. Renombrar tablas o truncar + copiar en una sola transacción SQL (`rpc` en Supabase).

---

## 12. Paso 6 — Observabilidad: endpoints y logs

### `GET /status/{session_id}`

```python
@app.get("/status/{session_id}")
async def get_status(session_id: str):
    r = supabase.table("francis_runs").select("*").eq(
        "id", session_id
    ).single().execute()
    if not r.data:
        raise HTTPException(404, "session_id no encontrado")
    return r.data
```

### `GET /runs?status=FAILED&limit=20`

```python
@app.get("/runs")
async def list_runs(status: str | None = None, limit: int = 20):
    q = supabase.table("francis_runs").select("*").order(
        "created_at", desc=True
    ).limit(limit)
    if status:
        q = q.eq("status", status)
    return q.execute().data
```

### `POST /runs/{id}/retry` — reintento manual

```python
@app.post("/runs/{session_id}/retry")
async def retry_run(session_id: str, background_tasks: BackgroundTasks):
    r = supabase.table("francis_runs").select("*").eq(
        "id", session_id
    ).single().execute().data
    if not r:
        raise HTTPException(404)
    if r["status"] not in ("FAILED",):
        raise HTTPException(400, "Solo se pueden reintentar runs FAILED")

    supabase.table("francis_runs").update({
        "status": "RETRYING",
        "retry_count": 0,
        "error_message": None,
    }).eq("id", session_id).execute()

    background_tasks.add_task(
        execute_francis, session_id, r["workflow_name"], r["params"]
    )
    return {"ok": True}
```

### `GET /health`

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 13. Paso 7 — Despliegue en la nube

### `requirements.txt`

```
fastapi>=0.111
uvicorn[standard]>=0.30
supabase>=2.5
python-dotenv>=1.0
pydantic>=2.7
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema (ej: para playwright en el futuro)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Francis Suite (instalar como paquete local)
COPY francis_suite/ /src/francis_suite/
COPY pyproject.toml /src/
RUN pip install /src

# Código del operador
COPY api.py executor.py loader.py errors.py db.py config.py ./
COPY workflows/ ./workflows/

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Railway en 5 pasos

1. `git push` del proyecto a GitHub.
2. Nuevo proyecto en Railway → "Deploy from repo".
3. Railway detecta el `Dockerfile` automáticamente.
4. Agregas variables de entorno: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TARGET_TABLE`.
5. Railway genera URL pública: `https://francis-operator.up.railway.app`.

### Prueba de humo

```bash
# 1. Disparar
curl -X POST https://francis-operator.up.railway.app/run \
  -H "Content-Type: application/json" \
  -d '{"workflow":"workflows/topPropiedades.xml","params":{"paginas":"5"}}'

# 2. Consultar
curl https://francis-operator.up.railway.app/status/<session_id>
```

---

## 14. Ideas de vanguardia (roadmap)

Ideas modernas que pueden llevar a `Francis Suite` al siguiente nivel. No son necesarias para la v1, pero vale la pena tenerlas mapeadas.

### 14.1. Event streaming en vivo con Server-Sent Events

Exponer `GET /stream/{session_id}` usando SSE para que un frontend vea en tiempo real qué `hand` se está ejecutando. El `EventBus` interno de Francis Suite se conecta a un generador async.

```python
@app.get("/stream/{session_id}")
async def stream(session_id: str):
    async def event_gen():
        # suscribirse al EventBus interno o a cambios en francis_runs
        ...
    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

### 14.2. Workflows versionados con hash

Cada `workflow.xml` se guarda en un bucket de Supabase Storage con hash SHA-256. El run registra `workflow_hash` para trazabilidad total: siempre sabes qué versión exacta del workflow corrió.

### 14.3. Extensión de navegador → Playwright hand

Una extensión Chrome captura clicks/selectores del usuario en una página y genera automáticamente un `workflow.xml` con hands Playwright. Convierte "escrapear algo" en un gesto de 30 segundos.

### 14.4. Diff inteligente en lugar de refresh total

En vez de borrar toda la tabla, comparar por clave primaria:

- Filas nuevas → INSERT
- Filas cambiadas → UPDATE
- Filas ausentes → DELETE (opcional, soft-delete)

Menos tráfico, menos riesgo, historial posible.

### 14.5. Integración n8n como orquestador externo

`n8n` no ejecuta `Francis Suite`, lo **orquesta**:

```
Cron n8n  →  POST /run a Francis Operator  →  poll /status
         →  si COMPLETED + LOADED  →  notificar Slack / enviar email
         →  si FAILED  →  abrir issue en GitHub / alertar
```

### 14.6. Scheduler propio de workflows

Tabla `francis_schedules`:

```sql
CREATE TABLE francis_schedules (
  id UUID PRIMARY KEY,
  workflow_name TEXT,
  cron_expr TEXT,         -- ej "0 */6 * * *"
  params JSONB,
  enabled BOOLEAN,
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ
);
```

Un worker que revisa cada minuto y dispara `POST /run` cuando toca.

### 14.7. Observabilidad con OpenTelemetry

Instrumentar FastAPI + subprocess con OTel. Exportar a Grafana Cloud (free tier). Ves latencias, p95, errores por workflow, duración por hand.

### 14.8. Quotas y rate limiting por workflow

Límite de X runs/hora por workflow. Evita golpear sitios externos y respeta robots.txt. Config declarativa:

```xml
<workflow name="topPropiedades" rate-limit="10/hour">
```

### 14.9. Dead letter queue

Runs que fallan FATAL van a una cola `francis_dlq` para revisión humana. Endpoint `POST /dlq/{id}/replay` para reintentar después de corregir.

### 14.10. Hands LLM: extracción semántica

Nuevo hand `<llm-extract>` que usa un LLM para extraer campos estructurados de HTML/texto según un schema JSON. Ideal cuando los selectores CSS cambian todo el tiempo.

```xml
<llm-extract model="gpt-4o-mini" schema="propiedad.schema.json">
  <box name="html"/>
</llm-extract>
```

### 14.11. Replays determinísticos

Guardar los responses HTTP crudos por run (compressed). Permite **re-correr un workflow offline** para debuggear sin volver a golpear sitios. Útil para tests de regresión.

### 14.12. Multi-tenant

Agregar `tenant_id` a `francis_runs`. Distintos clientes, mismos workflows, datos separados. Listo para producto.

---

## 15. Checklist de implementación

### Fase 1 — MVP operativo (1-2 semanas)

- [ ] Crear tabla `francis_runs` en Supabase
- [ ] Crear `.env` con credenciales
- [ ] Implementar `api.py` con `POST /run` y `GET /status`
- [ ] Implementar `executor.py` con subprocess + timeout
- [ ] Implementar detección de archivo principal
- [ ] Implementar clasificación de errores + retry con backoff
- [ ] Implementar `loader.py` con validar→borrar→insertar
- [ ] Probar local con `uvicorn api:app --reload`
- [ ] Dockerizar
- [ ] Deploy en Railway
- [ ] Prueba de humo extremo a extremo

### Fase 2 — Robustez (siguiente sprint)

- [ ] Endpoint `GET /runs` con filtros
- [ ] Endpoint `POST /runs/{id}/retry` manual
- [ ] Staging table + swap en Supabase
- [ ] Logs estructurados JSON
- [ ] Alertas básicas (webhook Slack en FAILED)

### Fase 3 — Vanguardia (roadmap)

- [ ] Scheduler de workflows
- [ ] Stream SSE en vivo
- [ ] Diff inteligente (upsert)
- [ ] Hands LLM
- [ ] OpenTelemetry
- [ ] Extensión de navegador

---

## 16. Qué poner en el CV cuando esté listo

Solo después de que **lo anterior corra en Railway**, puedes escribir con honestidad:

> **Francis Suite** — Framework de extracción y procesamiento de datos basado en workflows XML declarativos.
> Diseñé e implementé una capa operativa con **FastAPI** que expone ejecución y estado vía REST, con **reintentos clasificados por tipo de error**, **persistencia de estado en Supabase** y **refresh seguro de tablas destino** validando output antes de escribir. Desplegado en **Docker + Railway**.
> Stack: Python, FastAPI, Supabase, Docker, Railway, lxml, httpx.

Cuando sumes Playwright hands, n8n orquestador o LLM hands, actualizas la línea.

**Regla de oro**: solo va al CV lo que corre en producción. Lo demás vive en el roadmap.

---

> Documento vivo. Actualízalo cada vez que implementes una fase. Esta es la fuente de verdad operativa de `Francis Suite`.
