import assert from 'node:assert/strict'
import test from 'node:test'

import {
  EXPECTED_DEPLOYER,
  INITIAL_ADMIN,
  INITIAL_MINTER,
  INITIAL_RECIPIENT,
  MAX_SUPPLY,
  SEPOLIA_CHAIN_ID,
  assertDeploymentPreflight,
  contractUrl,
  transactionUrl,
} from './aztoken-deployer-config.mjs'

test('uses three valid, separated Sepolia role addresses', () => {
  assert.equal(INITIAL_RECIPIENT, EXPECTED_DEPLOYER)
  assert.notEqual(INITIAL_ADMIN, INITIAL_MINTER)
  assert.notEqual(INITIAL_ADMIN, EXPECTED_DEPLOYER)
  assert.notEqual(INITIAL_MINTER, EXPECTED_DEPLOYER)
})

test('sets the agreed 100,000,000 AZT maximum supply', () => {
  assert.equal(MAX_SUPPLY, 100_000_000n * 10n ** 18n)
})

test('allows only the expected deployer on Sepolia', () => {
  const result = assertDeploymentPreflight({
    address: EXPECTED_DEPLOYER.toLowerCase(),
    chainId: SEPOLIA_CHAIN_ID,
  })

  assert.equal(result.address, EXPECTED_DEPLOYER)
  assert.equal(result.chainId, SEPOLIA_CHAIN_ID)
})

test('blocks Ethereum Mainnet', () => {
  assert.throws(
    () => assertDeploymentPreflight({ address: EXPECTED_DEPLOYER, chainId: 1n }),
    /switch to Ethereum Sepolia/,
  )
})

test('blocks a wallet other than the selected deployer', () => {
  assert.throws(
    () =>
      assertDeploymentPreflight({
        address: INITIAL_ADMIN,
        chainId: SEPOLIA_CHAIN_ID,
      }),
    /connect the AZT Deployer wallet/,
  )
})

test('builds Sepolia explorer links', () => {
  const hash = `0x${'1'.repeat(64)}`
  assert.equal(transactionUrl(hash), `https://sepolia.etherscan.io/tx/${hash}`)
  assert.equal(
    contractUrl(EXPECTED_DEPLOYER),
    `https://sepolia.etherscan.io/address/${EXPECTED_DEPLOYER}`,
  )
})
