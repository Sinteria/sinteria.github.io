# Panel de Sinteria Automatizaciones

Estado del 29/10/2026: implementación preparada y probada; **todavía no desplegada**. El acceso de Google se intentó con `contacto.sinteria@gmail.com`. Cloudflare devolvió «Unable to sign in. Try again or use your email and password». No se confirmó el plan de esa cuenta ni se creó una base de datos remota. La web pública y su configuración de publicación siguen sin cambios.

## Funciones

Editor de 257 textos y 52 imágenes de las siete páginas existentes, títulos y descripciones SEO, 12 catálogos, WhatsApp, correo, TikTok y Facebook. Guardar borrador y publicar son acciones separadas. Resumen de visitas del mes, total desde la activación y gráfico diario. Las visitas son aproximadas; no representan personas únicas ni incluyen historial anterior al despliegue.

## Topes aplicados en servidor y base de datos

| Recurso | Tope |
| --- | --- |
| Imágenes nuevas simultáneas | 60 |
| Cada archivo optimizado | 512 KiB |
| Biblioteca completa | 20 MiB |
| Dimensiones por lado | 2000 píxeles |
| Vídeos, SVG y archivos ajenos a imágenes | 0 |
| Catálogos | 12 |
| Imágenes por catálogo | 6 |
| Subidas y eliminaciones | 30 al día, compartidas |
| Guardados | 30 al día |
| Publicaciones | 12 al día |
| Visitas registradas | 2000 al día y 50 000 al mes |
| Intentos de acceso por dirección | 5 cada 15 minutos |
| Intentos de acceso globales | 200 al día |
| Sesión administrativa | 2 horas |

Las 52 imágenes actuales se reutilizan sin consumir el cupo de nuevas subidas. El navegador reduce fotos a WebP de hasta 1600 píxeles; el servidor comprueba tamaño, formato y dimensiones. El tope agregado se comprueba mediante un trigger SQL atómico. Las fotos en uso no se eliminan. Los periodos diarios se calculan en Lima. Se conservan hasta 400 días de conteos diarios; el total agregado permanece. Al superar un límite se rechaza la operación; no se contrata un plan adicional.

## Publicación y SEO

El Worker maneja el panel, una base D1 y las imágenes nuevas. No usa R2, Stream, Images, KV, IA, servicios de pago ni un token personal de GitHub. La web comercial continúa en `https://sinteria.github.io/`, con sus siete URL originales y una nueva página `/catalogos.html`. El generador entrega HTML completo, metadatos, datos estructurados, imágenes estáticas y mapas XML/TXT. El panel y `/admin/` llevan `noindex`. Se preserva la verificación de Search Console. No se publican políticas pendientes.

El flujo de GitHub comprueba la versión cada 15 minutos y omite la compilación si no cambió. La cola puede retrasarlo; GitHub puede suspender tareas programadas tras 60 días sin actividad en un repositorio público. Los cambios también se pueden publicar con `workflow_dispatch`. Solo funciona en un repositorio público y un runner estándar. No usa caché y retira su propio artefacto temporal al terminar; como respaldo, el artefacto caduca al día. Si falla la limpieza, el registro del workflow lo muestra. Debe verificarse el presupuesto de GitHub antes de activarlo. No se promete indexación ni una posición en Google.

La web y sus imágenes publicadas no dependen del contador ni del Worker. Si se agota una cuota gratuita de Cloudflare, el panel o el conteo pueden detenerse, pero la última publicación sigue disponible.

## Condición de coste antes de activar

`FREE_PLAN_CONFIRMED` permanece en `false`. No cambiarlo hasta comprobar en **la cuenta correcta de Cloudflare** que Workers y D1 están en Free, que no se está dando de alta una suscripción y que no se activan productos facturables. El código no puede impedir cambios de plan realizados posteriormente por el titular ni controlar otros proyectos de esa cuenta. Revisar también GitHub Actions: repositorio público, runner estándar y presupuesto de uso facturable con bloqueo de gasto. No se modificaron tarjetas, suscripciones ni presupuestos de las cuentas.

