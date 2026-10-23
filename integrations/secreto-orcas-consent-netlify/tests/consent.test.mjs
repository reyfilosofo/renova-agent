import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const server=readFileSync(new URL('../netlify/functions/orcas-consent.mjs',import.meta.url),'utf8');
test('Nombre canónico',()=>assert.match(html,/<h1>Secreto de Orcas<\/h1>/));
test('No premarca casilla',()=>assert.match(html,/type="checkbox" disabled/));
test('Verifica pago y producto',()=>{assert.match(server,/payment_status === 'paid'/);assert.match(server,/ALLOWED_PAYMENT_LINKS.has/);});
test('Solo consentimiento afirmativo',()=>assert.match(server,/input.authorize !== true/));
test('Registra sin guardar fotografías',()=>{assert.match(server,/onlyIfNew:true/);assert.doesNotMatch(server,/req\.formData\(/);});
