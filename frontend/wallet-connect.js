import { createAppKit } from '@reown/appkit'
import { EthersAdapter } from '@reown/appkit-adapter-ethers'
import { mainnet } from '@reown/appkit/networks'
import { createAppKitWalletButton } from '@reown/appkit-wallet-button'

const root = document.querySelector('[data-wallet-connect]')
const connectButton = document.querySelector('#connectCryptoWallet')
const addressInput = document.querySelector('#walletAddress')
const status = document.querySelector('#walletConnectionStatus')

function setStatus(message, state = '') {
  if (!status) return
  status.textContent = message
  status.dataset.state = state
}

if (root && connectButton && addressInput && status) {
  const projectId = root.dataset.projectId

  if (!projectId) {
    setStatus('Wallet connection is not configured. Please contact support.', 'error')
  } else {
    const appKit = createAppKit({
      adapters: [new EthersAdapter()],
      networks: [mainnet],
      defaultNetwork: mainnet,
      projectId,
      metadata: {
        name: 'AZ Marketing Hub',
        description: 'Connect a wallet to save its public address.',
        url: 'https://azmarketinghub.com',
        icons: ['https://azmarketinghub.com/static/favicon.ico']
      },
      features: {
        analytics: false,
        email: false,
        socials: []
      }
    })

    const cryptoWalletButton = createAppKitWalletButton({ namespace: 'eip155' })

    cryptoWalletButton.subscribeIsReady(({ isReady }) => {
      connectButton.disabled = !isReady
      if (isReady && !appKit.getAddress()) {
        setStatus('Tap Verify to open Crypto.com Onchain and approve the connection.')
      }
    })

    appKit.subscribeAccount(({ address, isConnected }) => {
      if (isConnected && address) {
        addressInput.value = address
        setStatus('Crypto.com Onchain connected. Your public address is ready to save.', 'success')
      }
    })

    connectButton.addEventListener('click', async () => {
      connectButton.disabled = true
      setStatus('Opening Crypto.com Onchain…')

      try {
        await cryptoWalletButton.connect('crypto-com')
      } catch (error) {
        console.error('Crypto.com wallet connection failed', error)
        setStatus('Could not open Crypto.com Onchain. Choose it from the wallet list.', 'error')
        appKit.open({ view: 'Connect', namespace: 'eip155' })
      } finally {
        connectButton.disabled = false
      }
    })
  }
}
