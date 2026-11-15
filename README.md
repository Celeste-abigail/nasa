# A.R.T.E.M.I.S. · Aerospace Resilience, Telemetry, and Evaluation of Medical and Internal Stress

> **Desarrollado por LABQUIP (`LABQUIP.APP`) — NASA Space Apps Challenge**  
> *Agente autónomo de evaluación biomédica, telemetría multiparamétrica y soporte vital predictivo para misiones espaciales de larga duración y poblaciones vulnerables en la Tierra.*

---

## Resumen Ejecutivo y Propuesta de Valor

En misiones de espacio profundo (programa Artemis y tránsito marciano), el retraso en las comunicaciones y la carga cognitiva impiden que la tripulación interprete tablas clínicas crudas. **A.R.T.E.M.I.S.** transforma datos fisiológicos dispersos en un flujo de triaje autónomo:

```
planificar -> medir -> evaluar -> predecir -> prescribir -> exportar
```

1. **Monitoreo Multiparamétrico Integrado (4 Nodos Activos):** Evalúa en tiempo real la **desmineralización ósea** (método acústico confocal SCAN: BUA, UV/SOS, ATT y predicción de BV/TV), el **estrés neuroendocrino** (cortisol salival circadiano CLIA/ECLIA), el **estrés dosimétrico** (radiación ambiental TEPC en capas A/B/C) y la **carga alostática / salud mental** (NASA-TLX, DMRS/CDA, arquitectura de sueño y PVT-B).
2. **Interfaz Biomimética y Triaje Empático:** A.R.T.E.M.I.S. (representada por una tortuga marina espacial) actúa como agente de alerta temprana que traduce desviaciones matemáticas complejas en estados operativos inmediatos (`NOMINAL`, `PRECAUCIÓN`, `ALERTA`, `CRÍTICO`), reduciendo la fatiga de decisión del astronauta y del médico de vuelo.
3. **Doble Impacto (Espacio + Extrapolación Terrestre):**
   - **Investigación Científica (Big Data):** Exportación masiva estandarizada (`CSV` en formato largo, `JSON`, `PDF` y `HTML`) lista para alimentar pipelines bioinformáticos y estudios longitudinales.
   - **Despliegue Clínico en la Tierra:** El motor predictivo y las tablas poblacionales integradas permiten utilizar la plataforma directamente en entornos hospitalarios y geriátricos terrestres para el tamizaje preventivo de **osteopenia, osteoporosis y síndrome de fragilidad** en adultos mayores.

---

## Stack Tecnológico

| Capa | Tecnología | Motivo |
| --- | --- | --- |
| Toolchain | **mise** (node 24, python 3.13, uv, bun) | una sola versión reproducible, sin permisos de administrador |
| Backend | **FastAPI + SQLModel + SQLite** | validación estricta, OpenAPI y persistencia `.db` local |
| Ciencia | **Python puro** (sin dependencias pesadas) | dominio biomédico testeable, auditable y 100 % determinista |
| Frontend | **React 19 + TypeScript + Vite** | arquitectura modular por dominio y tipado estricto |
| Datos remotos | **TanStack Query** | caché reactiva, invalidación automática y estados de carga |
| i18n | **react-i18next** + catálogos del backend | soporte bilingüe completo (`es` y `en`) en tiempo real |
| Runtime dev | **bun** | instalación ultrarrápida y ejecución concurrente `bun run dev` |

Sin dependencia obligatoria de nube ni contenedores pesados: toda la telemetría corre localmente con latencia cero, apta para entornos aislados en órbita o clínicas rurales en la Tierra.

---

## Inicio Rápido

Requisitos: Windows 10/11 (probado), `mise` y `bun`.

```powershell
winget install --id jdx.mise -e
# abrir nueva terminal para que mise entre al PATH
bun run setup          # mise install + uv sync + bun install
bun run dev            # levanta API + interfaz web con recarga en vivo
```

