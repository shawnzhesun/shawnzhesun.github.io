/** Isolated local browser checks. No existing user profile or signed-in browser. */
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
const { chromium }=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BIN?{executablePath:process.env.CHROME_BIN}:{})});
const output=new URL('../build/qa/',import.meta.url);await mkdir(output,{recursive:true});
const base=process.env.STUDIO_URL||'http://127.0.0.1:4173';const errors=[];
async function ready(page){await page.locator('#room-loading').waitFor({state:'hidden'});assert.equal(await page.locator('#fallback-content').isVisible(),false);}
async function capture(page,name){await page.screenshot({path:new URL(name,output).pathname,fullPage:true});}
async function menu(page,key){await page.getByRole('button',{name:'Explore studio objects',exact:true}).click();await page.locator(`#object-menu [data-panel="${key}"]`).click();}
async function closeDialog(page){await page.keyboard.press('Escape');await page.locator('dialog').waitFor({state:'hidden'});await page.waitForTimeout(100);}
async function center(page){await page.getByRole('button',{name:'Center camera',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#scene').dataset.angle==='0');}
async function drag(page,from,to,steps=16){await page.mouse.move(...from);await page.mouse.down();await page.mouse.move(...to,{steps});await page.mouse.up();}
async function coverage(page){
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth===innerWidth&&document.documentElement.scrollHeight===innerHeight),true);
  // The full room height is always visible; horizontally it either covers the viewport or is centered whole.
  const fits=await page.locator('#scene').evaluate(e=>{const r=e.getBoundingClientRect();const tall=Math.abs(r.top)<=.5&&Math.abs(r.bottom-innerHeight)<=.5;const wide=r.width>=innerWidth-.5?r.left<=.5&&r.right>=innerWidth-.5:Math.abs(r.left-(innerWidth-r.right))<=1;return tall&&wide;});
  assert.equal(fits,true,'The whole room height must fit the viewport');
}
try{
  const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))errors.push(`${r.status()} ${r.url()}`);});
  await page.goto(base);await ready(page);await coverage(page);
  assert.equal(await page.locator('header,footer,.intro,.room-links').count(),0);
  assert.equal(await page.locator('.hotspot').count(),10);
  assert.equal(await page.locator('.hotspot').evaluateAll(b=>b.every(n=>getComputedStyle(n).opacity==='0'&&getComputedStyle(n).pointerEvents==='none')),true,'No visible markers over objects');
  assert.equal(await page.locator('#scene').getAttribute('data-angle'),'0');
  await page.mouse.move(10,10);await capture(page,'desktop.png');
  // Hovering an object draws only its outline.
  const box=await page.locator('#scene').boundingBox();const anchor=await page.locator('.hotspot[data-key="poster"]').evaluate(n=>[parseFloat(n.style.left)/100,parseFloat(n.style.top)/100]);
  await page.mouse.move(box.x+anchor[0]*box.width,box.y+anchor[1]*box.height);
  await page.waitForFunction(()=>{const c=document.querySelector('#highlight'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let edge=0;for(let i=3;i<d.length;i+=4)if(d[i]===255)edge++;return edge>50;});
  await capture(page,'poster-hover.png');
  await page.locator('.hotspot[data-key="poster"]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#panel-title').textContent(),'Tide of Echo');
  assert.equal(await page.getByRole('link',{name:'Listen to Journal on Spotify'}).getAttribute('href'),'https://open.spotify.com/album/2YukUrIciZZ9FmSAp3tRAm');
  for(let i=0;i<8;i++)await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(()=>Boolean(document.activeElement.closest('dialog'))),true);
  await capture(page,'band-panel.png');await closeDialog(page);
  assert.equal(await page.locator('dialog').isVisible(),false);
  // Actual perspective changes, without a drag accidentally opening an object.
  await center(page);const initialSrc=await page.locator('#room-image').getAttribute('src');
  await drag(page,[760,450],[470,450]);
  await page.waitForFunction(()=>Number(document.querySelector('#scene').dataset.angle)>0);
  await page.waitForFunction(()=>!document.querySelector('#room-image').src.includes('-small'));
  assert.notEqual(await page.locator('#room-image').getAttribute('src'),initialSrc);
  assert.equal(await page.locator('dialog').isVisible(),false);await coverage(page);await capture(page,'camera-right.png');
  const currentIndex=Number(await page.locator('#scene').getAttribute('data-view'));
  const manifest=await(await page.request.get(`${base}/studio/assets/scene.json`)).json();
  const poster=manifest.frames[currentIndex].hotspots.poster.anchor;
  const coords=await page.locator('.hotspot[data-key="poster"]').evaluate(n=>[parseFloat(n.style.left)/100,parseFloat(n.style.top)/100]);
  assert.ok(Math.abs(coords[0]-poster[0])<.00001&&Math.abs(coords[1]-poster[1])<.00001);
  // Click the rendered poster silhouette away from the HTML hotspot at the rotated angle.
  const maskPoint=await page.evaluate(async url=>{
    const im=new Image();im.src=url;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const cx=c.getContext('2d');cx.drawImage(im,0,0);const d=cx.getImageData(0,0,c.width,c.height).data;const p=[];
    for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(d[(y*c.width+x)*4]===4)p.push({x:x/c.width,y:y/c.height});return p[Math.floor(p.length*.12)];
  },`${base}/studio/assets/${manifest.frames[currentIndex].mask}`);
  // Clicks within 300 ms of a drag are intentionally ignored.
  await page.waitForTimeout(350);
  assert.ok(maskPoint);const rect=await page.locator('#scene').boundingBox();await page.mouse.click(rect.x+maskPoint.x*rect.width,rect.y+maskPoint.y*rect.height);
  await page.getByRole('dialog').waitFor({state:'visible'});assert.equal(await page.locator('#panel-title').textContent(),'Tide of Echo');await closeDialog(page);
  await center(page);await drag(page,[460,480],[750,480]);await page.waitForFunction(()=>Number(document.querySelector('#scene').dataset.angle)<0);await capture(page,'camera-left.png');
  // Reversing quickly must settle on the last requested view, not an earlier async load.
  await drag(page,[900,460],[350,460],8);await drag(page,[350,460],[900,460],8);
  await page.waitForFunction(()=>document.querySelector('#scene').dataset.angle==='-6');
  await center(page);
  await menu(page,'vinyl');assert.deepEqual(await page.locator('.record-links a').evaluateAll(a=>a.map(n=>n.href)),['https://open.spotify.com/track/1I2ffk4W1Rt6vi9Ht8p9Uw','https://open.spotify.com/track/4HbKy1HOeyikBuw9zeyz1a','https://open.spotify.com/album/2YukUrIciZZ9FmSAp3tRAm']);await page.waitForFunction(()=>[...document.querySelectorAll('dialog img')].length===6&&[...document.querySelectorAll('dialog img')].every(i=>i.complete&&i.naturalWidth>0));await capture(page,'records-panel.png');await closeDialog(page);
  for(const [key,href] of [['modern-times','https://open.spotify.com/track/1I2ffk4W1Rt6vi9Ht8p9Uw'],['echo-of-tide','https://open.spotify.com/track/4HbKy1HOeyikBuw9zeyz1a'],['journal','https://open.spotify.com/album/2YukUrIciZZ9FmSAp3tRAm']]){
    await page.locator(`.hotspot[data-key="${key}"]`).focus();await page.keyboard.press('Enter');
    assert.equal(await page.getByRole('link',{name:'Listen on Spotify'}).getAttribute('href'),href);
    await page.waitForFunction(()=>document.querySelector('dialog img.cover')?.naturalWidth>0);await capture(page,`album-${key}.png`);await closeDialog(page);
  }
  await page.locator('.hotspot[data-key="badge"]').focus();await page.keyboard.press('Enter');assert.equal(await page.getByRole('link',{name:'Connect on LinkedIn'}).getAttribute('href'),'https://www.linkedin.com/in/sunzhe/');await capture(page,'badge-panel.png');await closeDialog(page);
  await menu(page,'tv');await page.getByRole('button',{name:'Late night',exact:true}).click();assert.equal(await page.locator('#scene').getAttribute('data-mood'),'late-night');
  await menu(page,'tv');await page.getByRole('button',{name:'Sunset',exact:true}).click();
  await menu(page,'rack');assert.deepEqual(await page.locator('.signal-list strong').evaluateAll(n=>n.map(e=>e.firstChild.textContent)),['Neve 1073','AudioScape 1176','Teletronix LA-2A','Bus compressor']);await closeDialog(page);
  await menu(page,'pedals');assert.equal(await page.locator('.signal-list li').count(),5);await capture(page,'pedals-panel.png');await closeDialog(page);
  // The TV carries a live terminal pinned to the rendered screen.
  assert.equal(await page.locator('#tv-live').isVisible(),true);await capture(page,'terminal.png');
  await menu(page,'guitar');assert.equal(await page.getByRole('dialog').getByRole('button',{name:/play/i}).count(),0);assert.equal(await page.locator('#sound-toggle').count(),0);await closeDialog(page);
  await center(page);await page.locator('#room-viewport').focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('#scene').dataset.angle==='1');await page.keyboard.press('Home');await page.waitForFunction(()=>document.querySelector('#scene').dataset.angle==='0');
  // Phone framing and touch dragging, with reduced motion enabled.
  const phone=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true,reducedMotion:'reduce'});phone.on('pageerror',e=>errors.push(e.message));
  await phone.goto(base);await ready(phone);await coverage(phone);await capture(phone,'mobile.png');
  const session=await phone.context().newCDPSession(phone);
  await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:170,y:410}]});
  for(let i=1;i<=12;i++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:170+i*14,y:410}]});
  await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await phone.waitForFunction(()=>Number(document.querySelector('#scene').dataset.angle)<=-4);
  const touchPan=await phone.locator('#scene').evaluate(e=>parseFloat(e.style.getPropertyValue('--pan-x')));assert.ok(touchPan>120,'A complete touch drag must pan continuously after capture transfer');
  await phone.waitForFunction(()=>!document.querySelector('#room-image').src.includes('-small'));await coverage(phone);assert.equal(await phone.locator('dialog').isVisible(),false);await capture(phone,'mobile-drag.png');
  await menu(phone,'poster');assert.equal(await phone.locator('#panel-title').textContent(),'Tide of Echo');await capture(phone,'mobile-band.png');await phone.getByRole('button',{name:'Close details'}).tap();await coverage(phone);
  // Every scene object is reachable by keyboard even when cropped on a phone.
  await phone.locator('.hotspot[data-key="guitar"]').focus();await phone.keyboard.press('Tab');
  const focusState=await phone.evaluate(()=>{const e=document.activeElement,r=e.getBoundingClientRect();return{key:e.dataset.key,x:r.x,y:r.y,w:r.width,h:r.height};});
  assert.ok(focusState.x>=-1&&focusState.x+focusState.w<=391);
  // Deep links and graceful failures remain available inside the room.
  await page.goto(`${base}/#tide-of-echo`);await page.getByRole('dialog').waitFor({state:'visible'});await closeDialog(page);
  const fallback=await browser.newPage();await fallback.route('**/studio/assets/scene.json',r=>r.abort());await fallback.goto(base);await fallback.locator('#fallback-content').waitFor({state:'visible'});await fallback.locator('#fallback-content [data-panel="poster"]').click();assert.equal(await fallback.locator('#panel-title').textContent(),'Tide of Echo');
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(base);assert.equal(await nojs.locator('.no-script').isVisible(),true);assert.equal(await nojs.locator('#room-loading').isVisible(),false);
  assert.deepEqual(errors,[]);
  console.log('PASS: fullscreen composition, front camera, left/right rotation, rapid reversal, rotated silhouette hit-testing, aligned hotspots, desktop, touch drag, keyboard navigation, focus, panels, per-album records, badge, signal chain, pedalboard, live terminal, outline-only hover, no audio, moods, deep links, and fallback.');
  console.log('Screenshots:',output.pathname);
}finally{await browser.close();}
