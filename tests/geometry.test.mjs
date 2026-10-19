import test from 'node:test';
import assert from 'node:assert/strict';
import { pointInImage, fitScene, boundedPan, frameForAngle, hotspotFromPixels, quadTransform, applyQuadTransform } from '../studio/js/geometry.js';

test('hit testing accounts for image offsets, scaling, and mobile panning',()=>{
  const rect={left:-220,top:170,width:1200,height:800};
  assert.deepEqual(pointInImage(380,570,rect,600,400),{x:300,y:200});
  assert.equal(pointInImage(980,570,rect,600,400),null);
  assert.equal(pointInImage(0,169,rect,600,400),null);
  assert.equal(pointInImage(0,0,{left:0,top:0,width:0,height:0},600,400),null);
});

test('the whole room height always fits, with sideways panning only when needed',()=>{
  for(const [width,height]of[[1440,900],[1920,1080],[390,844],[844,390],[2560,1080]]){
    const size=fitScene(width,height,16/9);
    assert.equal(size.height,height);
    assert.ok(Math.abs(size.width/size.height-16/9)<1e-9);
    const pan=boundedPan(99999,-99999,size,{width,height});
    assert.equal(pan.x,Math.max(0,(size.width-width)/2));
    assert.equal(pan.y,0);
  }
  assert.deepEqual(boundedPan(-50,20,{width:1000,height:500},{width:1400,height:500}),{x:0,y:0});
});

test('camera selection is bounded and preserves the front-facing center',()=>{
  const frames=Array.from({length:25},(_,index)=>({index,angle:-6+index*.5}));
  assert.equal(frameForAngle(0,frames),12);
  assert.equal(frameForAngle(-500,frames),0);
  assert.equal(frameForAngle(500,frames),24);
  assert.equal(frameForAngle(2.6,frames),17);
});

test('touch tolerance finds nearby objects without wrapping across mask edges',()=>{
  const pixels=new Uint8ClampedArray(5*5*4);pixels[(2*5+2)*4]=4;pixels[(1*5+4)*4]=7;
  assert.equal(hotspotFromPixels(pixels,5,5,{x:2,y:2}),4);
  assert.equal(hotspotFromPixels(pixels,5,5,{x:1,y:2}),0);
  assert.equal(hotspotFromPixels(pixels,5,5,{x:1,y:2},1),4);
  assert.equal(hotspotFromPixels(pixels,5,5,{x:0,y:2},1),0);
  assert.equal(hotspotFromPixels(pixels,5,5,null,4),0);
});

test('the live screen maps its corners exactly onto the rendered TV quad',()=>{
  const quad=[[612,140],[1170,152],[1165,447],[618,438]];
  const m=quadTransform(960,540,quad);
  for(const [[x,y],[qx,qy]] of [[[0,0],quad[0]],[[960,0],quad[1]],[[960,540],quad[2]],[[0,540],quad[3]]]){
    const [X,Y]=applyQuadTransform(m,x,y);assert.ok(Math.abs(X-qx)<1e-6&&Math.abs(Y-qy)<1e-6,`${X},${Y} vs ${qx},${qy}`);
  }
});
