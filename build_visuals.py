from pathlib import Path
from html import escape
from urllib.parse import quote
import json
from lxml import html, etree

ROOT = Path(__file__).resolve().parent
ASSETS = json.loads((ROOT / 'visual-assets.json').read_text())
SYSTEM = '/sistema-personalizado.html'
WEB = '/pagina-web-personalizada.html'
RUC = '10742038551'


def icon(name='arrow'):
    paths = {
        'arrow': '<path d="M4 12h15m-6-6 6 6-6 6"/>',
        'expand': '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5M3 3l6 6m12-6-6 6M3 21l6-6m12 6-6-6"/>',
        'close': '<path d="m6 6 12 12M18 6 6 18"/>',
        'check': '<path d="m5 12 4 4L19 6"/>',
        'pause': '<path d="M8 5v14M16 5v14"/>',
        'left': '<path d="m14 5-7 7 7 7"/>',
        'right': '<path d="m10 5 7 7-7 7"/>',
    }
    return '<svg class="icon" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">' + paths[name] + '</svg>'


def photo(key, cls='', eager=False, decorative=False, sizes='(max-width: 600px) 90vw, (max-width: 900px) 60vw, 36vw'):
    item = ASSETS[key]
    alt = '' if decorative else item['alt']
    return f'<img class="{cls}" src="/{key}-900.webp" srcset="/{key}-480.webp 480w, /{key}-900.webp 900w, /{key}-1200.webp 1200w" sizes="{sizes}" width="900" height="{item["height900"]}" alt="{escape(alt, quote=True)}" loading="{"eager" if eager else "lazy"}" decoding="async"' + (' fetchpriority="high"' if eager else '') + '>'


def zoom(key, cls='', group='material', eager=False, caption=None):
    caption = caption or ASSETS[key]['title']
    return f'<a class="image-open {cls}" href="/{key}-1200.webp" data-full="/{key}-1200.webp" data-gallery="{group}" data-caption="{escape(caption,quote=True)}" aria-label="Ampliar imagen: {escape(caption,quote=True)}">{photo(key,eager=eager)}<span class="zoom-hint">{icon("expand")}<span>Ampliar imagen</span></span></a>'


def wa(label='Cotiza gratis con nosotros', service='proyecto', secondary=False):
    msg = quote(f'Hola, Sinteria. Quisiera una cotización gratuita para mi {service}. ¿Podemos conversar sobre lo que necesito?', safe='')
    return f'<a class="btn {"btn-secondary" if secondary else "btn-primary"}" href="https://wa.me/51932280554?text={msg}" target="_blank" rel="noopener noreferrer"><img class="whatsapp-icon" src="/whatsapp.svg" alt="" width="21" height="21">{label}</a>'


def heading(kicker, title, desc='', center=False):
    return f'<div class="v-heading reveal {"v-center" if center else ""}"><div><div class="eyebrow">{kicker}</div><h2>{title}</h2></div>' + (f'<p>{desc}</p>' if desc else '') + '</div>'


def section(content, cls='', ident=''):
    return f'<section class="v-section {cls}"'+(f' id="{ident}"' if ident else '')+f'><div class="container">{content}</div></section>'


