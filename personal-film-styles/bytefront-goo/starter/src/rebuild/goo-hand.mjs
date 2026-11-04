import {fileURLToPath} from 'node:url';
// One painted asset includes palm, wrist, ribbed cuff and sleeve overlap.
// The cuff is never attached as a separate floating rectangle.
import {loadImage} from '@napi-rs/canvas';
const actions=await loadImage(fileURLToPath(new URL('../../assets/goo-v04/hands-actions-v20.png',import.meta.url)));
const image=await loadImage(fileURLToPath(new URL('../../assets/goo-v04/hands-cuffs-v20.png',import.meta.url)));
export const HAND_SCALE=.24;
// Per-cell anatomical audit: palm-facing open/point/grip are LEFT;
// dorsal relaxed and the newly generated action cells are RIGHT.
// Prompt labels were wrong: sourceSide follows observed thumb/surface geometry.
// Mirror in forearm-local space exactly once. In the canonical right-facing actor,
// the far (screen-left) arm is anatomical right; the near arm is anatomical left.
export const GOO_FAR_HAND=1,GOO_NEAR_HAND=-1;
export const HAND_CELLS={
 relaxed:{crop:[148,7,267,428],wrist:[270,151],rotation:-Math.PI/2,tip:[300,413],palm:[280,270]},
 open:{sourceSide:-1,crop:[622,107,318,378],wrist:[753,333],rotation:Math.PI/2,tip:[889,133],palm:[776,273]},
 point:{sourceSide:-1,crop:[1158,23,230,460],wrist:[1253,334],rotation:Math.PI/2,tip:[1315,35],palm:[1251,262]},
 oldChin:{crop:[152,549,245,430],wrist:[250,805],rotation:Math.PI/2,tip:[292,578],palm:[257,718]},
 oldScratch:{crop:[634,516,289,467],wrist:[749,804],rotation:Math.PI/2,tip:[804,538],palm:[752,717]},
 writeGrip:{sourceSide:-1,crop:[1124,548,267,434],wrist:[1241,804],rotation:Math.PI/2,tip:[1316,640],palm:[1248,718]},
 grip:{sourceSide:-1,crop:[1124,548,267,434],wrist:[1241,804],rotation:Math.PI/2,tip:[1348,625],palm:[1248,718]}
,
 press:{crop:[70,135,720,310],wrist:[384,287],rotation:0,tip:[766,327],palm:[500,286],sourceSide:1,scale:.22,atlas:actions},
 scratch:{crop:[975,16,370,483],wrist:[1134,367],rotation:Math.PI/2,tip:[1229,43],palm:[1145,247],sourceSide:1,scale:.22,atlas:actions},
 chin:{crop:[975,535,340,469],wrist:[1132,846],rotation:Math.PI/2,tip:[1161,561],palm:[1150,724],sourceSide:1,scale:.18,atlas:actions},
 write:{crop:[62,554,703,398],wrist:[339,795],rotation:0,tip:[456,939],palm:[480,757],sourceSide:1,scale:.22,atlas:actions}
};
function cell(kind){return HAND_CELLS[kind==='flat'?'open':kind]||HAND_CELLS.grip;}
export function handMarker(kind='point',which='tip',side=1){const q=cell(kind),p=q[which],k=q.scale??HAND_SCALE,dx=(p[0]-q.wrist[0])*k,dy=(p[1]-q.wrist[1])*k;return [dx*Math.cos(q.rotation)-dy*Math.sin(q.rotation),(side/(q.sourceSide??1))*(dx*Math.sin(q.rotation)+dy*Math.cos(q.rotation))];}
export function handWorldMarker(wrist,a,kind='point',which='tip',side=1,k=1){const [dx,dy]=handMarker(kind,which,side);return [wrist[0]+k*(dx*Math.cos(a)-dy*Math.sin(a)),wrist[1]+k*(dx*Math.sin(a)+dy*Math.cos(a))];}
export function gooHand(c,x,y,a,kind='open',side=1,k=1){
 const q=cell(kind),[sx,sy,w,h]=q.crop;
 c.save();c.translate(x,y);c.rotate(a);c.scale(k,(side/(q.sourceSide??1))*k);c.rotate(q.rotation);c.scale(q.scale??HAND_SCALE,q.scale??HAND_SCALE);
 c.drawImage(q.atlas??image,sx,sy,w,h,sx-q.wrist[0],sy-q.wrist[1],w,h);c.restore();
}

export function wristAtContact(point,a,kind='point',side=1,k=1){const [dx,dy]=handMarker(kind,'tip',side);return [point[0]-k*(dx*Math.cos(a)-dy*Math.sin(a)),point[1]-k*(dx*Math.sin(a)+dy*Math.cos(a))];}
