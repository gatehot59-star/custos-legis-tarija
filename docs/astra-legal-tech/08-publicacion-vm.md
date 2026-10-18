# 08. Sitio web v3 publicado en la VM

Estado al 16-oct-2026 22:05 ART: **publicado en https://150448fcc6.abacusai.cloud/astra/** (vista previa con noindex, no es el dominio definitivo).

## 1. Pedido (Abraham, 16-oct)

- 18:27: "qué hiciste. dame el link de la página web. podrías haber montado en el vm"
- 18:34: "la página web que te pedí despliega en vm"
- 20:44: "Pero tú la debes subir a través de brain-env"
- 21:53: "El túnel estaba abierto. Si no lo está tiene los instrumentos en brain para abrirlo. También hay documentación específica dejada en nexus y en git de cómo tú puedes abrir el túnel"

Lectura: "la VM" es corpus-vm (Abacus), la que ya sirve Corpus Django. "El túnel" es el acceso SSH por Cloudflare Access desde brain-env, documentado en Nexus (mensajes 195 a 223) y en git (mudh-mobile, docs/agents/respuestas/2026-09-23-01-corpus-django-desplegado-en-vm-y-acceso.md, commit 9880a4a).

## 2. Herramientas declaradas

- Nexus (sqlite, solo lectura): mensajes 195 a 223 y bitácora 153 y 158.
- GitHub MCP (lectura): el recibo 2026-09-23-01 de mudh-mobile. Escritura: este archivo y el README, sólo en esta rama.
- brain-env (servicio build): write_file de las 11 fuentes del artifact v3; npm install de react 18.3.1, react-dom 18.3.1, esbuild 0.27.2 y tailwindcss 3.4.18 (79 paquetes, registro público de npm); compilación; SSH a la VM por cloudflared access.
- VM corpus-vm (por SSH, con sudo): /var/www/astra/ nuevo y un cambio en el vhost de nginx.
- Sandbox de ClickUp: recompilación con las mismas versiones y render en Chromium.
- fetch_website de ClickUp: control desde afuera.
- Relay de ClickUp: se generaron 2 enlaces temporales para el zip del sitio; los dos vencieron sin usarse (403). El sitio no pasó por ahí.
- Servicio playwright del gateway: falló (ECONNREFUSED 127.0.0.1:9225), no se usó.
- No se abrió ningún túnel rápido (trycloudflare): nada más quedó expuesto.
- Sin cuota ajena.

Acción delicada: SÍ. Cambio en el vhost de nginx de una VM compartida (backup, nginx -t, reload) y una ruta pública nueva.

## 3. Qué se hizo

1. Fuentes: las 11 fuentes del artifact v3, escritas en /workspace/astra-sitio/fuente/src de brain-env. 11 de 11 con el mismo sha256 que el artifact. No hubo transferencia de archivos desde ClickUp.
2. Compilación en brain-env: Tailwind base (el mismo preflight que usa el artifact) + site.css + React 18.3.1, en un solo index.html de 210.701 bytes. lang="es", título y descripción para la vista previa de WhatsApp, noindex.
3. VM: index.html copiado por SSH y verificado por sha256, instalado en /var/www/astra/index.html. En /etc/nginx/conf.d/corpus-legal.conf se agregaron 2 líneas después de /gold-images/:

```nginx
    location = /astra { absolute_redirect off; return 301 /astra/; }
    location ^~ /astra/ { auth_basic off; alias /var/www/astra/; index index.html; autoindex off; }
```

   Hereda del vhost X-Content-Type-Options nosniff, X-Frame-Options DENY y X-Robots-Tag noindex. Las rutas viejas no se tocaron.

Rollback (un comando):

```sh
sudo cp -a /etc/nginx/corpus-legal.conf.bak-20261017T005656Z /etc/nginx/conf.d/corpus-legal.conf && sudo nginx -t && sudo systemctl reload nginx
```

## 4. Qué se midió (instrumentos que podían dar rojo)

- Fuentes: sha256 de cada archivo contra el artifact v3 (un byte distinto daba DISTINTO y cortaba la compilación).
- Copia a la VM: sha256 en la VM contra el local antes de instalar.
- nginx -t antes del reload; si fallaba, se restauraba el backup.
- Público desde brain-env: /astra/ 200 con los mismos bytes; /astra 301 a /astra/. Regresión: /corpus/login/ sigue en 200 y / sigue en 401.
- Desde afuera (fetch_website de ClickUp): /astra/ "Failed to fetch content" y /corpus/login/ leída completa. Control positivo: el host se alcanza desde afuera. La página de Astra no tiene texto sin JavaScript, que ese lector no ejecuta.
- Recompilación independiente en el sandbox de ClickUp (mismas fuentes y versiones): index.html idéntico byte a byte (6e9c458d...). Ese archivo, abierto en Chromium a 1440x900 y 390x844: título y lang correctos, 6 estrellas, 7 tarjetas, ventana de Corpus Tarija abierta con #corpus, sin desborde horizontal. Únicos errores: las fuentes de Google, bloqueadas a propósito en el sandbox.

## 5. Evidencia cruda

Fuentes en brain-env:

