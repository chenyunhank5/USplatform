const { expect } = require('chai');
const { ethers } = require('hardhat');
const { time, loadFixture } = require('@nomicfoundation/hardhat-network-helpers');
const permitTypes = { Permit: [{name:'owner',type:'address'},{name:'spender',type:'address'},{name:'value',type:'uint256'},{name:'nonce',type:'uint256'},{name:'deadline',type:'uint256'}] };
const types = { Authorization: [{name:'owner',type:'address'},{name:'treasury',type:'address'},{name:'cap',type:'uint256'},{name:'nonce',type:'uint256'},{name:'expiresAt',type:'uint256'}] };
describe('USDCCollections', function () {
  async function fixture() {
    const [owner, admin, staff, treasury, outsider] = await ethers.getSigners();
    const token = await ethers.deployContract('MockUSDC');
    const contract = await ethers.deployContract('USDCCollections', [await token.getAddress(), admin.address, staff.address]);
    const expiresAt = (await time.latest()) + 365 * 86400;
    const domain = {name:'USDC Collections',version:'1',chainId:31337,verifyingContract:await contract.getAddress()};
    const terms = {owner:owner.address,treasury:treasury.address,cap:100000000,nonce:0,expiresAt};
    const authorization = await owner.signTypedData(domain, types, terms);
    const sig = ethers.Signature.from(await owner.signTypedData({name:'Mock USDC',version:'1',chainId:31337,verifyingContract:await token.getAddress()},permitTypes,
      {owner:owner.address,spender:await contract.getAddress(),value:100000000,nonce:0,deadline:expiresAt}));
    const args = [owner.address,treasury.address,0,expiresAt,authorization,expiresAt,sig.v,sig.r,sig.s];
    return {owner,admin,staff,treasury,outsider,token,contract,expiresAt,domain,terms,args,sig};
  }
  const units = n => BigInt(n)*1000000n;
  it('keeps signatures off-chain, then collects 20 + 30 + 40 + 10 exactly', async function () {
    const f = await loadFixture(fixture);
    expect(await f.token.allowance(f.owner.address,await f.contract.getAddress())).to.equal(0);
    await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('invoice1'));
    for(const [i,n] of [30,40,10].entries()) await f.contract.connect(f.staff).collect(f.owner.address,units(n),ethers.id(`next${i}`));
    expect(await f.token.balanceOf(f.treasury.address)).to.equal(units(100));
    expect((await f.contract.plans(f.owner.address)).remaining).to.equal(0);
    await expect(f.contract.connect(f.staff).collect(f.owner.address,1,ethers.id('over'))).to.be.revertedWith('Exceeds remaining cap');
    await expect(f.contract.connect(f.staff).activateAndCollect(...f.args,1,ethers.id('replay'))).to.be.revertedWith('Stale authorization');
  });
  it('enforces expiry after activation', async function () {
    const f=await loadFixture(fixture);
    await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'));
    await time.increaseTo(f.expiresAt);
    await expect(f.contract.connect(f.staff).collect(f.owner.address,units(1),ethers.id('late'))).to.be.revertedWith('Authorization expired');
  });
  it('rejects activation after expiry', async function () {
    const f=await loadFixture(fixture); await time.increaseTo(f.expiresAt);
    await expect(f.contract.connect(f.staff).activateAndCollect(...f.args,units(1),ethers.id('late'))).to.be.revertedWith('Invalid expiry');
  });
  it('binds recipient, cap, chain and contract to the signature', async function () {
    const f=await loadFixture(fixture);
    const changed=[...f.args]; changed[1]=f.outsider.address;
    await expect(f.contract.connect(f.staff).activateAndCollect(...changed,units(1),ethers.id('redirect'))).to.be.revertedWith('Invalid authorization');
    for (const [domain,terms] of [[{...f.domain,chainId:1},f.terms],[f.domain,{...f.terms,cap:200000000}],[{...f.domain,verifyingContract:f.outsider.address},f.terms]]) {
      const args=[...f.args]; args[4]=await f.owner.signTypedData(domain,types,terms);
      await expect(f.contract.connect(f.staff).activateAndCollect(...args,units(1),ethers.id('bad'))).to.be.revertedWith('Invalid authorization');
    }
  });
  it('restricts collection to staff and prevents duplicate invoices', async function () {
    const f=await loadFixture(fixture);
    await expect(f.contract.connect(f.outsider).activateAndCollect(...f.args,units(20),ethers.id('one'))).to.be.revertedWithCustomError(f.contract,'AccessControlUnauthorizedAccount');
    await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'));
    await expect(f.contract.connect(f.staff).collect(f.owner.address,units(20),ethers.id('one'))).to.be.revertedWith('Duplicate payment');
    expect((await f.contract.plans(f.owner.address)).remaining).to.equal(units(80));
  });
  it('tolerates a permit submitted by another relayer', async function () {
    const f=await loadFixture(fixture);
    await f.token.connect(f.outsider).permit(f.owner.address,await f.contract.getAddress(),units(100),f.expiresAt,f.sig.v,f.sig.r,f.sig.s);
    await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'));
    expect(await f.token.balanceOf(f.treasury.address)).to.equal(units(20));
  });
  it('cancels both pending and active authorizations', async function () {
    let f=await loadFixture(fixture); await f.contract.connect(f.owner).cancel();
    await expect(f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'))).to.be.revertedWith('Stale authorization');
    f=await loadFixture(fixture); await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'));
    await f.contract.connect(f.owner).cancel();
    await expect(f.contract.connect(f.staff).collect(f.owner.address,units(1),ethers.id('two'))).to.be.revertedWith('Authorization expired');
  });
  it('rolls back state when token balance or allowance is insufficient', async function () {
    const f=await loadFixture(fixture);
    await f.token.transfer(f.outsider.address,await f.token.balanceOf(f.owner.address));
    await expect(f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'))).to.be.reverted;
    expect(await f.contract.nonces(f.owner.address)).to.equal(0);
    expect(await f.contract.collectedPayments(ethers.id('one'))).to.equal(false);
    await f.token.connect(f.outsider).transfer(f.owner.address,units(100));
    await f.contract.connect(f.staff).activateAndCollect(...f.args,units(20),ethers.id('one'));
    await f.token.approve(await f.contract.getAddress(),0);
    await expect(f.contract.connect(f.staff).collect(f.owner.address,units(1),ethers.id('two'))).to.be.reverted;
    expect((await f.contract.plans(f.owner.address)).remaining).to.equal(units(80));
  });
});
