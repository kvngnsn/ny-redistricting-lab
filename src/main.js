import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import './style.css';
import { voteShare, margin, seatCounts, marginLabel, robustMargin, csvForPlan, clamp, marginFit } from './model.js';

const $ = id => document.getElementById(id);
maplibregl.setWorkerUrl(workerUrl);
const base = import.meta.env.BASE_URL;
const repo = 'https://github.com/kvngnsn/ny-redistricting-lab';
const number = new Intl.NumberFormat('en-US');
const esc = value => String(value).replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[s]));
const signed = (n, digits = 1) => `${n > 0 ? '+' : ''}${n.toFixed(digits)}`;
const palette = ['#2c6694','#cc7d47','#608d76','#9a7fa3','#bc9a48','#5f93ae','#bd696f','#7e8d4e','#5673ad','#b77b99','#53988f','#9e805f','#798ac2','#b08b4c','#6e9b69','#b06d4e','#739898','#b47682','#788758','#7f7a9b','#a78a76','#6f9fb8','#bb835e','#839471','#9c7895','#4a7d90'];
let hoverPopup;
let data, map, currentPlan, electionIndex = 12, selected = null, swing = 0, mode = 'margin', hovered = null, ready = false, unitsLoaded = false, unitsLoading = false, planRequest = 0;
const geometries = new Map();
const prefersReducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

