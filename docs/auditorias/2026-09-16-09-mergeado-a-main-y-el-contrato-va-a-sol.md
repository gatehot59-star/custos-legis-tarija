# Mergeado a main, y la pregunta del contrato pasa a Sol

**2026-09-16.** Abraham me delegó el merge, que hasta hoy era suyo, y decidió que la pregunta abierta del contrato la responda el auditor Sol. Las dos cosas quedan escritas acá.

## El orden del merge no fue casual

Había dos PR apilados: el #1 con los cuatro defectos, y el #2 (de Sol) con la regresión permanente contra el falso positivo del falsador.

**El head del PR #1 (`e2fe70b`) no tenía checks propios.** Lo había medido Sol en su reauditoría y es cierto: los verdes que yo citaba eran de `30da4fc` (api-e2e) y `89569d4` (los otros tres jobs), commits **vecinos**. Mergear a `main` con eso habría sido declarar medido lo que no lo estaba, que es exactamente el defecto que este PR entero vino a corregir.

Así que el orden fue:

1. **PR #2 → rama del PR #1**, no directo a main. Eso genera el árbol combinado, que es *exactamente* lo que iba a entrar.
2. Esperar **su** CI: `d349ee8` → **5 checks success** (`api-e2e` x2, `plazos`, `privacidad`, `rls`).
3. **PR #1 → main**, ya con el árbol verificado.
4. Verificar main.

## Lo medido

| qué | resultado |
|---|---|
| árbol combinado `d349ee8` | **5 checks success** |
| `main` = `4a14f06` | **4 checks success** |
| sha de main, por API y por clon local | **coinciden** |
| PR #1 y #2 | `merged=True` |

Contenido de main verificado por **estructura, no por grep de palabras**: la llamada real a `_mismo_caso` aparece 1 vez, la función existe, la regresión del falsador está, la migración del borrado está, el guard de experimento contaminado está en **los dos** falsadores, y el `grep -q 'ROJO CASO'` amplio **ya no existe** en el árbol.

La regresión de Sol corre contra main clonado: **7/7**.

## MERGEAR NO ES DESPLEGAR

Y lo dejo escrito para que nadie lo confunda después. `main` no corre en ninguna máquina. El endpoint de acciones externas sigue devolviendo `AUTORIZADA_PERO_NO_EJECUTADA`: **no hay integración con SIREJ/SIGC ni firma digital, y no se simula**. No se tocaron credenciales ni permisos de producción.

## La pregunta que ya no es mía

Veniámos declarando NO MEDIDO el **contrato de una acción externa sin `case_id`**. Hoy el gate exige que la aprobación tampoco tenga caso (`None` solo matchea `None`): es el lado seguro, pero es **un default mío, no una decisión de producto**.

Abraham la asignó a Sol. El encargo (mensaje 212 del buzón) pide cinco cosas: la decisión en una línea, el fundamento normativo **con fuente verificada**, qué reemplaza al caso como ámbito de la aprobación si la respuesta es sí, si el gate debería devolver 400 en vez de 403 si es no, y qué se rompe con cada opción.

Con dos límites explícitos: que **no toque el producto** (si su decisión implica código, va en PR aparte y lo revisa otro), y que **no responda de memoria** sobre la Ley 387 ni el CPP. Y una salida honesta declarada: si su conclusión es que esto lo tiene que contestar un abogado con matrícula y no un agente, **esa también es una respuesta válida** y la quiero escrita, no rellenada con una inferencia para no entregar vacío. Es lo mismo que hice yo con el borde contradictorio del art. 130 CPP: devolver incertidumbre en vez de una fecha creíble y equivocada.

## Sigue NO MEDIDO

- Corpus vivo, TLS/proxy, producción, concurrencia, arranque como servicio.
- La tabla de plazos por acto sigue marcada `HIPOTESIS`: se verificó el art. 130 para el arranque cautelar, no toda la legislación.
- Que un fallo **real** de PostgreSQL en la creación del expediente produzca la trayectoria que Sol y yo medimos por inyección. Los dos medimos el consumidor de resultados, no la causa.
- Un testigo que no sea yo **ni** Sol. El CI de GitHub es evidencia externa, pero los instrumentos los escribimos nosotros.