def hero(kind):
    configs = {
        'home': ('SOLUCIONES DIGITALES PARA TU NEGOCIO', 'Tus ideas.<br>Tu negocio.<br><span class="gradient-text">El siguiente nivel.</span>', 'Creamos <strong>sistemas personalizados y páginas web</strong> para que trabajes con más orden, automatices tus procesos y muestres lo mejor de tu negocio.', 'soluciones', 'stock', 'web', 'Sistemas + páginas web', 'Tu negocio, con nuevas posibilidades.'),
        'systems': ('GOOGLE SHEETS + GOOGLE APPS SCRIPT', 'Tu negocio tiene<br>su forma.<br><span class="gradient-text">Tu sistema también.</span>', 'Convierte tus registros y tareas manuales en un <strong>sistema personalizado</strong>. Inventarios, compras, ventas, pagos y los procesos que necesitas conectar.', 'stock', 'inventarios', 'prestamos', 'De tu hoja a tu sistema', 'Google Sheets + Google Apps Script'),
        'web': ('DISEÑO WEB PARA NEGOCIOS', 'Tu esencia.<br>Tu propia web.<br><span class="gradient-text">Una gran primera impresión.</span>', 'Creamos una <strong>página web personalizada</strong> para presentar tu negocio, mostrar lo que ofreces y facilitar que tus próximos clientes te contacten.', 'web', 'web-estudio', 'soluciones', 'Tu marca, en internet', 'Diseño para móvil y computadora'),
    }
    kicker, title, desc, main, left, right, badge, sub = configs[kind]
    current = '' if kind == 'home' else ('Sistema personalizado' if kind == 'systems' else 'Página web personalizada')
    crumb = f'<nav class="breadcrumb" aria-label="Ruta de navegación"><a href="/">Inicio</a><span aria-hidden="true">/</span><span aria-current="page">{current}</span></nav>' if current else ''
    actions = wa() + f'<a class="btn btn-secondary" href="{SYSTEM}">Explorar soluciones {icon()}</a>' if kind == 'home' else wa('Cotizar mi sistema' if kind == 'systems' else 'Cotizar mi página web', 'sistema personalizado' if kind == 'systems' else 'página web personalizada')
    return f'''<section class="v-hero v-hero-{kind}"><div class="v-orb orb-one" aria-hidden="true"></div><div class="v-orb orb-two" aria-hidden="true"></div><div class="container">{crumb}<div class="v-hero-grid"><div class="v-hero-copy reveal" data-from="left"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{desc}</p><div class="actions">{actions}</div><div class="v-hero-note">{icon('check')} Consulta y cotización gratuita · A tu medida</div><div class="v-mini-trail"><span></span><span></span><span></span> Tecnología que acompaña tu negocio.</div></div><div class="v-collage reveal" data-from="right"><div class="v-orbit orbit-a" aria-hidden="true"></div><div class="v-orbit orbit-b" aria-hidden="true"></div><div class="v-poster-back back-left">{photo(left,decorative=True)}</div><div class="v-poster-back back-right">{photo(right,decorative=True)}</div><div class="v-poster-main tilt">{zoom(main,'v-poster-image','hero',True)}<span class="v-image-label">SINTERIA · SOLUCIONES A TU MEDIDA</span></div><div class="v-floating-chip"><span class="v-chip-icon">{icon('check')}</span><span><strong>{badge}</strong><small>{sub}</small></span></div><p class="v-collage-caption">Material visual de Sinteria · Toca la imagen para ampliarla</p></div></div></div></section>'''


def service_card(key, title, desc, route, tags):
    return f'<article class="v-service reveal"><a class="v-service-photo" href="{route}">{photo(key)}<span class="v-photo-shade"></span><span class="v-photo-tag">SINTERIA / {"SISTEMAS" if route==SYSTEM else "DESARROLLO WEB"}</span></a><div class="v-service-body"><h3>{title}</h3><p>{desc}</p><div class="tags">'+''.join(f'<span>{t}</span>' for t in tags)+f'</div><a class="text-link" href="{route}">Descubre las posibilidades {icon()}</a></div></article>'


def gallery(keys, title, desc, group):
    cards = ''.join(f'<article class="v-gallery-card reveal">{zoom(key,"v-gallery-photo",group)}<div><span class="v-index">0{i+1} / SINTERIA</span><h3>{ASSETS[key]["title"]}</h3></div></article>' for i,key in enumerate(keys))
    return section(heading('IDEAS QUE TOMAN FORMA',title,desc)+f'<div class="v-gallery-grid">{cards}</div><p class="v-caption">Material promocional adaptado de Sinteria. Los paneles y datos son ilustrativos; el alcance de cada proyecto se define contigo.</p>','v-glow-section')


