import{a as e}from"./rolldown-runtime-D_juG1Xi.js";import{t}from"./react-BcXKmAwN.js";
/**
* @license lucide-react v0.544.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var n=e=>e.replace(/([a-z0-9])([A-Z])/g,`$1-$2`).toLowerCase(),r=e=>e.replace(/^([A-Z])|[\s-_]+(\w)/g,(e,t,n)=>n?n.toUpperCase():t.toLowerCase()),i=e=>{let t=r(e);return t.charAt(0).toUpperCase()+t.slice(1)},a=(...e)=>e.filter((e,t,n)=>!!e&&e.trim()!==``&&n.indexOf(e)===t).join(` `).trim(),o=e=>{for(let t in e)if(t.startsWith(`aria-`)||t===`role`||t===`title`)return!0},s={xmlns:`http://www.w3.org/2000/svg`,width:24,height:24,viewBox:`0 0 24 24`,fill:`none`,stroke:`currentColor`,strokeWidth:2,strokeLinecap:`round`,strokeLinejoin:`round`},c=e(t()),l=(0,c.forwardRef)(({color:e=`currentColor`,size:t=24,strokeWidth:n=2,absoluteStrokeWidth:r,className:i=``,children:l,iconNode:u,...d},f)=>(0,c.createElement)(`svg`,{ref:f,...s,width:t,height:t,stroke:e,strokeWidth:r?Number(n)*24/Number(t):n,className:a(`lucide`,i),...!l&&!o(d)&&{"aria-hidden":`true`},...d},[...u.map(([e,t])=>(0,c.createElement)(e,t)),...Array.isArray(l)?l:[l]])),u=(e,t)=>{let r=(0,c.forwardRef)(({className:r,...o},s)=>(0,c.createElement)(l,{ref:s,iconNode:t,className:a(`lucide-${n(i(e))}`,`lucide-${e}`,r),...o}));return r.displayName=i(e),r};export{u as t};