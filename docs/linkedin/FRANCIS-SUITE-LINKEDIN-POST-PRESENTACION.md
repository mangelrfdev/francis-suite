# Post de LinkedIn - Presentacion del Proyecto

## Version Principal (Recruiter-Friendly)

Hoy quiero compartir mi proyecto principal de portafolio tecnico: **Francis Suite**.

Es un framework low-code para extraccion y procesamiento de datos, donde los workflows se definen en XML y se ejecutan con un runtime en Python.

### Lo que resuelve

- Estandariza pipelines de scraping con una estructura declarativa.
- Separa logica de negocio de implementacion tecnica (hands reutilizables).
- Permite exportar resultados en formatos listos para integracion.
- Facilita evolucion de workflows sin reescribir todo el motor.

### Stack y tecnologias clave

- **Python 3.11+**
- **lxml** para parsing y XPath.
- **httpx** para requests HTTP.
- **Playwright** para escenarios browser automation.
- **XML workflows** como capa declarativa.
- **pytest** para calidad y regresion.
- **uv** para entorno y dependencias.

### Decisiones tecnicas destacables

- Arquitectura por capas: parser -> runtime -> context -> hands.
- Modelo de datos basado en boxes para mantener estado entre pasos.
- Variables sensibles con masking para logs seguros.
- Exportaciones pensadas para consumo real (ej. NDJSON para ingest).

### Aprendizajes

Este proyecto me reforzo algo clave:  
**un pipeline robusto no es solo extraer datos**, tambien es controlar contexto, errores, observabilidad y calidad de salida para que otro sistema lo pueda consumir sin friccion.

Si te interesa, feliz de compartir repo, arquitectura y decisiones de implementacion.

#Python #DataEngineering #WebScraping #Automation #ETL #Playwright #SoftwareEngineering #Portafolio

---

## Version Corta

Comparto mi proyecto de portafolio: **Francis Suite**.

Framework en Python para construir workflows XML de extraccion/procesamiento de datos con enfoque en mantenibilidad y outputs de integracion.

Aprendizaje principal: pasar de scripts aislados a una plataforma declarativa cambia por completo la velocidad de iteracion y la calidad operativa.

#Python #WebScraping #DataEngineering #Automation

---

## Mini Seccion de Portafolio (CV / GitHub / LinkedIn)

**Proyecto:** Francis Suite  
**Rol:** Arquitectura + desarrollo del framework  
**Stack:** Python, lxml, httpx, Playwright, XML, pytest

**Problema:** evitar pipelines de scraping fragiles y dispersos en scripts ad-hoc.

**Solucion:**
- Motor declarativo basado en workflows XML.
- Ejecucion por hands reutilizables y extensibles.
- Modelo de contexto con boxes para flujo de datos.
- Exportacion de resultados para integraciones aguas abajo.

**Enfoque tecnico clave:** separar motor, configuracion y reglas de datos para iterar mas rapido con menos deuda tecnica.
