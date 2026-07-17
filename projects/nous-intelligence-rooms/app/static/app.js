const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let selectedFiles = [];
let currentAnalysis = null;
let currentMode = 'demo';

const demoInput = {
  organization: 'SERESARTE',
  sector: 'Creative & cultural organization',
  goal: 'Clarify positioning and priorities',
  website: 'https://seresarte.org',
  context: 'SERESARTE is a multidisciplinary cultural platform founded by Carlos Jonathan González Rodríguez. It integrates philosophy, art, cultural production, publishing, strategic intelligence and social-impact projects. It has produced dozens of events and large volumes of content, but its value proposition is distributed across multiple brands, initiatives and formats. The immediate decision is how to structure the portfolio, clarify the institutional narrative and convert accumulated intellectual and cultural capital into a focused 90-day operating agenda.'
};

const demoAnalysis = {
  meta: { mode:'demo', model:'GPT-5.6 design target', confidence:84, generated_at:'2026-07-17' },
  organization: 'SERESARTE', sector: 'Creative & cultural organization', decision: 'Clarify positioning and priorities',
  thesis: 'SERESARTE has strong intellectual and cultural capital, but its value is fragmented across brands, programs and formats.',
  summary: 'The central issue is not a lack of ideas, legitimacy or production capacity. It is the absence of a visible operating architecture that connects institutional identity, commercial offers, evidence of impact and a disciplined decision sequence. The fastest path to growth is to consolidate the portfolio, define one institutional narrative and convert existing assets into a prioritized system of offers, proof and next actions.',
  decision_enabled: 'Adopt a portfolio architecture with SERESARTE as the institutional platform, NOUS as the strategic intelligence offer, and ℛenova as the proprietary philosophical framework—then execute a 90-day proof-and-conversion sprint.',
  overall_score:72, score_interpretation:'High potential, uneven systemization.',
  metrics:[
    {name:'Identity',score:78},{name:'Communication',score:64},{name:'Digital experience',score:58},{name:'Operational clarity',score:61},{name:'Growth readiness',score:82}
  ],
  top_opportunity:{title:'Convert the existing body of work into a portfolio architecture',why:'The organization already owns substantial intellectual property, events, publications and strategic capabilities. Reframing these as a coherent system can create immediate clarity without inventing a new brand.'},
  top_risk:{title:'Narrative and offer fragmentation',why:'Multiple initiatives can appear unrelated, forcing each prospect to reconstruct the organization’s value. This increases cognitive load, weakens conversion and dilutes institutional authority.'},
  signals:[
    {type:'Strength',tone:'opportunity',title:'Unusually rich proprietary intellectual capital',body:'The organization combines philosophy, artistic production, cultural management, publishing and strategic consulting. This is a defensible differentiation when presented as a system rather than a list.',confidence:92,source:'Founder profile and project inventory'},
    {type:'Constraint',tone:'risk',title:'The architecture is clearer internally than externally',body:'A visitor may encounter several names and offers before understanding the institutional hierarchy, intended audience and path to engagement.',confidence:88,source:'Narrative review'},
    {type:'Opportunity',tone:'opportunity',title:'Proof can be converted into decision assets',body:'Existing event metrics, partnerships, publications and client work can become case studies, dashboards and credibility modules that reduce perceived risk.',confidence:86,source:'Historical outputs'},
    {type:'Risk',tone:'risk',title:'Founder dependency limits scale',body:'A large share of context and decision logic remains concentrated in the founder. Without explicit frameworks and repeatable intake systems, execution capacity remains constrained.',confidence:81,source:'Operating-model inference'},
    {type:'Market signal',tone:'neutral',title:'Organizations need integrated interpretation, not another isolated report',body:'NOUS can differentiate by linking brand, digital experience, operations, risk and execution in one evidence-backed decision room.',confidence:80,source:'Service design synthesis'},
    {type:'Strategic principle',tone:'neutral',title:'Do not replace judgment—structure it',body:'The product should preserve human authority while making evidence, assumptions, confidence and trade-offs legible.',confidence:96,source:'NOUS methodology'}
  ],
  decisions:[
    {rank:1,title:'Define and publish the portfolio architecture',detail:'One hierarchy, one diagram, one sentence per entity, one primary CTA.',impact:'Very high',effort:'Low',urgency:'7 days',quadrant:'Act now'},
    {rank:2,title:'Build a proof library',detail:'Convert events, metrics, publications and client outcomes into reusable evidence cards.',impact:'High',effort:'Medium',urgency:'30 days',quadrant:'Act now'},
    {rank:3,title:'Productize NOUS Intelligence Rooms',detail:'Create a repeatable intake, analysis schema, decision map and exportable executive brief.',impact:'Very high',effort:'Medium',urgency:'30 days',quadrant:'Plan'},
    {rank:4,title:'Create a single conversion pathway',detail:'Route each audience to a relevant offer, meeting or diagnostic instead of presenting the entire ecosystem at once.',impact:'High',effort:'Medium',urgency:'45 days',quadrant:'Plan'},
    {rank:5,title:'Document founder knowledge',detail:'Turn implicit criteria into prompts, checklists, rubrics and case templates.',impact:'Medium',effort:'Medium',urgency:'60 days',quadrant:'Delegate'},
    {rank:6,title:'Defer non-strategic visual proliferation',detail:'Avoid adding more sub-brands or redesigns until the architecture and offer system are stable.',impact:'Medium',effort:'Low',urgency:'Now',quadrant:'Defer'}
  ],
  roadmap:{
    '0–30 days':[
      {title:'Portfolio architecture',detail:'Institutional hierarchy, descriptors and audience map.'},
      {title:'Executive narrative',detail:'One master description in Spanish and English.'},
      {title:'Proof inventory',detail:'Select 12 strongest evidence assets and normalize them.'},
      {title:'MVP Intelligence Room',detail:'Deploy the working intake → analysis → roadmap flow.'}
    ],
    '31–60 days':[
      {title:'Offer system',detail:'Package diagnostics, strategic rooms and implementation phases.'},
      {title:'Case-study library',detail:'Publish three traceable examples with problem, evidence, decision and outcome.'},
      {title:'Lead routing',detail:'Create targeted CTAs for organizations, cultural partners and founders.'},
      {title:'Evaluation baseline',detail:'Measure clarity, usefulness, completion time and recommendation acceptance.'}
    ],
    '61–90 days':[
      {title:'Pilot cohort',detail:'Run five supervised rooms with real organizations.'},
      {title:'Operational handbook',detail:'Standardize prompts, quality gates and human review.'},
      {title:'Commercial launch',detail:'Publish pricing logic, engagement process and proof.'},
      {title:'Learning loop',detail:'Use pilot evidence to refine scoring and prioritization.'}
    ]
  },
  evidence:[
    {id:'E-01',observation:'The project portfolio spans cultural production, publishing, philosophy and strategic intelligence.',source:'Organizational context',confidence:96,implication:'The institutional architecture must organize diversity without erasing it.'},
    {id:'E-02',observation:'The current challenge is described as clarity and prioritization rather than ideation.',source:'Decision brief',confidence:94,implication:'The product should prioritize decisions and sequencing, not generate more concepts.'},
    {id:'E-03',observation:'Substantial outputs and impact claims exist but are not yet presented as a normalized proof system.',source:'Project inventory',confidence:84,implication:'A proof library can increase trust and conversion quickly.'},
    {id:'E-04',observation:'Multiple brands and initiatives depend on founder-held context.',source:'Operating-model inference',confidence:81,implication:'Explicit frameworks are needed to reduce key-person dependency.'},
    {id:'E-05',observation:'NOUS methodology already uses observe, verify, analyze, convert and produce.',source:'Existing methodology',confidence:98,implication:'The product workflow can be grounded in an authentic operating method.'}
  ]
};