async function json(path) {
  const r = await fetch(base + path);
  if (!r.ok) throw new Error(`Could not load ${path} (${r.status}).`);
  return r.json();
}
function toast(text) {
  $('notice').textContent = text; $('notice').hidden = false;
  setTimeout(() => { $('notice').hidden = true; }, 5000);
}
function currentDistrict() { return currentPlan.districts.find(d => d.id === selected); }
function marginColor(m) { return m === null ? '#a9b5bf' : m >= 0 ? '#285faa' : '#b94e3a'; }
function historyRow(label, value, index, seatMode = false) {
  const left = value === null ? 50 : value >= 0 ? 50 : 50 + Math.max(value, -100) / 2;
  const width = value === null ? 0 : Math.min(50, Math.abs(value) / 2);
  return `<div class="history-row"><button data-election="${index}" title="Show ${esc(label)} on the map">${esc(label.replace('attorney general','AG').replace('comptroller','comptroller'))}</button><div class="history-track"><span class="history-fill" style="left:${left}%;width:${width}%;background:${marginColor(value)}"></span></div><span class="history-value" style="color:${marginColor(value)}">${seatMode ? `${value}/26` : esc(marginLabel(value))}</span></div>`;
}
function renderList() {
  let districts = [...currentPlan.districts];
  if ($('sort').value === 'margin') districts.sort((a,b) => (margin(a.votes[electionIndex],swing) ?? -101) - (margin(b.votes[electionIndex],swing) ?? -101));
  else if ($('sort').value === 'target') { const target=margin(data.elections[electionIndex].source_totals,swing); districts.sort((a,b)=>Math.abs(margin(b.votes[electionIndex],swing)-target)-Math.abs(margin(a.votes[electionIndex],swing)-target)); }
  else if ($('sort').value === 'population') districts.sort((a,b) => Math.abs(b.population-data.population/26)-Math.abs(a.population-data.population/26));
  else districts.sort((a,b) => a.id-b.id);
  $('district-list').innerHTML = districts.map(d => {
    const share = voteShare(d.votes[electionIndex], swing), m = margin(d.votes[electionIndex], swing);
    return `<button class="district-row ${selected === d.id ? 'selected' : ''}" data-district="${d.id}" aria-pressed="${selected === d.id}" aria-label="District ${d.id}, ${marginLabel(m)}, population ${number.format(d.population)}"><span class="district-id">NY ${String(d.id).padStart(2,'0')}</span><span class="district-track"><span style="width:${(share ?? 0)*100}%;background:${marginColor(m)}"></span></span><span class="district-margin" style="color:${marginColor(m)}">${marginLabel(m)}</span></button>`;
  }).join('');
  const counts = seatCounts(currentPlan.districts, electionIndex, swing);
  $('dem-seats').textContent = counts.dem; $('rep-seats').textContent = counts.rep; $('tie-seats').textContent = counts.tie;
}
function renderInspector() {
  const d = currentDistrict(), e = data.elections[electionIndex], target = data.population/26;
  const fit=marginFit(currentPlan.districts,electionIndex,e.source_totals,swing);
  $('clear-selection').hidden = !d;
  $('inspection-label').textContent = d ? 'District inspection' : 'State overview';
  if (d) {
    const value = margin(d.votes[electionIndex],swing);
    const worst = robustMargin(d);
    $('inspector-content').innerHTML = `<h2>District ${String(d.id).padStart(2,'0')}</h2><span class="result-label">${esc(e.label)}</span><div class="large-margin" style="color:${marginColor(value)}">${marginLabel(value)}</div><div class="margin-subtitle">Two-party margin${swing ? ' with scenario shift' : ' in the source election'}</div><div class="stat-lines"><div class="stat-line"><span>Gap from statewide margin</span><strong>${signed(value-fit.target,2)} pp</strong></div><div class="stat-line"><span>Population</span><strong>${number.format(d.population)}</strong></div><div class="stat-line"><span>Difference from ideal</span><strong>${signed(d.population-target,2)} people</strong></div><div class="stat-line"><span>Census blocks</span><strong>${number.format(d.blocks)}</strong></div><div class="stat-line"><span>Connected components</span><strong>${d.components}${d.island_exceptions ? ` + ${d.island_exceptions} island exceptions` : ''}</strong></div><div class="stat-line"><span>Weakest historical margin</span><strong style="color:${marginColor(worst)}">${marginLabel(worst)}</strong></div></div><h3>Across 13 elections</h3>${data.elections.map((e,i) => historyRow(e.label,margin(d.votes[i]),i)).join('')}<p class="micro">History uses the original election counts, without the swing scenario. Values below the map-unit level are estimates.</p><p class="analysis-note">${swing ? 'The swing slider shifts Democratic two-party vote share equally in every district. It does not simulate differential turnout or candidate effects.' : 'A historical Democratic lead is not a probability of winning a future election. Closely balanced districts are particularly sensitive to estimated precinct splits.'}</p>`;
  } else {
    const counts = seatCounts(currentPlan.districts,electionIndex,swing);
    const robust = currentPlan.districts.filter(d => robustMargin(d)>0).length;
    const weakest = Math.min(...currentPlan.districts.map(d => margin(d.votes[electionIndex],swing) ?? 0));
    $('inspector-content').innerHTML = `<h2>${currentPlan.id === 'reference' ? 'Adopted reference' : 'Search result'}</h2><span class="result-label ${counts.dem<26 ? 'warn':''}">${counts.dem===26 ? '26 Democratic leads in this scenario' : '26–0 target not reached in this scenario'}</span><p>${esc(currentPlan.description)}</p><div class="stat-lines"><div class="stat-line"><span>Largest gap from statewide</span><strong>${fit.maxGap.toFixed(2)} pp</strong></div><div class="stat-line"><span>Strongest district</span><strong>${marginLabel(fit.max)}</strong></div><div class="stat-line"><span>Weakest district</span><strong style="color:${marginColor(weakest)}">${marginLabel(weakest)}</strong></div><div class="stat-line"><span>D leads in every source election</span><strong>${robust} of 26 districts</strong></div><div class="stat-line"><span>Statewide two-party margin</span><strong>${marginLabel(margin(e.source_totals,swing))}</strong></div><div class="stat-line"><span>Largest population gap</span><strong>${number.format(currentPlan.validation.population_range)} ${currentPlan.validation.population_range===1?'person':'people'}</strong></div><div class="stat-line"><span>Connected districts</span><strong>${currentPlan.validation.connected_districts} / 26*</strong></div></div><h3>Democratic leads by election</h3>${data.elections.map((e,i) => {const seats=seatCounts(currentPlan.districts,i).dem;return `<div class="history-row"><button data-election="${i}">${esc(e.label.replace('attorney general','AG'))}</button><div class="district-track"><span style="width:${seats/26*100}%;background:#547fb5"></span></div><span class="history-value">${seats} / 26</span></div>`}).join('')}<p class="micro">*Two unpopulated island blocks retain their official assignment and are disclosed exceptions.</p><p class="analysis-note">${currentPlan.id!=='reference' ? 'This is a finite heuristic search, not a proof of the best possible map. Population and connectivity are checked independently after search.' : 'The reference uses the official February 2024 block assignments. These are modeled election results on that map, not the results of the 2024 House contests.'}</p><div class="download-links"><a href="${base}data/${currentPlan.file}" download>Download displayed district GeoJSON</a><a href="${base}data/${currentPlan.assignments}" download>Download full block assignments</a></div><p class="micro" style="margin-top:12px">Data downloads retain source-specific licenses. <button class="nav-button" data-doc="sources">Read credits and terms</button></p>`;
  }
}
function expression() {
  if (mode === 'district') return ['match',['get','district'],...currentPlan.districts.flatMap(d=>[d.id,palette[(d.id-1)%palette.length]]),'#c6d2dc'];
  if (mode === 'gap') return ['interpolate',['linear'],['get','targetGap'],-15,'#a5682c',0,'#f5f5ef',15,'#316e89'];
  if (mode === 'population') {
    const max=Math.max(...currentPlan.districts.map(d=>Math.abs(d.population-data.population/26)),1);
    return ['interpolate',['linear'],['get','deviation'],-max,'#a97b39',0,'#f1f3f4',max,'#316e89'];
  }
  return ['interpolate',['linear'],['get','margin'],-40,'#a73b2c',-15,'#da8b79',0,'#f4f4f0',15,'#97b7de',40,'#285faa'];
}
function mapData(geo) {
  return { ...geo,features:geo.features.map(f=>{
    const d=currentPlan.districts.find(d=>d.id===f.properties.district);
    return {...f,id:d.id,properties:{...f.properties,margin:margin(d.votes[electionIndex],swing) ?? 0,deviation:d.population-data.population/26,targetGap:(margin(d.votes[electionIndex],swing)??0)-(margin(data.elections[electionIndex].source_totals,swing)??0)}};
  })};
}
function updateMap() {
  if (!ready || !geometries.has(currentPlan.id)) return;
  map.getSource('districts').setData(mapData(geometries.get(currentPlan.id)));
  map.setPaintProperty('district-fill','fill-color',expression());
  map.setFilter('district-selected',['==',['get','district'],selected ?? -1]);
  $('legend').hidden=mode==='district';
  if(mode==='gap') $('legend').innerHTML='<div class="legend-ramp" style="background:linear-gradient(90deg,#a5682c,#f5f5ef,#316e89)"></div><div><span>−15 pp</span><span>Statewide</span><span>+15 pp</span></div>';
  else if(mode==='population') $('legend').innerHTML='<div class="legend-ramp" style="background:linear-gradient(90deg,#a97b39,#f1f3f4,#316e89)"></div><div><span>Below ideal</span><span>Ideal</span><span>Above ideal</span></div>';
  else $('legend').innerHTML='<div class="legend-ramp"></div><div><span>R +40</span><span>Even</span><span>D +40</span></div>';
  if(unitsLoaded) map.setPaintProperty('units-fill','fill-color',['case',['==',['get',`m${electionIndex}`],null],'#a9b5bf',['interpolate',['linear'],['coalesce',['get',`m${electionIndex}`],0],-40,'#a73b2c',-15,'#da8b79',0,'#f4f4f0',15,'#97b7de',40,'#285faa']]);
}
function render() {
  renderList();renderInspector();updateMap();
  $('map-plan-name').textContent=currentPlan.name;
  $('map-election-name').textContent=data.elections[electionIndex].label;
  $('swing-caption').hidden=!swing;
  $('swing-caption').textContent=`D vote share ${signed(swing)} pp`;
  const v=currentPlan.validation;
  $('validation-dot').className=`verification-dot ${v.population_range<=1 && v.connected_districts===26?'pass':'warn'}`;
  $('validation-line').textContent=`Population gap: ${number.format(v.population_range)} ${v.population_range===1?'person':'people'}. ${v.connected_districts}/26 connected; 2 island exceptions.`;
  const hash=new URLSearchParams({plan:currentPlan.id,election:data.elections[electionIndex].id});
  if(selected)hash.set('district',selected);if(swing)hash.set('swing',swing);
  history.replaceState(null,'',`#${hash}`);
}
async function switchPlan(id) {
  const request=++planRequest;
  currentPlan=data.plans.find(p=>p.id===id)??data.plans[0];
  $('plan').value=currentPlan.id;
  selected=null;
  if(!geometries.has(currentPlan.id)) geometries.set(currentPlan.id,await json(`data/${currentPlan.file}`));
  if(request!==planRequest)return;
  render();fitState();
}
function selectDistrict(id, fit=false) {
  selected=id;renderList();renderInspector();updateMap();
  if(fit && ready) {
    const bbox=currentDistrict().bbox;
    map.fitBounds([[bbox[0],bbox[1]],[bbox[2],bbox[3]]],{padding:60,duration:prefersReducedMotion?0:600,maxZoom:12});
  }
  const hash=new URLSearchParams(location.hash.slice(1));if(id)hash.set('district',id);else hash.delete('district');history.replaceState(null,'',`#${hash}`);
}
function fitState(){if(ready)map.fitBounds([[-79.80,40.43],[-71.72,45.05]],{padding:{top:100,left:35,right:35,bottom:100},duration:prefersReducedMotion?0:600});}

