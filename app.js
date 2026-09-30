'use strict';
const $=id=>document.getElementById(id);
const names={ARI:'Cardinals',ATL:'Falcons',BAL:'Ravens',BUF:'Bills',CAR:'Panthers',CHI:'Bears',CIN:'Bengals',CLE:'Browns',DAL:'Cowboys',DEN:'Broncos',DET:'Lions',GB:'Packers',HOU:'Texans',IND:'Colts',JAX:'Jaguars',KC:'Chiefs',LAC:'Chargers',LAR:'Rams',LV:'Raiders',MIA:'Dolphins',MIN:'Vikings',NE:'Patriots',NO:'Saints',NYG:'Giants',NYJ:'Jets',PHI:'Eagles',PIT:'Steelers',SEA:'Seahawks',SF:'49ers',TB:'Buccaneers',TEN:'Titans',WAS:'Commanders'};
let payload=null, selectedSeason=null, selectedWeek=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number.isFinite(n)?Number(n.toFixed(1)).toString():'—';
const date=s=>new Date(s).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
function result(g){return !g.actual_winner?'pending':g.actual_winner==='TIE'?'tie':g.pick===g.actual_winner?'win':'loss';}
function record(games){let wins=0,losses=0,pending=0,ties=0;for(const g of games){const r=result(g);if(r==='win')wins++;else if(r==='loss')losses++;else if(r==='tie')ties++;else pending++;}return {wins,losses,pending,ties,accuracy:wins+losses?100*wins/(wins+losses):null};}
const recordText=r=>`${r.wins}–${r.losses}${r.ties?`–${r.ties}`:''}`;
function weeks(){return payload.weeks.filter(w=>w.season===selectedSeason);}
function current(){return weeks().find(w=>w.week===selectedWeek);}
function view(which){for(const v of ['picks','record','elo']){$(v+'View').hidden=v!==which; $(v+'Tab').classList.toggle('active',v===which);$(v+'Tab').setAttribute('aria-pressed',String(v===which));}}
function render(){
 const ws=weeks(),all=record(ws.flatMap(w=>w.games)),pregame=record(ws.filter(w=>w.provenance!=='retrospective').flatMap(w=>w.games));
 $('seasonLabel').textContent=selectedSeason+' SEASON';$('allRecord').textContent=recordText(all);$('allCaption').textContent=ws.some(w=>w.provenance==='retrospective')?'Mixed history · see week labels':'Pregame predictions';$('pregameRecord').textContent=recordText(pregame);$('pregameCaption').textContent=`${pregame.wins+pregame.losses+pregame.ties} graded pregame picks`;$('accuracy').textContent=all.accuracy===null?'—':fmt(all.accuracy)+'%';$('weekCount').textContent=String(ws.length).padStart(2,'0');$('pending').textContent=all.pending+' picks awaiting a final';
 $('week').innerHTML=ws.slice().reverse().map(w=>`<option value="${w.week}">Week ${w.week}</option>`).join('');$('week').value=selectedWeek;
 $('updated').textContent='Updated '+date(payload.generated_at);
 $('checked').textContent=payload.scores_checked_at?'Final scores checked '+date(payload.scores_checked_at)+'. This page checks for updates every minute.':'Initial archive · imported final scores. Automatic score refresh is not connected yet.';
 $('recordRows').innerHTML=ws.map(w=>{const r=record(w.games);return `<tr><td><button data-week="${w.week}" aria-label="View week ${w.week} picks">Week ${w.week} ↗</button></td><td>${recordText(r)}</td><td>${r.accuracy===null?'—':fmt(r.accuracy)+'%'}</td><td>${r.pending}</td><td>${esc(w.provenance)}</td></tr>`;}).join('');
 for(const button of $('recordRows').querySelectorAll('button'))button.onclick=()=>{selectedWeek=Number(button.dataset.week);render();view('picks');};
 renderGames();
}
function renderGames(){
 const w=current();if(!w)return;const rec=record(w.games);
 $('weekHeading').textContent=`Week ${w.week} picks`;$('weekEyebrow').textContent=`${w.season} SEASON / ${w.games.length} MATCHUPS`;$('weekSource').textContent=w.provenance==='retrospective'?'Retrospective run':'Pregame snapshot';$('weekRecord').textContent=`${recordText(rec)} · ${rec.accuracy===null?'Not graded':fmt(rec.accuracy)+'% correct'}`;
 $('provenanceNote').textContent=w.provenance==='retrospective'?'These picks were recreated after the games. They count in the combined record, but are excluded from the pregame record.':`Imported snapshot. Published picks are preserved; final scores are tracked separately.`;
 const q=$('search').value.trim().toLowerCase(),filter=$('outcome').value;
 const games=w.games.filter(g=>(g.away+' '+g.home+' '+names[g.away]+' '+names[g.home]).toLowerCase().includes(q)&&(filter==='all'||result(g)===filter));
 $('empty').hidden=games.length>0;
 $('matchups').innerHTML=games.map(g=>{const r=result(g),label={win:'CORRECT',loss:'MISSED',pending:'PENDING',tie:'TIE'}[r];return `<article class="game" aria-label="${esc(names[g.away])} at ${esc(names[g.home])}"><div class="game-top"><span>${esc(g.away)} AT ${esc(g.home)}</span><span class="badge ${r}">${label}</span></div><div class="teams"><div><div class="team-code">${esc(g.away)}</div><div class="team-name">${esc(names[g.away])}</div></div><span class="at">@</span><div><div class="team-code">${esc(g.home)}</div><div class="team-name">${esc(names[g.home])}</div></div></div><div class="scoreline"><span>Projected <b>${fmt(g.away_score)}–${fmt(g.home_score)}</b></span><span>Final <b>${r==='pending'?'—':fmt(g.actual_away)+'–'+fmt(g.actual_home)}</b></span></div><div class="pickline"><span>THE PICK<strong>${esc(g.pick)}</strong></span><small>${g.confidence===null?'Confidence unavailable':fmt(g.confidence)+'% confidence'}</small></div></article>`;}).join('');
}
async function load(){
 $('refresh').disabled=true;
 try{const res=await fetch('results.json',{cache:'no-store'});if(!res.ok)throw new Error(`HTTP ${res.status}`);const next=await res.json();if(next.schema_version!==1||!Array.isArray(next.weeks)||!next.weeks.length)throw new Error('Invalid results');payload=next;const seasons=[...new Set(payload.weeks.map(w=>w.season))].sort((a,b)=>b-a);if(!seasons.includes(selectedSeason))selectedSeason=seasons[0];if(!weeks().some(w=>w.week===selectedWeek))selectedWeek=Math.max(...weeks().map(w=>w.week));$('season').innerHTML=seasons.map(s=>`<option value="${s}">${s}</option>`).join('');$('season').value=selectedSeason;$('error').hidden=true;render();}
 catch(e){$('error').textContent=payload?'Could not refresh. Showing the last loaded results; try again shortly.':'Results could not load. Please try Refresh results.';$('error').hidden=false;}
 finally{await loadElo();$('refresh').disabled=false;}
}
$('refresh').onclick=load;$('picksTab').onclick=()=>view('picks');$('recordTab').onclick=()=>view('record');$('search').oninput=renderGames;$('outcome').onchange=renderGames;$('week').onchange=()=>{selectedWeek=Number($('week').value);renderGames();};$('season').onchange=()=>{selectedSeason=Number($('season').value);selectedWeek=Math.max(...weeks().map(w=>w.week));render();};
$('download').onclick=()=>{const w=current();if(!w)return;const columns=['away','home','pick','away_score','home_score','confidence','actual_away','actual_home','actual_winner'];const csv=[columns.join(','),...w.games.map(g=>columns.map(k=>`"${String(g[k]??'').replace(/"/g,'""')}"`).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));const link=document.createElement('a');link.href=url;link.download=`NFL_${w.season}_Week_${w.week}_picks.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
let eloPayload=null, eloSeason=null, eloWeek=null;
function eloWeeks(){return eloPayload.weeks.filter(w=>w.season===eloSeason);}
function changeCell(n,position=false){
 if(n===null||!Number.isFinite(n))return '<td>—</td>';
 const value=position?n:Number(n.toFixed(1));
 if(value===0)return '<td class="elo-neutral">0</td>';
 const label=position?(value>0?'Up ':'Down ')+Math.abs(value)+' positions':(value>0?'Increase ':'Decrease ')+Math.abs(value)+' rating points';
 return `<td class="${value>0?'elo-up':'elo-down'}" aria-label="${label}">${position?(value>0?'↑ ':'↓ '):(value>0?'+':'−')}${fmt(Math.abs(value))}</td>`;
}
function renderElo(){
 if(!eloPayload)return;
 const ws=eloWeeks();
 $('eloWeek').innerHTML=ws.slice().sort((a,b)=>b.week-a.week).map(w=>`<option value="${w.week}">Week ${w.week}</option>`).join('');$('eloWeek').value=eloWeek;
 const snapshot=ws.find(w=>w.week===eloWeek),q=$('eloSearch').value.trim().toLowerCase(),sort=$('eloSort').value;
 $('eloHeading').textContent=`Week ${eloWeek} Elo rankings`;
 const rows=(snapshot?.teams||[]).filter(r=>(r.team+' '+names[r.team]).toLowerCase().includes(q)).slice().sort((a,b)=>a[sort].rank-b[sort].rank);
 $('eloRows').innerHTML=rows.map(r=>`<tr><td><strong>${esc(r.team)}</strong><small>${esc(names[r.team])}</small></td>`+['raw','network'].map(k=>`<td>${r[k].rank}</td><td>${fmt(r[k].rating)}</td>`+changeCell(r[k].rating_change)+changeCell(r[k].position_change,true)).join('')+'</tr>').join('');
 $('eloEmpty').hidden=rows.length>0;
 $('eloSource').textContent=snapshot?`${snapshot.season} · Entering Week ${snapshot.week}. Ratings use only earlier games. ${snapshot.reconstructed?'Historical rankings reconstructed from the model; pick history is unchanged.':'Saved weekly rating snapshot.'}`:'';
}
async function loadElo(){
 try{
  const res=await fetch('elo.json',{cache:'no-store'});if(!res.ok)throw Error('Ratings unavailable');
  const next=await res.json();
  if(next.schema_version!==1||!Array.isArray(next.weeks)||!next.weeks.length)throw Error('Invalid ratings');
  for(const w of next.weeks){
   if(!Number.isInteger(w.season)||!Number.isInteger(w.week)||!Array.isArray(w.teams)||w.teams.length!==32||new Set(w.teams.map(r=>r.team)).size!==32)throw Error('Incomplete ratings');
   for(const r of w.teams){if(!Object.hasOwn(names,r.team))throw Error('Invalid team');for(const k of ['raw','network']){const x=r[k];if(!x||!Number.isInteger(x.rank)||x.rank<1||x.rank>32||!Number.isFinite(x.rating)||![x.rating_change,x.position_change].every(v=>v===null||Number.isFinite(v)))throw Error('Invalid rating');}}
  }
  eloPayload=next;const seasons=[...new Set(next.weeks.map(w=>w.season))].sort((a,b)=>b-a);
  if(!seasons.includes(eloSeason))eloSeason=seasons[0];if(!eloWeeks().some(w=>w.week===eloWeek))eloWeek=Math.max(...eloWeeks().map(w=>w.week));
  $('eloSeason').innerHTML=seasons.map(s=>`<option value="${s}">${s}</option>`).join('');$('eloSeason').value=eloSeason;
  $('eloError').hidden=true;renderElo();
 }catch(e){$('eloError').textContent=eloPayload?'Could not refresh rankings. Showing the last loaded snapshot.':'Elo rankings are not available yet. Try Refresh results shortly.';$('eloError').hidden=false;}
}
$('eloTab').onclick=()=>view('elo');$('eloSearch').oninput=renderElo;$('eloSort').onchange=renderElo;
$('eloWeek').onchange=()=>{eloWeek=Number($('eloWeek').value);renderElo();};
$('eloSeason').onchange=()=>{eloSeason=Number($('eloSeason').value);eloWeek=Math.max(...eloWeeks().map(w=>w.week));renderElo();};
load();setInterval(()=>{if(!document.hidden)load();},60000);