def photo_cards(items, kind='features'):
    cards = ''
    for i, item in enumerate(items):
        key,title,desc,*service = item
        link = f'<a class="text-link" href="https://wa.me/51932280554?text={quote("Hola, Sinteria. Quisiera cotizar mi "+service[0]+".",safe="")}" target="_blank" rel="noopener noreferrer">Cuéntanos qué necesitas {icon()}</a>' if service else ''
        cards += f'<article class="v-photo-card reveal"><div class="v-card-photo crop-{i%4}">{photo(key)}<span class="v-index">0{i+1}</span></div><div class="v-card-copy"><h3>{title}</h3><p>{desc}</p>{link}</div></article>'
    return f'<div class="v-card-grid {"v-four" if kind=="benefits" else ""}">{cards}</div>'


def process(kind='systems'):
    items = [('automatizacion','Cuéntanos tu proceso','¿Qué haces hoy y qué te gustaría mejorar? Revisamos tu objetivo y los materiales de ejemplo.'),('soluciones','Definimos lo que necesitas','Acordamos las funciones, el diseño, los plazos y las condiciones de tu propuesta.'),('web-estudio' if kind=='web' else 'inventarios','Construimos y revisamos contigo','Desarrollamos, probamos y coordinamos la entrega según el alcance acordado.')]
    cards=''.join(f'<article class="v-process-card reveal"><div class="v-process-photo">{photo(k)}<span>0{i+1}</span></div><div><h3>{t}</h3><p>{d}</p></div></article>' for i,(k,t,d) in enumerate(items))
    return section(heading('ASÍ COMENZAMOS','De una buena idea<br>a una solución para ti.','Una conversación clara, una propuesta a tu medida y un trabajo que revisamos contigo.')+f'<div class="v-process-grid">{cards}</div>','v-muted-section')


def faq(kind):
    web = kind == 'web'
    items = [
        ('¿Pueden usar mi logo, fotos y colores?','Sí. Podemos trabajar con los materiales que proporciones y que tengas autorización para utilizar. Revisamos contigo cómo integrarlos al diseño.'),
        ('¿La web se verá bien en celular?','El diseño contempla pantallas móviles y de computadora. Probamos la navegación y la adaptación del contenido antes de coordinar su publicación.'),
        ('¿Incluye dominio y alojamiento?','Se define en tu propuesta. Te indicamos los servicios que requiere el proyecto, quién los administra y las condiciones o renovaciones que correspondan.'),
        ('¿Puedo pedir un catálogo o un panel de edición?','Sí. Evaluamos catálogos, paneles, formularios e integraciones y los detallamos expresamente en el alcance de tu proyecto.'),
    ] if web else [
        ('¿Tengo que saber programar?','No. Nos cuentas cómo trabajas y revisamos qué herramienta se adapta a tu proceso. La orientación y la entrega se definen contigo.'),
        ('¿Puede trabajar con la hoja que ya utilizo?','Podemos revisar su estructura y evaluar qué partes conviene conservar o adaptar. Para la primera consulta, utiliza datos de ejemplo.'),
        ('¿Todas las funciones están incluidas?','Las imágenes y los módulos muestran posibilidades. Las funciones, usuarios, permisos e integraciones incluidos se detallan en tu cotización.'),
        ('¿Cómo solicito una cotización gratuita?','Escríbenos por WhatsApp al +51 932 280 554 o por correo a contacto.sinteria@gmail.com. Cuéntanos qué necesitas organizar o automatizar.'),
    ]
    return section(f'<div class="v-faq-layout"><div class="v-faq-image reveal">{photo("web-estudio" if web else "negocios")}<div><span class="eyebrow">CONVERSEMOS CON CLARIDAD</span><h2>Tu siguiente paso<br><span class="gradient-text">empieza aquí.</span></h2><p>Te escuchamos antes de proponerte una solución.</p></div></div><div class="reveal">{heading("RESOLVEMOS TUS DUDAS","Antes de comenzar.")}<div class="faq-list">'+''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in items)+'</div></div></div>')


