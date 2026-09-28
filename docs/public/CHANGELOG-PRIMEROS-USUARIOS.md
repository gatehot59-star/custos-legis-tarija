# Custos Legis, changelog para primeros usuarios

**Versión:** MVP piloto 0.1.0, candidato de integración  
**Fecha:** 27 de septiembre de 2026  
**Estado:** listo para revisión humana en el [PR #16](https://github.com/gatehot59-star/custos-legis-tarija/pull/16)

## Qué llega

Custos Legis ya tiene un flujo vertical completo para transformar un documento jurídico en un borrador revisable:

1. Carga del documento y cálculo de su hash.
2. Investigación con citas y procedencia visible.
3. Cálculo de plazo asociado al caso.
4. Generación de borrador.
5. Verificación automática de citas, vigencia, hash y plazo.
6. Aprobación humana obligatoria.
7. Exportación a DOCX únicamente después de la aprobación.

## Lo más importante para usarlo

**Custos no decide ni presenta escritos por su cuenta.** La exportación queda bloqueada hasta que una persona habilitada revise y apruebe el borrador exacto que se va a descargar.

La investigación separa evidencia legal de memoria operativa. Si falta respaldo suficiente, el sistema marca la respuesta como `limited` o `abstain` en lugar de presentar una certeza inventada.

## Búsqueda y contexto legal

- Búsqueda léxica BM25 para localizar pasajes.
- Grafo dirigido para seguir relaciones normativas explícitas sin invertirlas.
- Retrieval completo de la consulta cuando se usa el motor gráfico, con fallo cerrado si no puede demostrarse que se leyó todo el resultado.
- Cada cita conserva URL, fragmento, hash y estado de vigencia.

## Protección entre estudios

Las rutas nuevas reutilizan la sesión existente y comprueban el estudio y el caso antes de leer o escribir. La persistencia MVP usa PostgreSQL con aislamiento por `tenant_id` y RLS; las decisiones y eventos de auditoría son inmutables.

## Qué no promete todavía

Esto sigue siendo un piloto, no un producto de producción jurídica autónoma. Todavía no están certificados:

- búsqueda contra el Corpus público operativo en vivo;
- validación por abogado externo;
- almacenamiento binario definitivo de los PDF;
- operación multi-worker y despliegue productivo;
- calidad jurídica general o predicción de resultados;
- una plataforma de seis agentes autónomos.

## Cómo dar feedback útil

Para cada caso de prueba, enviar:

- qué se preguntó;
- qué documento y jurisdicción se usaron;
- qué cita o plazo parece incorrecto;
- qué debería haber ocurrido;
- si el problema bloquea el trabajo o solo requiere mejora.

No enviar datos personales ni escritos reales sin anonimizar. El piloto necesita casos representativos, pero la privacidad va primero.

## Verificación de esta versión

El head candidato `fa9b3c1` cerró con **8/8 checks verdes** en API, MVP HTTP, persistencia PostgreSQL, RLS, privacidad y plazos. El [PR #16](https://github.com/gatehot59-star/custos-legis-tarija/pull/16) todavía requiere revisión humana y CI del árbol exacto contra `main`; hasta entonces, esto es un candidato de integración, no una declaración de producción.
