import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
const file=new URL("./operational-shell.html",import.meta.url);
const html=fs.readFileSync(file,"utf8");
const expected=["inicio","earn","observatorio","recursos","wallets","ledger","sistema"];
test("one document contains seven integrated modules",()=>{
  for(const id of expected){
    assert.match(html,new RegExp('<section class="view" id="'+id+'"'));
    assert.match(html,new RegExp('data-view="'+id+'"'));
  }
  assert.equal((html.match(/<html/g)||[]).length,1);
});
test("navigation and controls have unique IDs",()=>{
  const ids=[...html.matchAll(/\sid="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(new Set(ids).size,ids.length);
  assert.equal((html.match(/role="tab"/g)||[]).length,expected.length);
});
test("inline browser script is syntactically valid",()=>{
  const match=html.match(/<script type="module">([\s\S]*?)<\/script>/);
  assert.ok(match,"missing module script");
  assert.doesNotThrow(()=>new vm.Script(match[1]));
});
test("no wallet keys, financial execution or example prices",()=>{
  assert.doesNotMatch(html,/window\.ethereum\.request|eth_sendTransaction|personal_sign|eth_signTypedData|wallet_switchEthereumChain/i);
  assert.doesNotMatch(html,/\.innerHTML\s*=|eval\s*\(|new Function\s*\(/);
  assert.match(html,/No verificados|No verificado/);
  assert.match(html,/READ ONLY · PAPER/);
  assert.match(html,/NOT?|NO CONECTADA/);
});
test("public source is declared, private personal data is not embedded",()=>{
  assert.match(html,/raw\.githubusercontent\.com\/reyfilosofo\/renova-agent\/main\/money-resources\/data\/latest\.json/);
  assert.doesNotMatch(html,/sk-[a-z0-9]{10}|mnemonic|secretKey\s*=/i);
  assert.match(html,/ACCESS UNAVAILABLE/);
  assert.match(html,/last_verified_at_utc/);
});