- **Consola Web (`LABQUIP.APP`)**: <http://127.0.0.1:5173>
- **API / Swagger Docs**: <http://127.0.0.1:8000/docs>
- **Healthcheck**: <http://127.0.0.1:8000/api/health>

Cargar telemetría simulada y perfiles de prueba (opcional):

```powershell
mise run seed          # o: backend\.venv\Scripts\python.exe -m app.scripts.seed
```

---

## Experiencia de Usuario e Interfaz Biomimética (`ASTRO HEALTH MONITOR APP`)

Al abrir la plataforma se despliega el centro de comando **Resumen**, que consolida el estado del astronauta activo junto al agente **A.R.T.E.M.I.S.** y cuatro tarjetas de telemetría (Densidad Ósea, Cortisol, Radiación y Salud Mental) con su estado operativo, métrica primaria, indicadores secundarios, fecha de actualización y curva de tendencia (*sparkline*).

- **Filtros rápidos por nodo**: chips interactivos persistidos en `localStorage["nasa-space-summary"]`.
- **HUD de Estado General**: resume los contadores críticos del sujeto activo, el número de módulos que requieren intervención y la nota clínica contextual de A.R.T.E.M.I.S.
- **Sincronización de Caché**: TanStack Query reutiliza las consultas de `monitoring`, `cortisol`, `radiation` y `mental` al navegar hacia cada módulo detallado.
- **Tolerancia a Fallos**: si un sensor o módulo aún no registra lecturas, su tarjeta lo reporta de forma aislada sin bloquear el resto de la consola.

### Identidad Visual y Diseño Biomimético

