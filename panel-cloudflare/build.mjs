import {readFile,writeFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const seed=await readFile(new URL('seed.json',root),'utf8');
const ui=await readFile(new URL('admin.html',root),'utf8');
let worker=await readFile(new URL('worker.mjs',root),'utf8');
worker=worker.replace("import { SEED } from './seed.mjs';",'const SEED='+seed+';').replace("import { ADMIN_HTML } from './admin-ui.mjs';",'const ADMIN_HTML='+JSON.stringify(ui)+';');
await writeFile(new URL('deploy-worker.mjs',root),worker);
console.log('Worker compilado: '+Buffer.byteLength(worker)+' bytes. Sin claves incluidas.');
