import{aV as c,aS as f,aT as p,aR as m}from"./wallet-connect.js";import"./wallet-connect-index-CogVilYf.js";import"./wallet-connect-index-CUCn9rBR.js";import"./wallet-connect-index-dCBKkBlp.js";import"./wallet-connect-index-DDHBnAC-.js";import"./wallet-connect-index-DRhw5OpL.js";const d=c`
  :host > wui-flex:first-child {
    height: 500px;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none;
  }

  :host > wui-flex:first-child::-webkit-scrollbar {
    display: none;
  }
`;var u=function(o,t,i,n){var r=arguments.length,e=r<3?t:n===null?n=Object.getOwnPropertyDescriptor(t,i):n,l;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")e=Reflect.decorate(o,t,i,n);else for(var a=o.length-1;a>=0;a--)(l=o[a])&&(e=(r<3?l(e):r>3?l(t,i,e):l(t,i))||e);return r>3&&e&&Object.defineProperty(t,i,e),e};let s=class extends f{render(){return p`
      <wui-flex flexDirection="column" .padding=${["0","3","3","3"]} gap="3">
        <w3m-activity-list page="activity"></w3m-activity-list>
      </wui-flex>
    `}};s.styles=d;s=u([m("w3m-transactions-view")],s);export{s as W3mTransactionsView};
