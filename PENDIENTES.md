# Pendientes de Custos Legis Tarija

Priorizado el 2026-09-25 tras revisión objetiva. Regla: **un abogado real
antes que otro test**. Se retoma el 2026-09-26.

## A. Esta semana (antes que cualquier agente nuevo)

1. **Un abogado real usando el sistema con un caso real.** Hoy: 176
   aserciones verdes, 18 falsadores, **cero abogados**. El gate HITL nunca
   fue cruzado por un expediente de verdad.
2. **Motor de plazos visible.** Es la pieza más vendible y está enterrada en
   `plazos.py`. Un endpoint/UI mínima donde el abogado carga notificación +
   materia y ve su vencimiento día por día con fundamento. Eso se vende antes
   que un chat.
3. **Decidir la compuerta con el 17,3% sobre la mesa.** Opciones ya
   declaradas en ESTADO §10: (a) capa pública solo normativa + jurisprudencia
   tras login (la que el código ya implementa), (b) aprobar por matrícula en
   tandas, (c) reabrir todo con riesgo firmado. Hoy la compuerta protege un
   buscador que no toca: cablearla en el corpus o matarla como módulo
   separado.
4. **Apuntar `corpus_cliente.py` al contrato autenticado correcto.** Hoy
   `BASE = https://150448fcc6.abacusai.cloud` y `/buscar` público da 503 por
   diseño. Cuando corpus exponga API keys con scope, Custos debe ser el
   primer consumidor con key propia, no el endpoint público.
5. **Consolidar el nombre.** "Custos Legis" colisiona con el log HMAC de
   KAMPE IR. Decidir renombre o alias antes de que haya usuarios que lo
   aprendan.

## B. Después del piloto

6. Leer arts. Ley 548 (NNA) y 348 (violencia) para que la reserva legal
   tenga texto, no prudencia.
7. Confirmar tabla de plazos con arts. 252, 261 y 365 de la Ley 439 en la
   mano; el régimen "de momento a momento" del art. 264 Ley 1340 (identificado,
   no medido).
8. Medir recall de la compuerta contra texto real (hoy 9 fixtures, y el que
   escribió el detector eligió los fixtures: W-01).
9. Bind del backend del corpus (ya mitigado a loopback en producción, ver
   corpus-legal-tarija 2026-09-25-09): confirmar y cerrar el §9.11.

## C. NO hacer (anti-tareas, para no recaer)

- **No empezar el grafo LangGraph de 6 agentes** hasta que un abogado use el
   núcleo. Es la parte divertida y la trampa: en el corpus costó 33 commits
   sin mover el producto.
- **No agregar más falsadores** antes del primer usuario real.
- **No construir multi-bufete a fondo** (facturación, 200 tenants) para un
   piloto de 1-2 estudios.

## Convicción que guía el orden

La disciplina de Custos es ejemplar; su priorización era la trampa. Mejor
cimiento que Corpus y peor historia de uso. El próximo commit debería ser
una persona usándolo, no otro test.
