# 15 · Sitio v7 en astra.icca-engine.com (26-oct-2026, 00:18 ART)

Doc de ClickUp: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-27857
Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=7
Para verlo sin la copia vieja del navegador: https://astra.icca-engine.com/?v=7

## Pedido

Abraham, 25-oct 23:57 ART: "el link que me diste parece ser de v5, no v6. No tiene botón para logearse ni nueva vista distinta a la anterior ni todo lo otro que te solicité".

## Diagnóstico

1. Caché del navegador. El index v5 se servía con Last-Modified 18-oct-2026 02:58 UTC y sin Cache-Control. El navegador lo considera fresco el 10% de su edad: unas 19 horas desde que Abraham abrió el link (25-oct 22:10 ART). Medido: fecha del respaldo index.html.v5-20261026T022610Z y encabezados de nginx. NO MEDIDO: su teléfono.
2. En celular, Ingresar era sólo un ícono: regla de v6 bajo 560 px (`.cab-ingresar span { display: none }`).
3. v6 usaba la base visual de v5 (site.css de v5 + una cola v6): cambió el contenido, no el primer vistazo.

## Qué cambia

- Cabecera, héroe y pie de noche austral (#120F33) con el cielo del sur (Cielo.jsx, semilla 1991) y la Cruz del Sur con el asterisco de Astra.
- Ingresar y Crear cuenta con texto en todos los anchos (360 px incluido) y también en el héroe.
- Franja "Las citas de esta página salen de": Parlamento del MERCOSUR, Presidência da República · Brasil, Portal oficial del MERCOSUR.
- Sección Tu cuenta: registro con correo, pago con Mercado Pago cuando se habilita por país, descarga y borrado de datos, con muestra del panel.
- Acción en violeta de sello (#4A2DA0; #6A4BE0 sobre la noche). Pie: "Sitio v7 · 26/10/2026". Meta astra-version.
- Todo el contenido de v6 sigue; Corpus Tarija en su propia pestaña; 0 apariciones de "Argentina".
- nginx: `map $uri $astra_cache` → HTML con `Cache-Control: no-cache, no-transform`; /cuenta/ con `no-transform`.

## Fuentes y build

- v7 = fuentes del artifact v6 + `editar_v7.py` (sha c42044b2) + `cola-v7.css` (6cdc93b1) + `Cielo.jsx` (89e0d065). 21 de 21 sha256 iguales entre el sandbox y brain-env.
- App.jsx c4e2d536 · data.js 911587c8 · Iconos.jsx a9375df8 · site.css 2a0d0ef6 · resto igual a v6.
- esbuild: app.js 222.734 B (dce0a40c), app.css 54.916 B (f1d3b708). index 295.594 B, sha256 53a50e1bb71b38c060531bcaf72c0375c039e53aedd55fd770e10bf90769cf5f.
- Conf nginx nueva: 2.503 B, sha256 64a39b53668fb0e988829ef6b5de1ad34a3e598dcd917c1be7adaa3a4e7c8815.

## Publicación

- 26-oct 03:18:44 UTC: respaldo `/var/backups/astra/index.html.v6b-20261026T031844Z` y `/var/backups/astra/astra-icca-engine.conf.20261026T031844Z`; conf instalada; `nginx -t` OK; recarga; index instalado (root:root 644).
- Deshacer: copiar los dos respaldos a su lugar, `nginx -t`, recargar nginx.

## Resultado

PASS
- Público = origen: / y /?v=7 dan 295.594 B con sha 53a50e1b (antes Cloudflare agregaba 367 B); 404 propio = origen.
- Encabezados: HTML `no-cache, no-transform`; /cuenta/ `no-store` + `no-transform`; tipografías `max-age=31536000`.
- Chromium 153 (Playwright en brain-env) contra el sitio real: en 390, 360 y 1280 px Ingresar y Crear cuenta visibles con texto (360 px: 135-218 y 228-340), ancho del documento = ancho de pantalla, cabecera y héroe rgb(18,15,51), 11 tipografías propias cargadas, 7 pedidos y 0 a terceros, sin "Argentina". Ingresar de la cabecera → /cuenta/ingresar/ con email y clave.
- Cuenta en navegador real (390 px): crear cuenta desde la cabecera → panel con "Hola" y el correo visible, sin ofuscar → salir → el panel pide ingresar → ingresar con la misma clave → mis-datos JSON con el correo → eliminar ("Borramos tu cuenta y tus datos") → volver a ingresar falla ("El correo o la contraseña no coinciden").
- Base después: 1 usuario (gestión), 0 de prueba, 0 órdenes, 0 solicitudes. Servicios activos: nginx, astra-cuenta, cloudflared-corpus. /astra/ viejo → 301; /corpus/login/ 200.

FAIL
- Primera corrida de la prueba de cuenta: el selector genérico apretó el formulario Salir de la cabecera en vez de Eliminar; quedó un usuario de prueba (qa-v7-032207@example.com). Borrado con el ORM en la VM; la segunda corrida, con selectores por campo, dio bien.

NO MEDIDO
- Lo que muestra el teléfono de Abraham (caché propia).
- Cobro real: sigue apagado hasta cargar MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET y los precios por país.
- Filas 14 y 15 del README de esta carpeta: pendientes.

W-01: BRAIN verifica su trabajo con un instrumento distinto a la vista previa del artifact (Chromium contra el sitio público). Re-auditoría pendiente.
