// Parameterized audit. Parameters are a declared specification, not inferred from output.
const defaults={roomSize:22,originZ:12,capacity:8,height:6,wallInset:.24,doorHalf:2.5,tolerance:1e-8};
function evaluate(records,placements,rooms,spec=defaults){
 const s={...defaults,...spec},R=Math.max(1,Math.ceil(records.length/s.capacity)),ids=records.map(r=>r.id),out=placements.map(p=>p.id),half=s.roomSize/2,near=(a,b)=>Math.abs(a-b)<=s.tolerance;
 const roomIndex=p=>{for(let i=0;i<R;i++)if(p.z<s.originZ-i*s.roomSize&&p.z>s.originZ-(i+1)*s.roomSize)return i;return -1;};
 const groups=Array.from({length:R},(_,i)=>placements.filter(p=>roomIndex(p)===i));
 const checks={inputUnique:new Set(ids).size===ids.length,coverage:ids.every(id=>out.includes(id)),noDuplicates:new Set(out).size===out.length,noUnexpected:out.every(id=>ids.includes(id)),count:out.length===ids.length,allocation:rooms.length===R&&placements.every(p=>roomIndex(p)>=0)&&groups.every((g,i)=>g.length===Math.min(s.capacity,Math.max(0,ids.length-i*s.capacity))),finiteDimensions:true,wallAttachment:true,orientation:true,horizontalFootprint:true,verticalFootprint:true,doorClearance:true,thumbnailAvailable:true,thumbnailMembership:true,thumbnailFirst:true};
 const geometry=placements.map(p=>{const i=roomIndex(p),north=s.originZ-(i+1)*s.roomSize,south=s.originZ-i*s.roomSize;let wall=null,expectedRotation=null,foot=false,door=true;
  if(near(Math.abs(p.x),half-s.wallInset)){wall=p.x>0?'east':'west';expectedRotation=p.x>0?-90:90;foot=p.z-p.w/2>north&&p.z+p.w/2<south;}
  else if(near(p.z,north+s.wallInset)){wall='north';expectedRotation=0;foot=Math.abs(p.x)+p.w/2<half;if(i<R-1)door=Math.abs(p.x)-p.w/2>s.doorHalf;}
  else if(near(p.z,south-s.wallInset)){wall='south';expectedRotation=180;foot=Math.abs(p.x)+p.w/2<half;if(i>0)door=Math.abs(p.x)-p.w/2>s.doorHalf;}
  const c={finiteDimensions:[p.x,p.y,p.z,p.rotation,p.w,p.h].every(Number.isFinite)&&p.w>0&&p.h>0,wallAttachment:i>=0&&wall!==null,orientation:expectedRotation!==null&&near(p.rotation,expectedRotation),horizontalFootprint:foot,verticalFootprint:p.y-p.h/2>0&&p.y+p.h/2<s.height,doorClearance:door};
  for(const k of Object.keys(c))checks[k]&&=c[k];return {id:p.id,room:i+1,wall,...c};
 });
 const thumbnails=groups.map((group,i)=>{const physicalIds=new Set(group.map(p=>p.id)),first=records.find(r=>physicalIds.has(r.id))?.id??null,actual=rooms[i]?.auditThumbId??null;const c={thumbnailAvailable:group.length===0?actual===null:actual!==null,thumbnailMembership:group.length===0?actual===null:physicalIds.has(actual),thumbnailFirst:actual===first};for(const k of Object.keys(c))checks[k]&&=c[k];return {room:i+1,actual,expected:first,...c};});
 const identifier=['inputUnique','coverage','noDuplicates','noUnexpected','count'].every(k=>checks[k]);
 const plane=['finiteDimensions','wallAttachment','orientation','horizontalFootprint','verticalFootprint','doorClearance'].every(k=>checks[k]);
 return {checks,identifierPass:identifier,allocationPass:checks.allocation,geometryPass:plane,thumbnailPass:['thumbnailAvailable','thumbnailMembership','thumbnailFirst'].every(k=>checks[k]),geometry,thumbnails};
}
module.exports={defaults,evaluate};
