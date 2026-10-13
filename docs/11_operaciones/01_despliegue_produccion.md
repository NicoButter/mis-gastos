# Auditoría y despliegue de Mis Gastos — 13 de octubre de 2026

## Alcance y resultados

Auditoría del checkout local. No se consultó ni modificó el VPS, su base real,
Nginx, systemd, SELinux o Google Cloud. No se ejecutaron comandos remotos, commits
ni push. No se cargó `.env` local ni se usaron credenciales reales para las pruebas.
La configuración efectiva del servidor requiere la revisión manual descrita abajo.
No hay configuración de Kinetra versionada en este proyecto para comparar.

| Importancia | Hallazgo | Corrección o intervención |
|---|---|---|
| Alta | Producción heredaba `backend/staticfiles`, incompatible con Nginx y el actualizador. | Default `/srv/misgastos/static`, con override `STATIC_ROOT` absoluto fuera del repositorio. Desarrollo mantiene su ruta. |
| Alta | `GASTIO_FRONTEND_URL` podía faltar y heredar `http://localhost:4200`, afectando login, logout y errores OAuth. | Producción exige origen HTTPS explícito y host permitido; recompone redirecciones. Ajustar `.env` antes de reiniciar. |
| Alta | El parser no decodificaba contraseñas URL y descartaba opciones de TLS. | Decodifica usuario, clave y nombre; conserva `sslmode`, `sslrootcert`, `sslcert`, `sslkey`, `connect_timeout`. Socket `host`/`port` sigue soportado. |
| Media | CORS obligatorio impedía iniciar un despliegue correcto con el mismo origen. | Listas vacías válidas; si se usan, exige orígenes HTTPS explícitos sin comodines. |
| Media | Hosts admitían comodines y orígenes de producción podían usar HTTP. | Validación al importar producción. |
| Media | HSTS habilitaba `includeSubDomains` y `preload` sin evidencia de necesidad. | Ambos deshabilitados; conserva `max-age=31536000` en este host. |
| Media | Media de producción también apuntaba dentro del repositorio. | Default `/srv/misgastos/media`; no hay endpoints actuales de uploads ni se agrega exposición pública. |
| Media | Dependencias con rangos y sin lock de producción. | No se cambian rangos durante esta corrección. Conservar inventario y ensayar actualizaciones antes de instalar. |
| Pendiente | No están versionados `refrescar_misgastos`, Nginx ni la unidad systemd. | Revisar sus archivos reales manualmente; no se inventa ni sustituye el script. |

`production.py` mantiene `DEBUG=False`, HTTPS obligatorio, cookies Secure,
sesiones en PostgreSQL, sesión HttpOnly, SameSite=Lax y cookies sin dominio
compartido. CSRF permanece activo. Angular usa rutas relativas `/api/v1/` y
`/accounts/`, manda cookies y `X-CSRFToken`; el inicio Google es POST con token
obtenido de `/api/v1/auth/csrf/`. No requiere cambios de frontend.

`config/urls.py` ya registra las rutas solicitadas. No sirve estáticos con Django
ni intercepta las rutas de la SPA. `wsgi.py` y `asgi.py` usan producción por defecto,
pero `manage.py` usa desarrollo: **es obligatorio establecer
`DJANGO_SETTINGS_MODULE=config.settings.production` en actualizador y servicio**.
Los scripts `setup.sh`, `dev-start.sh`, `run-backend.sh` y `run-worker.sh` son locales;
`dev-start.sh` migra la base indicada por `.env`. No usarlos en el VPS ni con un
entorno de producción. Redis/Celery no son necesarios para los endpoints actuales.

## Entorno externo

Referencia: [production.env.example](../production.env.example). Editar
`/srv/misgastos/.env` preservando los secretos existentes, no copiar el ejemplo
sobre él. No se carga automáticamente un dotenv: systemd debe usar su
`EnvironmentFile`, y el actualizador debe exportar el mismo entorno.
Restringir lectura al operador/servicio autorizado. No imprimirlo en logs.

