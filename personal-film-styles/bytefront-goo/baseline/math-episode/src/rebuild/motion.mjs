// Short travel, readable contact hold, then withdrawal. Never retime narration.
import fs from 'node:fs';
export const C=JSON.parse(fs.readFileSync(new URL('../../content/motion-v16.json',import.meta.url)));
const clamp=x=>Math.max(0,Math.min(1,x));
// Cubic Bezier (.25,0,.15,1): brief acceleration followed by a longer ease-out.
export function decisive(u){u=clamp(u);if(!u||u===1)return u;let lo=0,hi=1,t=u;for(let i=0;i<14;i++){t=(lo+hi)/2;const x=3*(1-t)*(1-t)*t*.25+3*(1-t)*t*t*.15+t*t*t;if(x<u)lo=t;else hi=t;}return 3*(1-t)*t*t+t*t*t;}
export const travel=(t,a,b)=>decisive((t-a)/(b-a));
export const cue=(t,range)=>travel(t,...range);
// Optional rotation-only follow-through, no overshoot of the contact position.
export function settle(t,end,span=.25){const u=(t-end)/span;return u>0&&u<1?Math.sin(Math.PI*u)*(1-u):0;}
