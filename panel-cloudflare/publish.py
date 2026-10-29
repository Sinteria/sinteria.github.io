"""Publish the CMS snapshot as static HTML, retaining the established GitHub URLs."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qs, urlencode
from urllib.request import Request, urlopen
import argparse
import json
import re
import shutil
from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
CMS = ROOT / 'panel-cloudflare'
ORIGIN = 'https://sinteria.github.io'
MAX_BODY = 524288
MAX_IMAGE = 524288
MAX_STORAGE = 20971520
PAGES = ['index.html', 'sistema-personalizado.html', 'pagina-web-personalizada.html', 'sistema-inventarios-google-sheets.html', 'automatizacion-google-sheets-apps-script.html', 'sistema-compras-requerimientos.html', 'sistema-prestamos-pagos.html']

def read_remote(url, maximum, opener=urlopen):
    with opener(Request(url, headers={'User-Agent':'Sinteria-static-publisher/1.0'}), timeout=25) as response:
        if response.status != 200:
            raise ValueError('No se pudo obtener el contenido público del panel.')
        data = response.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError('El recurso supera el límite permitido.')
        return data

def validate(snapshot):
    seed = json.loads((CMS/'seed.json').read_text())
    c = snapshot['content']
    if c.get('schemaVersion') != 1 or len(c.get('fields', [])) != len(seed['fields']) or len(c.get('catalogs', [])) > 12:
        raise ValueError('Estructura inválida.')
    defs = {f['id']:f for f in seed['fields']}
    seen = set()
    for f in c['fields']:
        base = defs.get(f.get('id'))
        if not base or f['id'] in seen:
            raise ValueError('Campo desconocido o duplicado.')
        seen.add(f['id'])
        if base['kind'] == 'text' and (not isinstance(f.get('value'), str) or not f['value'].strip() or len(f['value']) > base['maxLength']):
            raise ValueError('Texto fuera de límite.')
    if {p['id'] for p in c['pages']} != {p['id'] for p in seed['pages']}:
        raise ValueError('Páginas inválidas.')
    for p in c['pages']:
        if not 1 <= len(p['seoTitle']) <= 80 or not 1 <= len(p['seoDescription']) <= 170:
            raise ValueError('Metadatos fuera de límite.')
    s = c['settings']
    if not re.fullmatch(r'\d{8,15}', s['phone']) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', s['email']):
        raise ValueError('Contacto inválido.')
    if not isinstance(s['brandName'], str) or not 1 <= len(s['brandName']) <= 80:
        raise ValueError('Nombre inválido.')
    for key, hosts in [('tiktok', ['tiktok.com']), ('facebook', ['facebook.com', 'fb.com'])]:
        if s.get(key):
            u = urlparse(s[key])
            if u.scheme != 'https' or u.username or u.password or not any(u.hostname == h or u.hostname.endswith('.'+h) for h in hosts):
                raise ValueError('Red social inválida.')
    allowed = {f['value']['src'] for f in seed['fields'] if f['kind'] == 'image'}
    images = [f['value'] for f in c['fields'] if defs[f['id']]['kind'] == 'image']
    catalog_ids = set()
    for cat in c['catalogs']:
        if not re.fullmatch(r'[a-z0-9-]{1,60}', cat['id']) or cat['id'] in catalog_ids or len(cat['images']) > 6:
            raise ValueError('Catálogo inválido.')
        catalog_ids.add(cat['id'])
        for field,maximum,required in [('title',100,True),('subtitle',200,False),('description',1600,True)]:
            value=cat[field]
            if not isinstance(value,str) or len(value)>maximum or (required and not value.strip()):
                raise ValueError('Texto de catálogo inválido.')
        images.extend(cat['images'])
    for image in images:
        if image.get('mediaId'):
            if not re.fullmatch(r'[a-f0-9-]{36}', image['mediaId']):
                raise ValueError('Identificador de imagen inválido.')
        elif image.get('src') not in allowed:
            raise ValueError('Imagen ajena a la biblioteca.')
        if not isinstance(image.get('alt'),str) or len(image['alt'])>200:
            raise ValueError('Descripción de imagen inválida.')
    return seed, c, images

def replace_text(element, value):
    for child in list(element):
        element.remove(child)
    element.text = value
    if element.tag == 'h1':
        element.text = None
        span = etree.SubElement(element,'span',{'class':'gradient-text'})
        span.text = value

def phone_display(phone):
    return '+51 '+phone[2:5]+' '+phone[5:8]+' '+phone[8:] if phone.startswith('51') and len(phone)==11 else '+'+phone

def serialize(doc):
    raw=html.tostring(doc,encoding='unicode',doctype='<!doctype html>')
    return raw.replace('viewbox=','viewBox=').replace('lineargradient','linearGradient')+'\n'

def update_json(value, settings):
    if isinstance(value, list): return [update_json(v,settings) for v in value]
    if not isinstance(value,dict): return value
    result={k:update_json(v,settings) for k,v in value.items()}
    if result.get('@type') in ['Organization','WebSite']:
        result['name']=settings['brandName']
    if result.get('@type')=='Organization':
        result['email']=settings['email']; result['telephone']=phone_display(settings['phone'])
        result['sameAs']=[settings[k] for k in ['facebook','tiktok'] if settings.get(k)]
    if result.get('@type')=='ContactPoint':result['telephone']=phone_display(settings['phone'])
    return result

def build(snapshot, output, panel_url, image_loader=None):
    seed,content,images=validate(snapshot)
    output=Path(output).resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError('La salida debe estar en una subcarpeta del proyecto.')
    output.mkdir(exist_ok=True,parents=True)
    # Copy only public resources. Backend source, credentials and templates never enter the artifact.
    for path in ROOT.iterdir():
        if path.is_file() and (path.suffix in ['.webp','.jpeg','.jpg','.png','.svg','.ico','.css','.js'] or path.name.startswith('google') and path.suffix=='.html' or path.name=='404.html'):
            shutil.copy2(path, output/path.name)
    image_ids=sorted({v['mediaId'] for v in images if v.get('mediaId')})
    if len(image_ids)>60:raise ValueError('Demasiadas imágenes.')
    media_paths={}; total=0
    upload_dir=output/'imagenes-panel';upload_dir.mkdir(exist_ok=True)
    from PIL import Image
    from io import BytesIO
    for image_id in image_ids:
        raw=image_loader(image_id) if image_loader else read_remote(panel_url+'/media/'+image_id,MAX_IMAGE)
        if len(raw)>MAX_IMAGE:raise ValueError('Imagen demasiado grande.')
        total+=len(raw)
        if total>MAX_STORAGE:raise ValueError('Almacenamiento fuera de límite.')
        with Image.open(BytesIO(raw)) as im:
            if im.width>2000 or im.height>2000 or im.format not in ['WEBP','PNG','JPEG'] or getattr(im,'n_frames',1)>1:
                raise ValueError('Formato o dimensiones inválidos.')
            im.load()
            extension={'WEBP':'webp','PNG':'png','JPEG':'jpg'}[im.format]
        dest=upload_dir/(image_id+'.'+extension);dest.write_bytes(raw)
        media_paths[image_id]='/imagenes-panel/'+dest.name
    def image_path(value):return media_paths[value['mediaId']] if value.get('mediaId') else value['src']
    settings=content['settings']; definitions={f['id']:f for f in seed['fields']};docs={}
    for page in content['pages']:
        source=next(p for p in seed['pages'] if p['id']==page['id'])
        doc=html.parse(str(CMS/'templates'/(source['file']+'.tpl')))
        for field in content['fields']:
            base=definitions[field['id']]
            if base['page']!=page['id']:continue
            if base['kind']=='text':
                if field['value']!=base['value']:
                    target=doc.xpath('//*[@data-cms-text=$id]',id=field['id'])
                    if len(target)!=1:raise ValueError('Marcador de texto no encontrado.')
                    replace_text(target[0],field['value'])
            else:
                target=doc.xpath('//*[@data-cms-image=$id]',id=field['id'])[0]
                value=field['value'];target.set('alt',value['alt'])
                if value.get('mediaId'):
                    path=image_path(value);target.set('src',path);target.attrib.pop('srcset',None);target.attrib.pop('sizes',None)
                    parent=target.getparent()
                    if parent.tag=='a' and 'image-open' in parent.get('class',''):
                        parent.set('href',path);parent.set('data-full',path);parent.set('data-caption',value['alt'])
                elif value['src']!=base['value']['src']:
                    target.set('src',value['src']);target.attrib.pop('srcset',None)
                    parent=target.getparent()
                    if parent.tag=='a' and 'image-open' in parent.get('class',''):
                        parent.set('href',value['src']);parent.set('data-full',value['src'])
        doc.xpath('//title')[0].text=page['seoTitle']
        for name,value in [('description',page['seoDescription']),('twitter:title',page['seoTitle']),('twitter:description',page['seoDescription'])]:
            for e in doc.xpath('//meta[@name=$name]',name=name):e.set('content',value)
        for name,value in [('og:title',page['seoTitle']),('og:description',page['seoDescription'])]:
            for e in doc.xpath('//meta[@property=$name]',name=name):e.set('content',value)
        for script in doc.xpath('//script[@type="application/ld+json"]'):
            data=update_json(json.loads(script.text),settings)
            for n in data.get('@graph',[]):
                if n.get('@type')=='WebPage':n['name']=page['seoTitle'];n['description']=page['seoDescription']
            script.text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
        for e in doc.xpath('//*[@href]'):
            link=e.get('href')
            if link.startswith('https://wa.me/'):
                parts=urlsplit(link);e.set('href',urlunsplit((parts.scheme,parts.netloc,'/'+settings['phone'],parts.query,'')))
            elif link.startswith('mailto:'):e.set('href','mailto:'+settings['email'])
            elif 'facebook.com' in link:
                if settings.get('facebook'):e.set('href',settings['facebook'])
                else:e.getparent().remove(e)
        for element in doc.iter():
            if element.tag in ['script','style']:continue
            for attr in ['text','tail']:
                value=getattr(element,attr,None)
                if value:
                    value=value.replace('contacto.sinteria@gmail.com',settings['email']).replace('+51 932 280 554',phone_display(settings['phone'])).replace('51 932 280 554',phone_display(settings['phone']).lstrip('+')).replace('Sinteria Automatizaciones',settings['brandName'])
                    setattr(element,attr,value)
        footer=doc.xpath('//footer//div[contains(concat(" ",@class," ")," footer-group ")]')
        if footer:
            etree.SubElement(footer[0],'a',href='/catalogos.html').text='Catálogos de soluciones'
            if settings.get('tiktok'):
                etree.SubElement(footer[-1],'a',href=settings['tiktok'],target='_blank',rel='noopener noreferrer').text='TikTok de Sinteria'
        script=etree.SubElement(doc.xpath('//body')[0],'script',src='/panel-visitas.js',defer='defer')
        script.set('data-panel',panel_url)
        docs[source['file']]=doc
    catalog=deepcopy(docs['index.html']);main=catalog.xpath('//main')[0]
    for e in list(main):main.remove(e)
    section=etree.SubElement(main,'section',{'class':'v-section v-glow-section'});container=etree.SubElement(section,'div',{'class':'container'})
    etree.SubElement(container,'div',{'class':'eyebrow'}).text='SINTERIA · SOLUCIONES PARA TU NEGOCIO'
    etree.SubElement(container,'h1').text='Catálogos de sistemas y automatización'
    etree.SubElement(container,'p').text='Explora soluciones a medida para organizar tus procesos y presentar tu negocio en internet. Consulta el alcance de cada proyecto con Sinteria.'
    grid=etree.SubElement(container,'div',{'class':'seo-feature-grid','style':'margin-top:30px'})
    visible=[c for c in content['catalogs'] if c.get('visible')]
    for item in visible:
        card=etree.SubElement(grid,'article',{'class':'seo-feature','id':'catalogo-'+item['id']})
        etree.SubElement(card,'h2').text=item['title']
        if item['subtitle']:etree.SubElement(card,'p',{'class':'eyebrow'}).text=item['subtitle']
        etree.SubElement(card,'p').text=item['description']
        for image in item['images']:
            etree.SubElement(card,'img',src=image_path(image),alt=image['alt'],loading='lazy',decoding='async',style='width:100%;height:auto;border-radius:12px;margin-top:18px')
        etree.SubElement(card,'a',href='https://wa.me/'+settings['phone'],target='_blank',rel='noopener noreferrer',**{'class':'text-link'}).text='Consultar por WhatsApp ↗'
    if not visible:
        for p in content['pages'][1:]:
            card=etree.SubElement(grid,'article',{'class':'seo-feature'});etree.SubElement(card,'h2').text=p['name'];etree.SubElement(card,'p').text=p['seoDescription'];etree.SubElement(card,'a',href='/'+p['file'],**{'class':'text-link'}).text='Ver esta solución ↗'
    title='Catálogos de sistemas y automatización | '+settings['brandName'];description='Explora los catálogos y servicios de Sinteria: sistemas personalizados, inventarios, automatización y páginas web para negocios en Perú.'
    catalog.xpath('//title')[0].text=title
    catalog.xpath('//link[@rel="canonical"]')[0].set('href',ORIGIN+'/catalogos.html')
    for name,value in [('description',description),('twitter:title',title),('twitter:description',description)]:
        for e in catalog.xpath('//meta[@name=$name]',name=name):e.set('content',value)
    for name,value in [('og:title',title),('og:description',description),('og:url',ORIGIN+'/catalogos.html')]:
        for e in catalog.xpath('//meta[@property=$name]',name=name):e.set('content',value)
    for e in catalog.xpath('//nav[@id="menu-principal"]/a'):e.attrib.pop('aria-current',None)
    for script in catalog.xpath('//script[@type="application/ld+json"]'):
        data=json.loads(script.text)
        data['@graph']=[n for n in data['@graph'] if n.get('@type') in ['Organization','WebSite']]
        data['@graph'].append({'@type':'CollectionPage','@id':ORIGIN+'/catalogos.html#pagina','url':ORIGIN+'/catalogos.html','name':title,'description':description,'inLanguage':'es-PE','isPartOf':{'@id':ORIGIN+'/#sitio'}})
        script.text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    docs['catalogos.html']=catalog
    for name,doc in docs.items():
        if len(doc.xpath('//h1'))!=1:raise ValueError('Encabezados inválidos.')
        (output/name).write_text(serialize(doc))
    # Only aggregate counts; no IP addresses, cookies or visitor identifiers are sent.
    (output/'panel-visitas.js').write_text("(()=>{try{const s=document.currentScript,p=s.dataset.panel,k='sinteria-visita',n=Date.now(),o=Number(sessionStorage.getItem(k)||0);if(!p||n-o<1800000)return;sessionStorage.setItem(k,String(n));navigator.sendBeacon(p+'/public/visit','visita')}catch{}})();\n")
    admin=output/'admin';admin.mkdir(exist_ok=True)
    safe_panel=json.dumps(panel_url+'/admin/').replace('<','\\u003c')
    (admin/'index.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Panel de Sinteria</title><p>Abriendo el panel administrativo…</p><script>location.replace('+safe_panel+')</script></html>')
    ns='http://www.sitemaps.org/schemas/sitemap/0.9';root=etree.Element('{'+ns+'}urlset',nsmap={None:ns});urls=[]
    date=str(snapshot.get('updatedAt','2026-10-29'))[:10]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):raise ValueError('Fecha inválida.')
    for name in docs:
        loc=ORIGIN+('/' if name=='index.html' else '/'+name);urls.append(loc);entry=etree.SubElement(root,'{'+ns+'}url');etree.SubElement(entry,'{'+ns+'}loc').text=loc;etree.SubElement(entry,'{'+ns+'}lastmod').text=date
    (output/'sitemap.xml').write_bytes(etree.tostring(root,xml_declaration=True,encoding='UTF-8',pretty_print=True));(output/'sitemap.txt').write_text('\n'.join(urls)+'\n');(output/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /panel-cloudflare/\n\nSitemap: '+ORIGIN+'/sitemap.xml\nSitemap: '+ORIGIN+'/sitemap.txt\n')
    (output/'cms-revision.json').write_text(json.dumps({'revision':snapshot['revision'],'updatedAt':snapshot['updatedAt']}))
    return {'pages':len(docs),'customImages':len(image_ids),'customImageBytes':total,'urls':urls}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--panel-url',required=True);parser.add_argument('--output',default=str(ROOT/'public-panel-build'));args=parser.parse_args()
    u=urlparse(args.panel_url)
    if u.scheme!='https' or u.username or u.password or u.path not in ['', '/'] or not u.hostname or not u.hostname.endswith(('.workers.dev','.pages.dev')):
        raise ValueError('Configura la URL HTTPS real del panel desplegado.')
    panel_url=args.panel_url.rstrip('/')
    snapshot=json.loads(read_remote(panel_url+'/public/feed',MAX_BODY))
    print(json.dumps(build(snapshot,args.output,panel_url),ensure_ascii=False))

if __name__=='__main__':main()
