const form=document.querySelector('#searchForm');
const field=document.querySelector('#problem');
const submit=document.querySelector('#submit');
const hero=document.querySelector('#hero');
const result=document.querySelector('#result');
let examples=[];
let conversation=[];

function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function showResult(){hero.classList.add('hidden');result.classList.remove('hidden');window.scrollTo({top:0,behavior:'smooth'});}
function startOver(){conversation=[];result.classList.add('hidden');hero.classList.remove('hidden');field.focus();window.scrollTo({top:0,behavior:'smooth'});}

function matchHtml(data){
  const m=data.match;
  if(!m){
    const extras=[data.understood_as?`Interpreted as: ${esc(data.understood_as)}`:'',data.device_model?`Device mentioned: ${esc(data.device_model)}; exact-model guidance may be missing.`:'',`Urgency estimate: ${esc(data.severity||'medium')} (based on wording).`].filter(Boolean).join(' · ');
    return `${extras?`<p class="understood">${extras}</p>`:''}<div class="no-match"><strong>No close guide in the supplied data</strong><p>${esc(data.message)}</p><p>Try adding the model, what you see, and when it began.</p></div>`;
  }
  const sections=(m.sections||[]).map((s,i)=>{
    const link=s.link_preview?`<div class="link-preview"><strong>Related setting · preview only</strong>${esc(s.link_preview.message)}<br>${esc(s.link_preview.description)}<br>The URI is masked, so this cannot open a real phone screen.</div>`:'';
    return `<details class="section" ${i===0?'open':''}><summary>${esc(s.title)}</summary><div class="section-body">${esc(s.text)}</div>${link}</details>`;
  }).join('');
  const modelNote=data.device_model?(m.model_match
    ?`Guide text contains ${esc(data.device_model)}.`
    :`The supplied guide has no verified instructions for ${esc(data.device_model)}; treat this as a general match.`):'';
  const severityNote=data.severity==='high'
    ?'Urgency estimate: high, based on wording. This is only a text-based estimate; follow the guide cautiously and seek qualified service for serious damage or safety concerns.'
    :data.severity==='low'?'Urgency estimate: low, based on wording.':'Urgency estimate: routine, based on wording.';
  const understood=data.understood_as?`<p class="understood"><strong>Interpreted as:</strong> ${esc(data.understood_as)}</p>`:'';
  return `${understood}<div class="match-card"><div class="match-top"><h3>${esc(m.title)}</h3><span class="confidence ${esc(data.severity)}">${esc(data.severity)} urgency</span></div><p class="matched-query"><strong>${esc(m.confidence)}</strong> · ${Math.min(100,Math.round(m.score*100))}% text match<br><strong>Related section:</strong> ${esc(m.matched_section||'Guide')}<br><strong>Closest example:</strong> ${esc(m.matched_query)}</p></div>${modelNote?`<div class="model-note">${modelNote}</div>`:''}<div class="severity-note">${severityNote}</div>${sections}<div class="notice"><strong>Dataset note:</strong> The supplied guides use TechCorp/Nexa names. The deeplink addresses are masked placeholders, so previews cannot open real Samsung settings screens.</div>`;
}

function renderConversation(loading=false){
  showResult();
  const turns=conversation.map(t=>t.role==='user'
    ?`<div class="chat-row user-row"><div class="user-bubble">${esc(t.content)}</div></div>`
    :`<div class="chat-row assistant-row"><div class="assistant-avatar">✳</div><div class="assistant-content"><div class="assistant-label">Phone Troubleshooter · local dataset</div><p class="assistant-message">${esc(t.content)}</p>${t.data?matchHtml(t.data):''}</div></div>`).join('');
  const wait=loading?'<div class="chat-row assistant-row"><div class="assistant-avatar">✳</div><div class="loading">Searching the guide…</div></div>':'';
  result.innerHTML=`<div class="chat-head"><button class="text-button" data-action="reset">← New conversation</button><span class="eyebrow">YOUR TROUBLESHOOTING CHAT</span></div><div class="transcript">${turns}${wait}</div><form id="followupForm" class="chat-composer"><label class="sr-only" for="followup">Ask a follow-up or describe another issue</label><textarea id="followup" rows="2" maxlength="1200" placeholder="Ask a follow-up or add another issue on the same phone…" required ${loading?'disabled':''}></textarea><div class="composer-bottom"><span>Recent messages and device model stay in context</span><button class="primary" type="submit" ${loading?'disabled':''}>Send <span>→</span></button></div></form><p class="chat-footnote">Local dataset only · severity is an estimate · check that each guide fits your phone.</p>`;
  result.scrollTop=result.scrollHeight;
}

async function sendMessage(text){
  text=(text||'').trim();if(!text)return;
  conversation.push({role:'user',content:text});
  conversation=conversation.slice(-20);
  renderConversation(true);
  try{
    const r=await fetch('/api/troubleshoot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:conversation.map(({role,content})=>({role,content}))})});
    const data=await r.json();if(!r.ok)throw new Error(data.error||'Could not search the guide');
    conversation.push({role:'assistant',content:data.message||'I searched the supplied guide.',data});
    conversation=conversation.slice(-20);
    renderConversation(false);
  }catch(e){
    conversation.pop();renderConversation(false);
    const p=document.createElement('p');p.className='chat-error';p.textContent=`Couldn’t search the guide: ${e.message}. Make sure the server window is still open.`;result.appendChild(p);
  }
}

form.addEventListener('submit',e=>{e.preventDefault();if(field.value.trim())sendMessage(field.value.trim());});
result.addEventListener('submit',e=>{if(e.target.id!=='followupForm')return;e.preventDefault();const box=e.target.querySelector('#followup');if(box.value.trim())sendMessage(box.value);});
result.addEventListener('click',e=>{if(e.target.closest('[data-action="reset"]'))startOver();});

fetch('/api/examples').then(r=>r.json()).then(data=>{
  examples=data.examples||[];
  const box=document.querySelector('#chips');
  const toggle=document.querySelector('#toggleExamples');
  let showAll=false;
  function drawExamples(){
    box.replaceChildren();
    (showAll?examples:examples.slice(0,6)).forEach(text=>{const b=document.createElement('button');b.className='chip';b.type='button';b.textContent=text.length>110?text.slice(0,107)+'…':text;b.title=text;b.addEventListener('click',()=>sendMessage(text));box.appendChild(b);});
    toggle.textContent=showAll?'Show fewer examples':`Show all ${examples.length} examples`;
    toggle.classList.toggle('hidden',examples.length<=6);
  }
  toggle.addEventListener('click',()=>{showAll=!showAll;drawExamples();});
  drawExamples();
}).catch(()=>{});