Valores necesarios antes de publicar:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=misgastos.vetrabyte.com.ar
GASTIO_FRONTEND_URL=https://misgastos.vetrabyte.com.ar
STATIC_ROOT=/srv/misgastos/static
MEDIA_ROOT=/srv/misgastos/media
```

Conservar `DJANGO_SECRET_KEY`, `DATABASE_URL` y ambas credenciales Google existentes.
Codificar caracteres reservados en usuario/contraseña de la URL PostgreSQL
(`@` como `%40`, `:` como `%3A`, etc.). No confundir URL de Django con opciones
de libpq: un `pg_dump` no admite indiscriminadamente todos los esquemas/parámetros.
Usar credenciales libpq mediante `.pgpass` protegido o archivo de servicio dedicado,
fuera de Git, sin contraseña en argumentos ni logs.

`CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` pueden quedar vacíos para este
despliegue bajo el mismo origen. Si se conservan, usar
`https://misgastos.vetrabyte.com.ar`, nunca las URLs locales. No se requieren
`DATABASE_TEST_NAME`, Redis ni worker en producción. `GASTIO_TERMS_VERSION` sólo
debe fijarse a una versión aprobada/publicada; no se cambia en esta auditoría.

## Publicar el código desde el equipo local

Revisar y ejecutar estos comandos manualmente; no fueron ejecutados por Codex:

```bash
git status --short
git diff --check
git diff
git add backend/config/settings/base.py backend/config/settings/production.py backend/tests/test_settings.py backend/tests/test_production_settings.py .env.example README.md docs/production.env.example docs/07_seguridad/08_google_oauth.md docs/11_operaciones/01_despliegue_produccion.md
git commit -m "Fix production static paths and HTTPS deployment settings"
git push origin HEAD:main
```

El último comando supone que la rama revisada debe publicarse en `main` y que
el repositorio permite push directo. Si exige revisión, publicar una rama y
fusionarla por el proceso habitual antes de actualizar el VPS. Este cambio no
modifica Angular: no requiere compilación ni rsync del frontend.

## Revisión manual del VPS antes de actualizar

Comandos de lectura para ejecutar allí:

```bash
systemctl cat mis-gastos.service
systemctl show mis-gastos.service -p User -p Group -p WorkingDirectory -p EnvironmentFiles -p ExecStart
command -v refrescar_misgastos
git -C /srv/misgastos/app status --short
git -C /srv/misgastos/app branch --show-current
git -C /srv/misgastos/app remote -v
sudo nginx -t
getenforce
ls -Zd /srv/misgastos/app/backend /srv/misgastos/static /srv/misgastos/www
/srv/misgastos/venv/bin/python --version
/srv/misgastos/venv/bin/python -m pip check
pg_dump --version
```

Revisar la ubicación encontrada para `refrescar_misgastos` sin asumir que es un
archivo (también puede ser función/alias). No compartir salidas con secretos.
El usuario del servicio necesita lectura/ejecución del backend y lectura del
entorno según cómo lo carga systemd; quien actualiza necesita escribir en static
y backups. Nginx sólo necesita lectura de static y www. Evitar permisos 777.

La unidad existente debería apuntar a `/srv/misgastos/app/backend` y usar
`/srv/misgastos/venv/bin/gunicorn --bind 127.0.0.1:8022 config.wsgi:application`
(o un `--chdir` equivalente), con entorno de producción. No se prescribe cambiar
workers/timeouts sin medir ni se crea otra unidad. `gunicorn --check-config` permite
detectar imports/configuración antes del reinicio, con el mismo entorno del servicio.
Python del VPS debe ser compatible con sus versiones de dependencias; el repositorio
usa Python 3.14 y Django >=5.2.12,<5.3, Gunicorn >=23,<24.

