# 14 · Cuenta Astra en línea y sitio v6 publicado

Fecha: 2026-10-25 ~22:35 ART (2026-10-26 ~01:35 UTC). Máquinas: brain-env (build y pruebas públicas) y corpus-vm (servicio).

## Qué quedó en línea

- Sitio v6: https://astra.icca-engine.com/ (index en origen 285.403 B, sha256 `3bbefd8f9dc6cf74eee24183f6cb59752a075ada07be69afd9b554030647da75`).
- Cuenta: https://astra.icca-engine.com/cuenta/ (registro, ingreso, panel, planes, reserva, pedido de acceso a Corpus, contacto, privacidad, exportar datos, baja).
- Gestión: https://astra.icca-engine.com/cuenta/gestion/ (cuenta de gestión para el correo de Abraham; el enlace de un solo uso para fijar la contraseña se entregó sólo por chat, nunca en git).
- La dirección vieja https://150448fcc6.abacusai.cloud/astra/ redirige 301 al dominio nuevo. Corpus Tarija sigue en su host, sin cambios.

## Arquitectura

- Servicio aparte `astra-cuenta.service` (Type=notify): gunicorn 23.0.0 en 127.0.0.1:8010, 2 workers, usuario de sistema `astra-cuenta`, ProtectSystem=strict, escritura sólo en `/var/lib/astra-cuenta`.
- Django 5.2.18 + WhiteNoise 6.12.0; SQLite en WAL (`/var/lib/astra-cuenta/cuenta.sqlite3`); límites de intentos en la tabla de caché `astra_limites`.
- Entorno en `/etc/astra-cuenta/entorno` (root:astra-cuenta 640). La clave de Django se generó en la VM y nunca se imprimió (86 caracteres).
- nginx `conf.d/astra-icca-engine.conf`: `/cuenta/` → 8010 con X-Real-IP tomado de CF-Connecting-IP sólo cuando la conexión llega del túnel local; `/fuentes/` con caché de 1 año; página 404 propia; http → https.
- `corpus-legal.conf`: cambiaron sólo 2 líneas (`/astra` y `/astra/` → 301 a https://astra.icca-engine.com/).
- Respaldos en `/var/backups/astra/`: `astra-icca-engine.conf.20261026T022610Z`, `corpus-legal.conf.20261026T022610Z`, `index.html.v5-20261026T022610Z`, `index.html.v6a-<TS>`.
- Código de la cuenta: 50 archivos, 121.775 B, en brain-env `/workspace/astra-cuenta/src` y en la VM `/opt/astra-cuenta/app` (copia verificada: 50 archivos).

## Cambio al sitio

- Tipografías propias: 14 woff2 en `/var/www/astra/fuentes/`; cada nombre lleva los primeros 8 hex de su sha256 y coinciden en la VM.
- `App.jsx`: Google Fonts sólo se pide si falta `<meta name="astra-fuentes" content="propias">` (vista previa). El sitio publicado lleva la marca. sha256 `a6cb448cb4fdf5aff2338a681f60d4a3b2dd19fceadd10c76b90b1c4c28bf640`, idéntico en brain-env y en la vista previa.
- Compilación reproducible: con el App.jsx anterior, el comando esbuild reprodujo exacto app.js `7312dadd360852ad` y app.css `839891fc9dba6770`. El app.js nuevo mide 219.099 B (`f90b89ac56ee02ac`); app.css no cambió.

## Cobro

- Mercado Pago Checkout Pro, apagado mientras `MP_ACCESS_TOKEN` esté vacío: los planes se reservan y no se cobra nada (`/cuenta/salud/` responde `"cobro": false`).
- Para encenderlo: access token de producción, secreto del webhook y precios por país (se cargan en gestión). Bolivia y Paraguay: dLocal más adelante.

## PASS

- 45/45 tests (ASTRA_PRUEBAS=1) en brain-env, después del arreglo de `aria-describedby` en `_campo.html`.
- `check --deploy`: sólo W005 y W021 (includeSubDomains y preload apagados a propósito).
- Migraciones aplicadas, 3 planes sin precio, 129 estáticos (387 post-procesados).
- En la VM: salud 200, http → 301 https, registro 200, CSS 200.
- Público: `/` 200 con la marca; fuente 200 `font/woff2`; `/cuenta/salud/` 200 con HSTS; `/cuenta/gestion/login/` 200; `/no-existe` 404 propia; `http://` 301 a https; viejo `/astra/` 301 al dominio nuevo; `/corpus/login/` 200; raíz vieja 401.
- Cookie `astra_csrf`: Secure, HttpOnly, SameSite=Lax, Path=/cuenta/.
- E2E público con una cuenta de prueba (`example.com`), formularios parseados del HTML servido: registro → `/cuenta/panel/` con saludo; exportación JSON 200 con el correo; baja con contraseña y confirmación; después `/cuenta/` redirige a ingresar. En la base: 1 usuario (gestión), 0 cuentas de prueba, 0 órdenes, 0 solicitudes; la limpieza de respaldo no encontró nada que borrar.
- Servicios activos después de todo: astra-cuenta, nginx, cloudflared-corpus, corpus-django-staging, corpus-api.

## FAIL

- Ninguno en lo medido.

## NO MEDIDO

- Cloudflare no entrega el HTML byte a byte: `/` llega con 285.770 B (sha `3697ff09…`) contra 285.403 B en origen, y `/no-existe` suma los mismos +367 B; `robots.txt` llega con 2.702 B (robots administrado de Cloudflare). Falta ver en el panel de Cloudflare qué función lo hace.
- En el panel, el correo de la cuenta de prueba no apareció en el HTML recibido (sí en la exportación JSON); compatible con la ofuscación de correos de Cloudflare, no verificado.
- Pago real con Mercado Pago (no hay token).
- Páginas de la cuenta en celular con emulación real (las capturas de 390 px salieron recortadas por el navegador sin cabeza).
- Que no salgan pedidos a Google en un navegador real: verificado por código (marca en el HTML y condición en el bundle), no con registro de red.
- Artefacto v7 de la vista previa sin guardar.
- Código de la cuenta todavía fuera de git; fila 14 del README pendiente.

## W-01

Las pruebas públicas salieron de brain-env a través de Cloudflare, no de la VM; los sha de origen se midieron en la VM con `sha256sum`. El E2E usa los formularios reales servidos al público, no los tests de Django.
