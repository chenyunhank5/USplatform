import { createAppKit } from '@reown/appkit'
import { EthersAdapter } from '@reown/appkit-adapter-ethers'
import { createAppKitWalletButton } from '@reown/appkit-wallet-button'
import { mainnet } from '@reown/appkit/networks'
import { BrowserProvider, Contract, Signature, TypedDataEncoder, formatUnits, parseUnits, id, getAddress } from 'ethers'
import { USDC, messages, permitTypes, termsTypes, verifyRecord, collectorAbi, tokenAbi } from './usdc-protocol.mjs'

const root = document.querySelector('[data-usdc]')
const config = JSON.parse(document.querySelector('#usdc-config').textContent)
const status = document.querySelector('#usdc-status')
const list = document.querySelector('#usdc-records')
const staff = root.dataset.mode === 'staff'
let app, selectedOwner
function say(message) { status.textContent = message }
function el(tag, text) { const node = document.createElement(tag); node.textContent = text; return node }
async function api(url, data) {
  const response = await fetch(url, { method: data ? 'POST' : 'GET', credentials: 'same-origin', cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
    body: data ? JSON.stringify(data) : undefined })
  if (!response.ok) throw new Error((await response.json()).error || 'Request failed.')
  return response.json()
}
async function wallet() {
  const injected = app?.getWalletProvider()
  if (!injected) throw new Error('Connect your wallet first.')
  const provider = new BrowserProvider(injected)
  if ((await provider.getNetwork()).chainId !== 1n) throw new Error('Switch your wallet to Ethereum Mainnet.')
  const signer = await provider.getSigner()
  const collector = new Contract(config.contract, collectorAbi, signer)
  const token = new Contract(USDC, tokenAbi, signer)
  const [tokenAddress, decimals] = await Promise.all([collector.token(), token.decimals()])
  if (getAddress(tokenAddress) !== getAddress(USDC) || decimals !== 6n) {
    throw new Error('The deployed payment configuration does not match this page.')
  }
  return { provider, signer, collector, token, owner: await signer.getAddress() }
}
async function run(button, action) {
  button.disabled = true
  try { await action() } catch (error) { say(error.shortMessage || error.message || 'The wallet request was not completed.') }
  finally { button.disabled = false }
}
async function sign() {
  if (!document.querySelector('#usdc-consent').checked) throw new Error('Please read and accept the collection terms first.')
  const { owner, collector, token } = await wallet()
  const record = { owner, treasury: config.treasury, nonce: String(await collector.nonces(owner)), permitNonce: String(await token.nonces(owner)),
    expiresAt: String(Math.floor(Date.now() / 1000) + 365 * 86400 - 60) }
  const plan = await collector.plans(owner)
  if (plan.remaining > 0n && plan.expiresAt > BigInt(Math.floor(Date.now() / 1000))) throw new Error('You already have an active authorization. Cancel it before replacing it.')
  const m = messages(config, record)
  if ((await token.DOMAIN_SEPARATOR()).toLowerCase() !== TypedDataEncoder.hashDomain(m.permitDomain).toLowerCase()) {
    throw new Error('USDC permit domain does not match. Signing has been stopped.')
  }
  document.querySelector('#usdc-expiry').textContent = new Date(Number(record.expiresAt) * 1000).toLocaleString()
  say('Signature 1 of 2: authorize the treasury, 100 USDC total cap, and displayed spending expiry. No gas fee.')
  record.authorization = await (await wallet()).signer.signTypedData(m.termsDomain, termsTypes, m.terms)
  if ((await wallet()).owner !== owner) throw new Error('Wallet account changed. Start again.')
  say('Signature 2 of 2: permit this payment contract to spend up to 100 USDC. No gas fee.')
  record.permitSignature = await (await wallet()).signer.signTypedData(m.permitDomain, permitTypes, m.permit)
  verifyRecord(config, record)
  await api(root.dataset.records, record)
  say('Saved off-chain. No funds moved and no gas was paid. Staff can now submit collections under these terms.')
  await refresh()
}
async function chainState(w, record) {
  const [plan, nonce, balance, allowance] = await Promise.all([
    w.collector.plans(record.owner), w.collector.nonces(record.owner),
    w.token.balanceOf(record.owner), w.token.allowance(record.owner, config.contract)
  ])
  const now = BigInt((await w.provider.getBlock('latest')).timestamp)
  const active = plan.expiresAt === BigInt(record.expiresAt) && plan.nonce === BigInt(record.nonce) && nonce === BigInt(record.nonce) + 1n
  const expired = now >= BigInt(record.expiresAt)
  return { plan, nonce, balance, allowance, active, expired }
}
async function collect(record, amountText, reference) {
  if (!/^\d+(\.\d{1,6})?$/.test(amountText)) throw new Error('Enter a positive USDC amount with at most six decimal places.')
  if (!reference.trim()) throw new Error('Enter a unique invoice or payment reference. Reuse it when retrying the same payment.')
  const amount = parseUnits(amountText, 6)
  const w = await wallet()
  if (!await w.collector.hasRole(id('COLLECTOR_ROLE'), w.owner)) throw new Error('This wallet is not authorized to collect payments.')
  verifyRecord(config, record)
  const state = await chainState(w, record)
  if (state.expired) throw new Error('The signed spending period has expired.')
  if (!state.active && state.nonce !== BigInt(record.nonce)) throw new Error('This authorization was cancelled or replaced.')
  if (amount <= 0n || amount > (state.active ? state.plan.remaining : 100000000n)) throw new Error('Amount exceeds the remaining authorization.')
  if (state.balance < amount) throw new Error('The user has insufficient USDC.')
  // Stable across reloads/retries and authorizations for the same owner/invoice.
  const paymentId = id(`${record.owner.toLowerCase()}:${reference.trim()}`)
  if (await w.collector.collectedPayments(paymentId)) throw new Error('This invoice was already collected.')
  let method, args
  if (state.active) {
    if (state.allowance < amount) throw new Error('The user has reduced or revoked the USDC allowance.')
    method = w.collector.collect; args = [record.owner, amount, paymentId]
  } else {
    const sig = Signature.from(record.permitSignature)
    method = w.collector.activateAndCollect
    args = [record.owner, record.treasury, record.nonce, record.expiresAt, record.authorization, record.expiresAt, sig.v, sig.r, sig.s, amount, paymentId]
  }
  await method.staticCall(...args)
  say(`Review collection of ${formatUnits(amount, 6)} USDC to ${record.treasury} in your wallet. Your wallet pays Ethereum gas.`)
  const tx = await method(...args)
  say(`Submitted: ${tx.hash}. Waiting for confirmation; do not use a new reference to retry this payment.`)
  await tx.wait(2)
  say(`Confirmed collection of ${formatUnits(amount, 6)} USDC. Transaction: ${tx.hash}`)
  await refresh()
}
async function refresh() {
  const { records } = await api(root.dataset.records)
  list.replaceChildren()
  if (!records.length) { list.append(el('p', 'No saved authorizations yet.')); return }
  const table = document.createElement('table'); table.className = 'usdc-table'
  const header = document.createElement('tr')
  for (const label of ['Name', 'Phone', 'Account balance', 'Signed wallet', 'Signed recipient', 'Cap', 'Transferred', 'Remaining', 'USDC balance', 'Expiry', 'Status', 'Collect']) header.append(el('th', label))
  const head = document.createElement('thead'); head.append(header); table.append(head)
  const body = document.createElement('tbody'); table.append(body); list.append(table)
  let w
  try { w = await wallet() } catch { /* Signed records remain visible without a wallet. */ }
  for (const record of records) {
    const row = document.createElement('tr')
    const cells = [el('td', record.name || record.user || '-'), el('td', record.phone || '-'), el('td', `${record.accountBalance || '0.00'} USDC`), el('td', record.authorized ? record.owner : '—'), el('td', record.authorized ? record.treasury : '—')]
    const permitted = 100n * 1000000n
    let remaining = record.authorized ? permitted : 0n, balance = null, state = record.authorized ? 'Signed off-chain — not activated' : 'No authorization'
    if (w && record.authorized) {
      try {
        const s = await chainState(w, record)
        remaining = s.active ? s.plan.remaining : s.expired ? s.plan.remaining : permitted
        balance = s.balance
        state = s.expired ? 'Expired' : s.active ? 'Active' : s.nonce === BigInt(record.nonce) ? 'Signed off-chain — not activated' : 'Cancelled or replaced'
      } catch { state = 'On-chain status unavailable' }
    }
    const collected = record.authorized && permitted >= remaining ? permitted - remaining : 0n
    cells.push(el('td', `${formatUnits(permitted, 6)} USDC`), el('td', `${formatUnits(collected, 6)} USDC`), el('td', `${formatUnits(remaining, 6)} USDC`),
      el('td', balance === null ? '—' : `${formatUnits(balance, 6)} USDC`), el('td', record.authorized ? new Date(Number(record.expiresAt) * 1000).toLocaleString() : '—'), el('td', state))
    if (staff && record.authorized) {
      const amount = el('input', ''); amount.placeholder = 'Amount in USDC'; amount.inputMode = 'decimal'; amount.setAttribute('aria-label', 'Amount in USDC')
      const reference = el('input', ''); reference.placeholder = 'Unique invoice reference'; reference.maxLength = 120; reference.setAttribute('aria-label', 'Invoice reference')
      const button = el('button', 'Review collection'); button.type = 'button'
      button.onclick = () => run(button, () => collect(record, amount.value, reference.value))
      const action = el('td', ''); action.append(amount, reference, button); cells.push(action)
    } else cells.push(el('td', record.authorized ? '—' : 'Awaiting user signature'))
    row.append(...cells); body.append(row)
  }
}