Revisar sólo el bloque Nginx de `misgastos.vetrabyte.com.ar`:

- `/api/`, `/accounts/` y `/admin/` se reenvían a `127.0.0.1:8022`, preservando
  la ruta completa (un `proxy_pass` con URI puede quitar el prefijo por error).
- El proxy fija `Host` al host público y **sobrescribe**
  `X-Forwarded-Proto` con `$scheme`; no acepta un valor arbitrario enviado por cliente.
- `/static/` corresponde a `alias /srv/misgastos/static/;`, con barras finales.
- La SPA usa `/srv/misgastos/www/`, fallback a `index.html` para `/app` y `/login`;
  sus reglas no deben capturar `/api/` ni `/accounts/`.
- Las rutas autenticadas no tienen caché de proxy. Los headers HSTS efectivos
  deben revisarse también en Nginx y no duplicarse con valores contradictorios.

No aplicar cambios si la configuración ya satisface esto. No añadir HSTS al
dominio padre ni tocar otros virtual hosts. El HSTS emitido por este subdominio
no afecta a sus hermanos, pero `includeSubDomains` sí cubría sus descendientes;
políticas cacheadas anteriores no desaparecen inmediatamente y un HSTS heredado
del dominio padre no puede eliminarse desde Django.

En Google Cloud verificar el cliente web y la URI exacta:
`https://misgastos.vetrabyte.com.ar/accounts/google/login/callback/`.
Usar un solo origen de configuración del proveedor: este proyecto usa `APP` en
settings; una fila Google adicional en `SocialApp` puede provocar selección ambigua.
No borrar registros automáticamente; revisar y resolver manualmente si existen.
Comprobar testers/estado del consentimiento. Tener credenciales sólo habilita el
botón: no prueba que Google acepte el cliente ni su redirect URI.

## Ajustes requeridos en el actualizador existente

No está disponible su contenido. Adaptarlo tras revisar el archivo real, con este
orden y alcance, exclusivamente backend:

1. Evitar ejecuciones concurrentes con lock dedicado. Verificar checkout correcto,
   rama `main`, remoto esperado y árbol limpio (incluidos archivos no rastreados).
   Registrar hash anterior y nuevo sin registrar el entorno.
2. Ejecutar `git -C /srv/misgastos/app pull --ff-only`; abortar si hay divergencia.
3. Exportar el entorno externo de producción; no cargar `.env.example` del repo.
   Si se usa `source`, asegurar que `.env` sea confiable y compatible con Bash:
   el formato `EnvironmentFile` de systemd no es un script de shell.
4. Actualizar Python cuando cambien `requirements/base.txt`, `requirements/prod.txt`
   o sus includes; la primera instalación también cuenta. Usar
   `/srv/misgastos/venv/bin/python -m pip install -r /srv/misgastos/app/backend/requirements/prod.txt`.
   Ejecutar `pip check`; registrar versiones antes/después en backups. No actualizar
   pip ni dependencias indiscriminadamente en cada refresco. Rangos sin lock pueden
   resolver versiones diferentes: ensayar previamente en un entorno aislado.
5. Ejecutar los checks siguientes y validar que `STATIC_ROOT` coincide con
   `/srv/misgastos/static` antes de tocar archivos. Si `check --deploy` usa
   `--fail-level WARNING`, W005/W021 detendrán el proceso por la política deliberada;
   revisar esos dos avisos sin silenciar los demás. Usar `--fail-level ERROR` para
   abortar en errores y conservar avisos en logs.
6. Crear backup **antes** de `migrate`, con cliente pg_dump compatible con PostgreSQL
   18 (un cliente anterior puede rechazar el servidor). `umask 077`, nombre único,
   formato custom, comprobar salida, archivo no vacío y `pg_restore --list`.
   Abortarlo todo si falla. Un listado no reemplaza un ensayo de restauración en
   una base aislada. Conservar backups anteriores y espacio suficiente.
