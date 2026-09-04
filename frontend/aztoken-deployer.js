import { createAppKit } from '@reown/appkit'
import { EthersAdapter } from '@reown/appkit-adapter-ethers'
import { sepolia } from '@reown/appkit/networks'
import { createAppKitWalletButton } from '@reown/appkit-wallet-button'
import {
  BrowserProvider,
  ContractFactory,
  ZeroHash,
  formatEther,
  formatUnits,
} from 'ethers'

import tokenArtifact from '../blockchain/aztoken/artifacts/contracts/AZToken.sol/AZToken.json'
import {
  EXPECTED_DEPLOYER,
  INITIAL_ADMIN,
  INITIAL_MINTER,
  INITIAL_RECIPIENT,
  INITIAL_SUPPLY,
  MAX_SUPPLY,
  assertDeploymentPreflight,
  contractUrl,
  transactionUrl,
} from './aztoken-deployer-config.mjs'

const DEFAULT_REOWN_PROJECT_ID = '0e9d36ba9775ba621552d60db6a74525'
const projectId = import.meta.env.VITE_REOWN_PROJECT_ID || DEFAULT_REOWN_PROJECT_ID
const status = document.querySelector('#deploymentStatus')
const connectButton = document.querySelector('#connectDeployer')
const deployButton = document.querySelector('#deployAZToken')
const preflightDetails = document.querySelector('#preflightDetails')
const deploymentResult = document.querySelector('#deploymentResult')

let activeProvider = null
let activeSigner = null
let deploymentStarted = false

function setStatus(message, state = 'idle') {
  status.textContent = message
  status.dataset.state = state
}

function shortAddress(address) {
  return `${address.slice(0, 8)}?${address.slice(-6)}`
}

function explainError(error) {
  if (error?.code === 4001 || error?.code === 'ACTION_REJECTED') {
    return 'The wallet request was rejected. No deployment occurred.'
  }
  return error?.shortMessage || error?.reason || error?.message || 'Unknown deployment error.'
}

const appKit = createAppKit({
  adapters: [new EthersAdapter()],
  networks: [sepolia],
  defaultNetwork: sepolia,
  projectId,
  metadata: {
    name: 'AZToken Sepolia Deployer',
    description: 'Deploy the reviewed Phase 1 AZToken contract to Ethereum Sepolia.',
    url: window.location.origin,
    icons: ['https://lazarevagency.com/static/favicon.ico']
  },
  features: {
    analytics: false,
    email: false,
    socials: []
  }
})

const cryptoWalletButton = createAppKitWalletButton({ namespace: 'eip155' })

async function runPreflight() {
  const walletProvider = appKit.getWalletProvider()
  if (!walletProvider) {
    throw new Error('The wallet provider is not ready. Reconnect the deployer wallet.')
  }

  activeProvider = new BrowserProvider(walletProvider, 'any')
  activeSigner = await activeProvider.getSigner()
  const address = await activeSigner.getAddress()
  const network = await activeProvider.getNetwork()
  assertDeploymentPreflight({ address, chainId: network.chainId })

  const balance = await activeProvider.getBalance(address)
  if (balance === 0n) {
    throw new Error('The deployer has no Sepolia ETH for deployment gas.')
  }

  const factory = new ContractFactory(tokenArtifact.abi, tokenArtifact.bytecode, activeSigner)
  const unsignedDeployment = await factory.getDeployTransaction(
    INITIAL_ADMIN,
    INITIAL_MINTER,
    INITIAL_RECIPIENT,
  )
  const estimatedGas = await activeProvider.estimateGas({
    ...unsignedDeployment,
    from: address,
  })
  const feeData = await activeProvider.getFeeData()
  const gasPrice = feeData.maxFeePerGas || feeData.gasPrice || 0n
  const estimatedMaximumFee = estimatedGas * gasPrice

  preflightDetails.hidden = false
  preflightDetails.innerHTML = `
    <strong>Preflight passed</strong><br>
    Wallet: ${shortAddress(address)}<br>
    Network: Ethereum Sepolia (${network.chainId})<br>
    Balance: ${formatEther(balance)} Sepolia ETH<br>
    Estimated gas limit: ${estimatedGas.toLocaleString()}<br>
    Estimated maximum network fee: ${formatEther(estimatedMaximumFee)} Sepolia ETH
  `
  setStatus('Preflight passed. Review the configuration, then approve deployment in your wallet.', 'success')
  deployButton.disabled = false
}

cryptoWalletButton.subscribeIsReady(({ isReady }) => {
  connectButton.disabled = !isReady
})