async function toggleUnits() {
  if(!ready)return;
  if($('units').checked&&mode!=='margin'){mode='margin';document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);b.setAttribute('aria-pressed',String(b.dataset.mode===mode));});updateMap();}
  if($('units').checked && !unitsLoaded && !unitsLoading) {
    unitsLoading=true;toast('Loading 14,191 historical voting units…');
    try {
      const geo=await json('data/voting-units.geojson');
      map.addSource('units',{type:'geojson',data:geo});
      map.addLayer({id:'units-fill',type:'fill',source:'units',paint:{'fill-opacity':.9,'fill-color':'#adc1d7'}},'district-outline');
      map.addLayer({id:'units-outline',type:'line',source:'units',paint:{'line-color':'#fff','line-width':.4,'line-opacity':.5}},'district-outline');
      map.on('click','units-fill',event=>{
        if(!$('units').checked || !event.features?.length)return;
        const p=event.features[0].properties;
        $('unit-tip').innerHTML=`<strong>2020 voting district ${esc(p.geoid)}</strong>Population: ${number.format(p.population)}<br>${esc(data.elections[electionIndex].label)}: ${marginLabel(p[`m${electionIndex}`]??null)}<br><span class="micro">Common-boundary estimates. This overlay is fixed while the district plan changes; swing is not applied.</span><br><button id="close-unit-tip">Close</button>`;
        $('unit-tip').hidden=false;
      });
      unitsLoaded=true;updateMap();
    }catch(error){$('units').checked=false;toast(error.message);}finally{unitsLoading=false;}
  }
  if(unitsLoaded){for(const layer of ['units-fill','units-outline'])map.setLayoutProperty(layer,'visibility',$('units').checked?'visible':'none');}
  if(!$('units').checked)$('unit-tip').hidden=true;
}

