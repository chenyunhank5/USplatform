import{aV as c,aO as m,aQ as u,aR as f,aS as b,aW as h,aT as d}from"./wallet-connect.js";import"./wallet-connect-index-nKFq4XGN.js";const v=c`
  :host {
    position: relative;
    display: inline-block;
    width: 100%;
  }
`;var a=function(o,i,r,l){var s=arguments.length,e=s<3?i:l===null?l=Object.getOwnPropertyDescriptor(i,r):l,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")e=Reflect.decorate(o,i,r,l);else for(var p=o.length-1;p>=0;p--)(n=o[p])&&(e=(s<3?n(e):s>3?n(i,r,e):n(i,r))||e);return s>3&&e&&Object.defineProperty(i,r,e),e};let t=class extends b{constructor(){super(...arguments),this.disabled=!1}render(){return d`
      <wui-input-text
        type="email"
        placeholder="Email"
        icon="mail"
        size="lg"
        .disabled=${this.disabled}
        .value=${this.value}
        data-testid="wui-email-input"
        tabIdx=${h(this.tabIdx)}
      ></wui-input-text>
      ${this.templateError()}
    `}templateError(){return this.errorMessage?d`<wui-text variant="sm-regular" color="error">${this.errorMessage}</wui-text>`:null}};t.styles=[m,v];a([u()],t.prototype,"errorMessage",void 0);a([u({type:Boolean})],t.prototype,"disabled",void 0);a([u()],t.prototype,"value",void 0);a([u()],t.prototype,"tabIdx",void 0);t=a([f("wui-email-input")],t);
