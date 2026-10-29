from pathlib import Path
from copy import deepcopy
from io import BytesIO
import json
from lxml import html,etree
from PIL import Image
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publisher',ROOT/'panel-cloudflare/publish.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
seed=json.loads((ROOT/'panel-cloudflare/seed.json').read_text());c=deepcopy(seed)
c['fields'][0]['value']='Automatización <script>alert(1)</script> para negocios'
c['settings']['phone']='51987654321';c['settings']['tiktok']='https://www.tiktok.com/@sinteria';c['settings']['email']='prueba@example.com'
image_id='12345678-1234-1234-1234-123456789abc'
c['fields'][next(i for i,v in enumerate(c['fields']) if v['kind']=='image')]['value']={'mediaId':image_id,'src':'','alt':'Imagen de prueba'}
c['catalogs']=[{'id':'catalogo-1','title':'Mi catálogo','subtitle':'Sistema a medida','description':'Inventarios para negocios. <img src=x onerror=alert(1)>','images':[{'mediaId':image_id,'src':'','alt':'Foto del catálogo'}],'visible':True}]
image=Image.new('RGB',(32,24),'#204b68');buf=BytesIO();image.save(buf,'WEBP');fixture=buf.getvalue()
snapshot={'revision':'test-revision','updatedAt':'2026-10-29T20:00:00Z','content':c}
output=ROOT/'panel-test-build'
result=module.build(snapshot,output,'https://panel-prueba.example.workers.dev',lambda _:fixture)
assert result['pages']==8 and result['customImages']==1
local_links=0
for file in output.glob('*.html'):
 if file.name.startswith('google') or file.name=='404.html':continue
 doc=html.parse(str(file))
 assert len(doc.xpath('//h1'))==1
 assert not doc.xpath('//main//script')
 assert not doc.xpath('//*[@onerror]')
 assert doc.xpath('string(//link[@rel="canonical"]/@href)').startswith('https://sinteria.github.io/')
 for script in doc.xpath('//script[@type="application/ld+json"]'):
  data=json.loads(script.text)
  org=next(n for n in data['@graph'] if n['@type']=='Organization')
  assert org['email']=='prueba@example.com' and org['telephone']=='+51 987 654 321'
 for link in doc.xpath('//a[starts-with(@href,"https://wa.me/")]/@href'):assert link.startswith('https://wa.me/51987654321')
 for link in doc.xpath('//*[@href or @src]'):
  for attr in ['href','src']:
   value=link.get(attr,'')
   if value.startswith('/') and not value.startswith('//'):
    target=(output/(value.split('?')[0].split('#')[0].lstrip('/') or 'index.html'))
    assert target.is_file(),(file.name,value)
    local_links+=1
 assert doc.xpath('//a[contains(@href,"tiktok.com/@sinteria")]')
assert 'Automatización &lt;script&gt;' in (output/'index.html').read_text()
assert not (output/'panel-cloudflare').exists()
assert not (output/'.git').exists()
urls=etree.parse(str(output/'sitemap.xml')).xpath('//*[local-name()="loc"]/text()');assert len(urls)==8
assert '/admin/' not in '\n'.join(urls)
bad=deepcopy(snapshot);bad['content']['settings']['tiktok']='javascript:alert(1)'
try:module.validate(bad);raise AssertionError('Unsafe URL accepted')
except ValueError:pass
bad=deepcopy(snapshot);bad['content']['catalogs'][0]['images']*=7
try:module.validate(bad);raise AssertionError('Image count accepted')
except ValueError:pass
print(json.dumps({'pages':result['pages'],'local_references':local_links,'seo_and_contacts':'passed','html_injection':'escaped','catalogs':'passed','image_bytes':len(fixture)},ensure_ascii=False))
(ROOT/'panel-cloudflare/fixture.webp').write_bytes(fixture)
