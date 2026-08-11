import{aN as l,aQ as h,aR as m,aS as c,aT as f}from"./wallet-connect.js";const p=l`
  :host {
    display: block;
    background: linear-gradient(
      90deg,
      ${({tokens:e})=>e.theme.foregroundPrimary} 0%,
      ${({tokens:e})=>e.theme.foregroundSecondary} 50%,
      ${({tokens:e})=>e.theme.foregroundPrimary} 100%
    );
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
    border-radius: ${({borderRadius:e})=>e[1]};
  }

  :host([data-rounded='true']) {
    border-radius: ${({borderRadius:e})=>e[16]};
  }

  @keyframes shimmer {
    0% {
      background-position: 100% 0;
    }
    100% {
      background-position: -100% 0;
    }
  }
`;var n=function(e,i,o,s){var d=arguments.length,t=d<3?i:s===null?s=Object.getOwnPropertyDescriptor(i,o):s,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")t=Reflect.decorate(e,i,o,s);else for(var u=e.length-1;u>=0;u--)(a=e[u])&&(t=(d<3?a(t):d>3?a(i,o,t):a(i,o))||t);return d>3&&t&&Object.defineProperty(i,o,t),t};let r=class extends c{constructor(){super(...arguments),this.width="",this.height="",this.variant="default",this.rounded=!1}render(){return this.style.cssText=`
      width: ${this.width};
      height: ${this.height};
    `,this.dataset.rounded=this.rounded?"true":"false",f`<slot></slot>`}};r.styles=[p];n([h()],r.prototype,"width",void 0);n([h()],r.prototype,"height",void 0);n([h()],r.prototype,"variant",void 0);n([h({type:Boolean})],r.prototype,"rounded",void 0);r=n([m("wui-shimmer")],r);
