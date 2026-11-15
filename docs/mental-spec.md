# Especificación · Módulo de salud mental

Derivado de `_local/salud_mental.md` (v1.1). Reemplaza el modelo anterior de diario M1–M8 + ALI. Se
compone de cuatro instrumentos interactivos, sin sensores, y un motor de seguimiento con semáforos
y prescripciones R1–R10.

## NASA-TLX posmisión

- Registro de tarea: descripción (3–300), categoría (8 opciones) y duración opcional.
- Seis escalas 0–100 en pasos de 5, sin valor por defecto:
  `MD`, `PD`, `TD`, `OP`, `EF`, `FR`.
- **15 comparaciones** de pares, en orden aleatorio distinto en cada sesión (modo `siempre`).
- `c_i` = veces elegida (0–5, suma 15); `w_i = c_i/15`.
- `TLX = Σ(v_i·c_i)/15`; `RTLX = Σv_i/6`; contribución `k_i = v_i·c_i/15`; dimensión dominante.
- Semáforo:
  - sesiones 1–5: verde ≤ 49.93, amarillo ≤ 68.00, rojo > 68.00 (Grier 2015).
  - desde la 6: `μ`/`σ≥5` de las 5 primeras, `z=(x−μ)/σ`, EWMA λ=0.3,
    `SE_t = σ√(λ/(2−λ)·[1−(1−λ)^{2t}])`, límites `μ+2SE`/`μ+3SE`; el peor de `z`, EWMA y TLX>68.
  - Aviso de subcarga si `TLX < 26.08`.

## Chequeo Diario de Ánimo (CDA)

- 10 ítems 0–10: 5 positivos (`animo`, `energia`, `motivacion`, `sueno`, `conexion`) y 5 negativos
  (`tension`, `tristeza`, `irritabilidad`, `estres`, `fatiga_mental`).
- `a_j` = valor o `10−valor`; `IAD = 10·media(a_j)`.
- Subíndices: afecto positivo, afecto negativo, estrés/fatiga, sueño y conexión.
- Provisional (<14 respuestas): verde ≥60, amarillo 40–60, rojo <40. Con línea base de 14 días:
  `MM7 ≤ μ−σ` o `z≤−2` o `IAD<40` o 3 días sin respuesta → amarillo; `MM7 ≤ μ−2σ`, `z≤−2` tres
  días seguidos o 7 días en amarillo → rojo.

## Sueño personalizado

- Perfil: horas necesarias, hora de despertar (UTC), ventana (min) y bloqueo.
- Registro matutino: entrada/salida del saco, latencia, despertares, WASO, causa A/B y subcausa,
  despertar final, calidad, inercia, sueños, descarte ambiental y siesta.
- `TIB = salida−entrada`; `TST = (despertar−entrada)−latencia−WASO`; `SE = 100·TST/TIB`;
  punto medio del sueño. SRI con ≥5 noches.
- Semáforos: TST (<5 h rojo, 5–6 h amarillo), tendencia de 3 noches, deuda de 7 días (≥7/≥14 h),
  `SE7<85 %`, desfase del punto medio ≥2 h. Noche con inercia ≥7 y descarte ambiental se excluye
  de la ventana.
- Ventana semanal: `SE7<85 %` → −15 min (piso 360), `>90 %` → +15 min (techo necesidad+30).

## PVT-B interactivo

- 60 s (rápido) o 180 s (validado); estímulo visual a intervalos aleatorios de 1–4 s; respuesta con
  clic o barra espaciadora.
- Válidos: RT ≥100 ms; lapso ≥355 ms; falsos inicios: respuesta antes del estímulo o RT <100 ms.
- `v = media(1000/TR)`; TR medio. Semáforo por `z_v` frente a la línea base (≥5 pruebas):
  `>−1` verde, `−2<z≤−1` amarillo, `≤−2` rojo; `σ` mínimo 0.209.
- Discrepancia si alerta subjetiva ≥7 y `z≤−1`.

## Prescripciones R1–R10

R1 eficiencia baja, R2 mente activa, R3 entorno, R4 inercia, R5 pesadillas, R6 alerta reducida,
R7 deuda de sueño, R8 desfase circadiano, R9 CO₂/ambiente, R10 discrepancia subjetiva. Cada una con
cápsula y acción concreta; se muestran en la pestaña Seguimiento.

## Persistencia y API

Tablas: `tlx_session`, `cda_day`, `sleep_profile`, `sleep_night`, `pvt_test`. Las tablas antiguas
(`mental_day`, `mental_task`) se eliminan en la migración.

```
GET  /api/v1/astronauts/{code}/mental
POST /api/v1/astronauts/{code}/mental/tlx
PUT  /api/v1/astronauts/{code}/mental/cda/{date}
GET/PUT /api/v1/astronauts/{code}/mental/sleep/profile
PUT  /api/v1/astronauts/{code}/mental/sleep/{date}
POST /api/v1/astronauts/{code}/mental/pvt
```

Todo en UTC. El color y las curvas se recalculan al leer.

## Límites

Herramienta de autorregulación y tamizaje; no es diagnóstico. El sueño es autoinformado (sin EEG) y
el modo PVT de 60 s no está validado clínicamente. Las alertas rojas no se comparten solas.