- **Blindaje Teselado Voronoi (Biomímesis)**: los contenedores principales incorporan en su vértice superior derecho un patrón vectorial inspirado en el desprendimiento de placas cefálicas de tortuga marina (*Chelonia mydas*), fusionado con cortes geométricos biselados a 45° en tarjetas, pestañas y controles.
- **Paleta Abisal-Nebulosa**: degradados profundos (`#050a14` → `#0b1225` → `#160e2a`) con bordes técnicos cian (`rgba(56, 189, 248, 0.26)`) y haces superiores luminosos según severidad clínica (`NOMINAL`, `PRECAUCIÓN`, `ALERTA`, `CRÍTICO`).
- **Tipografía Aeroespacial**: **Chakra Petch** (encabezados técnicos y métricas principales), **Space Grotesk** (lectura clínica) y **JetBrains Mono** (telemetría numérica, badges y ejes), servidas vía Google Fonts.
- **Estandarización Operativa**: selector de idioma (`ES | EN`) ubicado en la esquina superior derecha, selector anatómico contextual integrado dentro del módulo óseo y paneles de captura unificados bajo el estándar `// REGISTRAR DATOS` e `IMPORTAR DATOS +`.
- **Fotografía Espacial**: vista orbital nocturna *"In Darkness viewing Jakarta | International Space Station"*, acreditada con enlace directo a [Friends of NASA](https://www.friendsofnasa.org/search?updated-max=2024-07-31T12:43:00-07:00&max-results=16&reverse-paginate=true&m=0&hl=es-ES).

### Gestión de Tripulación y Exportación Científica

- **Tripulación**: control en cabecera para dar de alta astronautas (código, nombre, sexo, fecha de nacimiento) y archivarlos de forma reversible sin perder sus series históricas.
- **Descargas para Investigación**:
  - Reportes clínicos: `summary.html` (imprimible), `summary.pdf` (generado vía ReportLab) y `summary.json`.
  - Datasets crudos para ciencia de datos: `data.json` y `data.csv` unificado en formato largo (`module,recorded_at,metric,value,unit,flags,notes`).

---

## Arquitectura del Sistema

Implementa **Screaming Architecture** con separación estricta en cuatro capas y dependencias unidireccionales:

```
api (HTTP) → modules (casos de uso) → domain (reglas biomédicas puras) ← infrastructure (SQLite, archivos)
```

```
backend/
  app/
    core/            configuración, bus de eventos in-process, i18n, dependencias
    domain/          modelos SQLModel, esquemas Pydantic, motores matemáticos (bone.py, etc.)
    infrastructure/  engine SQLite, repositorios, parsers de archivos
    modules/
      astronauts/    gestión de perfiles de tripulación
      measurements/  registro, validación de dominio e importación masiva CSV/XLSX/JSON
      monitoring/    evaluación longitudinal, tasas de cambio y triaje
    api/v1/          routers FastAPI (contratos HTTP)
    i18n/            catálogos es.json / en.json (mensajes clínicos del backend)
    scripts/         generadores de referencias y seed de datos
  tests/             suite pytest: dominio matemático puro + integración HTTP
frontend/
  src/
    lib/             cliente API tipado, cálculo de severidades, formateadores
    i18n/            catálogos es/en y configuración de react-i18next
    modules/
      shell/         Header unificado, selector de idioma y navegación
      overview/      HUD principal, agente interactivo A.R.T.E.M.I.S. y SummaryCards
      measurements/  asistente de 3 pasos ("Registrar datos") e importación
      monitoring/    KPIs, gráficos vectoriales SVG y tablas de historial
```

### Bus de Eventos (`Event-Driven`)

`app/core/events.py` gestiona un bus en memoria que desacopla las lecturas del motor de evaluación:

| Tópico | Se dispara cuando | Efecto inmediato |
| --- | --- | --- |
| `measurement.created` | se registra una nueva medición | invalida la caché de evaluaciones del astronauta |
| `measurement.imported` | finaliza una carga masiva de archivos | recalcula series e invalida la caché |
| `astronaut.created` | se registra un nuevo tripulante | inicializa contexto e invalida caché |

### Base de Datos

- Archivo local: `backend/data/nasa_space.db` (excluido en git), inicializado automáticamente por el *lifespan* de FastAPI/Uvicorn.
- Escalable mediante la variable de entorno `NASA_DATABASE_URL` a cualquier motor compatible con SQLAlchemy (incluyendo PostgreSQL en producción).

---

## Fundamento Científico y Reglas Clínicas por Módulo

### 1. Módulo de Densidad Ósea (Método Acústico Confocal)

Captura **BUA** (atenuación de ultrasonido de banda ancha), **UV/SOS** (velocidad del sonido) y **ATT**, estima la fracción de volumen óseo trabecular (**BV/TV**) mediante regresión publicada y evalúa la velocidad de desmineralización respecto a la línea base:

| Concepto | Regla Matemática / Umbral |
| --- | --- |
| **BV/TV predicho** | `3.89e-4 · UV − 9e-4 · BUA − 0.456` |
| **Línea base** | Primera medición histórica de cada astronauta **por sitio anatómico** (`calcaneus` / `femoral_neck`) |
| **Pérdida acumulada** | `(BUA_base − BUA_actual) / BUA_base · 100` |
| **Tasa mensual** | `pérdida acumulada / meses desde la línea base` (mínimo 0.1 mes) |
| **Nivel 1 · Nominal** | Tasa `< 0.8 %/mes` |
| **Nivel 2 · Precaución / Riesgo** | `0.8 ≤ tasa ≤ 1.5 %/mes` |
| **Nivel 3 · Alerta Crítica** | Tasa `> 1.5 %/mes` **o** pérdida acumulada `> 3 %` |

- **Validación estricta de dominio** (rechaza valores físicamente imposibles sin extrapolar): `0 < BUA < 200 dB/MHz`, `1200 ≤ UV ≤ 2000 m/s`, `0 < ATT < 200 dB/cm`.
- **Referencias científicas (DOI)**: [10.1117/12.810048](https://doi.org/10.1117/12.810048) · [10.1016/j.actaastro.2012.08.032](https://doi.org/10.1016/j.actaastro.2012.08.032) · [10.1121/1.4784949](https://doi.org/10.1121/1.4784949).

#### Referencia Poblacional Terrestre y Extrapolación Geriátrica (Shin et al., 2005)

Cruza el sexo y la edad exacta del sujeto a la fecha de cada sesión contra las 12 cohortes normativas (n = 3.053 adultos):

| Sexo | Edad | n | BUA media ± DE (dB/MHz) | SOS media ± DE (m/s) |
|---|---|---:|---|---|
| Hombre | 20-29 | 50 | 121,4 ± 15,6 | 1556,1 ± 47,7 |
| Hombre | 30-39 | 77 | 121,2 ± 15,7 | 1554,6 ± 40,2 |
| Hombre | 40-49 | 137 | 119,2 ± 13,9 | 1548,7 ± 40,7 |
| Hombre | 50-59 | 327 | 114,2 ± 13,1 | 1545,0 ± 35,0 |
| Hombre | 60-69 | 506 | 111,6 ± 13,8 | 1541,0 ± 32,4 |
| Hombre | 70-74 | 128 | 108,7 ± 16,0 | 1527,3 ± 30,8 |
| Mujer | 20-29 | 55 | 113,2 ± 13,6 | 1556,1 ± 28,2 |
| Mujer | 30-39 | 109 | 113,9 ± 13,9 | 1548,5 ± 29,4 |
| Mujer | 40-49 | 228 | 111,1 ± 13,8 | 1547,3 ± 32,1 |
| Mujer | 50-59 | 519 | 105,2 ± 12,9 | 1537,3 ± 28,0 |
| Mujer | 60-69 | 756 | 95,4 ± 11,7 | 1520,8 ± 23,0 |
| Mujer | 70-74 | 161 | 90,2 ± 11,7 | 1507,6 ± 20,5 |

Cálculo automático de puntajes **Z** (ajustado por edad/sexo) y **T** (comparado contra adulto joven 20-29 años del mismo sexo):

```
Z = (valor − media_grupo_edad) / DE_grupo_edad
T = (valor − media_grupo_20_29) / DE_grupo_20_29
```

- **Criterio OMS sobre T-score**: `T > -1,0` Nominal · `-2,5 < T ≤ -1,0` Osteopenia · `T ≤ -2,5` Osteoporosis.

### 2. Módulo de Cortisol Salival (Ritmo Circadiano CLIA/ECLIA)

Evalúa muestras de cortisol salival ajustando dinámicamente la mediana esperada según la **hora exacta** de toma:

```
z = (ln(valor) − ln(mediana(hora))) / σ_ln        Nominal |z| ≤ 1,28 · Precaución ≤ 1,96 · Alerta > 1,96
```

- Ancla matutina (n = 56): mediana `0,474 µg/dL` (`σ_ln = 0,511`); ancla nocturna `0,155 µg/dL` con interpolación log-lineal entre 07:30 y 21:30.
- Conversión automática entre **µg/dL** y **nmol/L** (`÷ 27,59`).
- Incluye verificación de piso del ensayo pos-11:00, control externo p95 (Roche Cortisol II), razón vespertina/nocturna (15:30/21:00), basal individual con ≥ 3 muestras y alerta cruzada con pérdida ósea. Especificación completa en [docs/cortisol-spec.md](docs/cortisol-spec.md).

### 3. Módulo de Radiación Espacial (Dosimetría TEPC)

Construido sobre telemetría real de contador proporcional equivalente a tejido (`_local/data_radiacion.csv`, 1.441 muestras de 60 s). Evalúa la exposición en tres capas jerárquicas:

- **Capa A · Instantánea**: `≤ P95` Nominal · `P95–P99` Precaución · `> P99` Alerta (requiere 3 lecturas consecutivas para evitar falsos positivos por picos transitorios).
- **Capa B · Diaria**: dosis acumulada en 24 h frente a referencia diaria.
- **Capa C · Acumulada de Misión y Carrera**: calcula `F30 = H30 / 250 mSv` (límite de 30 días) y `F_carrera = (dosis_previa + misión + proyección) / 600 mSv`. Especificación en [docs/radiation-spec.md](docs/radiation-spec.md).

### 4. Módulo de Salud Mental y Carga Alostática (ALI)

Batería psicométrica y neuroconductual interactiva libre de hardware invasivo:

- **NASA-TLX**: carga de trabajo subjetiva en 6 dimensiones con seguimiento EWMA frente a referencia de Grier.
- **Chequeo Diario de Ánimo (CDA / DMRS)**: 10 ítems afectivos con línea base móvil de 14 días.
- **Arquitectura de Sueño**: eficiencia de sueño (TIB/TST/SE), índice de regularidad (SRI) y deuda acumulada de 7 días.
- **PVT-B Interactivo**: test de vigilancia psicomotora de 60/180 s para cuantificar lapsos de atención, falsos inicios y fatiga objetiva frente a percepción subjetiva. Especificación en [docs/mental-spec.md](docs/mental-spec.md).

---

## Contratos de la API REST

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/health` | Estado operativo del servicio y conexión a base de datos |
| GET | `/api/v1/meta` | Metadatos del modelo, umbrales, unidades, sitios e idiomas |
| GET | `/api/v1/astronauts` | Lista de astronautas activos y archivados |
| POST | `/api/v1/astronauts` | Alta de tripulante (`{"code","name","sex","birth_date"}`) |
| PATCH | `/api/v1/astronauts/{code}` | Actualización de perfil demográfico |
| GET | `/api/v1/astronauts/{code}/measurements?site=` | Historial de sesiones ultrasónicas |
| POST | `/api/v1/astronauts/{code}/measurements` | Registro de nueva medición ósea |
| POST | `/api/v1/astronauts/{code}/preview` | Simulación previa al guardado (paso 3 del asistente) |
| POST | `/api/v1/astronauts/{code}/measurements/import` | Importación masiva de archivos (CSV/XLSX/JSON) |
| GET | `/api/v1/astronauts/{code}/monitoring?site=&window=&lang=` | Serie evaluada, BV/TV, Z/T-scores y nivel de triaje |
| POST | `/api/v1/astronauts/{code}/cortisol` | Registro y evaluación circadiana de muestra de cortisol |
| GET | `/api/v1/astronauts/{code}/cortisol?days=` | Serie histórica de cortisol, razón tarde/noche y basal |
| POST | `/api/v1/astronauts/{code}/cortisol/import` | Importación masiva de muestras de cortisol |
| GET | `/api/v1/astronauts/{code}/radiation` | Lecturas TEPC + evaluación por capas A/B/C + proyección |
| POST | `/api/v1/astronauts/{code}/radiation` | Registro de lectura dosimétrica (UTC) |
| GET | `/api/v1/astronauts/{code}/mental?days=` | Serie diaria EWMA, índice de carga alostática (ALI) y zona |
| PUT | `/api/v1/astronauts/{code}/mental/{date}` | Registro/actualización diaria de pruebas cognitivas y ánimo |

---

## Formato de Importación Masiva

Soporta archivos **CSV**, **XLSX** y **JSON** con validación fila por fila (las filas corruptas se reportan con número de línea sin abortar las filas válidas):

```csv
date,bua,uv,att,site
2026-07-01,118.0,1552,52,calcaneus
2026-07-31,77.5,1556,51.6,calcaneus
```

- Formatos de fecha admitidos: `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYY/MM/DD`, `DD-MM-YYYY`, `MM/DD/YYYY`.
- Sitios válidos: `calcaneus` (`calcáneo` / `talón`) y `femoral_neck` (`cuello femoral`).
- Archivos de prueba disponibles en la carpeta `examples/`.

---

## Calidad de Software y Estado del Proyecto

- **127 tests automatizados de backend** (reglas de dominio, tablas poblacionales, cortisol, radiación, salud mental y endpoints HTTP) y **4 suites de frontend** pasando en verde.
- Linter **Ruff** limpio, tipado **TypeScript estricto** y compilación de producción verificada.

Consultar [DEV.md](DEV.md) para comandos adicionales de mantenimiento y pruebas.
