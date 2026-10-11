# Montar el sitio en un VPS · fimnme.qumran.cc

El sitio es **estático**: Jekyll lo compila a la carpeta `sitio/_site/`, que
son solo archivos HTML, CSS, JavaScript, imágenes y PDF. No usa base de datos
ni PHP.

Todas las direcciones llevan el año de la edición:
`https://fimnme.qumran.cc/2026/`, `…/2026/programacion/`,
`…/2026/conciertos/…/`. Así, en el mismo dominio pueden convivir varias
ediciones (`/2026/`, `/2027/`…). La raíz (`https://fimnme.qumran.cc/`) solo
redirige a la edición actual. El año sale de `baseurl` en
`sitio/_config.yml`.

En el servidor hace falta:

1. que el dominio apunte al VPS;
2. un servidor web con HTTPS;
3. copiar ahí los archivos compilados, lo que hace `sitio/publicar.sh`.

Los pasos están pensados para Ubuntu o Debian. Donde dice `usuario`, va tu
usuario del VPS.

---

## 1. DNS

En el panel donde administras `qumran.cc`, crea un registro:

| Tipo | Nombre | Valor |
|---|---|---|
| `A` | `fimnme` | la IP (IPv4) del VPS |
| `AAAA` (si el VPS tiene IPv6) | `fimnme` | la IPv6 del VPS |

Comprueba que ya resuelve (puede tardar unos minutos):

```bash
dig +short fimnme.qumran.cc      # debe responder la IP del VPS
```

## 2. Paquetes en el VPS

```bash
sudo apt update
sudo apt install -y git rsync ruby-full build-essential zlib1g-dev
sudo gem install bundler
```

Ruby 3 o posterior basta (Ubuntu 22.04 o 24.04, Debian 12).

## 3. El repositorio

El repositorio es privado, así que el VPS necesita una **clave de despliegue**
(solo lectura):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/fimnme -N ""
cat ~/.ssh/fimnme.pub
```

En GitHub, en *jesarx/48fimnme → Settings → Deploy keys → Add deploy key*,
pega esa clave (sin marcar «Allow write access»). Después:

```bash
cat >> ~/.ssh/config <<'EOF'
Host github-fimnme
  HostName github.com
  IdentityFile ~/.ssh/fimnme
