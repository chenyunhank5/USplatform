import{aN as p,aO as h,aQ as d,aR as g,aS as b,aT as u}from"./wallet-connect.js";const f=p`
  :host {
    position: relative;
    display: flex;
    width: 100%;
    height: 1px;
    background-color: ${({tokens:t})=>t.theme.borderPrimary};
    justify-content: center;
    align-items: center;
  }

  :host > wui-text {
    position: absolute;
    padding: 0px 8px;
    transition: background-color ${({durations:t})=>t.lg}
      ${({easings:t})=>t["ease-out-power-2"]};
    will-change: background-color;
  }

  :host([data-bg-color='primary']) > wui-text {
    background-color: ${({tokens:t})=>t.theme.backgroundPrimary};
  }

  :host([data-bg-color='secondary']) > wui-text {
    background-color: ${({tokens:t})=>t.theme.foregroundPrimary};
  }
`;var c=function(t,r,o,i){var n=arguments.length,e=n<3?r:i===null?i=Object.getOwnPropertyDescriptor(r,o):i,s;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")e=Reflect.decorate(t,r,o,i);else for(var l=t.length-1;l>=0;l--)(s=t[l])&&(e=(n<3?s(e):n>3?s(r,o,e):s(r,o))||e);return n>3&&e&&Object.defineProperty(r,o,e),e};let a=class extends b{constructor(){super(...arguments),this.text="",this.bgColor="primary"}render(){return this.dataset.bgColor=this.bgColor,u`${this.template()}`}template(){return this.text?u`<wui-text variant="md-regular" color="secondary">${this.text}</wui-text>`:null}};a.styles=[h,f];c([d()],a.prototype,"text",void 0);c([d()],a.prototype,"bgColor",void 0);a=c([g("wui-separator")],a);
