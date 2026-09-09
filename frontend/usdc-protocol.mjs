import { TypedDataEncoder, verifyTypedData, getAddress } from 'ethers'

export const CAP = '100000000'
export const USDC = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
export const permitTypes = { Permit: [
  { name: 'owner', type: 'address' }, { name: 'spender', type: 'address' },
  { name: 'value', type: 'uint256' }, { name: 'nonce', type: 'uint256' },
  { name: 'deadline', type: 'uint256' }
] }
export const termsTypes = { Authorization: [
  { name: 'owner', type: 'address' }, { name: 'treasury', type: 'address' },
  { name: 'cap', type: 'uint256' }, { name: 'nonce', type: 'uint256' },
  { name: 'expiresAt', type: 'uint256' }
] }
export function messages(config, record) {
  return {
    permitDomain: { name: 'USD Coin', version: '2', chainId: 1, verifyingContract: USDC },
    termsDomain: { name: 'USDC Collections', version: '1', chainId: 1, verifyingContract: config.contract },
    permit: { owner: record.owner, spender: config.contract, value: CAP, nonce: record.permitNonce, deadline: record.expiresAt },
    terms: { owner: record.owner, treasury: record.treasury, cap: CAP, nonce: record.nonce, expiresAt: record.expiresAt }
  }
}
export function verifyRecord(config, record) {
  const m = messages(config, record)
  const owner = getAddress(record.owner)
  if (verifyTypedData(m.permitDomain, permitTypes, m.permit, record.permitSignature) !== owner ||
      verifyTypedData(m.termsDomain, termsTypes, m.terms, record.authorization) !== owner) {
    throw new Error('Signatures do not match the authorization owner.')
  }
  return TypedDataEncoder.hash(m.termsDomain, termsTypes, m.terms)
}
export const collectorAbi = [
  'function token() view returns(address)',
  'function nonces(address) view returns(uint256)',
  'function plans(address) view returns(uint256 remaining,uint256 expiresAt,uint256 nonce,address treasury)',
  'function hasRole(bytes32,address) view returns(bool)',
  'function collectedPayments(bytes32) view returns(bool)',
  'function activateAndCollect(address,address,uint256,uint256,bytes,uint256,uint8,bytes32,bytes32,uint256,bytes32)',
  'function collect(address,uint256,bytes32)', 'function cancel()',
  'event Collected(address indexed owner,bytes32 indexed paymentId,uint256 amount,uint256 remaining)'
]
export const tokenAbi = [
  'function nonces(address) view returns(uint256)', 'function DOMAIN_SEPARATOR() view returns(bytes32)',
  'function decimals() view returns(uint8)', 'function balanceOf(address) view returns(uint256)',
  'function allowance(address,address) view returns(uint256)'
]
