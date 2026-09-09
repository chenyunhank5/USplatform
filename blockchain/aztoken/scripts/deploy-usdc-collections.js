const hre = require('hardhat');

const USDC_MAINNET = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';

function requiredAddress(name) {
  const value = process.env[name];
  if (!value || !hre.ethers.isAddress(value) || value === hre.ethers.ZeroAddress) throw new Error(`${name} must be a valid non-zero address.`);
  return hre.ethers.getAddress(value);
}

async function main() {
  const network = await hre.ethers.provider.getNetwork();
  if (network.chainId !== 1n) throw new Error(`Refusing deployment: expected Ethereum Mainnet (1), got ${network.chainId}.`);
  const [deployer] = await hre.ethers.getSigners();
  const admin = requiredAddress('USDC_ADMIN_ADDRESS');
  const collector = requiredAddress('USDC_COLLECTOR_ADDRESS');
  console.log(`Deploying USDCCollections from ${deployer.address}`);
  console.log(`USDC: ${USDC_MAINNET}`);
  console.log(`Admin: ${admin}`);
  console.log(`Collector: ${collector}`);
  const contract = await hre.ethers.deployContract('USDCCollections', [USDC_MAINNET, admin, collector]);
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log(`USDCCollections deployed at ${address}`);
  console.log(`Verify with: npx hardhat verify --network mainnet ${address} ${USDC_MAINNET} ${admin} ${collector}`);
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
