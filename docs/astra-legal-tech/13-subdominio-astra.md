# 13 · El sitio en astra.icca-engine.com

25-oct-2026, 22:10 ART (26-oct 01:10 UTC). Agente: BRAIN. Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-27817

## Pedido

Abraham: "TENGO UN DOMINIO ICCA.COM". Después: "¡Perfecto!" con una guía genérica para conectar Abacus.ai a un subdominio de icca-engine.com por Cloudflare.

## Lo medido antes de tocar nada

- icca.com no es de Abraham: registrado el 21-jun-2002 en GoDaddy, DNS de Efty (`ns1/ns2.eftydns.com`), y la página dice "icca.com domain name may be for sale · Price upon request".
- icca-engine.com sí: Namecheap, alta el 15-mar-2026, DNS en Cloudflare (`harvey`/`mariah.ns.cloudflare.com`), MX con reenvío de Namecheap. La raíz y www muestran el estacionamiento de Namecheap. No había registros `astra`, `astratech` ni `legal`, ni comodín (DoH: NXDOMAIN).
- La guía no aplica tal cual: la página no es una app de Abacus, la sirve nginx en la VM. Además pide "DNS only" (nube gris): con túnel de Cloudflare el CNAME tiene que ir Proxied (naranja).
- La VM ya tenía un túnel con nombre, `corpus-vm` (`02518b70-761d-441f-82be-10c65e27c38a`), con configuración local en `/home/ubuntu/.cloudflared/config.yml` y servicio `cloudflared-corpus` (binario `/home/ubuntu/cloudflared` 2026.10.3, corre como root). Llevaba sólo el SSH.
- En brain-env hay un certificado de origen de Cloudflare, `/tmp/cert.pem` (282 B, 22-sep-2026 00:55 UTC, root, modo 644). `cloudflared tunnel list` con ese certificado muestra `corpus-vm` y `mudh-mcp`; la API (sólo lectura) dice que su zona es `icca-engine.com`, activa, y que no existía ningún registro `astra`.

## Nombre

`astra.icca-engine.com`. No `astratech`: la marca es Astra Legal Tech.

## Cambios (todos con respaldo)

1. nginx en la VM: archivo nuevo `/etc/nginx/conf.d/astra-icca-engine.conf`. `server_name astra.icca-engine.com`; `root /var/www/astra`; `/` sirve `index.html`; `/astra` y `/astra/` van con 301 a `/`; `/corpus/` va con 302 a `https://150448fcc6.abacusai.cloud$request_uri` (Corpus queda en su host, sin tocarlo); cabeceras `nosniff`, `X-Frame-Options DENY`, `X-Robots-Tag noindex, nofollow, noarchive` y `Referrer-Policy strict-origin-when-cross-origin`. `corpus-legal.conf` no se tocó (respaldo igual en `/var/backups/astra/corpus-legal.conf.20261026T010411Z`). `nginx -t` OK, reload OK.
2. Túnel: regla nueva `astra.icca-engine.com → http://127.0.0.1:80` antes del `http_status:404` final. Respaldo `config.yml.bak-20261026T010411Z` (sha256 `89bb6aab88163ebdc419cfea5edace0713bb550eaafc92240cb44fe12c060456`); config nueva sha256 `6fc046577457c2c0345fb11598fd4f985841cda02a57a2473fb88aa61d3b2451`. `ingress validate` OK; `ingress rule`: astra → regla #1, corpus-vm → regla #0.
3. Reinicio del túnel con `systemd-run --on-active=5` (01:05:01 UTC) y vuelta atrás programada con `systemd-run --on-active=300` (restaurar el respaldo y reiniciar). El SSH volvió a las 01:05:29 y la vuelta atrás se canceló (`systemctl stop astra-cf-rollback.timer`). PID nuevo 34254; 4 conexiones (sea07, sea09, sea10, sea11).
4. DNS: `cloudflared tunnel --origincert /tmp/cert.pem route dns 02518b70-761d-441f-82be-10c65e27c38a astra.icca-engine.com` a las 01:09:52 UTC. API: `CNAME astra.icca-engine.com → 02518b70-761d-441f-82be-10c65e27c38a.cfargotunnel.com`, `proxied: true`.

## PASS

- `https://astra.icca-engine.com/` 200, 248.776 B, sha256 `0d4fc6e004b4…1773`, idéntico a `/var/www/astra/index.html` (v5); TLS válido (`ssl_verify_result 0`); igual forzando la IP de Cloudflare y por DNS público.
- `/corpus/login/` 302 a `https://150448fcc6.abacusai.cloud/corpus/login/`; `/astra/` 301 a `/`; `/no-existe` 404; las 4 cabeceras presentes.
- Host viejo intacto: `/astra/` 200, `/` 401, `/corpus/login/` 200.
- Después del reinicio: `cloudflared-corpus`, `nginx`, `corpus-django-staging` y `corpus-api` activos; config en uso = la nueva.

## FAIL

- Ninguno en este cambio. Siguen en FAIL los de la entrega 12: la cuenta (registro, ingreso, base de datos y cobro) no existe y la v6 no está publicada.

## NO MEDIDO

- `http://` sin s (la redirección a https depende de la configuración de la zona).
- Que ningún buscador la indexe: va con noindex, no se midió.
- Log de arranque del túnel: `journalctl -u cloudflared-corpus` no muestra entradas.

## Riesgo que queda

- `/tmp/cert.pem` en brain-env da control de DNS y túneles de icca-engine.com y es legible por cualquier usuario de esa máquina (644). Conviene moverlo a un lugar con permiso 600, o revocarlo en Cloudflare y volver a loguearse cuando haga falta. No se tocó.
- La dirección queda atada a ICCA. Para la marca, `astralegaltech.com` seguía sin registrar el 25-oct (RDAP de Verisign: 404); moverla es una regla de túnel y un CNAME más.

## Cómo deshacer

1. DNS: borrar el CNAME `astra` en el panel de Cloudflare de icca-engine.com.
2. Túnel: `cp -a /home/ubuntu/.cloudflared/config.yml.bak-20261026T010411Z /home/ubuntu/.cloudflared/config.yml` y reiniciar con `sudo systemd-run --on-active=5 /bin/systemctl restart cloudflared-corpus` (el reinicio corta el SSH unos segundos).
3. nginx: `sudo rm /etc/nginx/conf.d/astra-icca-engine.conf && sudo nginx -t && sudo systemctl reload nginx`.

## Lo que sigue

- Cuando exista la cuenta, la v6 se publica en las dos direcciones y `conexiones.js` pasa a usar `https://astra.icca-engine.com` para el sitio y la cuenta; Corpus sigue en su host.

## Método

- Herramientas: brain-env por MUDH Gateway (RDAP de Verisign, DoH de Cloudflare, curl; SSH a corpus-vm por el túnel; cloudflared 2026.8.3 con el certificado de origen; API de Cloudflare sólo para leer zona y registros); GitHub MCP para este archivo.
- Instrumentos que podían dar rojo: `nginx -t`; `cloudflared ingress validate` e `ingress rule`; sha256 del index servido contra el archivo de la VM; códigos HTTP del host viejo (`/` tenía que seguir en 401); la API para la zona del certificado (podía ser otra).
- W-01: BRAIN mide su propio cambio, con instrumentos externos al cambio (curl por Cloudflare y la API). Re-auditoría pendiente.
