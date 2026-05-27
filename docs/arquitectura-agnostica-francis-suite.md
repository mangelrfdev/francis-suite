# Francis Suite — Arquitectura Agnóstica y Portable

> **Cómo diseñar la capa operativa de `Francis Suite` para que no dependa de ninguna tecnología concreta. Supabase, n8n, Railway, AWS, Postgres, Redis: todos deben ser piezas intercambiables, no dependencias acopladas.**

---

## Tabla de contenidos

- [Francis Suite — Arquitectura Agnóstica y Portable](#francis-suite--arquitectura-agnóstica-y-portable)
  - [Tabla de contenidos](#tabla-de-contenidos)
  - [1. Por qué este documento existe](#1-por-qué-este-documento-existe)
  - [2. Principios rectores](#2-principios-rectores)
  - [3. Arquitectura hexagonal aplicada a Francis Suite](#3-arquitectura-hexagonal-aplicada-a-francis-suite)
  - [4. Las 6 fronteras (puertos) del sistema](#4-las-6-fronteras-puertos-del-sistema)
  - [5. Contratos abstractos (interfaces)](#5-contratos-abstractos-interfaces)
  - [6. Adapters: implementaciones intercambiables](#6-adapters-implementaciones-intercambiables)
  - [7. El núcleo puro: lógica sin dependencias](#7-el-núcleo-puro-lógica-sin-dependencias)
  - [8. Configuración declarativa del stack](#8-configuración-declarativa-del-stack)
  - [9. Inyección de dependencias y bootstrap](#9-inyección-de-dependencias-y-bootstrap)
  - [10. Estrategia de migración entre tecnologías](#10-estrategia-de-migración-entre-tecnologías)
  - [11. Tests: la garantía de portabilidad](#11-tests-la-garantía-de-portabilidad)
  - [12. Escenarios reales de intercambio](#12-escenarios-reales-de-intercambio)
  - [13. Anti-patrones que rompen la portabilidad](#13-anti-patrones-que-rompen-la-portabilidad)
  - [14. Checklist de portabilidad](#14-checklist-de-portabilidad)

---

## 1. Por qué este documento existe

El documento `flujo-operativo-francis-suite.md` muestra **una** forma concreta de operar Francis Suite: FastAPI + Supabase + Railway.

Pero eso es **una implementación**, no **la arquitectura**. Mañana puede aparecer:

- Un cliente que exige **AWS** en vez de Railway.
- Una empresa que usa **PostgreSQL managed** en vez de Supabase.
- Un equipo que prefiere **Airflow** o **Temporal** en vez de orquestar con n8n.
- Un caso donde todo debe correr **on-premise** sin cloud.
- Un stack totalmente distinto: **Redis Streams**, **MinIO**, **Kafka**, **Nats**.

Si acoplamos el código a Supabase y a FastAPI, cualquiera de estos cambios será un **reescribirlo todo**. Si desacoplamos bien, será **cambiar un adapter**.

**Este documento es el contrato de portabilidad de Francis Suite.**

---

## 2. Principios rectores

- **Depender de abstracciones, no de implementaciones.** El núcleo nunca `import supabase`.
- **Inversión de dependencias.** Los detalles dependen del core, no al revés.
- **Interfaces pequeñas y estables.** Mejor 5 interfaces de 3 métodos que 1 de 15.
- **Adapters reemplazables en un archivo.** Cambiar de Supabase a Postgres debería ser crear 1 nuevo adapter, no tocar el core.
- **Configuración externa.** Qué adapter se usa se decide en `.env` / `config.yaml`, nunca en el código.
- **Tests con fakes.** Cada interfaz tiene un fake en memoria para testear sin infra real.
- **Formato neutro en la frontera.** Nada de tipos de Supabase/FastAPI atravesando el core.

---

## 3. Arquitectura hexagonal aplicada a Francis Suite

```
                    ┌─────────────────────────────────┐
                    │       NÚCLEO (domain)           │
                    │                                 │
  ┌─────────┐       │  - Run                          │       ┌──────────────┐
  │  HTTP   │──────▶│  - ExecutionPolicy              │──────▶│ RunRepository│
  │ Adapter │       │  - RetryPolicy                  │       │   (Supabase /│
  └─────────┘       │  - OutputValidator              │       │    Postgres /│
                    │  - LoadOrchestrator             │       │    SQLite)   │
  ┌─────────┐       │                                 │       └──────────────┘
  │  CLI    │──────▶│  NO IMPORTA: fastapi, supabase, │──────▶┌──────────────┐
  │ Adapter │       │  boto3, httpx, redis, nada.     │       │ DataSink     │
  └─────────┘       │                                 │       │ (Supabase /  │
                    │  Solo usa interfaces (puertos). │       │  S3 / Mongo /│
  ┌─────────┐       │                                 │       │  Postgres)   │
  │  Cron   │──────▶│                                 │──────▶└──────────────┘
  │ Adapter │       │                                 │
  └─────────┘       └─────────────────────────────────┘       ┌──────────────┐
                            │                                 │ Executor     │
                            └────────────────────────────────▶│ (subprocess /│
                                                              │  docker /    │
                                                              │  k8s job)    │
                                                              └──────────────┘
```

**Izquierda: quién invoca al core** (driving adapters).
**Derecha: a qué infraestructura accede el core** (driven adapters).
**Centro: el dominio puro**, sin dependencias de frameworks ni servicios externos.

---

## 4. Las 6 fronteras (puertos) del sistema

Toda la capa operativa de Francis Suite se puede modelar con **6 puertos**. Cualquier tecnología concreta implementa uno de estos puertos.

| # | Puerto | Responsabilidad | Ejemplos de adapters |
|---|---|---|---|
| 1 | **RunRepository** | Persistir estado de cada run | Supabase, Postgres, SQLite, DynamoDB, Firestore, JSON file |
| 2 | **DataSink** | Cargar datos finales al destino | Supabase table, Postgres, S3, MongoDB, BigQuery, MySQL |
| 3 | **Executor** | Ejecutar un workflow | subprocess local, Docker, Kubernetes Job, AWS Batch, Cloud Run |
| 4 | **ArtifactStore** | Guardar archivos generados | Filesystem local, S3, Azure Blob, GCS, MinIO |
| 5 | **Trigger** | Disparar ejecuciones | HTTP REST, CLI, cron, Kafka, RabbitMQ, SQS, webhook |
| 6 | **Notifier** | Comunicar estado hacia fuera | Slack, Email, webhook, Discord, Teams, SSE, log |

Cada puerto es una **clase abstracta pequeña**. Cada tecnología concreta es una **implementación**.

---

## 5. Contratos abstractos (interfaces)

El corazón de la portabilidad. Todas las interfaces viven en `francis_operator/ports/`.

### 5.1. `RunRepository`

```python
# francis_operator/ports/run_repository.py
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
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    output_row_count: Optional[int] = None
    load_status: str = "PENDING"
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

### 5.2. `DataSink`

```python
# francis_operator/ports/data_sink.py
from abc import ABC, abstractmethod
from typing import Iterable

class DataSink(ABC):
    @abstractmethod
    def replace_all(self, target: str, rows: Iterable[dict]) -> int:
        """Borra el destino y carga todo de nuevo. Retorna filas insertadas."""

    @abstractmethod
    def upsert(self, target: str, rows: Iterable[dict], key: str) -> int:
        """Inserta o actualiza por clave. Retorna filas afectadas."""

    @abstractmethod
    def count(self, target: str) -> int: ...
```

### 5.3. `Executor`

```python
# francis_operator/ports/executor.py
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
    def run(
        self,
        workflow: str,
        params: dict,
        output_dir: Path,
        timeout_sec: int,
    ) -> ExecutionResult: ...
```

### 5.4. `ArtifactStore`

```python
# francis_operator/ports/artifact_store.py
from abc import ABC, abstractmethod
from pathlib import Path

class ArtifactStore(ABC):
    @abstractmethod
    def put(self, local_path: Path, remote_key: str) -> str:
        """Sube archivo. Retorna URI/URL del recurso."""

    @abstractmethod
    def get(self, remote_key: str, local_path: Path) -> None: ...

    @abstractmethod
    def exists(self, remote_key: str) -> bool: ...
```

### 5.5. `Trigger`

```python
# francis_operator/ports/trigger.py
from abc import ABC, abstractmethod
from typing import Callable

class Trigger(ABC):
    @abstractmethod
    def start(self, on_run: Callable[[str, dict], str]) -> None:
        """
        Arranca el adapter de entrada.
        on_run(workflow, params) -> session_id
        """
```

### 5.6. `Notifier`

```python
# francis_operator/ports/notifier.py
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def notify(self, event: str, payload: dict) -> None: ...
    # event: "run.completed" | "run.failed" | "load.failed" | ...
```

---

## 6. Adapters: implementaciones intercambiables

Cada adapter vive en `francis_operator/adapters/<tecnología>/`.

### 6.1. Ejemplos para `RunRepository`

```
francis_operator/adapters/repo/
├── supabase_repo.py      # usa supabase-py
├── postgres_repo.py      # usa psycopg
├── sqlite_repo.py        # usa sqlite3 (default, zero-config)
├── dynamodb_repo.py      # usa boto3
├── mongo_repo.py         # usa pymongo
└── memory_repo.py        # in-memory, para tests
```

### 6.2. Ejemplos para `DataSink`

```
francis_operator/adapters/sink/
├── supabase_sink.py
├── postgres_sink.py
├── s3_parquet_sink.py    # escribe parquet a S3
├── bigquery_sink.py
├── mongo_sink.py
└── file_sink.py          # escribe a disco (útil en on-prem)
```

### 6.3. Ejemplos para `Executor`

```
francis_operator/adapters/executor/
├── subprocess_executor.py   # local
├── docker_executor.py       # docker run
├── k8s_job_executor.py      # crea Jobs en Kubernetes
├── cloudrun_executor.py     # Google Cloud Run Jobs
└── aws_batch_executor.py
```

### 6.4. Ejemplos para `Trigger`

```
francis_operator/adapters/trigger/
├── http_fastapi_trigger.py
├── http_flask_trigger.py
├── cli_trigger.py
├── cron_trigger.py
├── kafka_trigger.py
└── sqs_trigger.py
```

### 6.5. Regla de oro

**Un adapter nunca debe filtrar su tipo concreto hacia el core.** Si Supabase devuelve un `PostgrestResponse`, el adapter lo convierte a `Run` (dataclass neutro) antes de retornarlo. El núcleo **solo ve `Run`**.

---

## 7. El núcleo puro: lógica sin dependencias

El `core/` es lo que **nunca cambia** aunque cambies toda la infraestructura.

```
francis_operator/core/
├── models.py              # Run, ExecutionResult, etc. (dataclasses puros)
├── retry_policy.py        # Clasificación de errores + backoff
├── output_validator.py    # Reglas para identificar archivo principal
├── load_orchestrator.py   # Validar → borrar → insertar (usa DataSink)
└── run_service.py         # Orquesta todo usando los puertos
```

### Ejemplo: `RunService` sin acoplamientos

```python
# francis_operator/core/run_service.py
from uuid import uuid4
from datetime import datetime, timezone

from francis_operator.ports.run_repository import RunRepository, Run
from francis_operator.ports.executor import Executor
from francis_operator.ports.data_sink import DataSink
from francis_operator.ports.notifier import Notifier
from francis_operator.core.retry_policy import RetryPolicy
from francis_operator.core.output_validator import find_main_output

class RunService:
    def __init__(
        self,
        repo: RunRepository,
        executor: Executor,
        sink: DataSink,
        notifier: Notifier,
        retry: RetryPolicy,
        target_table: str,
    ):
        self.repo = repo
        self.executor = executor
        self.sink = sink
        self.notifier = notifier
        self.retry = retry
        self.target_table = target_table

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
        result = self.executor.run(
            run.workflow_name, run.params,
            output_dir=self._output_dir(run_id),
            timeout_sec=600,
        )

        if result.success:
            self._handle_success(run, result)
        else:
            self._handle_failure(run, result)

    def _handle_success(self, run, result):
        main_file = find_main_output(result.output_dir)
        if main_file is None:
            self.repo.update(
                run.id, status="FAILED",
                error_type="FATAL",
                error_message="Sin archivos de datos",
            )
            self.notifier.notify("run.failed", {"id": run.id})
            return

        rows = list(self._read_rows(main_file))
        if not rows:
            self.repo.update(run.id, status="FAILED", error_type="FATAL",
                             error_message="Archivo vacío")
            return

        # Carga segura
        self.repo.update(run.id, status="COMPLETED", load_status="LOADING",
                         output_path=str(main_file), output_row_count=len(rows))
        try:
            inserted = self.sink.replace_all(self.target_table, rows)
            self.repo.update(run.id, load_status="LOADED")
            self.notifier.notify("run.completed", {"id": run.id, "rows": inserted})
        except Exception as e:
            self.repo.update(run.id, load_status="LOAD_FAILED",
                             error_message=str(e)[:500])
            self.notifier.notify("load.failed", {"id": run.id})

    def _handle_failure(self, run, result):
        decision = self.retry.decide(result.stderr, run.retry_count, run.max_retries)
        if decision.should_retry:
            self.repo.update(run.id, status="RETRYING",
                             retry_count=run.retry_count + 1)
            decision.wait()
            self.execute(run.id)
        else:
            self.repo.update(run.id, status="FAILED",
                             error_type=decision.error_type,
                             error_message=result.stderr[-1000:])
            self.notifier.notify("run.failed", {"id": run.id})
```

**Observa**: este archivo no tiene un solo `import supabase`, `import fastapi`, `import boto3`. Se puede mover a cualquier lado.

---

## 8. Configuración declarativa del stack

El qué-usar-para-qué se define en un archivo de config, no en el código.

### Ejemplo: `config.yaml`

```yaml
run_repository:
  driver: supabase         # supabase | postgres | sqlite | dynamodb | mongo
  options:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_KEY}
    table: francis_runs

data_sink:
  driver: supabase
  options:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_KEY}
  target: tu_tabla_de_datos

executor:
  driver: subprocess        # subprocess | docker | k8s | cloudrun
  options:
    timeout_sec: 600
    runs_dir: ./runs

artifact_store:
  driver: filesystem        # filesystem | s3 | gcs | azure
  options:
    root: ./runs

trigger:
  driver: http_fastapi      # http_fastapi | cli | cron | kafka
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

### Migración futura

Cambiar de Supabase a Postgres + de Railway a AWS:

```yaml
run_repository:
  driver: postgres
  options:
    dsn: ${DATABASE_URL}
    table: francis_runs

data_sink:
  driver: postgres
  options:
    dsn: ${DATABASE_URL}
  target: tu_tabla_de_datos

executor:
  driver: aws_batch
  options:
    job_queue: francis-queue
    job_definition: francis-runner:1
```

**Cero cambios en el core.** Solo editas YAML.

---

## 9. Inyección de dependencias y bootstrap

Un único lugar construye los adapters según la config y los inyecta en el core.

```python
# francis_operator/bootstrap.py
import yaml, os
from francis_operator.core.run_service import RunService
from francis_operator.core.retry_policy import RetryPolicy

# Registry de drivers disponibles
from francis_operator.adapters.repo import supabase_repo, postgres_repo, sqlite_repo
from francis_operator.adapters.sink import supabase_sink, postgres_sink, s3_parquet_sink
from francis_operator.adapters.executor import subprocess_executor, docker_executor
from francis_operator.adapters.notifier import log_notifier, slack_notifier

REPO_DRIVERS = {
    "supabase": supabase_repo.SupabaseRunRepository,
    "postgres": postgres_repo.PostgresRunRepository,
    "sqlite":   sqlite_repo.SqliteRunRepository,
}
SINK_DRIVERS = {
    "supabase": supabase_sink.SupabaseDataSink,
    "postgres": postgres_sink.PostgresDataSink,
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
    cfg = yaml.safe_load(_expand_env(open(path).read()))

    repo     = REPO_DRIVERS[cfg["run_repository"]["driver"]](**cfg["run_repository"]["options"])
    sink     = SINK_DRIVERS[cfg["data_sink"]["driver"]](**cfg["data_sink"]["options"])
    executor = EXECUTOR_DRIVERS[cfg["executor"]["driver"]](**cfg["executor"]["options"])
    notifier = NOTIFIER_DRIVERS[cfg["notifier"]["driver"]](**cfg["notifier"]["options"])

    retry = RetryPolicy(
        max_retries=cfg["retry"]["max_retries"],
        base_sec=cfg["retry"]["backoff_base_sec"],
        factor=cfg["retry"]["backoff_factor"],
    )

    return RunService(
        repo=repo, executor=executor, sink=sink, notifier=notifier,
        retry=retry, target_table=cfg["data_sink"]["target"],
    )

def _expand_env(text: str) -> str:
    return os.path.expandvars(text)
```

El resto del sistema solo usa `RunService`. Nunca sabe qué hay detrás.

---

## 10. Estrategia de migración entre tecnologías

Patrón recomendado cuando hay que cambiar un adapter en producción sin downtime.

### Fase 1: dual-write
El core escribe a **viejo y nuevo** adapter a la vez (wrapper compuesto).

```python
class DualRunRepository(RunRepository):
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary
    def create(self, run):
        self.primary.create(run)
        try: self.secondary.create(run)
        except Exception: pass  # no romper por el nuevo
    # ...
```

### Fase 2: validación
Comparas datos entre ambos. Cuando están alineados durante X tiempo, pasas a Fase 3.

### Fase 3: switch
Cambias la config: el nuevo pasa a ser `primary`, el viejo se retira.

### Fase 4: retiro
Eliminas el adapter viejo del proyecto.

---

## 11. Tests: la garantía de portabilidad

Cada puerto tiene un **test suite genérico** que cualquier adapter debe pasar.

```python
# tests/ports/test_run_repository_contract.py
import pytest
from francis_operator.ports.run_repository import Run

class RunRepositoryContract:
    """Cualquier adapter de RunRepository debe pasar estos tests."""

    @pytest.fixture
    def repo(self):
        raise NotImplementedError  # cada adapter la sobreescribe

    def test_create_and_get(self, repo):
        run = Run(id="1", workflow_name="w", params={}, status="CREATED")
        repo.create(run)
        got = repo.get("1")
        assert got.id == "1"
        assert got.status == "CREATED"

    def test_update_fields(self, repo):
        run = Run(id="2", workflow_name="w", params={}, status="CREATED")
        repo.create(run)
        repo.update("2", status="RUNNING")
        assert repo.get("2").status == "RUNNING"
```

```python
# tests/adapters/test_memory_repo.py
from francis_operator.adapters.repo.memory_repo import InMemoryRunRepository
from tests.ports.test_run_repository_contract import RunRepositoryContract

class TestMemoryRepo(RunRepositoryContract):
    @pytest.fixture
    def repo(self):
        return InMemoryRunRepository()
```

```python
# tests/adapters/test_sqlite_repo.py
class TestSqliteRepo(RunRepositoryContract):
    @pytest.fixture
    def repo(self, tmp_path):
        return SqliteRunRepository(str(tmp_path / "test.db"))
```

**Si un adapter nuevo pasa el contract test, está garantizado que funciona con el core.**

---

## 12. Escenarios reales de intercambio

Casos concretos y qué cambia en cada uno.

### Escenario A: "ya no queremos Supabase, queremos Postgres en AWS RDS"
- Nuevo adapter: `postgres_repo.py`, `postgres_sink.py` (ya existen si los escribimos).
- Cambio: `config.yaml` — `driver: postgres`.
- Core: **sin cambios**.

### Escenario B: "cliente exige on-premise, sin cloud"
- `run_repository.driver: sqlite`
- `data_sink.driver: postgres` (local)
- `executor.driver: subprocess`
- `artifact_store.driver: filesystem`
- `trigger.driver: http_fastapi`
- `notifier.driver: log`
- Core: **sin cambios**.

### Escenario C: "queremos escalar a Kubernetes"
- `executor.driver: k8s`
- `run_repository.driver: postgres` (managed)
- `artifact_store.driver: s3`
- Core: **sin cambios**.

### Escenario D: "ya no queremos n8n, preferimos Airflow"
- n8n nunca tocó el core. Era solo un cliente HTTP externo.
- Airflow llama al mismo `POST /run` con un `HttpOperator`.
- **Cero cambios en Francis Suite.**

### Escenario E: "queremos eventos en vez de HTTP"
- Nuevo trigger: `kafka_trigger.py` que consume un topic y llama a `RunService.start_run`.
- `trigger.driver: kafka`.
- Core: **sin cambios**.

### Escenario F: "el destino ahora es BigQuery, no Supabase"
- Nuevo adapter: `bigquery_sink.py`.
- `data_sink.driver: bigquery`.
- Core: **sin cambios**.

---

## 13. Anti-patrones que rompen la portabilidad

Cosas que **nunca** deben pasar en el core.

- **`from supabase import create_client` en `run_service.py`.** Si está ahí, ya perdiste.
- **Lanzar `HTTPException` de FastAPI desde el core.** El core lanza `ValueError`, `NotFound`; el adapter HTTP los traduce.
- **Devolver objetos de `postgrest` / `boto3` / `pymongo` desde un adapter.** Siempre convertir a dataclasses neutros.
- **Leer variables de entorno dentro del core.** El `bootstrap.py` las lee y las inyecta.
- **Acoplar el esquema SQL a Supabase.** Si usas features exclusivas, encapsúlalas o documéntalas.
- **Hardcodear nombres de tablas en el core.** Siempre por parámetro/config.
- **Imports circulares entre adapters.** Los adapters no se conocen entre sí, solo conocen al core vía puertos.
- **Tests que requieren Supabase real.** El core se testea 100% con fakes. Solo los adapter tests tocan infra.

---

## 14. Checklist de portabilidad

Úsalo como filtro al agregar cualquier feature nueva.

- [ ] ¿Mi cambio vive en `core/` o en `adapters/`?
- [ ] Si está en `core/`, ¿agrega algún `import` de una librería de infraestructura? **No debería.**
- [ ] ¿El nuevo flujo pasa por un puerto existente o necesito uno nuevo?
- [ ] Si agrego un puerto, ¿tiene un contract test genérico?
- [ ] ¿Tengo al menos un fake in-memory para ese puerto?
- [ ] ¿La config nueva está reflejada en `config.yaml`?
- [ ] ¿Puedo correr los tests del core **sin red, sin DB, sin nada**?
- [ ] Si mañana cambio de cloud, ¿qué archivos tocaría? (Deberían ser solo adapters y config.)

---

## Palabras finales

Este documento es el **contrato con el futuro** de Francis Suite.

El doc `flujo-operativo-francis-suite.md` te dice **cómo hacerlo funcionar hoy con Supabase**.
Este doc te asegura que **mañana puedas reemplazar Supabase en una tarde**.

Ambos son necesarios. Uno sin el otro es frágil:

- Solo el operativo → funciona, pero te atas a un stack.
- Solo el arquitectónico → portable, pero no tienes nada corriendo.

La clave: **implementa el primero siguiendo las reglas del segundo.**

> Documento vivo. Actualízalo cuando aparezca un puerto nuevo, un adapter nuevo, o un anti-patrón detectado en el código.