async function init(){
  try{const r=await fetch('/api/health');const h=await r.json();if(h.live_available){$('#statusDot').classList.add('live');$('#modeText').textContent='Live API available';$('#modelText').textContent=h.model||'GPT-5.6';}else{$('#modeText').textContent='Demo mode';$('#modelText').textContent='Add API key for live analysis';}}catch(e){}
}
function setView(id){$$('.view').forEach(v=>v.classList.remove('active'));$(id).classList.add('active');window.scrollTo(0,0)}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2500)}
function fileSize(n){return n>1048576?(n/1048576).toFixed(1)+' MB':Math.ceil(n/1024)+' KB'}
function renderFiles(){const box=$('#fileList');box.innerHTML='';selectedFiles.forEach((f,i)=>{const el=document.createElement('div');el.className='file-chip';el.innerHTML=`<span>${f.name} · ${fileSize(f.size)}</span><button type="button" aria-label="Remove file">×</button>`;el.querySelector('button').onclick=()=>{selectedFiles.splice(i,1);renderFiles()};box.appendChild(el)})}
function addFiles(files){for(const f of files){if(selectedFiles.length>=3){toast('Maximum 3 files');break}if(f.size>8*1024*1024){toast(`${f.name} exceeds 8 MB`);continue}selectedFiles.push(f)}renderFiles()}
$('#files').addEventListener('change',e=>addFiles(e.target.files));
const dz=$('#dropzone');['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('drag')}));['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('drag')}));dz.addEventListener('drop',e=>addFiles(e.dataTransfer.files));
$('#loadDemoBtn').onclick=()=>{Object.entries(demoInput).forEach(([k,v])=>$('#'+k).value=v);$('#consent').checked=true;toast('Curated SERESARTE case loaded')};

