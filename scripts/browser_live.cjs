// Actual PHP/MySQL frontend and browser-owned pointer lock. No API fixtures/getter injection.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),base=process.env.AUDIT_BASE_URL;
assert(base&&/^http:\/\/127\.0\.0\.1:\d+$/.test(base));
(async()=>{
 const headless=process.env.AUDIT_HEADLESS!=='0';
 const browser=await chromium.launch({headless,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const runs=[];
 try{
 for(const sensitivity of [1,1.5]){
   console.log('Live browser condition',sensitivity,'loading');
   const page=await browser.newPage({viewport:{width:960,height:600}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base,{waitUntil:'load'});
   await page.waitForFunction(()=>document.querySelector('a-scene')?.hasLoaded&&!document.getElementById('enter-btn').disabled,null,{timeout:45000});
   console.log('Live browser scene ready',sensitivity);
   const state=await page.evaluate(()=>({exhibits:document.querySelectorAll('[exhibit]').length,rooms:window.GALLERY_TELEPORTS.length-1,records:Object.keys(ART_DATA).length}));
   assert.equal(state.exhibits,17);assert.equal(state.rooms,3);
   await page.evaluate(s=>{window.MOUSE_SENSITIVITY=s;},sensitivity);
   await page.locator('#enter-btn').click();
   console.log('Live browser Enter clicked',sensitivity);
   let locked=true;
   try{await page.waitForFunction(()=>document.pointerLockElement===document.querySelector('.a-canvas'),null,{timeout:3000});}catch{locked=false;}
   if(!locked){
     await page.bringToFront();
     await page.locator('.a-canvas').click({position:{x:300,y:300},force:true});
     try{await page.waitForFunction(()=>document.pointerLockElement===document.querySelector('.a-canvas'),null,{timeout:5000});locked=true;}catch{}
   }
   const errorsBeforeMovement=errors.slice();
   console.log('Live pointer lock acquired',sensitivity,locked);
   let delivered=[];
   if(locked){
     await page.evaluate(()=>{window.AUDIT_MOUSE=[];document.querySelector('.a-canvas').addEventListener('mousemove',e=>window.AUDIT_MOUSE.push({trusted:e.isTrusted,x:e.movementX,y:e.movementY}));});
     await Promise.race([page.mouse.move(485,302),new Promise((_,reject)=>setTimeout(()=>reject(new Error('mouse move timed out')),10000))]);await page.waitForTimeout(200);
     delivered=await page.evaluate(()=>window.AUDIT_MOUSE);
   }
   runs.push({sensitivity,backend:'actual PHP/MySQL',state,pointerLockAcquired:locked,pointerLockGetterInjected:false,input:'Playwright/CDP trusted mouse input after clicking Enter; no human participant',delivered,errorsBeforeMovement,errorsAfterMovement:errors.slice(errorsBeforeMovement.length)});
   await page.keyboard.press('Escape');await page.close();
 }
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
 await mobile.goto(base,{waitUntil:'load'});await mobile.waitForFunction(()=>document.querySelector('a-scene')?.hasLoaded,null,{timeout:45000});
 const emulation=await mobile.evaluate(()=>({viewport:[innerWidth,innerHeight],exhibits:document.querySelectorAll('[exhibit]').length,scrollWidth:document.documentElement.scrollWidth,touchCapable:navigator.maxTouchPoints>0}));await mobile.close();
 const report={environment:{browser:browser.version(),headless,rendering:'software WebGL'},scope:'Integrated desktop frontend and browser-owned pointer-lock automation; mobile emulation only, no manual participant or physical device',runs,mobileEmulation:emulation};
 report.summary={backendScenesLoaded:runs.length,pointerLockAcquired:runs.map(r=>r.pointerLockAcquired),baselineTrustedCanvasEvents:runs[0].delivered.filter(e=>e.trusted).length,nondefaultCanvasEvents:runs[1].delivered.length,nondefaultStackError:runs[1].errorsAfterMovement.some(e=>e.includes('Maximum call stack')),mobileEmulatedExhibits:emulation.exhibits};
 fs.writeFileSync(path.join(root,'results/browser_live.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.summary,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
