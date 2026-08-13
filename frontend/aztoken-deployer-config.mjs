import { getAddress } from 'ethers'

export const SEPOLIA_CHAIN_ID = 11155111n
export const SEPOLIA_EXPLORER_URL = 'https://sepolia.etherscan.io'
export const EXPECTED_DEPLOYER = getAddress('0xed36412d2183014fB9A355F1880DB9A4102b683a')
export const INITIAL_ADMIN = getAddress('0xb1ba83c74940A4077C85025d88e42211443bA685')
export const INITIAL_MINTER = getAddress('0x5decc0fD8EffC851A04D720e82D255cDEA9CB93C')
export const INITIAL_RECIPIENT = EXPECTED_DEPLOYER
export const INITIAL_SUPPLY = 10_000_000n * 10n ** 18n
export const MAX_SUPPLY = 100_000_000n * 10n ** 18n

export function assertDeploymentPreflight({ address, chainId }) {
  const normalizedAddress = getAddress(address)
  const normalizedChainId = BigInt(chainId)

  if (normalizedChainId !== SEPOLIA_CHAIN_ID) {
    throw new Error(
      `Deployment blocked: switch to Ethereum Sepolia (chain ${SEPOLIA_CHAIN_ID}).`,
    )
  }

  if (normalizedAddress !== EXPECTED_DEPLOYER) {
    throw new Error(`Deployment blocked: connect the AZT Deployer wallet ${EXPECTED_DEPLOYER}.`)
  }

  if (INITIAL_ADMIN === INITIAL_MINTER) {
    throw new Error('Deployment blocked: admin and minter must be different addresses.')
  }

  return {
    address: normalizedAddress,
    chainId: normalizedChainId,
  }
}

export function transactionUrl(transactionHash) {
  return `${SEPOLIA_EXPLORER_URL}/tx/${transactionHash}`
}

export function contractUrl(contractAddress) {
  return `${SEPOLIA_EXPLORER_URL}/address/${getAddress(contractAddress)}`
}
