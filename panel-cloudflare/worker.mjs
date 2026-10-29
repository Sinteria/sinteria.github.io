import { SEED } from './seed.mjs';
import { ADMIN_HTML } from './admin-ui.mjs';

export const LIMITS=Object.freeze({maxImages:60,imageBytes:524288,storageBytes:20971520,catalogs:12,imagesPerCatalog:6,bodyBytes:524288,savesPerDay:30,publishesPerDay:12,uploadsPerDay:30,visitsPerDay:2000,visitsPerMonth:50000});
const encoder=new TextEncoder();
const headers={'X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin','X-Robots-Tag':'noindex, nofollow','Cache-Control':'no-store'};
class Problem extends Error {constructor(status,message){super(message);this.status=status;}}
const json=(data,status=200,extra={})=>new Response(JSON.stringify(data),{status,headers:{...headers,'Content-Type':'application/json; charset=utf-8',...extra}});
const hex=bytes=>Array.from(new Uint8Array(bytes),n=>n.toString(16).padStart(2,'0')).join('');
export async function digest(value){return hex(await crypto.subtle.digest('SHA-256',encoder.encode(value)));}
const b64=bytes=>btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
function unb64(value){const normalized=value.replaceAll('-','+').replaceAll('_','/');return Uint8Array.from(atob(normalized+'='.repeat((4-normalized.length%4)%4)),c=>c.charCodeAt(0));}
const dateKey=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Lima',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
function text(value,max,label,empty=false){if(typeof value!=='string'||value.length>max||(!empty&&!value.trim())||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value))throw new Problem(400,'Revisa '+label+'.');return value.trim();}
function social(value,hosts,label){value=text(value,300,label,true);if(!value)return '';let u;try{u=new URL(value);}catch{throw new Problem(400,'Enlace inválido: '+label);}if(u.protocol!=='https:'||u.username||u.password||!hosts.some(h=>u.hostname===h||u.hostname.endsWith('.'+h)))throw new Problem(400,'Enlace no permitido: '+label);return u.href;}
export function validateContent(input){
 if(!input||input.schemaVersion!==1||!Array.isArray(input.fields)||!Array.isArray(input.pages)||!Array.isArray(input.catalogs)||input.catalogs.length>LIMITS.catalogs)throw new Problem(400,'Estructura o cantidad de catálogos inválida.');
 const settings=input.settings||{},phone=text(settings.phone,15,'el WhatsApp');
 if(!/^\d{8,15}$/.test(phone))throw new Problem(400,'El WhatsApp debe incluir el código de país y solo números.');
 if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(settings.email||''))throw new Problem(400,'Revisa el correo de contacto.');
 const clean={schemaVersion:1,settings:{brandName:text(settings.brandName,80,'el nombre'),phone,email:text(settings.email,160,'el correo'),tiktok:social(settings.tiktok,['tiktok.com'],'TikTok'),facebook:social(settings.facebook,['facebook.com','fb.com'],'Facebook')},pages:[],fields:[],catalogs:[]};
 if(input.pages.length!==SEED.pages.length||input.fields.length!==SEED.fields.length)throw new Problem(400,'No se pueden eliminar las páginas o los campos del sitio.');
 for(const base of SEED.pages){const p=input.pages.find(p=>p.id===base.id);if(!p)throw new Problem(400,'Falta una página.');clean.pages.push({...base,seoTitle:text(p.seoTitle,80,'el título SEO'),seoDescription:text(p.seoDescription,170,'la descripción SEO')});}
 const originals=new Set(SEED.fields.filter(f=>f.kind==='image').map(f=>f.value.src));
 const image=(v,allowOriginal=true)=>{if(!v||typeof v!=='object')throw new Problem(400,'Selecciona una imagen.');if(v.mediaId){if(!/^[a-f0-9-]{36}$/.test(v.mediaId))throw new Problem(400,'Imagen inválida.');return{mediaId:v.mediaId,src:'',alt:text(v.alt,200,'la descripción de la imagen',true)};}if(!allowOriginal||!originals.has(v.src))throw new Problem(400,'Usa una imagen de la biblioteca.');return{mediaId:null,src:v.src,alt:text(v.alt,200,'la descripción de la imagen',true)};};
 const usedIds=new Set();
 for(const base of SEED.fields){const matches=input.fields.filter(f=>f.id===base.id);if(matches.length!==1||usedIds.has(base.id))throw new Problem(400,'Campo duplicado o faltante.');usedIds.add(base.id);const f=matches[0];clean.fields.push({...base,value:base.kind==='image'?image(f.value):text(f.value,base.maxLength,base.label)});}
 const catalogIds=new Set();
 for(const item of input.catalogs){if(!/^[a-z0-9-]{1,60}$/.test(item.id)||catalogIds.has(item.id)||!Array.isArray(item.images)||item.images.length>LIMITS.imagesPerCatalog)throw new Problem(400,'Revisa las imágenes o el identificador del catálogo.');catalogIds.add(item.id);clean.catalogs.push({id:item.id,title:text(item.title,100,'el nombre del catálogo'),subtitle:text(item.subtitle,200,'el subtítulo',true),description:text(item.description,1600,'la descripción'),images:item.images.map(v=>image(v)),visible:item.visible===true});}
 if(encoder.encode(JSON.stringify(clean)).length>LIMITS.bodyBytes)throw new Problem(413,'El contenido supera el límite del panel.');return clean;
}
async function limited(request,max){const announced=Number(request.headers.get('content-length'));if(announced>max)throw new Problem(413,'El archivo o contenido supera el límite.');if(!request.body)return new Uint8Array();const reader=request.body.getReader(),parts=[];let total=0;while(true){const{value,done}=await reader.read();if(done)break;total+=value.length;if(total>max){await reader.cancel();throw new Problem(413,'El archivo o contenido supera el límite.');}parts.push(value);}const result=new Uint8Array(total);let offset=0;for(const part of parts){result.set(part,offset);offset+=part.length;}return result;}
async function body(request){try{return JSON.parse(new TextDecoder().decode(await limited(request,LIMITS.bodyBytes)));}catch(e){if(e instanceof Problem)throw e;throw new Problem(400,'El contenido no es válido.');}}
export function imageInfo(bytes,mime){
 const data=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let width=0,height=0;
 if(mime==='image/png'&&bytes.length>32&&bytes[0]===137&&String.fromCharCode(...bytes.slice(1,4))==='PNG'){width=data.getUint32(16);height=data.getUint32(20);}
 else if(mime==='image/webp'&&bytes.length>30&&String.fromCharCode(...bytes.slice(0,4))==='RIFF'&&String.fromCharCode(...bytes.slice(8,12))==='WEBP'){
  const kind=String.fromCharCode(...bytes.slice(12,16));if(kind==='VP8X'){if(bytes[20]&2)throw new Problem(400,'Utiliza una imagen fija.');width=1+bytes[24]+(bytes[25]<<8)+(bytes[26]<<16);height=1+bytes[27]+(bytes[28]<<8)+(bytes[29]<<16);}else if(kind==='VP8 '&&bytes[23]===157&&bytes[24]===1&&bytes[25]===42){width=data.getUint16(26,true)&16383;height=data.getUint16(28,true)&16383;}else if(kind==='VP8L'&&bytes[20]===47){const packed=data.getUint32(21,true);width=1+(packed&16383);height=1+((packed>>>14)&16383);}}
 else if(mime==='image/jpeg'&&bytes[0]===255&&bytes[1]===216){let i=2;while(i+9<bytes.length){if(bytes[i++]!==255)continue;const marker=bytes[i++];if(marker===216||marker===217)continue;const length=data.getUint16(i);if(length<2||i+length>bytes.length)break;if([192,193,194,195,197,198,199,201,202,203,205,206,207].includes(marker)){height=data.getUint16(i+3);width=data.getUint16(i+5);break;}i+=length;}}
 if(width<1||height<1||width>2000||height>2000)throw new Problem(400,'Imagen inválida o mayor de 2000 píxeles. El panel puede optimizarla antes de subirla.');return{width,height};
}
async function quota(db,key,limit,day=dateKey()){const row=await db.prepare('INSERT INTO quota(key,day,count) VALUES(?1,?2,1) ON CONFLICT(key) DO UPDATE SET count=count+1 WHERE count<?3 RETURNING count').bind(key,day,limit).first();if(!row)throw new Problem(429,'Se alcanzó el límite de esta operación. Inténtalo en el siguiente periodo.');return row.count;}
async function signingKey(env){return crypto.subtle.importKey('raw',encoder.encode(env.SESSION_SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
async function sessionCookie(env){const data=b64(encoder.encode(JSON.stringify({exp:Date.now()+7200000,nonce:crypto.randomUUID()})));const signature=await crypto.subtle.sign('HMAC',await signingKey(env),encoder.encode(data));return 'sinteria_admin='+data+'.'+b64(signature)+'; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=7200';}
async function authenticated(request,env){try{const cookie=request.headers.get('cookie')?.match(/(?:^|;\s*)sinteria_admin=([^;]+)/)?.[1];if(!cookie)return false;const[data,signature,extra]=cookie.split('.');if(extra||!signature||data.length>500)return false;const valid=await crypto.subtle.verify('HMAC',await signingKey(env),unb64(signature),encoder.encode(data));return valid&&JSON.parse(new TextDecoder().decode(unb64(data))).exp>Date.now();}catch{return false;}}
function requireOrigin(request,url){if(request.headers.get('origin')!==url.origin)throw new Problem(403,'Solicitud no permitida.');}
async function state(env){let row=await env.DB.prepare('SELECT * FROM content WHERE id=1').first();if(!row){const seed=JSON.stringify(SEED);await env.DB.prepare('INSERT OR IGNORE INTO content(id,draft,published,published_rev,updated_at) VALUES(1,?1,?1,?2,?3)').bind(seed,'initial',new Date().toISOString()).run();row=await env.DB.prepare('SELECT * FROM content WHERE id=1').first();}return row;}
async function refsExist(db,content){const ids=new Set([...content.fields.filter(f=>f.kind==='image').map(f=>f.value.mediaId),...content.catalogs.flatMap(c=>c.images.map(i=>i.mediaId))].filter(Boolean));for(const id of ids){if(!await db.prepare('SELECT id FROM media WHERE id=?1').bind(id).first())throw new Problem(400,'Una imagen seleccionada ya no existe.');}}
async function mediaList(db){return(await db.prepare('SELECT id,name,mime,bytes,width,height,created_at FROM media ORDER BY created_at DESC').all()).results;}
async function api(request,env,ctx){
 const url=new URL(request.url),path=url.pathname;
 if(path==='/'||path==='/admin'||path==='/admin/')return new Response(ADMIN_HTML,{headers:{...headers,'Content-Type':'text/html; charset=utf-8','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' https://sinteria.github.io blob: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}});
 if(path==='/robots.txt')return new Response('User-agent: *\nDisallow: /\n',{headers:{...headers,'Content-Type':'text/plain; charset=utf-8'}});
 if(path==='/health')return json({service:'Sinteria panel',configured:!!env.DB&&env.FREE_PLAN_CONFIRMED==='true'&&!!env.ADMIN_PASSWORD_HASH&&!!env.SESSION_SECRET});
 if(!env.DB||env.FREE_PLAN_CONFIRMED!=='true'||!env.ADMIN_PASSWORD_HASH||!env.SESSION_SECRET||env.SESSION_SECRET.length<32)throw new Problem(503,'El panel espera la configuración y la confirmación del plan gratuito.');
 if(path.startsWith('/media/')&&request.method==='GET'){
  const id=path.slice(7);if(!/^[a-f0-9-]{36}$/.test(id))throw new Problem(404,'Imagen no encontrada.');
  const key=new Request(url.origin+path);if(globalThis.caches?.default){const cached=await caches.default.match(key);if(cached)return cached;}
  const row=await env.DB.prepare('SELECT mime,body FROM media WHERE id=?1').bind(id).first();if(!row)throw new Problem(404,'Imagen no encontrada.');
  const imageHeaders={'Content-Type':row.mime,'Cache-Control':'public, max-age=86400, immutable','X-Content-Type-Options':'nosniff','Cross-Origin-Resource-Policy':'cross-origin','Access-Control-Allow-Origin':'*'};const response=new Response(new Uint8Array(row.body),{headers:imageHeaders});if(globalThis.caches?.default&&ctx?.waitUntil)ctx.waitUntil(caches.default.put(key,response.clone()));return response;
 }
 if(path==='/public/feed'&&request.method==='GET'){const row=await state(env);const etag='"'+row.published_rev+'"';if(request.headers.get('if-none-match')===etag)return new Response(null,{status:304,headers:{ETag:etag,'Cache-Control':'public, max-age=60'}});return json({revision:row.published_rev,updatedAt:row.updated_at,content:JSON.parse(row.published)},200,{'Cache-Control':'public, max-age=60',ETag:etag,'Access-Control-Allow-Origin':'*'});}
 if(path==='/public/visit'&&request.method==='POST'){
  if(request.headers.get('origin')!=='https://sinteria.github.io')return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Origin':'https://sinteria.github.io'}});
  const day=dateKey(),month=day.slice(0,7);try{await quota(env.DB,'visits:'+day,LIMITS.visitsPerDay);await quota(env.DB,'visit-month:'+month,LIMITS.visitsPerMonth);}catch(e){if(e.status===429)return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Origin':'https://sinteria.github.io'}});throw e;}
  await env.DB.batch([env.DB.prepare('INSERT INTO visits(day,count) VALUES(?1,1) ON CONFLICT(day) DO UPDATE SET count=count+1').bind(day),env.DB.prepare("UPDATE counters SET count=count+1 WHERE key='total'")]);return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Origin':'https://sinteria.github.io'}});
 }
 if(path==='/api/login'&&request.method==='POST'){
  requireOrigin(request,url);const input=await body(request);const ip=request.headers.get('CF-Connecting-IP')||'local';const stamp=Math.floor(Date.now()/900000);const ipHash=await digest(env.SESSION_SECRET+ip+dateKey());await quota(env.DB,'login:'+ipHash.slice(0,24)+':'+stamp,5);await quota(env.DB,'login-day:'+dateKey(),200);
  if(typeof input.password!=='string'||input.password.length>256)throw new Problem(400,'Revisa la clave.');const actual=await digest(input.password);const expected=String(env.ADMIN_PASSWORD_HASH).toLowerCase();if(!/^[a-f0-9]{64}$/.test(expected)||!await crypto.subtle.verify('HMAC',await signingKey(env),await crypto.subtle.sign('HMAC',await signingKey(env),encoder.encode(expected)),encoder.encode(actual)))throw new Problem(401,'La clave no es correcta.');
  await env.DB.batch([env.DB.prepare("DELETE FROM quota WHERE (day<?1 AND key NOT LIKE 'visit-month:%') OR day<?2").bind(new Date(Date.now()-3*86400000).toISOString().slice(0,10),new Date(Date.now()-65*86400000).toISOString().slice(0,10)),env.DB.prepare('DELETE FROM visits WHERE day<?1').bind(new Date(Date.now()-400*86400000).toISOString().slice(0,10))]);return json({ok:true},200,{'Set-Cookie':await sessionCookie(env)});
 }
 if(!path.startsWith('/api/'))throw new Problem(404,'Ruta no encontrada.');
 if(!await authenticated(request,env))throw new Problem(401,'Inicia sesión para continuar.');
 if(request.method!=='GET')requireOrigin(request,url);
 if(path==='/api/logout'&&request.method==='POST')return json({ok:true},200,{'Set-Cookie':'sinteria_admin=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0'});
 if(path==='/api/state'&&request.method==='GET'){const row=await state(env),media=await mediaList(env.DB);return json({content:JSON.parse(row.draft),revision:row.draft_rev,publishedRevision:row.published_rev,media,limits:LIMITS,storageBytes:media.reduce((n,m)=>n+m.bytes,0),updatedAt:row.updated_at});}
 if(path==='/api/content'&&request.method==='PUT'){
  const input=await body(request),clean=validateContent(input.content);await refsExist(env.DB,clean);await quota(env.DB,'save:'+dateKey(),LIMITS.savesPerDay);await state(env);
  const result=await env.DB.prepare('UPDATE content SET draft=?1,draft_rev=draft_rev+1,updated_at=?2 WHERE id=1 AND draft_rev=?3').bind(JSON.stringify(clean),new Date().toISOString(),input.revision).run();if(result.meta.changes!==1)throw new Problem(409,'El contenido cambió en otra sesión. Recarga antes de guardar.');return json({ok:true,revision:input.revision+1});
 }
 if(path==='/api/publish'&&request.method==='POST'){
  const input=await body(request),row=await state(env);if(input.revision!==row.draft_rev)throw new Problem(409,'Guarda la última versión antes de publicarla.');const clean=validateContent(JSON.parse(row.draft));await refsExist(env.DB,clean);await quota(env.DB,'publish:'+dateKey(),LIMITS.publishesPerDay);const revision=crypto.randomUUID();const result=await env.DB.prepare('UPDATE content SET published=?1,published_rev=?2,updated_at=?3 WHERE id=1 AND draft_rev=?4').bind(JSON.stringify(clean),revision,new Date().toISOString(),input.revision).run();if(result.meta.changes!==1)throw new Problem(409,'El borrador cambió mientras se publicaba. Guarda y vuelve a publicar.');return json({ok:true,revision,message:'Versión preparada. La actualización automática de la web puede tardar 15 minutos o más según la cola de publicación.'});
 }
 if(path==='/api/media'&&request.method==='POST'){
  const mime=request.headers.get('content-type')?.split(';')[0];if(!['image/webp','image/png','image/jpeg'].includes(mime))throw new Problem(415,'Solo se permiten imágenes JPG, PNG y WebP.');const bytes=await limited(request,LIMITS.imageBytes);const dimensions=imageInfo(bytes,mime);await quota(env.DB,'upload:'+dateKey(),LIMITS.uploadsPerDay);const id=crypto.randomUUID(),name=text(decodeURIComponent(request.headers.get('x-file-name')||'Imagen'),120,'el nombre de imagen');
  try{await env.DB.prepare('INSERT INTO media(id,name,mime,bytes,width,height,body,created_at) VALUES(?1,?2,?3,?4,?5,?6,?7,?8)').bind(id,name,mime,bytes.length,dimensions.width,dimensions.height,bytes,new Date().toISOString()).run();}catch(e){if(String(e).includes('MEDIA_LIMIT'))throw new Problem(409,'Biblioteca llena: máximo 60 imágenes y 20 MiB en total.');throw e;}return json({ok:true,id,...dimensions},201);
 }
 if(/^\/api\/media\/[a-f0-9-]{36}$/.test(path)&&request.method==='DELETE'){
  const id=path.split('/').pop(),row=await state(env);if(row.draft.includes(id)||row.published.includes(id))throw new Problem(409,'La imagen está en uso. Reemplázala y publica los cambios antes de eliminarla.');await quota(env.DB,'upload:'+dateKey(),LIMITS.uploadsPerDay);await env.DB.prepare('DELETE FROM media WHERE id=?1').bind(id).run();return json({ok:true});
 }
 if(path==='/api/stats'&&request.method==='GET'){
  const day=dateKey(),month=day.slice(0,7),daily=(await env.DB.prepare('SELECT day,count FROM visits WHERE day>=?1 AND day<=?2 ORDER BY day').bind(month+'-01',day).all()).results,total=await env.DB.prepare("SELECT count FROM counters WHERE key='total'").first();return json({month,total:total?.count||0,monthVisits:daily.reduce((n,d)=>n+d.count,0),daily,limit:LIMITS.visitsPerDay,notes:'Visitas registradas desde la activación; aproximadas, no personas únicas. Al alcanzar el límite se pausa el conteo, la web continúa disponible.'});
 }
 throw new Problem(404,'Ruta no encontrada.');
}
export default {async fetch(request,env,ctx){try{return await api(request,env,ctx);}catch(e){return json({error:e instanceof Problem?e.message:'No se pudo completar la operación. La web pública sigue disponible.'},e.status||503);}}};