Documentación oficial revisada:

- https://developers.cloudflare.com/workers/platform/pricing/ — Workers Free tiene 100 000 solicitudes/día; al agotarse la cuota gratuita deja de ejecutar solicitudes.
- https://developers.cloudflare.com/d1/platform/pricing/ — D1 Free: 5 millones de filas leídas/día, 100 000 escritas/día y 5 GB de almacenamiento por cuenta. Las cuotas diarias gratuitas detienen consultas al agotarse.
- https://developers.cloudflare.com/r2/pricing/ — R2 admite cobro por uso adicional; se excluye de esta implementación.
- https://docs.github.com/en/billing/concepts/product-billing/github-actions — runners estándar gratuitos en repositorios públicos; almacenamiento y presupuestos deben revisarse por separado.
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule — los horarios pueden retrasarse o desactivarse por inactividad.

Los topes de aplicación son adicionales y mucho menores que el almacenamiento incluido de D1. No sustituyen las condiciones vigentes del proveedor.

## Instalación pendiente, cuando se resuelva el acceso

1. Verificar identidad `contacto.sinteria@gmail.com` y los planes gratuitos antes de crear recursos.
2. Desde esta carpeta, ejecutar `node build.mjs`. El resultado `deploy-worker.mjs` contiene todo el panel, sin claves.
3. Crear únicamente la base D1 `sinteria-automatizaciones-panel`, copiar su ID real a `wrangler.jsonc` y ejecutar `schema.sql` en esa base. No hay que borrar otras bases o aplicaciones.
4. Configurar dos secretos del Worker: `ADMIN_PASSWORD_HASH` (SHA-256 hexadecimal de la clave del panel, calculado fuera del código público) y `SESSION_SECRET` (32 bytes aleatorios o más). La clave nunca se escribe en este repositorio. Un correo público como clave es fácil de adivinar; la autenticación queda pendiente de configurar.
5. Poner `FREE_PLAN_CONFIRMED` en `true` únicamente después de la comprobación de plan, desplegar con Wrangler oficial y verificar `/health`, inicio de sesión, guardado, subida y publicación con la URL real.
6. Integrar estos archivos en `main`, instalar `workflow.yml` como `.github/workflows/publicar-contenido.yml`, crear la variable de repositorio `SINTERIA_PANEL_URL` con la URL HTTPS real del Worker y seleccionar GitHub Actions como origen de Pages. La variable es pública y no es una credencial.
7. Ejecutar el flujo, comprobar las ocho páginas, contactos, imágenes, `/admin/`, sitemap y el contador en producción. Solo entonces comunicar que el panel está activo. La configuración actual no publica ni redirige a una URL ficticia.

Para revertir, devolver Pages a su origen anterior `main / (root)` y retirar el workflow del panel. Las páginas comerciales originales permanecen en el repositorio. No se debe conectar el generador con datos de prueba.

## Pruebas

Desde la raíz del repositorio:

```sh
python -m pip install lxml==5.4.0 Pillow==11.3.0
python panel-cloudflare/test_publish.py
node panel-cloudflare/build.mjs
npm --prefix panel-cloudflare install
npm --prefix panel-cloudflare test
```

Se comprobaron 17 casos sobre Worker/D1 con Miniflare: acceso, origen, cookie, formatos, tamaño real, listas de campos, catálogos, concurrencia de edición, separación borrador/publicado, imágenes en uso, cupos y aplicación cerrada si no se confirma Free. El generador pasó ocho páginas y 315 referencias locales, contactos, canonical, metadatos e inyección HTML escapada. Las seis secciones del panel se revisaron a 320, 390, 768 y 1440 píxeles sin desbordes horizontales. Estas pruebas locales no sustituyen la validación pendiente en la cuenta remota.
