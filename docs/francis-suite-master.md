# Francis Suite — Documento Maestro

> **Documento único, oficial y definitivo. Contiene todo lo necesario para entender, construir, operar, desplegar, evolucionar y presentar profesionalmente `Francis Suite`. No requiere leer ningún otro documento.**

---

## Tabla de contenidos

- [Francis Suite — Documento Maestro](#francis-suite--documento-maestro)
  - [Tabla de contenidos](#tabla-de-contenidos)
  - [Parte I — Fundamentos](#parte-i--fundamentos)
    - [1. Qué es Francis Suite](#1-qué-es-francis-suite)
    - [2. Problema que resuelve](#2-problema-que-resuelve)
    - [3. Conceptos del núcleo](#3-conceptos-del-núcleo)
    - [4. Estado actual vs roadmap](#4-estado-actual-vs-roadmap)
  - [Parte II — Arquitectura](#parte-ii--arquitectura)
    - [5. Principios rectores](#5-principios-rectores)
    - [6. Arquitectura hexagonal](#6-arquitectura-hexagonal)
    - [7. Los 6 puertos del sistema](#7-los-6-puertos-del-sistema)
    - [8. Interfaces (contratos de código)](#8-interfaces-contratos-de-código)
    - [9. El núcleo puro sin dependencias](#9-el-núcleo-puro-sin-dependencias)
    - [10. Configuración declarativa del stack](#10-configuración-declarativa-del-stack)
    - [11. Bootstrap e inyección de dependencias](#11-bootstrap-e-inyección-de-dependencias)
  - [Parte III — Operación](#parte-iii--operación)
    - [12. Flujo operativo extremo a extremo](#12-flujo-operativo-extremo-a-extremo)
    - [13. Modelo de datos: tabla de estado](#13-modelo-de-datos-tabla-de-estado)
    - [14. Paso 1 — Trigger (disparar ejecución)](#14-paso-1--trigger-disparar-ejecución)
    - [15. Paso 2 — Ejecutar Francis Suite](#15-paso-2--ejecutar-francis-suite)
    - [16. Paso 3 — Éxito: identificar archivo](#16-paso-3--éxito-identificar-archivo)
    - [17. Paso 4 — Fallo: clasificar y reintentar](#17-paso-4--fallo-clasificar-y-reintentar)
    - [18. Paso 5 — Cargar datos de forma segura](#18-paso-5--cargar-datos-de-forma-segura)
    - [19. Paso 6 — Observabilidad](#19-paso-6--observabilidad)
  - [Parte IV — Despliegue](#parte-iv--despliegue)
    - [20. Estructura del proyecto](#20-estructura-del-proyecto)
    - [21. Docker y contenedorización](#21-docker-y-contenedorización)
    - [22. Despliegue en la nube](#22-despliegue-en-la-nube)
    - [23. Stack por defecto y alternativas](#23-stack-por-defecto-y-alternativas)
  - [Parte V — Portabilidad](#parte-v--portabilidad)
    - [24. Cómo cambiar de tecnología sin romper nada](#24-cómo-cambiar-de-tecnología-sin-romper-nada)
    - [25. Tests como garantía de portabilidad](#25-tests-como-garantía-de-portabilidad)
    - [26. Anti-patrones prohibidos](#26-anti-patrones-prohibidos)
  - [Parte VI — Evolución](#parte-vi--evolución)
    - [27. Roadmap por fases](#27-roadmap-por-fases)
    - [28. Ideas de vanguardia](#28-ideas-de-vanguardia)
  - [Parte VII — Presentación profesional](#parte-vii--presentación-profesional)
    - [29. Cómo presentar Francis Suite en un CV](#29-cómo-presentar-francis-suite-en-un-cv)
    - [30. Regla de honestidad técnica](#30-regla-de-honestidad-técnica)
  - [Parte VIII — Checklists](#parte-viii--checklists)
    - [31. Checklist de implementación](#31-checklist-de-implementación)
    - [32. Checklist de portabilidad](#32-checklist-de-portabilidad)
  - [Glosario](#glosario)

---

# Parte I — Fundamentos

## 1. Qué es Francis Suite

`Francis Suite` es un **framework universal de extracción y procesamiento de datos**, **low-code**, **declarativo** y **extensible**.

Los workflows se definen en **XML**. El runtime los ejecuta como **árboles de hands** (unidades de trabajo). Cada ejecución guarda resultados en **boxes** (unidades de dato), produce **records** (datasets estructurados con schema) y puede exportarlos en múltiples formatos: JSON, CSV, NDJSON, XML, HTML, TXT, Excel, Parquet.

En una frase: **Francis Suite convierte un archivo XML declarativo en datos procesados listos para consumir.**

## 2. Problema que resuelve

- Automatizar extracciones web y de APIs sin escribir scripts frágiles para cada caso.
- Procesar, transformar y persistir datos con una sintaxis uniforme.
- Operar flujos complejos (requests, parsing, regex, transformación, guardado) desde un solo documento.
- Producir outputs estandarizados y reutilizables en múltiples formatos.
- Ser un sustrato **reusable** en cualquier contexto (scraping, ETL ligero, recolección de datos internos).

## 3. Conceptos del núcleo

| Concepto | Qué es |
|---|---|
| **Workflow XML** | Declaración de qué hacer, en forma de árbol |
| **FParser** | Parsea el XML a un árbol de `FNode` |
| **FNode** | Nodo del árbol, bridge universal desde el XML |
| **Hand** | Unidad de ejecución registrada con `@hand(tag="...")` |
| **FRuntime** | Ejecuta hands recorriendo el árbol |
| **FContext** | Contexto de ejecución + `boxes` (dato) |
| **Box** | Contenedor de dato accesible por nombre |
| **FVariable** | Tipo base: `FNodeVariable`, `FListVariable`, `FEmptyVariable` |
| **FRecord** | Dataset estructurado con schema + metadata + persistencia |
| **FSession** | Contenedor de ejecución con UUID y `status` |
| **EventBus** | Canal de eventos entre sesión y hands |

**Filosofía**: *todo se guarda en boxes*.

### Estados de sesión

`CREATED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`.

### Pipeline conceptual

```
workflow.xml → FParser → FNodes → FRuntime → Hand.execute() → FVariable
                                                                    ↓
                                                             FContext (boxes)
                                                                    ↓
                                                                 EventBus
```

## 4. Estado actual vs roadmap

### Ya implementado
- Core: FParser, FRuntime, FContext, EventBus
- Hands: variables, HTTP, parsing, convert, regex, text, flow control, functions, files, records
- Record-save multi-formato: json, csv, ndjson, xml, html, txt, xlsx, parquet
- CLI: `francis-suite run`, `francis-suite schema`

### Roadmap
- API REST (FastAPI): `POST /run`, `GET /status/:id`
- Hands Playwright (browser automation)
- Cloud storage de artefactos
- Liveness/limits: `session-deadline-ms`, `silence-limit-ms`, `session-max-rss-mb`
- Scheduler interno
- Extensión de navegador → generación de workflows
- Hands LLM para extracción semántica

---

# Parte II — Arquitectura

## 5. Principios rectores

- **Depender de abstracciones, no de implementaciones.** El núcleo nunca importa Supabase, FastAPI, boto3 ni ningún SDK de infraestructura.
- **Inversión de dependencias.** Los detalles dependen del core; el core no conoce los detalles.
- **Interfaces pequeñas y estables.** Preferir 5 interfaces de 3 métodos sobre 1 de 15.
- **Adapters reemplazables en un archivo.** Cambiar de Supabase a Postgres = un archivo nuevo + config.
- **Configuración externa.** Qué adapter se usa se decide en `.env` / `config.yaml`, jamás en el código.
- **Tests con fakes.** Cada interfaz tiene un fake en memoria. El core se testea sin infra real.
- **Formato neutro en la frontera.** Nada de tipos de Supabase/FastAPI/boto3 cruzando el core.
- **Idempotencia.** Un mismo run debe poder repetirse sin corromper datos.
- **Atomicidad práctica.** Nunca borrar la tabla destino antes de validar el nuevo output.
- **Observabilidad por defecto.** Cada paso deja rastro persistente.

## 6. Arquitectura hexagonal

```
                    ┌─────────────────────────────────┐
                    │       NÚCLEO (domain)           │
                    │                                 │
  ┌─────────┐       │  - Run                          │       ┌──────────────┐
  │  HTTP   │──────▶│  - ExecutionPolicy              │──────▶│ RunRepository│
  │ Adapter │       │  - RetryPolicy                  │       │  (Supabase / │
  └─────────┘       │  - OutputValidator              │       │   Postgres / │
                    │  - LoadOrchestrator             │       │   SQLite)    │
  ┌─────────┐       │  - RunService                   │       └──────────────┘
  │  CLI    │──────▶│                                 │──────▶┌──────────────┐
  │ Adapter │       │  NO IMPORTA fastapi, supabase,  │       │ DataSink     │
  └─────────┘       │  boto3, redis, nada.            │       │ (Supabase /  │
                    │                                 │       │  S3 / Mongo /│
  ┌─────────┐       │  Solo usa puertos (interfaces). │       │  Postgres)   │
  │  Cron   │──────▶│                                 │──────▶└──────────────┘
  │ Adapter │       │                                 │
  └─────────┘       └─────────────────────────────────┘       ┌──────────────┐
                            │                                 │ Executor     │
                            └────────────────────────────────▶│ (subprocess /│
                                                              │  docker /    │
                                                              │  k8s job)    │
                                                              └──────────────┘
```

**Izquierda**: quién invoca al core (driving adapters).
**Centro**: dominio puro, sin dependencias de frameworks.
**Derecha**: a qué infraestructura accede el core (driven adapters).

## 7. Los 6 puertos del sistema

Cualquier tecnología concreta implementa uno de estos 6 puertos.

| # | Puerto | Responsabilidad | Ejemplos de adapters |
|---|---|---|---|
| 1 | **RunRepository** | Persistir estado de cada run | Supabase, Postgres, SQLite, DynamoDB, Firestore, JSON file, in-memory |
| 2 | **DataSink** | Cargar datos finales al destino | Supabase table, Postgres, S3, MongoDB, BigQuery, MySQL |
| 3 | **Executor** | Ejecutar un workflow | subprocess local, Docker, Kubernetes Job, AWS Batch, Cloud Run |
| 4 | **ArtifactStore** | Guardar archivos generados | Filesystem local, S3, Azure Blob, GCS, MinIO |
| 5 | **Trigger** | Disparar ejecuciones | HTTP REST, CLI, cron, Kafka, RabbitMQ, SQS, webhook |
| 6 | **Notifier** | Comunicar estado hacia fuera | Slack, Email, webhook, Discord, Teams, SSE, log |

## 8. Interfaces (contratos de código)

Todas viven en `francis_operator/ports/`.

### 8.1. `RunRepository`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Run:
    id: str
    workflow_name: str
    params: dict
    status: str                   # CREATED | RUNNING | COMPLETED | FAILED | RETRYING
    retry_count: int = 0
    max_retries: int = 3
    error_type: Optional[str] = None        # RECOVERABLE | FATAL
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    output_format: Optional[str] = None
    output_row_count: Optional[int] = None
    load_status: str = "PENDING"            # PENDING | LOADING | LOADED | LOAD_FAILED
    loaded_rows: Optional[int] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class RunRepository(ABC):
    @abstractmethod
    def create(self, run: Run) -> None: ...
    @abstractmethod
    def get(self, run_id: str) -> Optional[Run]: ...
    @abstractmethod
    def update(self, run_id: str, **fields) -> None: ...
    @abstractmethod
    def list(self, status: Optional[str] = None, limit: int = 50) -> list[Run]: ...
```

### 8.2. `DataSink`

```python
from abc import ABC, abstractmethod
from typing import Iterable

class DataSink(ABC):
    @abstractmethod
    def replace_all(self, target: str, rows: Iterable[dict]) -> int: ...
    @abstractmethod
    def upsert(self, target: str, rows: Iterable[dict], key: str) -> int: ...
    @abstractmethod
    def count(self, target: str) -> int: ...
```

### 8.3. `Executor`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    output_dir: Path

class Executor(ABC):
    @abstractmethod
    def run(self, workflow: str, params: dict,
            output_dir: Path, timeout_sec: int) -> ExecutionResult: ...
```

### 8.4. `ArtifactStore`

```python
from abc import ABC, abstractmethod
from pathlib import Path

class ArtifactStore(ABC):
    @abstractmethod
    def put(self, local_path: Path, remote_key: str) -> str: ...
    @abstractmethod
    def get(self, remote_key: str, local_path: Path) -> None: ...
    @abstractmethod
    def exists(self, remote_key: str) -> bool: ...
```

### 8.5. `Trigger`

```python
from abc import ABC, abstractmethod
from typing import Callable

class Trigger(ABC):
    @abstractmethod
    def start(self, on_run: Callable[[str, dict], str]) -> None: ...
```

### 8.6. `Notifier`

```python
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def notify(self, event: str, payload: dict) -> None: ...
    # event: "run.completed" | "run.failed" | "load.failed" | ...
```

## 9. El núcleo puro sin dependencias

El `core/` nunca cambia aunque cambie toda la infraestructura.

```
francis_operator/core/
├── models.py              # Run, ExecutionResult (dataclasses)
├── retry_policy.py        # Clasificación de errores + backoff
├── output_validator.py    # Reglas para identificar archivo principal
├── load_orchestrator.py   # validar → borrar → insertar
└── run_service.py         # Orquesta todo usando los puertos
```

### `RunService` completo (el corazón del sistema)

```python
# francis_operator/core/run_service.py
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

from francis_operator.ports.run_repository import RunRepository, Run
from francis_operator.ports.executor import Executor
from francis_operator.ports.data_sink import DataSink
from francis_operator.ports.notifier import Notifier
from francis_operator.core.retry_policy import RetryPolicy
from francis_operator.core.output_validator import find_main_output, read_rows

class RunService:
    def __init__(self, repo: RunRepository, executor: Executor,
                 sink: DataSink, notifier: Notifier, retry: RetryPolicy,
                 target_table: str, runs_dir: Path):
        self.repo = repo
        self.executor = executor
        self.sink = sink
        self.notifier = notifier
        self.retry = retry
        self.target_table = target_table
        self.runs_dir = runs_dir

    def start_run(self, workflow: str, params: dict) -> str:
        run = Run(
            id=str(uuid4()),
            workflow_name=workflow,
            params=params,
            status="CREATED",
            started_at=datetime.now(timezone.utc),
        )
        self.repo.create(run)
        return run.id

    def execute(self, run_id: str) -> None:
        run = self.repo.get(run_id)
        if not run:
            return
        self.repo.update(run_id, status="RUNNING")

        output_dir = self.runs_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        result = self.executor.run(
            run.workflow_name, run.params,
            output_dir=output_dir, timeout_sec=600,
        )

        if result.success:
            self._handle_success(run, result)
        else:
            self._handle_failure(run, result)

    def _handle_success(self, run: Run, result) -> None:
        main_file = find_main_output(result.output_dir)
        if main_file is None:
            self._mark_failed(run.id, "FATAL", "Sin archivos de datos", result.duration_ms)
            self.notifier.notify("run.failed", {"id": run.id})
            return

        rows = list(read_rows(main_file))
        if not rows:
            self._mark_failed(run.id, "FATAL", "Archivo vacío", result.duration_ms)
            return

        self.repo.update(run.id,
            status="COMPLETED",
            ended_at=datetime.now(timezone.utc),
            duration_ms=result.duration_ms,
            output_path=str(main_file),
            output_format=main_file.suffix.lstrip("."),
            output_row_count=len(rows),
            load_status="LOADING",
        )

        try:
            inserted = self.sink.replace_all(self.target_table, rows)
            self.repo.update(run.id, load_status="LOADED", loaded_rows=inserted)
            self.notifier.notify("run.completed",
                                 {"id": run.id, "rows": inserted})
        except Exception as e:
            self.repo.update(run.id, load_status="LOAD_FAILED",
                             error_message=f"Carga fallida: {str(e)[:500]}")
            self.notifier.notify("load.failed", {"id": run.id})

    def _handle_failure(self, run: Run, result) -> None:
        decision = self.retry.decide(result.stderr, run.retry_count, run.max_retries)
        if decision.should_retry:
            self.repo.update(run.id, status="RETRYING",
                             retry_count=run.retry_count + 1,
                             error_type=decision.error_type,
                             error_message=result.stderr[-500:])
            decision.wait()
            self.execute(run.id)
        else:
            self._mark_failed(run.id, decision.error_type,
                              result.stderr[-1000:], result.duration_ms)
            self.notifier.notify("run.failed", {"id": run.id})

    def _mark_failed(self, run_id: str, error_type: str,
                     message: str, duration_ms: int) -> None:
        self.repo.update(run_id,
            status="FAILED", error_type=error_type,
            error_message=message, duration_ms=duration_ms,
            ended_at=datetime.now(timezone.utc),
        )
```

**Observa**: ni un solo `import supabase`, `import fastapi`, `import boto3`. Portable a cualquier stack.

### `RetryPolicy` y `OutputValidator`

```python
# francis_operator/core/retry_policy.py
import time
from dataclasses import dataclass

RECOVERABLE_PATTERNS = (
    "timeout", "timed out",
    "connection refused", "connection reset", "connection aborted",
    "temporary failure", "name resolution", "dns",
    "429", "too many requests", "rate limit",
    "502", "503", "504",
    "blocked", "try again", "retry",
)

@dataclass
class RetryDecision:
    should_retry: bool
    error_type: str          # RECOVERABLE | FATAL
    wait_seconds: int = 0
    def wait(self):
        if self.wait_seconds > 0:
            time.sleep(self.wait_seconds)

class RetryPolicy:
    def __init__(self, max_retries=3, base_sec=30, factor=2):
        self.max_retries = max_retries
        self.base_sec = base_sec
        self.factor = factor

    def _classify(self, stderr: str) -> str:
        s = (stderr or "").lower()
        return "RECOVERABLE" if any(p in s for p in RECOVERABLE_PATTERNS) else "FATAL"

    def decide(self, stderr: str, retries: int, maximum: int) -> RetryDecision:
        err = self._classify(stderr)
        if err == "RECOVERABLE" and retries < maximum:
            return RetryDecision(True, err, self.base_sec * (self.factor ** retries))
        return RetryDecision(False, err)
```

```python
# francis_operator/core/output_validator.py
import json, csv
from pathlib import Path
from typing import Iterable

DATA_EXTENSIONS = {".json", ".csv", ".ndjson", ".xlsx", ".parquet"}
EXCLUDE_KEYWORDS = ("metadata", "log", "debug")

def find_main_output(output_dir: Path) -> Path | None:
    candidates = [
        f for f in output_dir.rglob("*")
        if f.is_file()
        and f.suffix.lower() in DATA_EXTENSIONS
        and not any(kw in f.name.lower() for kw in EXCLUDE_KEYWORDS)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_size)

def read_rows(filepath: Path) -> Iterable[dict]:
    suf = filepath.suffix.lower()
    if suf == ".json":
        data = json.loads(filepath.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON debe ser array de objetos")
        return data
    if suf == ".csv":
        with open(filepath, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if suf == ".ndjson":
        return [json.loads(ln) for ln in
                filepath.read_text(encoding="utf-8").splitlines() if ln.strip()]
    raise ValueError(f"Formato no soportado: {suf}")
```

## 10. Configuración declarativa del stack

Qué-usar-para-qué se define en YAML, no en código.

```yaml
# config.yaml
run_repository:
  driver: supabase         # supabase | postgres | sqlite | dynamodb | mongo | memory
  options:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_KEY}
    table: francis_runs

data_sink:
  driver: supabase         # supabase | postgres | s3_parquet | bigquery | mongo
  options:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_KEY}
  target: tu_tabla_de_datos

executor:
  driver: subprocess        # subprocess | docker | k8s | cloudrun | aws_batch
  options:
    timeout_sec: 600
    runs_dir: ./runs

artifact_store:
  driver: filesystem        # filesystem | s3 | gcs | azure
  options:
    root: ./runs

trigger:
  driver: http_fastapi      # http_fastapi | cli | cron | kafka | sqs
  options:
    host: 0.0.0.0
    port: 8000

notifier:
  driver: log               # log | slack | webhook | email
  options: {}

retry:
  max_retries: 3
  backoff_base_sec: 30
  backoff_factor: 2
```

Migrar a Postgres + AWS Batch: solo editas este YAML.

## 11. Bootstrap e inyección de dependencias

Un único archivo construye el sistema según la config.

```python
# francis_operator/bootstrap.py
import yaml, os
from francis_operator.core.run_service import RunService
from francis_operator.core.retry_policy import RetryPolicy

from francis_operator.adapters.repo import supabase_repo, postgres_repo, sqlite_repo, memory_repo
from francis_operator.adapters.sink import supabase_sink, postgres_sink, s3_parquet_sink
from francis_operator.adapters.executor import subprocess_executor, docker_executor
from francis_operator.adapters.notifier import log_notifier, slack_notifier

REPO_DRIVERS = {
    "supabase": supabase_repo.SupabaseRunRepository,
    "postgres": postgres_repo.PostgresRunRepository,
    "sqlite":   sqlite_repo.SqliteRunRepository,
    "memory":   memory_repo.InMemoryRunRepository,
}
SINK_DRIVERS = {
    "supabase":   supabase_sink.SupabaseDataSink,
    "postgres":   postgres_sink.PostgresDataSink,
    "s3_parquet": s3_parquet_sink.S3ParquetSink,
}
EXECUTOR_DRIVERS = {
    "subprocess": subprocess_executor.SubprocessExecutor,
    "docker":     docker_executor.DockerExecutor,
}
NOTIFIER_DRIVERS = {
    "log":   log_notifier.LogNotifier,
    "slack": slack_notifier.SlackNotifier,
}

def build_from_config(path: str = "config.yaml") -> RunService:
    cfg = yaml.safe_load(os.path.expandvars(open(path).read()))

    repo     = REPO_DRIVERS[cfg["run_repository"]["driver"]](**cfg["run_repository"]["options"])
    sink     = SINK_DRIVERS[cfg["data_sink"]["driver"]](**cfg["data_sink"]["options"])
    executor = EXECUTOR_DRIVERS[cfg["executor"]["driver"]](**cfg["executor"]["options"])
    notifier = NOTIFIER_DRIVERS[cfg["notifier"]["driver"]](**cfg["notifier"]["options"])

    retry = RetryPolicy(
        max_retries=cfg["retry"]["max_retries"],
        base_sec=cfg["retry"]["backoff_base_sec"],
        factor=cfg["retry"]["backoff_factor"],
    )

    from pathlib import Path
    return RunService(
        repo=repo, executor=executor, sink=sink, notifier=notifier,
        retry=retry,
        target_table=cfg["data_sink"]["target"],
        runs_dir=Path(cfg["executor"]["options"]["runs_dir"]),
    )
```

---

# Parte III — Operación

## 12. Flujo operativo extremo a extremo

```
1. TRIGGER
   POST /run  →  session_id + CREATED

2. EJECUCIÓN
   Executor.run(workflow, params)  →  RUNNING

3. RESULTADO
   ├── ÉXITO
   │   ├── find_main_output()
   │   ├── read_rows()
   │   ├── repo.update(COMPLETED)
   │   └── sink.replace_all() → LOADED
   │
   └── FALLO
       ├── RetryPolicy.decide(stderr)
       ├── RECOVERABLE + intentos → RETRYING + backoff + re-ejecutar
       └── FATAL / sin intentos → FAILED

4. NOTIFICACIÓN
   notifier.notify(event, payload)

5. CONSULTA
   GET /status/{id}  →  estado completo
```

## 13. Modelo de datos: tabla de estado

Independiente del motor concreto. Ejemplo en Postgres/Supabase:

```sql
CREATE TABLE francis_runs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_name    TEXT NOT NULL,
  params           JSONB DEFAULT '{}'::jsonb,
  status           TEXT NOT NULL DEFAULT 'CREATED',
  started_at       TIMESTAMPTZ DEFAULT NOW(),
  ended_at         TIMESTAMPTZ,
  duration_ms      INTEGER,
  retry_count      INTEGER DEFAULT 0,
  max_retries      INTEGER DEFAULT 3,
  error_type       TEXT,
  error_message    TEXT,
  output_path      TEXT,
  output_format    TEXT,
  output_row_count INTEGER,
  load_status      TEXT DEFAULT 'PENDING',
  loaded_rows      INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_runs_status   ON francis_runs(status);
CREATE INDEX idx_runs_workflow ON francis_runs(workflow_name);
CREATE INDEX idx_runs_created  ON francis_runs(created_at DESC);
```

Equivalente en SQLite (para on-premise o dev local):

```sql
CREATE TABLE francis_runs (
  id               TEXT PRIMARY KEY,
  workflow_name    TEXT NOT NULL,
  params           TEXT DEFAULT '{}',
  status           TEXT NOT NULL DEFAULT 'CREATED',
  started_at       TEXT, ended_at TEXT, duration_ms INTEGER,
  retry_count      INTEGER DEFAULT 0, max_retries INTEGER DEFAULT 3,
  error_type       TEXT, error_message TEXT,
  output_path      TEXT, output_format TEXT, output_row_count INTEGER,
  load_status      TEXT DEFAULT 'PENDING', loaded_rows INTEGER,
  created_at       TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 14. Paso 1 — Trigger (disparar ejecución)

Adapter HTTP con FastAPI (intercambiable por CLI, Cron, Kafka).

```python
# francis_operator/adapters/trigger/http_fastapi_trigger.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from pathlib import Path

class RunRequest(BaseModel):
    workflow: str
    params: dict = {}

def build_app(service):
    app = FastAPI(title="Francis Operator")

    @app.post("/run")
    async def run(req: RunRequest, bg: BackgroundTasks):
        if not Path(req.workflow).exists():
            raise HTTPException(400, f"Workflow no encontrado: {req.workflow}")
        session_id = service.start_run(req.workflow, req.params)
        bg.add_task(service.execute, session_id)
        return {"session_id": session_id, "status": "CREATED"}

    @app.get("/status/{sid}")
    async def status(sid: str):
        run = service.repo.get(sid)
        if not run:
            raise HTTPException(404, "session_id no encontrado")
        return run.__dict__

    @app.get("/runs")
    async def list_runs(status: str | None = None, limit: int = 50):
        return [r.__dict__ for r in service.repo.list(status=status, limit=limit)]

    @app.post("/runs/{sid}/retry")
    async def retry(sid: str, bg: BackgroundTasks):
        run = service.repo.get(sid)
        if not run: raise HTTPException(404)
        if run.status != "FAILED":
            raise HTTPException(400, "Solo se reintentan runs FAILED")
        service.repo.update(sid, status="RETRYING", retry_count=0, error_message=None)
        bg.add_task(service.execute, sid)
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

## 15. Paso 2 — Ejecutar Francis Suite

Adapter `subprocess` por defecto (local o dentro de contenedor).

```python
# francis_operator/adapters/executor/subprocess_executor.py
import subprocess, time
from pathlib import Path
from francis_operator.ports.executor import Executor, ExecutionResult

class SubprocessExecutor(Executor):
    def __init__(self, timeout_sec: int = 600, runs_dir: str = "./runs"):
        self.timeout_sec = timeout_sec

    def run(self, workflow, params, output_dir: Path, timeout_sec: int):
        cmd = ["francis-suite", "run", workflow]
        for k, v in params.items():
            cmd.extend(["--param", f"{k}={v}"])

        start = time.time()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout_sec, cwd=output_dir)
            return ExecutionResult(
                success=(r.returncode == 0),
                exit_code=r.returncode,
                stdout=r.stdout, stderr=r.stderr,
                duration_ms=int((time.time() - start) * 1000),
                output_dir=output_dir,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False, exit_code=-1, stdout="",
                stderr="TIMEOUT: excedido tiempo máximo",
                duration_ms=int((time.time() - start) * 1000),
                output_dir=output_dir,
            )
```

## 16. Paso 3 — Éxito: identificar archivo

Ya implementado en `core/output_validator.py` (sección 9). Reglas:

1. Solo extensiones de datos: `.json .csv .ndjson .xlsx .parquet`.
2. Se descartan archivos con `metadata`, `log`, `debug` en el nombre.
3. De los restantes, se toma el **más grande**.
4. Si no hay ninguno → FAILED (FATAL).

## 17. Paso 4 — Fallo: clasificar y reintentar

Ya implementado en `core/retry_policy.py` (sección 9). Matriz de decisión:

| Situación | Acción |
|---|---|
| RECOVERABLE + `retries < max` | RETRYING, backoff exponencial, re-ejecutar |
| RECOVERABLE + `retries >= max` | FAILED |
| FATAL | FAILED inmediato |
| Excepción inesperada | FAILED (FATAL) |

Backoff por defecto: **30s, 60s, 120s**.

### Clasificación de errores

**RECOVERABLE** (transitorios, tiene sentido reintentar):
- `timeout`, `timed out`
- `connection refused / reset / aborted`
- `DNS`, `name resolution`, `temporary failure`
- HTTP 429, 502, 503, 504
- `rate limit`, `blocked`, `try again`

**FATAL** (de lógica/configuración, reintentar no ayuda):
- XML mal formado
- Hand inexistente
- Schema inválido
- Ruta de archivo inválida
- Bug en el código

## 18. Paso 5 — Cargar datos de forma segura

Principio: **validar → borrar → insertar**. La tabla destino nunca queda vacía por error.

```
Leer archivo  ✔
      │
      ▼
Validar >0 filas  ✔
      │
      ▼  (solo aquí empieza la escritura destructiva)
DELETE destino
INSERT por lotes
      │
      ▼
Marcar LOADED
```

Ejemplo de adapter Supabase para `DataSink`:

```python
# francis_operator/adapters/sink/supabase_sink.py
from supabase import create_client
from francis_operator.ports.data_sink import DataSink

class SupabaseDataSink(DataSink):
    def __init__(self, url: str, key: str, batch_size: int = 500):
        self.client = create_client(url, key)
        self.batch_size = batch_size

    def replace_all(self, target: str, rows) -> int:
        rows = list(rows)
        if not rows:
            raise ValueError("0 filas; abortando para no vaciar la tabla")

        self.client.table(target).delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        inserted = 0
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]
            self.client.table(target).insert(batch).execute()
            inserted += len(batch)
        return inserted

    def upsert(self, target: str, rows, key: str) -> int:
        rows = list(rows)
        if not rows: return 0
        total = 0
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]
            self.client.table(target).upsert(batch, on_conflict=key).execute()
            total += len(batch)
        return total

    def count(self, target: str) -> int:
        r = self.client.table(target).select("*", count="exact").limit(1).execute()
        return r.count or 0
```

### Mejora opcional: staging + swap

Para máxima seguridad en producción:

1. Insertar en `tu_tabla_staging`.
2. Validar conteo/formato.
3. Swap atómico por RPC (`BEGIN; TRUNCATE prod; INSERT INTO prod SELECT * FROM staging; COMMIT;`).

## 19. Paso 6 — Observabilidad

### Endpoints mínimos
- `POST /run` — disparar
- `GET /status/{id}` — consultar un run
- `GET /runs?status=FAILED&limit=20` — listar
- `POST /runs/{id}/retry` — reintento manual
- `GET /health` — liveness probe

### Logs estructurados
Cada paso emite un log JSON con `run_id`, `event`, `duration_ms`, `error_type`.

### Métricas recomendadas
- Runs por minuto
- Duración p50/p95/p99
- Ratio `FAILED/COMPLETED`
- Latencia del loader

### Notificaciones
`Notifier` emite eventos: `run.completed`, `run.failed`, `load.failed`. Cada adapter decide a dónde: Slack, email, webhook, log.

---

# Parte IV — Despliegue

## 20. Estructura del proyecto

```
francis-suite/
├── francis_suite/            # el framework (core existente)
│   ├── hands/
│   ├── cli.py
│   └── ...
├── francis_operator/         # capa operativa (lo nuevo)
│   ├── core/
│   │   ├── models.py
│   │   ├── retry_policy.py
│   │   ├── output_validator.py
│   │   └── run_service.py
│   ├── ports/
│   │   ├── run_repository.py
│   │   ├── data_sink.py
│   │   ├── executor.py
│   │   ├── artifact_store.py
│   │   ├── trigger.py
│   │   └── notifier.py
│   ├── adapters/
│   │   ├── repo/            # supabase, postgres, sqlite, memory
│   │   ├── sink/            # supabase, postgres, s3_parquet
│   │   ├── executor/        # subprocess, docker, k8s
│   │   ├── store/           # filesystem, s3
│   │   ├── trigger/         # http_fastapi, cli, cron
│   │   └── notifier/        # log, slack, webhook
│   └── bootstrap.py
├── workflows/
│   └── topPropiedades.xml
├── tests/
│   ├── core/                # tests puros (sin infra)
│   ├── ports/               # contract tests
│   └── adapters/            # tests de cada adapter
├── config.yaml
├── .env
├── requirements.txt
├── Dockerfile
└── main.py                  # entrypoint: uvicorn
```

## 21. Docker y contenedorización

### `requirements.txt`

```
fastapi>=0.111
uvicorn[standard]>=0.30
pyyaml>=6.0
pydantic>=2.7
# adapters opcionales (solo los que uses)
supabase>=2.5
psycopg[binary]>=3.2
boto3>=1.34
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY francis_suite/ /src/francis_suite/
COPY pyproject.toml /src/
RUN pip install /src

COPY francis_operator/ ./francis_operator/
COPY workflows/ ./workflows/
COPY config.yaml main.py ./

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `main.py`

```python
from francis_operator.bootstrap import build_from_config
from francis_operator.adapters.trigger.http_fastapi_trigger import build_app

service = build_from_config("config.yaml")
app = build_app(service)
```

## 22. Despliegue en la nube

### Railway (recomendado para empezar)
1. Push a GitHub.
2. Nuevo proyecto Railway → "Deploy from repo".
3. Detecta `Dockerfile` automáticamente.
4. Variables de entorno: `SUPABASE_URL`, `SUPABASE_KEY`.
5. URL pública: `https://francis-operator.up.railway.app`.

### Render / Fly.io
Mismo patrón con Dockerfile.

### AWS (ECS/Fargate)
- Subir imagen a ECR.
- Task Definition con 1 contenedor.
- Service + Application Load Balancer.

### Kubernetes
- Deployment + Service + Ingress.
- Secrets para credenciales.

### On-premise
- `docker compose up` con `config.yaml` apuntando a SQLite + filesystem.

### Prueba de humo

```bash
curl -X POST https://tu-url/run \
  -H "Content-Type: application/json" \
  -d '{"workflow":"workflows/topPropiedades.xml","params":{"paginas":"5"}}'

curl https://tu-url/status/<session_id>
```

## 23. Stack por defecto y alternativas

### Stack por defecto (simple, cloud-friendly)
| Capa | Tecnología |
|---|---|
| Trigger | FastAPI + Uvicorn |
| Repository | Supabase |
| Sink | Supabase |
| Executor | subprocess |
| Store | filesystem |
| Notifier | log |
| Deploy | Docker + Railway |

### Stack enterprise on-premise
| Capa | Tecnología |
|---|---|
| Trigger | FastAPI |
| Repository | Postgres self-hosted |
| Sink | Postgres |
| Executor | Docker |
| Store | MinIO |
| Notifier | Slack webhook |
| Deploy | Docker Compose |

### Stack escalable (alta concurrencia)
| Capa | Tecnología |
|---|---|
| Trigger | Kafka consumer |
| Repository | DynamoDB |
| Sink | S3 Parquet + Athena |
| Executor | Kubernetes Jobs |
| Store | S3 |
| Notifier | SNS |
| Deploy | EKS |

**El core es el mismo en los 3 casos.** Solo cambian adapters y config.

---

# Parte V — Portabilidad

## 24. Cómo cambiar de tecnología sin romper nada

### Escenario: "Supabase → Postgres en AWS RDS"
- Nuevo adapter: `postgres_repo.py`, `postgres_sink.py`.
- Editar `config.yaml`: `driver: postgres`.
- Core: **sin cambios**.

### Escenario: "Cliente exige on-premise"
- `run_repository.driver: sqlite`
- `data_sink.driver: postgres` (local)
- `artifact_store.driver: filesystem`
- `notifier.driver: log`
- Core: **sin cambios**.

### Escenario: "Escalar a Kubernetes"
- `executor.driver: k8s`
- `run_repository.driver: postgres` managed
- `artifact_store.driver: s3`
- Core: **sin cambios**.

### Escenario: "Reemplazar n8n por Airflow"
- n8n nunca tocó el core. Era un cliente HTTP externo.
- Airflow llama al mismo `POST /run` con `HttpOperator`.
- **Cero cambios en el proyecto**.

### Escenario: "Eventos en vez de HTTP"
- Nuevo trigger: `kafka_trigger.py`.
- `trigger.driver: kafka`.
- Core: **sin cambios**.

### Escenario: "Destino ahora es BigQuery"
- Nuevo adapter: `bigquery_sink.py`.
- `data_sink.driver: bigquery`.
- Core: **sin cambios**.

### Migración dual-write (sin downtime)

```python
class DualRunRepository(RunRepository):
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary
    def create(self, run):
        self.primary.create(run)
        try: self.secondary.create(run)
        except Exception: pass
```

Fases: **dual-write → validación → switch → retiro**.

## 25. Tests como garantía de portabilidad

Cada puerto tiene un **contract test** que cualquier adapter debe pasar.

```python
# tests/ports/test_run_repository_contract.py
class RunRepositoryContract:
    @pytest.fixture
    def repo(self):
        raise NotImplementedError

    def test_create_and_get(self, repo):
        run = Run(id="1", workflow_name="w", params={}, status="CREATED")
        repo.create(run)
        assert repo.get("1").status == "CREATED"

    def test_update_fields(self, repo):
        run = Run(id="2", workflow_name="w", params={}, status="CREATED")
        repo.create(run)
        repo.update("2", status="RUNNING")
        assert repo.get("2").status == "RUNNING"

    def test_get_missing_returns_none(self, repo):
        assert repo.get("ghost") is None
```

```python
# tests/adapters/test_memory_repo.py
class TestMemory(RunRepositoryContract):
    @pytest.fixture
    def repo(self): return InMemoryRunRepository()

# tests/adapters/test_sqlite_repo.py
class TestSqlite(RunRepositoryContract):
    @pytest.fixture
    def repo(self, tmp_path): return SqliteRunRepository(str(tmp_path/"t.db"))
```

**Si un adapter pasa el contract test, está garantizado que funciona con el core.**

## 26. Anti-patrones prohibidos

Cosas que nunca deben pasar:

- `from supabase import create_client` en `run_service.py`.
- `HTTPException` de FastAPI lanzada desde el core.
- Devolver objetos de `postgrest` / `boto3` / `pymongo` desde un adapter.
- Leer `os.environ` dentro del core.
- Hardcodear nombres de tablas en el core.
- Imports circulares entre adapters (los adapters no se conocen entre sí).
- Tests del core que requieran infra real.
- Acoplar el esquema SQL a features exclusivas de un vendor sin encapsular.

---

# Parte VI — Evolución

## 27. Roadmap por fases

### Fase 1 — MVP operativo (1-2 semanas)
- Tabla `francis_runs` (Supabase o SQLite).
- Core completo: `RunService`, `RetryPolicy`, `OutputValidator`.
- Puertos definidos.
- Adapters mínimos: `subprocess_executor`, `supabase_repo`, `supabase_sink`, `http_fastapi_trigger`, `log_notifier`.
- Docker + deploy en Railway.
- Prueba de humo extremo a extremo.

### Fase 2 — Robustez
- Listado y retry manual.
- Staging + swap en el sink.
- Logs estructurados JSON.
- Alertas en Slack (`slack_notifier`).
- Métricas básicas.

### Fase 3 — Escalabilidad
- Scheduler interno (tabla `francis_schedules`).
- Adapter `docker_executor` / `k8s_executor`.
- Adapter `s3_parquet_sink`.
- Rate limiting por workflow.

### Fase 4 — Vanguardia
- Hands Playwright.
- Hands LLM.
- Extensión de navegador → generador de workflows.
- OpenTelemetry.
- SSE streaming en vivo.
- Multi-tenant.

## 28. Ideas de vanguardia

Ideas modernas para elevar el proyecto. Cada una es opcional y cabe en la arquitectura sin refactors.

- **Server-Sent Events en vivo**: `GET /stream/{id}` para ver qué hand está corriendo.
- **Workflows versionados con hash**: SHA-256 de cada `workflow.xml` guardado en el artifact store.
- **Extensión de navegador**: captura clicks/selectores del usuario y genera un `workflow.xml` con hands Playwright.
- **Diff inteligente (upsert)**: en vez de refresh total, compara por clave y solo actualiza lo que cambió.
- **n8n como orquestador externo**: n8n dispara `POST /run`, espera `status`, avisa en Slack. El core no sabe que existe.
- **Scheduler propio**: tabla `francis_schedules` con cron expressions.
- **OpenTelemetry**: trazas distribuidas en Grafana Cloud (free tier).
- **Dead Letter Queue**: runs FATAL van a `francis_dlq` para revisión humana.
- **Hands LLM**: `<llm-extract>` que extrae campos estructurados con un modelo según un schema JSON.
- **Replays determinísticos**: guardar responses HTTP crudos para re-correr offline.
- **Multi-tenant**: agregar `tenant_id` a `francis_runs` para producto multi-cliente.
- **Rate limiting declarativo**: `<workflow rate-limit="10/hour">` directo en el XML.

---

# Parte VII — Presentación profesional

## 29. Cómo presentar Francis Suite en un CV

### Bullet honesto y fuerte (cuando MVP esté en producción)

> **Francis Suite** — Framework universal de extracción y procesamiento de datos basado en workflows XML declarativos. Diseñé e implementé una capa operativa con **FastAPI** que expone ejecución y estado vía REST, con **clasificación de errores y reintentos** con backoff exponencial, **persistencia de estado** y **refresh seguro de tablas destino** validando output antes de escribir. Arquitectura **hexagonal** con adapters intercambiables para repositorio, data sink, executor y notifier. Desplegado en **Docker + Railway**.
> Stack: Python, FastAPI, Supabase, Docker, lxml, httpx.

### Stack a declarar (solo lo implementado)

| Tecnología | Cuándo declararla |
|---|---|
| Python, lxml, httpx | Siempre (está en el core) |
| FastAPI | Cuando el MVP operativo corra |
| Supabase | Cuando haya al menos un adapter funcionando |
| Docker | Cuando el Dockerfile esté en uso |
| Railway / Render / AWS | El que efectivamente uses |
| Playwright | Solo cuando exista al menos un hand Playwright real |
| n8n | Solo cuando lo uses en un flujo real |

## 30. Regla de honestidad técnica

- **Al CV solo va lo que corre en producción.**
- Tecnologías "en estudio" / "roadmap" van en una sección aparte (p. ej. *"Tecnologías en exploración"*), nunca mezcladas con el stack principal.
- **Diseñar** una integración no es **haberla implementado**. Ser claro en el verbo: *"diseñé la integración con n8n para una futura fase"* vs *"integré n8n en producción"*.
- Si un reclutador pregunta, debes poder **mostrarlo corriendo**. Si no puedes, no lo pongas.

---

# Parte VIII — Checklists

## 31. Checklist de implementación

### Fase 1 — MVP
- [ ] Crear tabla de estado en el repositorio elegido
- [ ] Implementar core completo (`models`, `retry_policy`, `output_validator`, `run_service`)
- [ ] Implementar puertos (6 interfaces)
- [ ] Implementar adapters mínimos
- [ ] Escribir `config.yaml` y `bootstrap.py`
- [ ] Escribir tests del core con fakes
- [ ] Escribir contract tests para cada puerto
- [ ] Dockerizar
- [ ] Deploy en cloud
- [ ] Prueba de humo extremo a extremo
- [ ] Actualizar CV con lo que ya corre

### Fase 2 — Robustez
- [ ] Listado + retry manual
- [ ] Staging + swap
- [ ] Logs JSON
- [ ] Notificaciones reales (Slack)
- [ ] Métricas básicas

### Fase 3 — Escalar
- [ ] Scheduler
- [ ] Executor Docker/K8s
- [ ] Sink S3/BigQuery
- [ ] Rate limiting

## 32. Checklist de portabilidad

Úsalo como filtro en cada PR.

- [ ] ¿Mi cambio vive en `core/` o en `adapters/`?
- [ ] Si está en `core/`, ¿agrega algún import de infraestructura? (No debería)
- [ ] ¿El flujo nuevo pasa por un puerto existente o necesita uno nuevo?
- [ ] Si hay puerto nuevo, ¿tiene contract test?
- [ ] ¿Hay fake in-memory para ese puerto?
- [ ] ¿La config nueva está en `config.yaml`?
- [ ] ¿Corren los tests del core sin red, sin DB, sin nada?
- [ ] Si mañana cambiamos de cloud, ¿qué archivos se tocarían? (Solo adapters y config)

---

## Glosario

| Término | Definición |
|---|---|
| **Workflow** | Archivo XML declarativo que describe qué hacer |
| **Hand** | Unidad de ejecución registrada con `@hand(tag=...)` |
| **Box** | Contenedor de dato accesible por nombre dentro del contexto |
| **FVariable** | Tipo base de dato en el runtime |
| **FRecord** | Dataset estructurado con schema y persistencia |
| **FSession** | Contenedor de una ejecución (UUID + status) |
| **Run** | Representación persistente de una ejecución en la capa operativa |
| **Puerto** | Interfaz abstracta que el core consume (hexagonal) |
| **Adapter** | Implementación concreta de un puerto para una tecnología |
| **Driving adapter** | Quien invoca al core (HTTP, CLI, Cron, Kafka) |
| **Driven adapter** | A qué accede el core (DB, storage, ejecutor) |
| **DataSink** | Destino final de los datos procesados |
| **RetryPolicy** | Política de clasificación de errores y backoff |
| **Staging + swap** | Patrón de carga segura: cargar a tabla auxiliar y cambiar |

---

> **Este es el documento único de Francis Suite.** Todo lo que necesitas para entender, construir, operar, desplegar, evolucionar y presentar el proyecto está acá. Actualízalo cuando aparezca un puerto nuevo, un adapter nuevo, un anti-patrón detectado o una fase completada del roadmap.