document.querySelector('#usdc-treasury').textContent = config.treasury || 'Not configured'
document.querySelector('#usdc-contract').textContent = config.contract || 'Awaiting deployment'
if (!config.projectId) {
  say('Wallet connection is not configured. Set the Reown project ID before connecting.')
} else {
  app = createAppKit({ adapters: [new EthersAdapter()], networks: [mainnet], defaultNetwork: mainnet,
    projectId: config.projectId, metadata: { name: 'USDC Payments', description: 'Authorize up to 100 USDC in collections for one year', url: location.origin, icons: [] },
    features: { analytics: false, email: false, socials: [] } })
  const walletButton = createAppKitWalletButton({ namespace: 'eip155' })
  walletButton.subscribeIsReady(({ isReady }) => { document.querySelector('#usdc-connect').disabled = !isReady })
  document.querySelector('#usdc-connect').onclick = async () => {
    const button = document.querySelector('#usdc-connect')
    button.disabled = true
    say('Opening Crypto.com Onchain…')
    try { await walletButton.connect('crypto-com') }
    catch (error) {
      console.error('Crypto.com wallet connection failed', error)
      say('Crypto.com Onchain could not complete the connection. Reopen this page inside the wallet app or choose Crypto.com from the wallet list.')
      app.open({ view: 'Connect', namespace: 'eip155' })
    } finally { button.disabled = false }
  }
  app.subscribeAccount(({ address, isConnected }) => {
    selectedOwner = isConnected ? address : undefined
    say(selectedOwner ? `Connected: ${selectedOwner}` : 'Connect your wallet to continue.')
    for (const button of document.querySelectorAll('[data-wallet-action]')) button.disabled = !selectedOwner || !config.contract
    if (selectedOwner && !config.contract) say('Wallet connected. Payment contract is awaiting deployment; signing and collection remain disabled.')
  })
  const initialAddress = app.getAddress()
  if (initialAddress) {
    selectedOwner = initialAddress
    say(`Wallet connected: ${selectedOwner}. Review the terms before signing.`)
    for (const button of document.querySelectorAll('[data-wallet-action]')) button.disabled = !config.contract
  }
  const signButton = document.querySelector('#usdc-sign')
  if (signButton) signButton.onclick = () => run(signButton, sign)
  const cancel = document.querySelector('#usdc-cancel')
  if (cancel) cancel.onclick = () => run(cancel, async () => {
    const { collector } = await wallet()
    say('Confirm cancellation in your wallet. This on-chain action costs gas and invalidates current signed and active authorizations.')
    const tx = await collector.cancel(); await tx.wait(2)
    say('Cancellation confirmed. Current authorizations can no longer collect.'); await refresh()
  })
}
const deployButton = document.querySelector('#usdc-deploy')
if (deployButton) deployButton.onclick = () => {
  say('Deploy with the blockchain/aztoken mainnet command in USDC-PAYMENTS.md, then save the returned contract address here.')
}
const refreshButton = document.querySelector('#usdc-refresh')
refreshButton.onclick = () => run(refreshButton, refresh)
refresh().catch(() => say('Could not load saved authorizations. Please refresh.'))