async function handleConnectedWallet(address, isConnected) {
  if (!isConnected || !address || deploymentStarted) return

  connectButton.disabled = true
  deployButton.disabled = true
  setStatus('Checking wallet, Sepolia network, balance, and deployment gas...', 'working')

  try {
    await appKit.switchNetwork(sepolia, { throwOnFailure: true })
    await runPreflight()
  } catch (error) {
    console.error('AZToken deployment preflight failed', error)
    setStatus(explainError(error), 'error')
    connectButton.disabled = false
  }
}

appKit.subscribeAccount(({ address, isConnected }) => {
  void handleConnectedWallet(address, isConnected)
})

// Reown may restore an already-approved WalletConnect session while the page
// is loading without emitting a new account event. Poll only briefly during
// startup so a refresh resumes safely without another QR scan.
for (const delay of [500, 1500, 3000]) {
  window.setTimeout(() => {
    const account = appKit.getAccount('eip155')
    void handleConnectedWallet(account?.address, account?.isConnected)
  }, delay)
}

connectButton.addEventListener('click', async () => {
  connectButton.disabled = true
  setStatus('Opening Crypto.com Onchain. Connect the AZT Deployer wallet on Sepolia.', 'working')

  try {
    await cryptoWalletButton.connect('crypto-com')
    // Wallet-button connections can complete before AppKit's account subscription is
    // delivered to this page. Run the preflight directly as well, so a successful
    // phone approval never leaves the page waiting for an event that already fired.
    await appKit.close()
    await runPreflight()
  } catch (error) {
    console.error('Crypto.com Onchain connection failed', error)
    const account = appKit.getAccount('eip155')

    if (account?.isConnected && account.address) {
      try {
        await appKit.close()
        await runPreflight()
        return
      } catch (preflightError) {
        console.error('AZToken deployment preflight retry failed', preflightError)
        setStatus(explainError(preflightError), 'error')
      }
    } else {
      setStatus('Choose Crypto.com Onchain from the wallet list.', 'error')
      appKit.open({ view: 'Connect', namespace: 'eip155' })
    }

    connectButton.disabled = false
  }
})

deployButton.addEventListener('click', async () => {
  if (deploymentStarted) return

  deploymentStarted = true
  deployButton.disabled = true
  connectButton.disabled = true
  deploymentResult.hidden = true
  setStatus('Confirm the contract deployment in Crypto.com Onchain. Do not approve if it says Mainnet.', 'working')

  try {
    await runPreflight()
    deployButton.disabled = true

    const factory = new ContractFactory(tokenArtifact.abi, tokenArtifact.bytecode, activeSigner)
    const token = await factory.deploy(INITIAL_ADMIN, INITIAL_MINTER, INITIAL_RECIPIENT)
    const deploymentTransaction = token.deploymentTransaction()

    setStatus('Deployment submitted. Waiting for Sepolia confirmation?', 'working')
    deploymentResult.hidden = false
    deploymentResult.innerHTML = `
      Transaction submitted:<br>
      <a href="${transactionUrl(deploymentTransaction.hash)}" target="_blank" rel="noreferrer">
        ${deploymentTransaction.hash}
      </a>
    `

    await token.waitForDeployment()
    const contractAddress = await token.getAddress()
    const [name, symbol, totalSupply, cap, adminRole, minterRole] = await Promise.all([
      token.name(),
      token.symbol(),
      token.totalSupply(),
      token.cap(),
      token.hasRole(ZeroHash, INITIAL_ADMIN),
      token.hasRole(await token.MINTER_ROLE(), INITIAL_MINTER),
    ])

    if (
      name !== 'AZToken' ||
      symbol !== 'AZT' ||
      totalSupply !== INITIAL_SUPPLY ||
      cap !== MAX_SUPPLY ||
      !adminRole ||
      !minterRole
    ) {
      throw new Error('Deployment confirmed, but post-deployment validation did not match the reviewed configuration.')
    }

    setStatus('AZToken was deployed and its on-chain configuration passed validation.', 'success')
    deploymentResult.innerHTML = `
      <strong>Deployment complete</strong><br>
      Contract: <a href="${contractUrl(contractAddress)}" target="_blank" rel="noreferrer">${contractAddress}</a><br>
      Initial supply: ${formatUnits(totalSupply, 18)} AZT<br>
      Maximum supply: ${formatUnits(cap, 18)} AZT<br>
      Transaction: <a href="${transactionUrl(deploymentTransaction.hash)}" target="_blank" rel="noreferrer">view on Sepolia Etherscan</a>
    `
  } catch (error) {
    console.error('AZToken deployment failed', error)
    setStatus(explainError(error), 'error')
    deploymentStarted = false
    connectButton.disabled = false
  }
})
