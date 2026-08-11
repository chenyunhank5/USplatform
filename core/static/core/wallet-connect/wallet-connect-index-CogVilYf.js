import{aV as f,aO as y,aQ as l,aR as $,aS as b,aT as x}from"./wallet-connect.js";const h=".",d={getSpacingStyles(t,e){if(Array.isArray(t))return t[e]?`var(--apkt-spacing-${t[e]})`:void 0;if(typeof t=="string")return`var(--apkt-spacing-${t})`},getFormattedDate(t){return new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric"}).format(t)},formatCurrency(t=0,e={}){const r=Number(t);return isNaN(r)?"$0.00":new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2,...e}).format(r)},getHostName(t){try{return new URL(t).hostname}catch{return""}},getTruncateString({string:t,charsStart:e,charsEnd:r,truncate:n}){return t.length<=e+r?t:n==="end"?`${t.substring(0,e)}...`:n==="start"?`...${t.substring(t.length-r)}`:`${t.substring(0,Math.floor(e))}...${t.substring(t.length-Math.floor(r))}`},generateAvatarColors(t){const r=t.toLowerCase().replace(/^0x/iu,"").replace(/[^a-f0-9]/gu,"").substring(0,6).padEnd(6,"0"),n=this.hexToRgb(r),s=getComputedStyle(document.documentElement).getPropertyValue("--w3m-border-radius-master"),c=100-3*Number(s?.replace("px","")),p=`${c}% ${c}% at 65% 40%`,u=[];for(let m=0;m<5;m+=1){const g=this.tintColor(n,.15*m);u.push(`rgb(${g[0]}, ${g[1]}, ${g[2]})`)}return`
    --local-color-1: ${u[0]};
    --local-color-2: ${u[1]};
    --local-color-3: ${u[2]};
    --local-color-4: ${u[3]};
    --local-color-5: ${u[4]};
    --local-radial-circle: ${p}
   `},hexToRgb(t){const e=parseInt(t,16),r=e>>16&255,n=e>>8&255,s=e&255;return[r,n,s]},tintColor(t,e){const[r,n,s]=t,o=Math.round(r+(255-r)*e),c=Math.round(n+(255-n)*e),p=Math.round(s+(255-s)*e);return[o,c,p]},isNumber(t){return{number:/^[0-9]+$/u}.number.test(t)},getColorTheme(t){return t||(typeof window<"u"&&window.matchMedia&&typeof window.matchMedia=="function"?window.matchMedia("(prefers-color-scheme: dark)")?.matches?"dark":"light":"dark")},splitBalance(t){const e=t.split(".");return e.length===2?[e[0],e[1]]:["0","00"]},roundNumber(t,e,r){return t.toString().length>=e?Number(t).toFixed(r):t},cssDurationToNumber(t){return t.endsWith("s")?Number(t.replace("s",""))*1e3:t.endsWith("ms")?Number(t.replace("ms","")):0},maskInput({value:t,decimals:e,integers:r}){if(t=t.replace(",","."),t===h)return`0${h}`;const[n="",s]=t.split(h).map(g=>g.replace(/[^0-9]/gu,"")),o=r?n.substring(0,r):n,c=o.length===2?String(Number(o)):o,p=typeof e=="number"?s?.substring(0,e):s,u=typeof e!="number"||e>0;return(typeof p=="string"&&u?[c,p].join(h):c)??""},capitalize(t){return t?t.charAt(0).toUpperCase()+t.slice(1):""}},w=f`
  :host {
    display: flex;
    width: inherit;
    height: inherit;
    box-sizing: border-box;
  }
`;var a=function(t,e,r,n){var s=arguments.length,o=s<3?e:n===null?n=Object.getOwnPropertyDescriptor(e,r):n,c;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(t,e,r,n);else for(var p=t.length-1;p>=0;p--)(c=t[p])&&(o=(s<3?c(o):s>3?c(e,r,o):c(e,r))||o);return s>3&&o&&Object.defineProperty(e,r,o),o};let i=class extends b{render(){return this.style.cssText=`
      flex-direction: ${this.flexDirection};
      flex-wrap: ${this.flexWrap};
      flex-basis: ${this.flexBasis};
      flex-grow: ${this.flexGrow};
      flex-shrink: ${this.flexShrink};
      align-items: ${this.alignItems};
      justify-content: ${this.justifyContent};
      column-gap: ${this.columnGap&&`var(--apkt-spacing-${this.columnGap})`};
      row-gap: ${this.rowGap&&`var(--apkt-spacing-${this.rowGap})`};
      gap: ${this.gap&&`var(--apkt-spacing-${this.gap})`};
      padding-top: ${this.padding&&d.getSpacingStyles(this.padding,0)};
      padding-right: ${this.padding&&d.getSpacingStyles(this.padding,1)};
      padding-bottom: ${this.padding&&d.getSpacingStyles(this.padding,2)};
      padding-left: ${this.padding&&d.getSpacingStyles(this.padding,3)};
      margin-top: ${this.margin&&d.getSpacingStyles(this.margin,0)};
      margin-right: ${this.margin&&d.getSpacingStyles(this.margin,1)};
      margin-bottom: ${this.margin&&d.getSpacingStyles(this.margin,2)};
      margin-left: ${this.margin&&d.getSpacingStyles(this.margin,3)};
      width: ${this.width};
    `,x`<slot></slot>`}};i.styles=[y,w];a([l()],i.prototype,"flexDirection",void 0);a([l()],i.prototype,"flexWrap",void 0);a([l()],i.prototype,"flexBasis",void 0);a([l()],i.prototype,"flexGrow",void 0);a([l()],i.prototype,"flexShrink",void 0);a([l()],i.prototype,"alignItems",void 0);a([l()],i.prototype,"justifyContent",void 0);a([l()],i.prototype,"columnGap",void 0);a([l()],i.prototype,"rowGap",void 0);a([l()],i.prototype,"gap",void 0);a([l()],i.prototype,"padding",void 0);a([l()],i.prototype,"margin",void 0);a([l()],i.prototype,"width",void 0);i=a([$("wui-flex")],i);export{d as U};
