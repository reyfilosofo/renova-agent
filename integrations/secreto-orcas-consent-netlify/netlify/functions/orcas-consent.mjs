import { createHash, createHmac } from 'node:crypto';
import { getStore } from '@netlify/blobs';
const ALLOWED_PAYMENT_LINKS = new Set(['plink_1U84edGYktVBPuyCfPf3vPwm','plink_1U7sU4GYktVBPuyCTse426AJ']);
const VERSION='2.2';
const TEXT='Confirmo que cuento con autorización para compartir las imágenes proporcionadas y permito su uso exclusivamente para crear y entregarme mi edición personalizada de Secreto de Orcas mediante herramientas digitales y de inteligencia artificial. Las imágenes no se utilizarán para publicidad ni difusión pública sin autorización adicional. Las copias operativas bajo control de la editorial se eliminarán dentro de los 30 días posteriores a la entrega, conforme al aviso de privacidad. Acepto y declaro contar con facultades legales suficientes para ello.';
const digest=createHash('sha256').update(TEXT).digest('hex');
const env=k=>Netlify.env.get(k);
const ready=()=>!!(env('STRIPE_SECRET_KEY')&&env('ORCAS_CONSENT_HASH_KEY')&&env('ORCAS_PRIVACY_URL'));
const reply=(obj,status=200)=>Response.json(obj,{status,headers:{'cache-control':'no-store','referrer-policy':'no-referrer','x-content-type-options':'nosniff'}});
const valid=s=>typeof s==='string'&&s.length<190&&/^cs_(live_|test_)[A-Za-z0-9]+$/.test(s);
const hash=s=>createHmac('sha256',env('ORCAS_CONSENT_HASH_KEY')).update(s).digest('hex');
async function paidAndRelevant(s){
 const r=await fetch('https://api.stripe.com/v1/checkout/sessions/'+encodeURIComponent(s),{headers:{Authorization:'Bearer '+env('STRIPE_SECRET_KEY')},signal:AbortSignal.timeout(9000)});
 if(!r.ok)return false;
 const session=await r.json();
 return session.livemode===true&&session.payment_status === 'paid'&&session.status==='complete'&&ALLOWED_PAYMENT_LINKS.has(session.payment_link);
}
export default async function handler(req) {
 if(!['GET','POST'].includes(req.method))return reply({error:'method_not_allowed'},405);
 if(req.method==='POST'&&req.headers.get('origin')!==new URL(req.url).origin)return reply({error:'origin_mismatch'},403);
 if(!ready())return reply({ready:false,error:'requires_private_configuration'},503);
 let input;try{input=req.method==='POST'?await req.json():{session_id:new URL(req.url).searchParams.get('session_id')};}catch{return reply({error:'invalid_json'},400);}
 if(!valid(input.session_id))return reply({error:'invalid_session'},400);
 try{
  if(!await paidAndRelevant(input.session_id))return reply({error:'not_an_eligible_paid_order'},403);
  const key=hash(input.session_id),store=getStore({name:'secreto-orcas-consent-v22',consistency:'strong'});
  const old=await store.get(key,{type:'json'});
  if(req.method==='GET')return reply({ready:true,paid:true,previously_authorized:!!old,version:VERSION,privacy_url:env('ORCAS_PRIVACY_URL')});
  if(input.authorize !== true||input.declares_legal_authority!==true||input.version!==VERSION)return reply({error:'affirmative_legal_consent_required'},422);
  if(old)return reply({recorded:true,previously_recorded:true,version:VERSION});
  const receipt={version:VERSION,date_utc:new Date().toISOString(),payment_session_hmac_sha256:key,consent_text_sha256:digest,declares_legal_authority:true,notice_url:env('ORCAS_PRIVACY_URL'),purpose:'Crear y entregar Secreto de Orcas personalizado, sin uso publicitario'};
  const write=await store.setJSON(key,receipt,{onlyIfNew:true});
  if(!write.modified&&!(await store.get(key,{type:'json'})))return reply({error:'not_persisted'},500);
  return reply({recorded:true,version:VERSION});
 }catch(e){console.error('Consent backend temporarily unavailable',e?.name||'Error');return reply({error:'service_unavailable'},503);}
}
export const config={path:'/api/orcas-consent',method:['GET','POST'],rateLimit:{action:'rate_limit',aggregateBy:'ip',windowSize:60,windowLimit:15}};