def contact(kind='systems'):
    return section(f'<div class="v-contact reveal"><div class="v-contact-photo">{photo("web-estudio" if kind=="web" else "automatizacion")}</div><div class="v-contact-copy"><div class="eyebrow">TU SIGUIENTE PASO EMPIEZA AQUÍ</div><h2>Cuéntanos tu idea.<br><span class="gradient-text">Démosle forma juntos.</span></h2><p>Tú nos cuentas lo que necesitas; nosotros le damos forma a una solución para tu negocio.</p>{wa(service="página web personalizada" if kind=="web" else "proyecto")}<a class="v-mail" href="mailto:contacto.sinteria@gmail.com">contacto.sinteria@gmail.com {icon()}</a></div></div>','v-contact-section')


def home():
    cards=service_card('stock','Sistema personalizado','Conecta tus hojas de cálculo, registros y procesos en una herramienta creada para tu negocio.',SYSTEM,['Inventarios','Compras','Ventas','Pagos y reportes'])+service_card('web','Página web personalizada','Presenta tu marca, muestra lo que ofreces y abre una conversación con tus próximos clientes.',WEB,['Tu identidad','Catálogos','WhatsApp','Móvil y PC'])
    benefits=[('automatizacion','Menos trabajo manual','Dedica tu tiempo a tu negocio, con tareas y registros más conectados.'),('negocios','Todo más organizado','Productos, movimientos y procesos con una estructura más clara.'),('automatizar','Datos para decidir','Consulta la información y los reportes que tu operación necesita.'),('web-estudio','A tu alcance','Sistemas y páginas pensados para diferentes dispositivos.')]
    approach=f'<div class="v-editorial"><div class="v-editorial-photo reveal" data-from="left">{photo("automatizacion")}<span class="v-editorial-caption">DE TU FORMA DE TRABAJAR A TU PRÓXIMA SOLUCIÓN</span></div><div class="reveal" data-from="right"><div class="eyebrow">¿POR QUÉ SINTERIA?</div><h2>Primero entendemos<br><span class="gradient-text">tu forma de trabajar.</span></h2><p>Cada negocio tiene sus propios retos. Te escuchamos, revisamos tus necesidades y construimos una propuesta con lo que realmente necesitas.</p><blockquote>“Si tú lo puedes imaginar, nosotros podemos convertirlo en realidad”.</blockquote>{wa("Hablemos sobre tu idea")}</div></div>'
    return hero('home')+section(heading('DOS CAMINOS. UN MISMO OBJETIVO.','Que tu negocio funcione<br><span class="gradient-text">y se vea mejor.</span>','Desde el control interno hasta tu presencia en internet. Tú eliges por dónde empezamos.')+f'<div class="v-services-grid">{cards}</div>')+gallery(['soluciones','automatizar','negocios'],'Un vistazo a lo que<br><span class="gradient-text">podemos crear contigo.</span>','Tus procesos, tus productos y tus ideas, con una nueva forma de trabajar.','inicio')+section(heading('TECNOLOGÍA CON UN PROPÓSITO','Más claridad en tu día a día.')+photo_cards(benefits,'benefits'),'v-muted-section')+section(approach)+contact()


