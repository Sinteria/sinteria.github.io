# Sinteria Automatizaciones

Sitio existente: https://sinteria.github.io/ — repositorio Sinteria/sinteria.github.io.

Tres páginas comerciales independientes: Inicio, Sistema personalizado y Página web personalizada. Incluye 404, verificación de Google y el logotipo original.

La actualización visual incorpora los siete afiches del paquete del titular, adaptados para retirar bordes de captura, corregir contactos y eliminar la tarifa antigua, junto con 45 imágenes conceptuales (43 creadas en la corrección de repeticiones). Cada una de las 52 imágenes de contenido se utiliza una sola vez en las tres páginas; las variantes responsive y la ampliación representan la misma ubicación. El logotipo y el icono de WhatsApp son elementos comunes de navegación. Las portadas, tarjetas, galerías, proceso, preguntas frecuentes y contacto incluyen imágenes. La galería permite ampliar, avanzar y retroceder; funciona con teclado y conserva el foco al cerrar. Los enlaces a las imágenes también funcionan sin JavaScript.

Animaciones de entrada, profundidad al mover el puntero, tarjetas flotantes y efectos al pasar el cursor. Se respeta el movimiento reducido del sistema y hay una opción para pausar las animaciones.

RUC facilitado por el titular: 10742038551. Contacto comercial: +51 932 280 554 / contacto.sinteria@gmail.com. No se afirma una verificación externa del estado tributario.

Los archivos estáticos se sirven desde la raíz. No se necesitan paquetes ni compilación para GitHub Pages. site.css conserva los componentes generales; visuales.css añade la presentación con imágenes y site.js controla navegación, galería y movimiento. No se añadieron analítica, cookies propias, almacenamiento ni formularios de captura.

El respaldo remoto respaldo/antes-imagenes-20261022 conserva el commit 13c85014d30725f9a87eb2b60be0e4924376e649. El respaldo del sitio original sigue en respaldo/antes-rediseno-20261022.

Los afiches y visuales muestran ejemplos. Las funciones y condiciones se acuerdan en una cotización. Las políticas pendientes de aprobación no forman parte de esta publicación ni se modificaron en esta actualización visual.

verify_visuals.py comprueba la unicidad global, las variantes WebP, las dimensiones y las secciones con imagen. build_visuals.py rechaza una segunda ubicación de la misma imagen. El respaldo remoto respaldo/antes-imagenes-unicas-20261022 conserva la versión b8fab6065552f0dec6034083ee445b5d3dc463fc.

El archivo visual-assets.json registra la procedencia y los tamaños. ASSET_NOTES.md documenta la preparación y los prompts. build_visuals.py actualiza el contenido de las páginas existentes con Python y lxml; no se ejecuta en el navegador ni es necesario para servir la web.
