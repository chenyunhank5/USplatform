const { getAddress, isAddress, ZeroAddress } = require("ethers");

const HARDHAT_CHAIN_ID = 31337n;
const SEPOLIA_CHAIN_ID = 11155111n;

function assertTestnetChain(chainId) {
  const normalizedChainId = BigInt(chainId);

  if (normalizedChainId !== HARDHAT_CHAIN_ID && normalizedChainId !== SEPOLIA_CHAIN_ID) {
    throw new Error(
      `Deployment blocked: chain ${normalizedChainId} is not Hardhat (31337) or Sepolia (11155111).`,
    );
  }
}

function requireDeploymentAddress(value, variableName) {
  if (!value || !isAddress(value) || getAddress(value) === ZeroAddress) {
    throw new Error(`${variableName} must be a valid non-zero address.`);
  }

  return getAddress(value);
}

function assertSeparateAdminAndMinter(adminAddress, minterAddress) {
  if (getAddress(adminAddress) === getAddress(minterAddress)) {
    throw new Error("ADMIN_ADDRESS and MINTER_ADDRESS must be different addresses.");
  }
}

module.exports = {
  HARDHAT_CHAIN_ID,
  SEPOLIA_CHAIN_ID,
  assertSeparateAdminAndMinter,
  assertTestnetChain,
  requireDeploymentAddress,
};