EOF
git clone git@github-fimnme:jesarx/48fimnme.git ~/48fimnme
```

Instala Jekyll para el sitio y la gema de los códigos QR de la página de
descargas (quedan dentro de `sitio/vendor/`, sin tocar el sistema):

```bash
cd ~/48fimnme/sitio
bundle config set --local path vendor/bundle
bundle install
```

## 4. Carpeta pública y primera publicación

```bash
sudo mkdir -p /var/www/fimnme.qumran.cc
sudo chown "$USER": /var/www/fimnme.qumran.cc
~/48fimnme/sitio/publicar.sh /var/www/fimnme.qumran.cc
```

`publicar.sh` compila el sitio y lo copia en `/var/www/fimnme.qumran.cc/2026/`
con `rsync --delete`: esa carpeta queda idéntica a `sitio/_site/2026/`. En la
raíz deja la redirección a `/2026/` (`index.html`) y el `robots.txt`. No toca
nada más de la raíz, así que otras ediciones no se ven afectadas.

## 5. Servidor web con HTTPS

Elige **una** de las dos opciones.

### Opción A · Caddy (la más sencilla: el certificado HTTPS es automático)

Úsala si en el VPS no hay otro servidor web en los puertos 80 y 443.

```bash
sudo apt install -y caddy
```

Pon esto en `/etc/caddy/Caddyfile`. Si ya hay otros sitios, agrega el bloque
al final.

```caddy
fimnme.qumran.cc {
	root * /var/www/fimnme.qumran.cc
	encode zstd gzip
	file_server
	header /2026/assets/* Cache-Control "public, max-age=604800"
	handle_errors {
		rewrite * /2026/{err.status_code}.html
		file_server
	}
}
```

```bash
sudo systemctl reload caddy
```

### Opción B · Nginx + Certbot

Úsala si el VPS ya sirve otros sitios con Nginx.

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo tee /etc/nginx/sites-available/fimnme.qumran.cc > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name fimnme.qumran.cc;

    root /var/www/fimnme.qumran.cc;
    index index.html;
    error_page 404 /2026/404.html;

    location / {
        try_files $uri $uri/ =404;
    }
    location /2026/assets/ {
        expires 7d;
        add_header Cache-Control "public";
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
EOF
sudo ln -s /etc/nginx/sites-available/fimnme.qumran.cc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d fimnme.qumran.cc     # certificado HTTPS (se renueva solo)
```

### Cortafuegos

Si usas `ufw`:

```bash
sudo ufw allow 80,443/tcp
```

## 6. Comprobar

Abre <https://fimnme.qumran.cc>: debe llevarte a
<https://fimnme.qumran.cc/2026/>. Revisa la portada, la programación, una
página de concierto y las descargas. Desde la terminal:

```bash
curl -I https://fimnme.qumran.cc/2026/programacion/   # debe responder 200
curl -I https://fimnme.qumran.cc/2026/no-existe/      # debe responder 404 (con la página de error del sitio)
```

Mientras sea de prueba, el sitio pide a los buscadores que **no lo indexen**
(`indexar: false` en `_config.yml`, con `robots.txt` y `<meta name="robots">`).

---

## Actualizar el sitio

Cada vez que cambie el programa:

1. **En tu computadora:** corrige `fimnme2026-programa.md` y ejecuta
   `./compila.sh`. Regenera los PDF y también el contenido del sitio. Luego
   haz commit y push.
2. **En el VPS:**

   ```bash
   cd ~/48fimnme && git pull && sitio/publicar.sh /var/www/fimnme.qumran.cc
   ```

Si en tu computadora también tienes Jekyll, puedes publicar desde ahí, sin
`git pull` en el servidor (por SSH):

```bash
sitio/publicar.sh usuario@IP-del-VPS:/var/www/fimnme.qumran.cc
```

Para revisar los cambios antes de publicarlos: `sitio/genera.sh --servir`
(los muestra en <http://localhost:4000/2026/>).

Si ya habías publicado una versión anterior **sin el año** en la dirección,
borra de la raíz lo que quedó de ella (todo menos `2026/`, `index.html` y
`robots.txt`):

```bash
cd /var/www/fimnme.qumran.cc
rm -rf 404.html assets coloquio conciertos creditos descargas programacion sedes
```

## Una nueva edición

Para la edición de 2027, en `sitio/_config.yml` cambia `baseurl` a `"/2027"`
y publica igual. El sitio nuevo queda en `/2027/` y la raíz pasa a redirigir
ahí. `/2026/` se queda como está, mientras no se vuelva a publicar con
`baseurl: "/2026"`. En Caddy o Nginx, cambia `2026` por `2027` en la página de
error y en la caché de `assets`.

## Pasar al dominio definitivo

Cuando el sitio quede aprobado en `forodemusicanueva.inba.gob.mx`:

1. En `sitio/_config.yml`, cambia `url` a `"https://forodemusicanueva.inba.gob.mx"`
   e `indexar` a `true`. Haz commit. Los códigos QR de la página de descargas
   se generan al compilar con ese `url`: al publicar de nuevo ya apuntan al
   dominio definitivo (si antes se imprimió alguno con el de prueba, conviene
   la redirección del paso 3).
2. Hay dos caminos:
   - **Si el sitio se queda en este VPS:** el registro DNS del dominio (lo
     administra el INBAL) debe apuntar a su IP. Después repite el paso 5 con el
     nuevo dominio (en Caddy, cambia el nombre del bloque; en Nginx,
     `server_name` y `certbot -d`). Publica con `publicar.sh` en la carpeta
     nueva.
   - **Si el sitio lo aloja el INBAL:** basta entregar el contenido de
     `sitio/_site/` ya compilado (la carpeta `2026/` y la redirección de la
     raíz). Son archivos estáticos que sirve cualquier servidor (Apache,
     Nginx, IIS).
3. Opcional: redirige el dominio de prueba al definitivo.
   - En Caddy:

     ```caddy
     fimnme.qumran.cc {
     	redir https://forodemusicanueva.inba.gob.mx{uri} permanent
     }
     ```

   - En Nginx: `return 301 https://forodemusicanueva.inba.gob.mx$request_uri;`

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| `bundle install` falla al compilar extensiones | Faltan `build-essential` o `zlib1g-dev` (paso 2). |
| El certificado no se emite | El DNS aún no apunta al VPS (`dig +short fimnme.qumran.cc`), o los puertos 80 y 443 están cerrados. |
| `/2026/programacion/` da 404 pero la portada abre | El servidor no busca `index.html` dentro de las carpetas: en Nginx falta `try_files $uri $uri/ =404;`. |
| Páginas sin estilos o enlaces rotos | El contenido de `sitio/_site/2026/` se copió en la raíz del dominio y no en `/2026/`. `publicar.sh` lo copia bien. |
| `publicar.sh` dice que no encuentra Jekyll | Falta `bundle install` en `sitio/` (paso 3). |