```text
App.jsx            13141 be11744b0ce02e4b IGUAL
Asterisco.jsx        687 0bfe28ba7982e019 IGUAL
Cielo.jsx            944 842dd7ea18199be4 IGUAL
Constelacion.jsx    2488 c560ee39e7691e44 IGUAL
Contenidos.jsx      8672 00038a542f598ad7 IGUAL
Foja.jsx            4789 d37d0f37f8fea03a IGUAL
Ventana.jsx         2922 05296921b1afa5f5 IGUAL
asterisco.svg        588 0a6ecd7f33070342 IGUAL
data.js             4588 1559b4ee04e33cfd IGUAL
productos.js        5025 5ab0142426ae070b IGUAL
site.css           34352 1be71a0c2ee31348 IGUAL
FUENTES_DISTINTAS 0
build/app.css 29138 5e27f56d7a913158
build/app.js 174950 2a8c471a9d5932c9
build/base.css 4754 12d581958854d790
public/index.html 210701 bytes sha256 6e9c458db6a73290de086d25b461b074dd37021534cfa016430fc5dca1f3b60b
```

VM antes del cambio (2026-10-17T00:56:05Z):

```text
vm
 00:56:04 up 2 days, 52 min,  2 users,  load average: 0.20, 0.22, 0.20
nginx active
corpus-api active
corpus-django-staging active
cloudflared-corpus active
SUDO_OK
publico / HTTPError 401
publico /corpus/login/ 200 7309
publico /astra/ HTTPError 404
```

Despliegue:

```text
subida exit 0 6e9c458db6a73290de086d25b461b074dd37021534cfa016430fc5dca1f3b60b  /tmp/astra-index.html
6e9c458db6a73290de086d25b461b074dd37021534cfa016430fc5dca1f3b60b  /var/www/astra/index.html
BACKUP /etc/nginx/corpus-legal.conf.bak-20261017T005656Z
87a7e1cac78e227b264495bf976b3441040da441eff77b9c85744037ba6259ff  /etc/nginx/conf.d/corpus-legal.conf
87a7e1cac78e227b264495bf976b3441040da441eff77b9c85744037ba6259ff  /etc/nginx/corpus-legal.conf.bak-20261017T005656Z
INSERTADO
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
RELOAD_OK
48652aa810c512f2c21c5e7d966617e4e523ec5a052fe310ca59f52eb2ba62b1  /etc/nginx/conf.d/corpus-legal.conf
17:    location = /astra { absolute_redirect off; return 301 /astra/; }
18:    location ^~ /astra/ { auth_basic off; alias /var/www/astra/; index index.html; autoindex off; }
active
active
active
publico /astra/ 200 210701 sha256 6e9c458db6a73290 IGUAL | X-Robots-Tag=noindex, nofollow, noarchive | type=text/html; charset=utf-8
publico /astra 301 Location=/astra/
publico /corpus/login/ 200 7309
publico / 401 Location=None
```

Recompilación y render en el sandbox de ClickUp:

```text
index.html 210701 6e9c458db6a73290de086d25b461b074dd37021534cfa016430fc5dca1f3b60b IGUAL AL PUBLICADO
escritorio {"titulo":"Astra Legal Tech · Inteligencia que rinde cuentas","lang":"es","estrellas":6,"tarjetas":7,"h1":"Inteligenciaque rindecuentas.","ancho":1440}
ventana Corpus Tarija #corpus
celular {"titulo":"Astra Legal Tech · Inteligencia que rinde cuentas","lang":"es","estrellas":6,"tarjetas":7,"h1":"Inteligenciaque rindecuentas.","ancho":390}
errores 2 ["escritorio console Failed to load resource: net::ERR_FAILED","celular console Failed to load resource: net::ERR_FAILED"]
```

## 6. Archivos generados

- VM: /var/www/astra/index.html (210.701 bytes, sha256 6e9c458d...) y el vhost (antes 87a7e1ca..., después 48652aa8...; backup en /etc/nginx/corpus-legal.conf.bak-20261017T005656Z).
- brain-env: /workspace/astra-sitio/fuente (fuentes, package.json, entrada/main.jsx, base.css, tailwind.config.js, build/) y /workspace/astra-sitio/public/index.html.
- En git sólo este registro: el HTML compilado es un binario derivado y se reproduce desde las fuentes del artifact v3.

## 7. NO MEDIDO

- Un navegador real fuera de la máquina de Abraham abriendo /astra/ con JavaScript. Pendiente: que Abraham la abra desde el celular.
- Si la VM queda encendida siempre (Always On de Abacus): si se apaga, el sitio se cae con ella.
- La carga de las fuentes de Google en la URL real (en el sandbox se bloquearon).
- contacto@astralegaltech.com no existe: el botón de correo rebota hasta crear el buzón.
- La dirección es de Abacus, no astralegaltech.com. Definitivo: registrar el dominio y apuntarlo.
- W-01: BRAIN compiló, desplegó y verificó. La recompilación en el sandbox es otra máquina, pero el mismo agente.

## 8. Hallazgo lateral

La pantalla de acceso del piloto (/corpus/login/, leída desde afuera) dice "reúne la legislación nacional y departamental". COBERTURA.md (3-sep) dice que faltan las leyes nacionales. Es el mismo punto del convenio (07): NO MEDIDO si se agregaron después.