async function filePayload(){const out=[];for(const f of selectedFiles){const data=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(String(r.result).split(',')[1]);r.onerror=rej;r.readAsDataURL(f)});out.push({name:f.name,type:f.type||'application/octet-stream',data})}return out}
$('#intakeForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const payload={organization:$('#organization').value.trim(),sector:$('#sector').value,goal:$('#goal').value,website:$('#website').value.trim(),context:$('#context').value.trim(),use_live:$('#liveToggle').checked,files:await filePayload()};
  setView('#loadingView');$('#pageTitle').textContent='Analysis in progress';
  const steps=['Structuring evidence...','Testing consistency and confidence...','Detecting strategic signals...','Prioritizing decisions...','Producing the 30/60/90-day roadmap...'];
  let i=0;const timer=setInterval(()=>{i=Math.min(i+1,4);$('#loadingStep').textContent=steps[i];$('#progressBar').style.width=((i+1)*20)+'%';$$('.loading-steps span').forEach((s,n)=>s.classList.toggle('done',n<=i))},430);
  try{const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||'Analysis failed');currentAnalysis=data.analysis;currentMode=data.mode||'demo';}catch(err){currentAnalysis={...demoAnalysis,organization:payload.organization||demoAnalysis.organization,sector:payload.sector,decision:payload.goal,meta:{...demoAnalysis.meta,fallback_reason:String(err.message)}};currentMode='demo-fallback';}
  clearInterval(timer);$('#progressBar').style.width='100%';setTimeout(()=>{renderAnalysis(currentAnalysis);setView('#resultsView');$('#pageTitle').textContent='Intelligence Room';$('#printBtn').disabled=false;$('#exportJsonBtn').disabled=false},350);
});