7. Aplicar `migrate --noinput`, verificar `migrate --check`, luego
   `collectstatic --noinput`. No usar `--fake`, SQLite ni recrear datos.
8. Ejecutar `restorecon` sólo sobre rutas afectadas del backend/static del proyecto,
   de acuerdo con sus reglas SELinux ya existentes. `restorecon` no crea reglas
   faltantes: ante AVC revisar etiquetas y permisos del proyecto manualmente.
   No modificar booleans globales, no desactivar Enforcing y no tocar `www`.
9. Reiniciar sólo `mis-gastos.service` después de todos los pasos exitosos.
10. Verificar `is-active`, consultar journal acotado a esta unidad y hacer smoke
    tests con reintentos limitados. Registrar fase y código de salida ante error;
    no continuar hacia reinicio tras un fallo previo.

Con el entorno exportado, estos son los comandos Django de referencia:

```bash
cd /srv/misgastos/app/backend
/srv/misgastos/venv/bin/python manage.py check
/srv/misgastos/venv/bin/python manage.py check --deploy --fail-level ERROR
/srv/misgastos/venv/bin/python manage.py shell -c 'from django.conf import settings; from pathlib import Path; assert settings.SETTINGS_MODULE == "config.settings.production"; assert Path(settings.STATIC_ROOT) == Path("/srv/misgastos/static"); print("Configuración y STATIC_ROOT correctos")'
/srv/misgastos/venv/bin/python manage.py makemigrations --check --dry-run
/srv/misgastos/venv/bin/python manage.py migrate --plan
/srv/misgastos/venv/bin/gunicorn --check-config --bind 127.0.0.1:8022 config.wsgi:application
# Crear y verificar el backup con las credenciales libpq dedicadas antes de seguir.
/srv/misgastos/venv/bin/python manage.py migrate --noinput
/srv/misgastos/venv/bin/python manage.py migrate --check
/srv/misgastos/venv/bin/python manage.py collectstatic --noinput
sudo restorecon -R /srv/misgastos/app/backend /srv/misgastos/static
sudo systemctl restart mis-gastos.service
systemctl is-active mis-gastos.service
sudo journalctl -u mis-gastos.service --since '5 minutes ago' --no-pager -n 100
```

Para el backup, configurar primero un servicio libpq privado con los valores
reales de esta base (host, puerto, dbname, user y passfile), separado de otros
proyectos. Con ese servicio, ejecutar **antes de migrate** en Bash:

```bash
(
  set -euo pipefail
  umask 077
  read -r -p 'Nombre del servicio libpq configurado para Mis Gastos: ' backup_pg_service
  test -n "$backup_pg_service"
  backup_partial=$(mktemp /srv/misgastos/backups/pre-migrate-XXXXXXXX.partial)
  pg_dump --format=custom --dbname="service=$backup_pg_service" --file="$backup_partial"
  test -s "$backup_partial"
  pg_restore --list "$backup_partial" > /dev/null
  mv "$backup_partial" "${backup_partial%.partial}.dump"
  printf 'Backup verificado: %s\n' "${backup_partial%.partial}.dump"
)
```

Si falla, detener la actualización; el `.partial` no es un backup aprobado.
Verificar previamente que el servicio libpq identifica la base de Mis Gastos.
Un restore de ensayo debe hacerse en una base aislada.

El bloque Django es una referencia para integrar al script; ejecutar cada paso
sólo si el anterior pasó y el backup fue verificado. No pegarlo como un script
sin control de errores. Fijar los valores reales de base/usuario en la
configuración libpq privada del actualizador.
Tras completar la revisión y adaptación, ejecutar manualmente `refrescar_misgastos`.
No ejecutar a la vez la secuencia manual y el actualizador.

