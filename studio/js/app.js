import { ITEMS, RECORDS, MOODS, PANEL_COPY, LINKEDIN, PORTRAIT, POSTER, SIGNAL_CHAIN, PEDALBOARD } from './content.js';
import { clamp, fitScene, frameForAngle, boundedPan, pointInImage, hotspotFromPixels, quadTransform } from './geometry.js';
import { LiveTerminal, TERMINAL_SIZE } from './terminal.js';
const $ = s => document.querySelector(s);
const room=$('#room'),scene=$('#scene'),view=$('#room-viewport'),picture=$('#room-image'),hotspots=$('#hotspots');
const dialog=$('#detail-dialog'),panel=$('#panel-content');
const canvas=$('#highlight'),ctx=canvas.getContext('2d'),tvCanvas=$('#tv-live');
const mobile=matchMedia('(max-width:700px)'),reducedMotion=matchMedia('(prefers-reduced-motion:reduce)');
const buttons=new Map(),cache=new Map(),pending=new Map(),highRes=new Map();
let metadata,current=null,desired=0,angle=0,pan={x:0,y:0},size={width:0,height:0},gesture=null,active=null,mood='golden-hour',lastFocus=null,toastTimer,hintTimer,frameSerial=0,initialized=false;
let suppressClickUntil=0;
const asset=p=>new URL(`../assets/${p}`,import.meta.url).href;
const terminal=tvCanvas.getContext('2d')?new LiveTerminal(tvCanvas,{still:reducedMotion.matches}):null;
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n;}
function announce(message){$('#announcer').textContent=message;}
function toast(message){const n=$('#scene-toast');n.textContent=message;n.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>n.classList.remove('show'),3000);announce(message);}
function hint(){if(reducedMotion.matches)return;$('#room-hint').classList.add('visible');room.classList.add('show-controls');clearTimeout(hintTimer);hintTimer=setTimeout(()=>{$('#room-hint').classList.remove('visible');room.classList.remove('show-controls');},4500);}
function applyPan(){pan=boundedPan(pan.x,pan.y,size,{width:view.clientWidth,height:view.clientHeight});scene.style.setProperty('--pan-x',`${pan.x}px`);scene.style.setProperty('--pan-y',`${pan.y}px`);}
function resize(){if(!metadata)return;size=fitScene(view.clientWidth,view.clientHeight,metadata.width/metadata.height);scene.style.setProperty('--scene-width',`${size.width}px`);scene.style.setProperty('--scene-height',`${size.height}px`);applyPan();placeScreen(current);}
// Pin the live terminal onto this camera's projected TV corners.
function placeScreen(frame){if(!frame?.screen||!terminal){tvCanvas.hidden=true;return;}tvCanvas.hidden=false;const q=frame.screen.map(([u,v])=>[u*size.width,v*size.height]);tvCanvas.style.transform=`matrix3d(${quadTransform(TERMINAL_SIZE.width,TERMINAL_SIZE.height,q).join(',')})`;}
new ResizeObserver(resize).observe(view);
async function image(src){const im=new Image();im.decoding='async';im.src=src;await im.decode();return im;}
async function loadFrame(index){
  if(cache.has(index))return cache.get(index);
  if(pending.has(index))return pending.get(index);
  const f=metadata.frames[index];
  const work=(async()=>{
    const [im,mask]=await Promise.all([image(asset(index===metadata.defaultView?'studio.webp':f.small)),image(asset(f.mask)).catch(()=>null)]);
    let pixels=null,w=0,h=0;
    if(mask){w=mask.naturalWidth;h=mask.naturalHeight;const c=document.createElement('canvas');c.width=w;c.height=h;const cx=c.getContext('2d',{willReadFrequently:true});if(cx){cx.drawImage(mask,0,0);pixels=cx.getImageData(0,0,w,h).data;}}
    const frame={...f,im,pixels,w,h};if(index===metadata.defaultView)highRes.set(index,im);cache.set(index,frame);pending.delete(index);return frame;
  })().catch(e=>{pending.delete(index);throw e;});pending.set(index,work);return work;
}
function placeButtons(frame){for(const [key,b]of buttons){const p=frame.hotspots[key].anchor;b.style.left=`${p[0]*100}%`;b.style.top=`${p[1]*100}%`;}}
function showFrame(frame){
  // Image, mask and target positions are committed together; old masks never track a new angle.
  current=frame;picture.src=highRes.get(frame.index)?.src||frame.im.src;picture.width=metadata.width;picture.height=metadata.height;
  scene.dataset.view=String(frame.index);scene.dataset.angle=String(frame.angle);
  placeButtons(frame);placeScreen(frame);canvas.width=frame.w;canvas.height=frame.h;hover(null,true);
}
async function requestView(index){
  desired=index;const serial=++frameSerial;
  try{const frame=await loadFrame(index);if(serial!==frameSerial||desired!==index)return;showFrame(frame);if(!gesture)sharpen(frame.index);}catch{if(serial===frameSerial)toast('That angle is still tuning in. Try again.');}
}
async function sharpen(index){
  if(highRes.has(index)||!current)return;
  try{const im=await image(asset(metadata.frames[index].image));highRes.set(index,im);if(current?.index===index&&!gesture)picture.src=im.src;
    // Keep only a small number of full-size images decoded.
    if(highRes.size>4)for(const key of highRes.keys()){if(key!==index&&key!==metadata.defaultView){highRes.delete(key);break;}}
  }catch{/* Low-resolution image is already usable. */}
}
function setAngle(value){if(!metadata)return;angle=clamp(value,...metadata.rotationRange);const index=frameForAngle(angle,metadata.frames);if(index!==desired||!current)requestView(index);}
async function prefetch(){
  if(navigator.connection?.saveData)return;
  const center=metadata.defaultView,queue=[];
  for(let d=1;d<metadata.frames.length;d++)for(const i of[center-d,center+d])if(i>=0&&i<metadata.frames.length)queue.push(i);
  const worker=async()=>{while(queue.length){const i=queue.shift();try{await loadFrame(i);}catch{/* Retry on demand. */}}};
  await Promise.all([worker(),worker()]);
}
function resetView(){angle=0;pan={x:0,y:0};resize();if(metadata)requestView(metadata.defaultView);announce('Camera centered, facing the desk.');}
$('#reset-view').addEventListener('click',resetView);
function hover(key,force=false){
  if(key===active&&!force)return;active=key;
  for(const[k,b]of buttons)b.classList.toggle('is-active',k===key);
  if(!gesture)view.style.cursor=key?'pointer':'grab';
  if(!ctx)return;ctx.clearRect(0,0,canvas.width,canvas.height);
  if(!key||!current?.pixels||gesture)return;
  if(key==='tv'&&current.monitor){outlineMonitor(current);return;}
  const {pixels,w,h}=current,id=current.hotspots[key].id,out=ctx.createImageData(w,h);
  // Outline only: mark the object's edge pixels, leave its interior untouched.
  for(let i=0;i<pixels.length;i+=4)if(pixels[i]===id){const p=i/4,x=p%w;
    if(x===0||x===w-1||pixels[i-4]!==id||pixels[i+4]!==id||pixels[i-w*4]!==id||pixels[i+w*4]!==id){out.data[i]=255;out.data[i+1]=236;out.data[i+2]=196;out.data[i+3]=255;}}
  ctx.putImageData(out,0,0);
}
// Outline the monitor as its projected rectangle rather than its pixel silhouette.
function outlineMonitor(frame){
  ctx.beginPath();frame.monitor.forEach(([u,v],i)=>{const x=u*frame.w,y=v*frame.h;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
  ctx.closePath();ctx.strokeStyle='rgb(255,236,196)';ctx.lineWidth=1.5;ctx.lineJoin='round';ctx.stroke();
}
function pick(event){if(!current?.pixels)return null;const p=pointInImage(event.clientX,event.clientY,scene.getBoundingClientRect(),current.w,current.h);const id=hotspotFromPixels(current.pixels,current.w,current.h,p,event.pointerType==='touch'?5:0);return Object.keys(current.hotspots).find(k=>current.hotspots[k].id===id)||null;}
function revealObject(key){
  if(!current?.hotspots[key])return;const [u,v]=current.hotspots[key].anchor;
  pan={x:-(u-.5)*size.width,y:-(v-.5)*size.height};applyPan();hover(key);
}
view.addEventListener('pointerdown',e=>{
  if(e.button!==0||!metadata||dialog.open)return;
  gesture={id:e.pointerId,x:e.clientX,y:e.clientY,angle,pan:{...pan},moved:false};
  $('#room-hint').classList.remove('visible');
});
view.addEventListener('pointermove',e=>{
  if(gesture&&gesture.id===e.pointerId){
    const dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;
    if(!gesture.moved&&Math.hypot(dx,dy)>7){gesture.moved=true;view.setPointerCapture(e.pointerId);view.classList.add('is-dragging');hover(null,true);}
    if(gesture.moved){e.preventDefault();setAngle(gesture.angle-dx*.025);pan={x:gesture.pan.x+dx*.85,y:gesture.pan.y+dy*.85};applyPan();return;}
  }
  if(e.pointerType!=='touch')hover(pick(e));
});
function endDrag(e){
  if(!gesture||gesture.id!==e.pointerId)return;
  const moved=gesture.moved;gesture=null;view.classList.remove('is-dragging');view.style.cursor='grab';
  if(view.hasPointerCapture(e.pointerId))view.releasePointerCapture(e.pointerId);
  if(moved){suppressClickUntil=performance.now()+300;if(current)sharpen(current.index);}
}
view.addEventListener('pointerup',endDrag);view.addEventListener('pointercancel',endDrag);
view.addEventListener('lostpointercapture',e=>{if(e.target===view&&!view.hasPointerCapture(e.pointerId)){gesture=null;view.classList.remove('is-dragging');}});
view.addEventListener('pointerleave',()=>{if(!gesture)hover(null);});
view.addEventListener('click',e=>{if(performance.now()<suppressClickUntil||e.target.closest('button'))return;const key=pick(e);if(key)openPanel(key);});
view.addEventListener('keydown',e=>{
  if(e.target.closest('button'))return;
  if(['ArrowLeft','ArrowRight','Home'].includes(e.key)){e.preventDefault();
    if(e.key==='Home')resetView();
    if(e.key==='ArrowLeft'||e.key==='ArrowRight'){const dir=e.key==='ArrowLeft'?-1:1;setAngle(angle+dir);pan.x-=dir*80;applyPan();}
  }
});
function toggleMenu(force){const menu=$('#object-menu'),open=force??menu.hidden;menu.hidden=!open;$('#explore-toggle').setAttribute('aria-expanded',String(open));room.classList.toggle('show-points',open);if(open)hint();}
$('#explore-toggle').setAttribute('aria-expanded','false');$('#explore-toggle').addEventListener('click',()=>toggleMenu());
document.addEventListener('pointerdown',e=>{if(!e.target.closest('#object-menu')&&!e.target.closest('#explore-toggle'))toggleMenu(false);});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!dialog.open){toggleMenu(false);$('#explore-toggle').focus();}});
$('#fullscreen-toggle').hidden=!document.fullscreenEnabled;
$('#fullscreen-toggle').addEventListener('click',async()=>{try{document.fullscreenElement?await document.exitFullscreen():await document.documentElement.requestFullscreen();}catch{toast('Fullscreen is unavailable in this browser.');}});
document.addEventListener('fullscreenchange',()=>{$('#fullscreen-toggle').setAttribute('aria-label',document.fullscreenElement?'Exit fullscreen':'Enter fullscreen');});
function link(text, href, cls='panel-action') { const a=el('a',cls,text); a.href=href; a.target='_blank'; a.rel='noopener noreferrer'; return a; }
function openPanel(key) {
  if (!ITEMS[key]) return;
  lastFocus = document.activeElement; toggleMenu(false); hover(null);
  const record = ITEMS[key].record, copy = record ? { ...PANEL_COPY.record, title: record.title, body: record.body } : PANEL_COPY[key]; panel.replaceChildren();
  const layout=el('div','panel-layout'), art=el('div',`panel-art panel-art-${record?'record':key}`), content=el('div','panel-copy');
  if (key==='poster') { const im=el('img'); im.src=POSTER; im.alt='Tide of Echo poster: the band logo over a breaking night wave'; art.append(im); }
  else if (key==='badge') { const im=el('img','portrait'); im.src=PORTRAIT; im.alt='Portrait of Shawn Sun'; art.append(im); }
  else if (record) { const a=link('',record.href,'cover-link'); const im=el('img','cover'); im.src=record.art; im.alt=`${record.title} cover art`; a.append(im); a.setAttribute('aria-label',`${record.title} on Spotify`); art.append(a); }
  else if (key==='vinyl') { const stack=el('div','album-stack'); for (const r of RECORDS) { const a=link('',r.href,''); const im=el('img'); im.src=r.art; im.alt=''; a.append(im); a.setAttribute('aria-label',`${r.title} on Spotify`); stack.append(a); } art.append(stack); }
  else { const glyph=el('div','gear-art',({rack:'Analog soul',guitar:'six.',amp:'VOX',pedals:'drive.',tv:'>_'})[key]); glyph.append(el('small','',({rack:'OUTBOARD GEARS',guitar:'STRINGS & STORIES',amp:'TURN IT UP',pedals:'A LITTLE COLOR',tv:'ALWAYS RUNNING'})[key])); art.append(glyph); }
  art.append(el('span','panel-badge','SHAWN’S STUDIO'));
  content.append(el('p','eyebrow',copy.eyebrow)); const h=el('h2','',copy.title); h.id='panel-title'; content.append(h,el('p','',copy.body));
  if (key==='badge') content.append(link('Connect on LinkedIn ↗',LINKEDIN));
  if (key==='poster') content.append(link('Listen to Journal on Spotify ↗',RECORDS[2].href));
  if (record) content.append(link('Listen on Spotify ↗',record.href));
  if (key==='vinyl') { const list=el('div','record-links'); for (const record of RECORDS) { const a=link('',record.href,''); const cover=el('img'); cover.src=record.art; cover.alt=''; const label=el('span','',record.title); label.append(el('small','',record.subtitle)); a.append(cover,label,el('span','','↗')); a.setAttribute('aria-label',`${record.title} on Spotify`); list.append(a); } content.append(list); }
  if (key==='rack'||key==='pedals') { const list=el('ol','signal-list'); (key==='rack'?SIGNAL_CHAIN:PEDALBOARD).forEach((unit,i)=>{const li=el('li');const text=el('div');const name=el('strong','',unit.name);name.append(el('small','',unit.role));text.append(name,el('p','',unit.note));li.append(el('span','',String(i+1).padStart(2,'0')),text);list.append(li);}); content.append(list); }
  if (key==='tv') { const options=el('div','mode-options'); for (const option of MOODS) { const b=el('button','',option.name); b.setAttribute('aria-pressed',String(mood===option.id)); b.addEventListener('click',()=>{mood=option.id;scene.dataset.mood=mood; for(const o of options.children)o.setAttribute('aria-pressed',String(o===b)); closePanel(); announce(`${option.name} selected`);});options.append(b);}content.append(options); }
  content.append(el('p','panel-note',copy.note)); layout.append(art,content);panel.append(layout);
  if (!dialog.open) dialog.showModal();
  history.replaceState(null,'',`#${ITEMS[key].hash}`);
}
function closePanel() { dialog.close(); }
$('#close-panel').addEventListener('click',closePanel);
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closePanel();}});
dialog.addEventListener('close',()=>{history.replaceState(null,'',location.pathname+location.search);if(lastFocus instanceof HTMLElement && lastFocus!==document.body){if(lastFocus.closest('#object-menu'))$('#explore-toggle').focus({preventScroll:true});else lastFocus.focus({preventScroll:true});}});
for(const a of document.querySelectorAll('[data-panel]'))a.addEventListener('click',e=>{e.preventDefault();revealObject(a.dataset.panel);openPanel(a.dataset.panel);});
function followHash() { const key=Object.keys(ITEMS).find(k=>`#${ITEMS[k].hash}`===location.hash);if(key)openPanel(key); }
window.addEventListener('hashchange',followHash);
async function init(){
  if(initialized)return;initialized=true;$('#room-loading').hidden=false;
  try{
    const response=await fetch(asset('scene.json'));if(!response.ok)throw new Error('Scene unavailable');metadata=await response.json();
    if(!metadata.frames?.length)throw new Error('The camera sequence is not ready.');
    desired=metadata.defaultView;
    for(const[key,data]of Object.entries(metadata.hotspots)){
      if(!ITEMS[key])continue;
      const b=el('button','hotspot');b.dataset.key=key;b.type='button';b.setAttribute('aria-label',ITEMS[key].action);b.setAttribute('aria-haspopup','dialog');
      const label=el('span','hotspot-name',ITEMS[key].title);label.append(el('small','',ITEMS[key].subtitle));b.append(label);
      b.addEventListener('click',e=>{e.stopPropagation();if(performance.now()<suppressClickUntil)return;openPanel(key);});
      b.addEventListener('focus',()=>{if(b.matches(':focus-visible'))revealObject(key);else hover(key);});
      b.addEventListener('blur',()=>hover(null));hotspots.append(b);buttons.set(key,b);
    }
    resize();await requestView(desired);if(!current)throw new Error('Initial image unavailable');
    $('#room-loading').hidden=true;$('#fallback-content').hidden=true;terminal?.start();
    $('#room-hint').lastElementChild.textContent=mobile.matches?'Drag to look around · Tap an object':'Drag to look around · Click to explore';hint();followHash();
    // Start background loading after the default room has become visible.
    if('requestIdleCallback'in window)requestIdleCallback(()=>prefetch(),{timeout:1800});else setTimeout(prefetch,1200);
  }catch{
    initialized=false;$('#room-loading').hidden=true;$('#fallback-content').hidden=false;
    hotspots.replaceChildren();buttons.clear();
  }
}
$('#retry-scene').addEventListener('click',init);
init();