function openDoc(which) {
  const title={methodology:'How the experiment works',sources:'Sources, attribution & licenses',validation:'Independent validation'}[which];
  $('dialog-title').textContent=title;
  if(which==='methodology') $('dialog-body').innerHTML=`<p><strong>The question:</strong> can 26 connected, equally populated New York districts all show Democratic leads in 2024, and how does that map perform across a large historical panel? This project publishes a measured search result, including failures.</p><h3>The data</h3><p>All ${number.format(data.blocks)} 2020 Census blocks are assigned exactly once. Population is the unadjusted Census total of ${number.format(data.population)}. Thirteen statewide contests span 2008–2024; no congressional races or composite averages determine the search.</p><h3>Election estimates</h3><p>DRA v05 supplies harmonized historical VTD counts. The New York Times, with Benjamin J. Rosenblatt, supplies 2024 precincts. Source counts are allocated to blocks using population weights and largest-remainder rounding. A split precinct's block votes are <strong>estimates, not observed ballots</strong>. Source totals are preserved; source coverage gaps are not silently filled.</p><h3>Matching the statewide margin</h3><p>The newest experiment penalizes margins both above and below the statewide 2024 result. The inspector shows each district’s difference and the largest absolute gap. <a href="${repo}/blob/main/docs/EQUALIZATION.md" target="_blank" rel="noopener">Read the equalization method and its limitations</a>.</p><h3>The original searches</h3><p>A fixed-seed heuristic starts from the adopted map, moves connected geographic units and recombines adjacent districts using spanning-tree cuts. The 2024 sweep penalizes low 2024 margins; the separate historical stress search uses each district’s weakest margin across all 13 elections. Exact whole-block transfers and swaps balance populations while preserving connected fixed cores. Full-assignment validation then checks every district. Search-time tolerances do not define final success.</p><h3>The constraints</h3><ul><li><strong>Equal population:</strong> exactly 23 districts at 776,971 people and 3 at 776,972, in both experimental maps. No fractional people or fractional Census blocks.</li><li><strong>Contiguity:</strong> shared-boundary Census-block adjacency, including Census water polygons. Corner contact does not count. No synthetic nearest-neighbor edges.</li><li><strong>Two disclosed exceptions:</strong> the zero-population Liberty Island and Ellis Island blocks retain their adopted assignment.</li></ul><p>These are the experiment's constraints. It does not evaluate every legal requirement or certify a legally adoptable plan.</p><h3>Reading the results</h3><div class="method-equation">Two-party margin = 100 × (Democratic − Republican) / (Democratic + Republican)</div><p style="margin-top:15px">Other votes remain available in exports. A positive margin means a Democratic lead in that particular historical scenario. It is not a future win probability. A 1-point swing in Democratic vote share changes the two-party margin by 2 points.</p><a class="document-link" href="${repo}/blob/main/docs/METHODOLOGY.md" target="_blank" rel="noopener">Full methodology</a><a class="document-link" href="${repo}/tree/main/scripts" target="_blank" rel="noopener">Reproduction scripts</a>`;
  if(which==='sources') $('dialog-body').innerHTML=`<p>The site and research code are <strong>MIT licensed</strong>. The underlying election data retains its original licenses and use restrictions; it is not relicensed as MIT.</p><table><thead><tr><th>Source</th><th>Contribution and terms</th></tr></thead><tbody><tr><td><a href="https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html" target="_blank" rel="noopener">U.S. Census Bureau</a></td><td>2020 Census blocks, population, VTD boundaries and geographic crosswalk. Public federal data.</td></tr><tr><td><a href="https://latfor.state.ny.us/maps/?sec=2024_congress" target="_blank" rel="noopener">New York LATFOR</a></td><td>Official 2024 congressional block assignments.</td></tr><tr><td><a href="https://github.com/dra2020/vtd_data" target="_blank" rel="noopener">Dave's Redistricting / Social Good Fund</a></td><td>Historical VTD data, version 05. CC BY-SA 4.0 with an additional stated no-sale condition.</td></tr><tr><td>Steve Gerontakis & John Mifflin</td><td>2008 presidential source data, through DRA.</td></tr><tr><td>Ryne Rohla / Decision Desk HQ</td><td>2012 presidential source data, through DRA.</td></tr><tr><td>Voting and Election Science Team (VEST)</td><td>2016, 2018 and 2020 data. The pinned DRA archive identifies CC BY 4.0.</td></tr><tr><td><a href="https://www.benjrosenblatt.com/new-york-2022-election-district-level-data" target="_blank" rel="noopener">Benjamin J. Rosenblatt</a></td><td>2022 election data through the independently supplied DRA v05 package; 2024 New York results and boundaries through NYT. County election boards and OpenElections are credited in the full source notes.</td></tr><tr><td><a href="https://github.com/nytimes/presidential-precinct-map-2024" target="_blank" rel="noopener">The New York Times</a></td><td>“2024 Precinct-Level Election Results.” C-UDA terms require attribution and noncommercial use of data and derived results.</td></tr><tr><td>MapLibre GL JS; Public Sans</td><td>Interactive map rendering (BSD-3-Clause) and typography (SIL Open Font License). See third-party notices.</td></tr></tbody></table><h3>Coverage is disclosed</h3><p>Source totals can differ slightly from certified statewide totals. The 2024 spatial allocation leaves ${number.format(data.coverage.unassigned_2020_population)} Census residents in ${number.format(data.coverage.unassigned_blocks)} blocks outside the available precinct geometry; those blocks are not claimed to have observed zero votes. Every supplied source precinct's votes are allocated and conserved.</p><p>RDH-distributed datasets and later DRA election packages incorporating RDH restrictions are excluded. The source chain and license files identify exactly which independently supplied versions this build uses.</p><a class="document-link" href="${repo}/blob/main/docs/SOURCES.md" target="_blank" rel="noopener">Full source audit & credits</a><a class="document-link" href="${repo}/blob/main/docs/DATA-LICENSES.md" target="_blank" rel="noopener">Data license terms</a><a class="document-link" href="${base}notices/software.md" target="_blank" rel="noopener">Software notices</a>`;
  if(which==='validation') {
    const v=currentPlan.validation;
    const badge=(pass,text)=>`<span class="audit-badge ${pass?'':'fail'}">${text}</span>`;
    $('dialog-body').innerHTML=`<p><strong>${esc(currentPlan.name)}</strong>. These checks recompute results from the full block assignment, independently of the simplified display map.</p><table><tbody><tr><th>Complete coverage</th><td>${badge(v.complete,'All 288,819 blocks assigned once')}</td></tr><tr><th>Population conservation</th><td>${badge(v.population_conserved,number.format(data.population)+' people')}</td></tr><tr><th>Equal population</th><td>${badge(v.population_range<=1,`${v.population_range}-person largest gap`)}<br>Required gap: at most 1 person.</td></tr><tr><th>Contiguity</th><td>${badge(v.connected_districts===26,`${v.connected_districts} of 26 districts connected`)}<br>Two inherited zero-population island exceptions.</td></tr><tr><th>Election totals</th><td>${badge(v.votes_conserved,'All 13 source panels conserved')}</td></tr><tr><th>26–0 across all 13 elections</th><td>${badge(v.robust_democratic_districts===26,`${v.robust_democratic_districts} districts lead in every election`)}</td></tr></tbody></table><h3>Population by district</h3><table><thead><tr><th>District</th><th>Population</th><th>Components*</th><th>Worst margin</th></tr></thead><tbody>${currentPlan.districts.map(d=>`<tr><td>NY ${d.id}</td><td>${number.format(d.population)}</td><td>${d.components}${d.island_exceptions?' + islands':''}</td><td>${marginLabel(robustMargin(d))}</td></tr>`).join('')}</tbody></table><p class="micro">*Connected components exclude two zero-population blocks: 360610001001000 and 360610001001001. Full geographic contiguity without island exceptions is not claimed. The display polygons are simplified; validation uses unsimplified source geometry.</p><a class="document-link" href="${base}data/validation.json" target="_blank" rel="noopener">Download machine-readable audit</a><a class="document-link" href="${repo}/blob/main/scripts/validate.py" target="_blank" rel="noopener">Read the independent validator</a>`;
  }
  $('doc-dialog').showModal();
}