def systems():
    items=[('inventarios','Inventarios y stock','Organiza productos, entradas, salidas, ubicaciones y niveles de stock según tu operación.','sistema de inventarios y stock'),('automatizacion','Compras y requerimientos','Conecta solicitudes, proveedores, cotizaciones y seguimiento de entregas.','sistema de compras y requerimientos'),('negocios','Ventas y pedidos','Lleva el registro de clientes, pedidos y productos con el seguimiento que necesitas.','sistema de ventas y pedidos'),('prestamos','Pagos y cobranzas','Ordena vencimientos, pagos, saldos y pendientes en un mismo flujo.','sistema de pagos y cobranzas'),('prestamos','Préstamos y cuotas','Consulta cronogramas, cuotas y movimientos con la estructura que definamos contigo.','sistema de préstamos y cuotas'),('automatizar','Dashboards y reportes','Reúne indicadores y resúmenes que te ayuden a entender tus datos.','dashboard y reportes')]
    note='<p class="v-caption">No es un paquete fijo de funciones. Los módulos, usuarios e integraciones se definen en tu cotización.</p>'
    editorial=f'<div class="v-editorial"><div class="reveal"><div class="eyebrow">DE LA HOJA DE CÁLCULO A TU HERRAMIENTA</div><h2>Menos pasos repetidos.<br><span class="gradient-text">Más conexión entre tus datos.</span></h2><p>Google Sheets puede ser el punto de partida. Con Apps Script creamos interfaces y automatizaciones alrededor de tus procesos.</p><ul class="v-checks"><li>{icon("check")} Registros pensados para tu equipo.</li><li>{icon("check")} Procesos que siguen el flujo de tu negocio.</li><li>{icon("check")} Reportes con la información que necesitas.</li></ul>{wa("Hablemos de tu automatización","automatización con Apps Script")}</div><div class="v-editorial-photo reveal">{photo("automatizacion")}<span class="v-editorial-caption">TU OPERACIÓN, CONECTADA</span></div></div>'
    return hero('systems')+section(heading('IMAGINA LO QUE PODEMOS ORGANIZAR','Un sistema.<br><span class="gradient-text">Muchas posibilidades.</span>','Estos son ejemplos de lo que podemos desarrollar. Cada propuesta se adapta a tu forma de trabajar.')+photo_cards(items)+note,'v-muted-section')+gallery(['inventarios','stock','prestamos'],'Herramientas que se adaptan<br><span class="gradient-text">a tu operación.</span>','Explora el material de Sinteria para inventarios, movimientos, préstamos y pagos.','sistemas')+section(editorial)+process()+faq('systems')+contact()


def websites():
    items=[('web-estudio','Diseño con tu identidad','Colores, imágenes y una estructura que representen a tu negocio.'),('web','Móvil y computadora','Una experiencia adaptable para navegar con comodidad en distintas pantallas.'),('negocios','Catálogos de productos o servicios','Imágenes, descripciones y una organización pensada para tus clientes.'),('web','Contacto por WhatsApp','Facilita la conversación con botones y mensajes orientados a tu servicio.'),('web-estudio','Formularios según tu proyecto','Definimos los campos, su destino y el tratamiento de la información.'),('soluciones','SEO básico y estructura clara','Títulos, descripciones y una base que ayude a comprender tus páginas.')]
    types=[('web','Servicios profesionales','Explica tu propuesta y facilita que te contacten.'),('negocios','Comercios y catálogos','Presenta tus productos y abre nuevas conversaciones.'),('web-estudio','Restaurantes y experiencias','Muestra lo que te hace especial con imágenes y contenido propio.'),('soluciones','Tu próximo proyecto','Turismo, emprendimientos y más: cuéntanos tu idea.')]
    spotlight=f'<div class="v-web-showcase"><div class="v-web-showcase-main reveal">{photo("web-estudio")}</div><div class="v-web-showcase-copy reveal"><div class="eyebrow">TU MARCA, EN CADA DETALLE</div><h2>Tu negocio tiene<br><span class="gradient-text">mucho que mostrar.</span></h2><p>Diseño, imágenes y contenido que acompañan tu propuesta y ayudan a que te conozcan.</p>{wa("Diseñemos tu próxima web","página web personalizada")}</div><div class="v-web-poster reveal">{zoom("web","v-web-poster-link","web")}</div></div><p class="v-caption">Las vistas son ilustrativas y no se presentan como trabajos reales de clientes.</p>'
    return hero('web')+section(heading('UN DISEÑO BONITO QUE TAMBIÉN SEA ÚTIL','Todo empieza con<br><span class="gradient-text">lo que quieres comunicar.</span>','Definimos contigo las páginas, el contenido y las herramientas que tu negocio necesita.')+photo_cards(items)+'<p class="v-caption">Las funciones se acuerdan para cada proyecto. El SEO básico no garantiza posiciones; dominio, alojamiento y servicios externos se revisan en la propuesta.</p>','v-muted-section')+section(spotlight,'v-glow-section')+section(heading('UNA WEB QUE HABLE DE TI','Cada negocio tiene<br><span class="gradient-text">su propia historia.</span>')+photo_cards(types,'benefits'))+process('web')+faq('web')+contact('web')


