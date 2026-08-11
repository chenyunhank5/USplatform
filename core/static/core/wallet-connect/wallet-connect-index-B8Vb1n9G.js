import{ax as l,ay as g,aY as h,b4 as w,aA as m,az as c,bf as _,bg as E,a_ as R,aN as b,aO as y,aQ as p,aR as v,aS as C,aT as S,aP as O,aW as $}from"./wallet-connect.js";function T(){try{return c.returnOpenHref(`${R.SECURE_SITE_SDK_ORIGIN}/loading`,"popupWindow","width=600,height=800,scrollbars=yes")}catch{throw new Error("Could not open social popup")}}async function A(){h.push("ConnectingFarcaster");const e=w.getAuthConnector();if(e&&!l.getAccountData()?.farcasterUrl)try{const{url:t}=await e.provider.getFarcasterUri();l.setAccountProp("farcasterUrl",t,l.state.activeChain)}catch(t){h.goBack(),m.showError(t)}}async function I(e){h.push("ConnectingSocial");const r=w.getAuthConnector();let t=null;try{const i=setTimeout(()=>{throw new Error("Social login timed out. Please try again.")},45e3);if(r&&e){if(c.isTelegram()||(t=T()),t)l.setAccountProp("socialWindow",_(t),l.state.activeChain);else if(!c.isTelegram())throw new Error("Could not create social popup");const{uri:n}=await r.provider.getSocialRedirectUri({provider:e});if(!n)throw t?.close(),new Error("Could not fetch the social redirect uri");if(t&&(t.location.href=n),c.isTelegram()){E.setTelegramSocialProvider(e);const o=c.formatTelegramSocialLoginUrl(n);c.openHref(o,"_top")}clearTimeout(i)}}catch(i){t?.close();const n=c.parseError(i);m.showError(n),g.sendEvent({type:"track",event:"SOCIAL_LOGIN_ERROR",properties:{provider:e,message:n}})}}async function j(e){l.setAccountProp("socialProvider",e,l.state.activeChain),g.sendEvent({type:"track",event:"SOCIAL_LOGIN_STARTED",properties:{provider:e}}),e==="farcaster"?await A():await I(e)}const L=b`
  :host {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 40px;
    height: 40px;
    border-radius: ${({borderRadius:e})=>e[20]};
    overflow: hidden;
  }

  wui-icon {
    width: 100%;
    height: 100%;
  }
`;var x=function(e,r,t,i){var n=arguments.length,o=n<3?r:i===null?i=Object.getOwnPropertyDescriptor(r,t):i,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,r,t,i);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(o=(n<3?a(o):n>3?a(r,t,o):a(r,t))||o);return n>3&&o&&Object.defineProperty(r,t,o),o};let f=class extends C{constructor(){super(...arguments),this.logo="google"}render(){return S`<wui-icon color="inherit" size="inherit" name=${this.logo}></wui-icon> `}};f.styles=[y,L];x([p()],f.prototype,"logo",void 0);f=x([v("wui-logo")],f);const U=b`
  :host {
    width: 100%;
  }

  button {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: ${({spacing:e})=>e[3]};
    width: 100%;
    background-color: transparent;
    border-radius: ${({borderRadius:e})=>e[4]};
  }

  wui-text {
    text-transform: capitalize;
  }

  @media (hover: hover) {
    button:hover:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    }
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;var d=function(e,r,t,i){var n=arguments.length,o=n<3?r:i===null?i=Object.getOwnPropertyDescriptor(r,t):i,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,r,t,i);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(o=(n<3?a(o):n>3?a(r,t,o):a(r,t))||o);return n>3&&o&&Object.defineProperty(r,t,o),o};let u=class extends C{constructor(){super(...arguments),this.logo="google",this.name="Continue with google",this.disabled=!1}render(){return S`
      <button ?disabled=${this.disabled} tabindex=${$(this.tabIdx)}>
        <wui-flex gap="2" alignItems="center">
          <wui-image ?boxed=${!0} logo=${this.logo}></wui-image>
          <wui-text variant="lg-regular" color="primary">${this.name}</wui-text>
        </wui-flex>
        <wui-icon name="chevronRight" size="lg" color="default"></wui-icon>
      </button>
    `}};u.styles=[y,O,U];d([p()],u.prototype,"logo",void 0);d([p()],u.prototype,"name",void 0);d([p()],u.prototype,"tabIdx",void 0);d([p({type:Boolean})],u.prototype,"disabled",void 0);u=d([v("wui-list-social")],u);export{j as e};