async function init() {
  try {
    data=await json('data/summary.json');
    const params=new URLSearchParams(location.hash.slice(1));
    electionIndex=data.elections.findIndex(e=>e.id===(params.get('election')??'24_PRES'));if(electionIndex<0)electionIndex=data.elections.length-1;
    swing=clamp(Number(params.get('swing'))||0,-10,10);$('swing').value=swing;$('swing-output').textContent=`${signed(swing)} pp`;
    $('plan').innerHTML=data.plans.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('');
    $('election').innerHTML=data.elections.map((e,i)=>`<option value="${i}">${esc(e.label)}</option>`).join('');$('election').value=electionIndex;
    currentPlan=data.plans.find(p=>p.id===params.get('plan'))??data.plans[0];$('plan').value=currentPlan.id;
    const requestedDistrict=Number(params.get('district'));if(requestedDistrict>=1&&requestedDistrict<=26)selected=requestedDistrict;
    geometries.set(currentPlan.id,await json(`data/${currentPlan.file}`));
    render();$('plan').disabled=false;$('election').disabled=false;
    map=new maplibregl.Map({container:'map',style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#e7eef3'}}]},center:[-75.4,42.6],zoom:6,attributionControl:false,renderWorldCopies:false,maxBounds:[[-83,38],[-68,47]],minZoom:4,maxZoom:15});
    map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
    map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:['U.S. Census Bureau','NY LATFOR','<a href="https://github.com/dra2020/vtd_data" target="_blank" rel="noopener">DRA & contributors</a>','<a href="https://github.com/nytimes/presidential-precinct-map-2024" target="_blank" rel="noopener">2024: The New York Times / B. Rosenblatt</a>']}),'bottom-right');
    map.on('load',()=>{
      map.addSource('districts',{type:'geojson',data:mapData(geometries.get(currentPlan.id)),promoteId:'district'});
      map.addLayer({id:'district-fill',type:'fill',source:'districts',paint:{'fill-color':expression(),'fill-opacity':.9}});
      map.addLayer({id:'district-outline',type:'line',source:'districts',paint:{'line-color':'#fff','line-width':['interpolate',['linear'],['zoom'],5,.7,10,1.6],'line-opacity':.95}});
      map.addLayer({id:'district-selected',type:'line',source:'districts',filter:['==',['get','district'],-1],paint:{'line-color':'#dfaa3c','line-width':3}});
      map.on('click','district-fill',event=>{if(event.features?.length&&!$('units').checked)selectDistrict(event.features[0].properties.district);});
      map.on('mousemove','district-fill',event=>{map.getCanvas().style.cursor='pointer';if(event.features?.length&&!$('units').checked){hovered=event.features[0].properties.district;const d=currentPlan.districts.find(d=>d.id===hovered);hoverPopup??=new maplibregl.Popup({closeButton:false,closeOnClick:false,offset:12});hoverPopup.setLngLat(event.lngLat).setText(`NY ${hovered} · ${marginLabel(margin(d.votes[electionIndex],swing))} · ${number.format(d.population)} people`).addTo(map);}});
      map.on('mouseleave','district-fill',()=>{map.getCanvas().style.cursor='';hovered=null;hoverPopup?.remove();});
      ready=true;fitState();updateMap();$('map-loading').hidden=true;
    });
    map.on('error',event=>{console.error('Map error',event.error);if(!ready){$('map-loading').innerHTML='<strong>Map rendering unavailable</strong><span>District results and downloads remain available.</span>';}});
  } catch(error) {
    console.error(error);$('map-loading').innerHTML=`<strong>Could not load the explorer</strong><span>${esc(error.message)}</span><button onclick="location.reload()">Reload</button>`;$('district-list').textContent='Data loading failed. Reload the page to try again.';
  }
}
$('plan').addEventListener('change',()=>switchPlan($('plan').value).catch(e=>toast(e.message)));
$('election').addEventListener('change',()=>{electionIndex=Number($('election').value);$('unit-tip').hidden=true;render();});
$('swing').addEventListener('input',()=>{swing=Number($('swing').value);$('swing-output').textContent=`${signed(swing)} pp`;if(data)render();});
$('reset-swing').addEventListener('click',()=>{$('swing').value=0;$('swing').dispatchEvent(new Event('input'));});
$('sort').addEventListener('change',()=>{if(data)renderList();});
$('fit-map').addEventListener('click',fitState);
$('units').addEventListener('change',toggleUnits);
$('clear-selection').addEventListener('click',()=>{selected=null;render();});
$('close-dialog').addEventListener('click',()=>$('doc-dialog').close());
$('doc-dialog').addEventListener('click',e=>{if(e.target===$('doc-dialog'))$('doc-dialog').close();});
$('download-csv').addEventListener('click',()=>{
  if(!data)return;
  const url=URL.createObjectURL(new Blob([csvForPlan(currentPlan,data.elections)],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=`ny-${currentPlan.id}-historical-results.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast('Exported original counts. Data terms: DRA BY-SA + no-sale; NYT C-UDA noncommercial.');
});
document.addEventListener('click',event=>{
  const doc=event.target.closest('[data-doc]');if(doc&&data)openDoc(doc.dataset.doc);
  const district=event.target.closest('[data-district]');if(district)selectDistrict(Number(district.dataset.district),true);
  const election=event.target.closest('[data-election]');if(election){electionIndex=Number(election.dataset.election);$('election').value=electionIndex;render();}
  const modeButton=event.target.closest('[data-mode]');if(modeButton){mode=modeButton.dataset.mode;if(mode!=='margin'&&$('units').checked){$('units').checked=false;toggleUnits();}document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b===modeButton);b.setAttribute('aria-pressed',String(b===modeButton));});updateMap();}
  if(event.target.id==='close-unit-tip')$('unit-tip').hidden=true;
});
init();