function renderAnalysis(a){
  $('#roomOrganization').textContent=a.organization;$('#roomSector').textContent=(a.sector||'Organization').toUpperCase();$('#roomDecision').textContent='Decision: '+a.decision;$('#confidenceScore').textContent=(a.meta?.confidence||80)+'%';$('#modeBadge').textContent=currentMode.includes('live')?'Live GPT-5.6':'Curated demo';
  $('#thesis').textContent=a.thesis;$('#summary').textContent=a.summary;$('#decisionEnabled').textContent=a.decision_enabled;$('#overallScore').textContent=a.overall_score;$('#scoreInterpretation').textContent=a.score_interpretation;$('#ringValue').style.strokeDashoffset=(307.9*(1-a.overall_score/100)).toFixed(1);
  const mg=$('#metricGrid');mg.innerHTML='';a.metrics.forEach(m=>{mg.insertAdjacentHTML('beforeend',`<div class="metric"><div class="metric-head"><span>${m.name}</span><b>${m.score}</b></div><div class="metric-bar"><i style="width:${m.score}%"></i></div></div>`)});
  $('#topOpportunity').textContent=a.top_opportunity.title;$('#topOpportunityWhy').textContent=a.top_opportunity.why;$('#topRisk').textContent=a.top_risk.title;$('#topRiskWhy').textContent=a.top_risk.why;
  const sg=$('#signalsGrid');sg.innerHTML='';a.signals.forEach(s=>sg.insertAdjacentHTML('beforeend',`<article class="signal-card ${s.tone||''}"><div class="type">${s.type}</div><h3>${s.title}</h3><p>${s.body}</p><div class="signal-meta"><span>${s.source}</span><span>${s.confidence}% confidence</span></div></article>`));
  const dl=$('#decisionList');dl.innerHTML='';a.decisions.forEach(d=>dl.insertAdjacentHTML('beforeend',`<article class="decision-card"><div class="decision-rank">${String(d.rank).padStart(2,'0')}</div><div><h3>${d.title}</h3><p>${d.detail}</p></div><div class="decision-badges"><span>${d.quadrant}</span><span>Impact: ${d.impact}</span><span>Effort: ${d.effort}</span><span>${d.urgency}</span></div></article>`));
  const rg=$('#roadmapGrid');rg.innerHTML='';Object.entries(a.roadmap).forEach(([phase,items],idx)=>{rg.insertAdjacentHTML('beforeend',`<article class="roadmap-column"><div class="phase">PHASE ${idx+1}</div><h3>${phase}</h3>${items.map(it=>`<div class="roadmap-item"><strong>${it.title}</strong><span>${it.detail}</span></div>`).join('')}</article>`)});
  const eb=$('#evidenceBody');eb.innerHTML='';a.evidence.forEach(e=>eb.insertAdjacentHTML('beforeend',`<tr><td><strong>${e.id}</strong></td><td>${e.observation}</td><td>${e.source}</td><td><span class="confidence-pill">${e.confidence}%</span></td><td>${e.implication}</td></tr>`));
}
$$('.tab').forEach(t=>t.onclick=()=>{$$('.tab').forEach(x=>x.classList.remove('active'));$$('.tab-panel').forEach(x=>x.classList.remove('active'));t.classList.add('active');$('#tab-'+t.dataset.tab).classList.add('active')});
$$('.nav-item').forEach(n=>n.onclick=()=>{$$('.nav-item').forEach(x=>x.classList.remove('active'));n.classList.add('active');if(n.dataset.nav==='submission'){setView('#submissionView');$('#pageTitle').textContent='Build Week submission'}else if(currentAnalysis){setView('#resultsView');$('#pageTitle').textContent='Intelligence Room';const target=n.dataset.nav==='evidence'?'evidence':n.dataset.nav==='roadmap'?'roadmap':'overview';document.querySelector(`.tab[data-tab="${target}"]`).click()}else{setView('#intakeView');$('#pageTitle').textContent='New Intelligence Room'}});
$('#printBtn').onclick=()=>window.print();
$('#exportJsonBtn').onclick=()=>{if(!currentAnalysis)return;const blob=new Blob([JSON.stringify(currentAnalysis,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`NOUS_${currentAnalysis.organization.replace(/\W+/g,'_')}_Intelligence_Room.json`;a.click();URL.revokeObjectURL(a.href)};
$('#languageBtn').onclick=()=>toast('The submission package includes Spanish and English copy.');
init();
