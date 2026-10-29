"""Skip scheduled publication when the public revision has not changed."""
import json, os
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def get(url, maximum=524288):
    with urlopen(Request(url,headers={'User-Agent':'Sinteria-static-publisher/1.0','Cache-Control':'no-cache'}),timeout=30) as response:
        data=response.read(maximum+1)
        if len(data)>maximum:raise ValueError('Contenido fuera de límite')
        return json.loads(data)

panel=os.environ['SINTERIA_PANEL_URL'].rstrip('/')
u=urlparse(panel)
if u.scheme!='https' or u.username or u.password or u.path or not u.hostname or not u.hostname.endswith(('.workers.dev','.pages.dev')):raise ValueError('URL del panel inválida')
feed=get(panel+'/public/feed')
try:
    current=get('https://sinteria.github.io/cms-revision.json',4096)
except HTTPError as e:
    if e.code!=404:raise
    current={}
changed=feed.get('revision')!=current.get('revision') or os.environ.get('SINTERIA_FORCE_BUILD')=='true'
with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('changed='+str(changed).lower()+'\n')
print('Hay una versión nueva para publicar.' if changed else 'Sin cambios; no se crea ningún archivo de publicación.')