LIGHTBOX='''<dialog class="v-lightbox" id="galeria-ampliada" aria-labelledby="galeria-titulo"><div class="v-lightbox-toolbar"><p id="galeria-titulo"></p><button type="button" class="v-lightbox-close" aria-label="Cerrar imagen ampliada">''' + icon('close') + '''</button></div><div class="v-lightbox-stage"><button type="button" class="v-lightbox-prev" aria-label="Imagen anterior">''' + icon('left') + '''</button><img class="v-lightbox-image" alt="" width="1200" height="1800"><button type="button" class="v-lightbox-next" aria-label="Imagen siguiente">''' + icon('right') + '''</button></div><p class="v-lightbox-count" aria-live="polite"></p></dialog>'''


def by_class(doc,name):
    return doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " '+name+' ")]')


for file, content in [('index.html',home()),('sistema-personalizado.html',systems()),('pagina-web-personalizada.html',websites())]:
    doc=html.fromstring((ROOT/file).read_text())
    main=doc.find('body/main')
    main.clear()
    main.attrib.update({'class':'visual-main','id':'contenido','tabindex':'-1'})
    for fragment in html.fragments_fromstring(content):main.append(fragment)
    for existing in doc.xpath('//link[starts-with(@href,"/visuales.css")] | //*[@id="galeria-ampliada"]')+by_class(doc,'motion-toggle')+by_class(doc,'ruc-line'):
        existing.getparent().remove(existing)
    doc.find('head').append(etree.Element('link',rel='stylesheet',href='/visuales.css?v=20261022b'))
    for script in doc.xpath('//script[starts-with(@src,"/site.js")]'):
        script.set('src','/site.js?v=20261022b')
    org=doc.xpath('//script[@type="application/ld+json"]')[0]
    data=json.loads(org.text);data['taxID']=RUC
    org.text=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    ruc=etree.Element('p',attrib={'class':'ruc-line'});ruc.text='RUC: '+RUC
    by_class(doc,'footer-about')[0].append(ruc)
    pause=etree.Element('button',attrib={'type':'button','class':'motion-toggle','aria-pressed':'false'})
    pause.text='Pausar animaciones'
    by_class(doc,'footer-bottom')[0].append(pause)
    doc.find('body').append(html.fromstring(LIGHTBOX))
    (ROOT/file).write_text(html.tostring(doc,encoding='unicode',doctype='<!doctype html>'),encoding='utf-8')

doc=html.fromstring((ROOT/'404.html').read_text())
if not by_class(doc,'ruc-line'):
    ruc=etree.Element('p',attrib={'class':'ruc-line'});ruc.text='RUC: '+RUC
    by_class(doc,'footer-about')[0].append(ruc)
org=doc.xpath('//script[@type="application/ld+json"]')[0]
data=json.loads(org.text);data['taxID']=RUC
org.text=json.dumps(data,ensure_ascii=False,separators=(',',':'))
(ROOT/'404.html').write_text(html.tostring(doc,encoding='unicode',doctype='<!doctype html>'),encoding='utf-8')
print('Updated three visual pages and RUC on four pages.')