Las migraciones incluyen funciones PL/pgSQL, constraints/triggers diferidos y seed
de categorías. Requieren propiedad/permisos adecuados sobre tablas y funciones;
una prueba sobre base vacía no demuestra que los datos actuales satisfagan todas
las restricciones. Ensayar el plan sobre una copia autorizada antes de una migración
con datos reales. En fallos, guardar journal y hashes; no hacer rollback automático
de esquema/datos. La restauración requiere procedimiento y ventana propios.

## Smoke tests después del reinicio (manuales)

```bash
curl --fail --silent --show-error https://misgastos.vetrabyte.com.ar/api/v1/health/
curl --fail --silent --show-error https://misgastos.vetrabyte.com.ar/api/v1/auth/config/
curl --silent --show-error -o /dev/null -w '%{http_code}\n' https://misgastos.vetrabyte.com.ar/api/v1/auth/me/
curl --silent --show-error -I https://misgastos.vetrabyte.com.ar/static/admin/css/base.css
curl --silent --show-error -I https://misgastos.vetrabyte.com.ar/app
```

Esperar health 200 con `status=ok` (consulta PostgreSQL); config 200 con
`googleLoginEnabled=true` si están ambas credenciales; me 403 sin sesión con la
autenticación SessionAuthentication actual, y 200 después de login. Static y SPA
deben responder 200 con CSS y HTML respectivamente, no HTML bajo una URL de API.
En navegador probar Google, callback, recarga de `/app`, selección de hogar y
logout; comprobar Secure/HttpOnly/SameSite en la sesión y HTTPS en redirect URI.
No registrar cookies ni códigos OAuth en evidencias públicas.

## Verificaciones locales

Variables ficticias y cluster PostgreSQL **18.6** nuevo en `/tmp`, socket privado,
sin usar `.env` ni conectar a bases existentes. Python 3.14, Django 5.2.18,
allauth 65.19.7. Pruebas de settings usan procesos limpios con credenciales dummy.

- Suite backend: **103 aprobadas, 12 omitidas** (benchmark optativo y POC contable
  que requieren configuración dedicada); dos deprecaciones de drf-spectacular.
- Ruff de settings/tests modificados, sintaxis Bash de los cuatro scripts y
  `git diff --check`: correctos. Black verifica los archivos Python modificados.
- `pip check`: sin dependencias incompatibles en el entorno local.
- `check`: sin errores; `check --deploy`: sólo W005 y W021 por HSTS limitado al
  host y sin preload, deliberadamente conservados y documentados.
- `makemigrations --check --dry-run`: sin cambios de modelos; `migrate --plan` y
  `migrate --noinput` completos sobre base temporal vacía; `migrate --check`: sin
  migraciones pendientes allí. No implica que el VPS esté actualizado.
- `collectstatic`: 165 archivos en `/tmp`, segunda ejecución 0 copiados y 165
  sin cambios. No se generaron estáticos de producción dentro del repositorio.
- Smoke Django con PostgreSQL: health 200, auth/config 200, me anónimo 403.
- Gunicorn 23.0.0 descargado sólo a `/tmp`: `--check-config` con WSGI de producción
  y variables ficticias correcto. No se abrió un listener ni se arrancó un servicio.
- Nuevas regresiones: STATIC_ROOT, independencia de desarrollo, HTTPS reenviado,
  callback Google generado por Allauth, redirect de HTTP, cookies, CSRF, configuración
  pública, rechazo de hosts/orígenes/rutas inseguros y credenciales PostgreSQL escapadas.

La validación real de Nginx, permisos/contextos SELinux, systemd, backup de producción
y login externo en Google queda pendiente de intervención manual en el VPS.

Referencias oficiales: [settings Django 5.2](https://docs.djangoproject.com/en/5.2/ref/settings/)
(STATIC_ROOT, SECURE_PROXY_SSL_HEADER y HSTS) y
[proveedor Google de Allauth](https://docs.allauth.org/en/latest/socialaccount/providers/google.html)
(callback y configuración del cliente).
