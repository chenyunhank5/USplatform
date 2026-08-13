const hre = require("hardhat");
const {
  HARDHAT_CHAIN_ID,
  assertSeparateAdminAndMinter,
  assertTestnetChain,
  requireDeploymentAddress,
} = require("./deployment-safety");

async function deploymentAddresses(chainId) {
  if (chainId === HARDHAT_CHAIN_ID) {
    const [deployer, localAdmin, localMinter, localRecipient] = await hre.ethers.getSigners();

    return {
      deployer: deployer.address,
      admin: localAdmin.address,
      minter: localMinter.address,
      recipient: localRecipient.address,
    };
  }

  const [deployer] = await hre.ethers.getSigners();

  return {
    deployer: deployer.address,
    admin: requireDeploymentAddress(process.env.ADMIN_ADDRESS, "ADMIN_ADDRESS"),
    minter: requireDeploymentAddress(process.env.MINTER_ADDRESS, "MINTER_ADDRESS"),
    recipient: requireDeploymentAddress(
      process.env.INITIAL_RECIPIENT_ADDRESS,
      "INITIAL_RECIPIENT_ADDRESS",
    ),
  };
}

async function main() {
  const network = await hre.ethers.provider.getNetwork();
  const chainId = network.chainId;

  assertTestnetChain(chainId);

  const addresses = await deploymentAddresses(chainId);
  assertSeparateAdminAndMinter(addresses.admin, addresses.minter);

  console.log(`Deploying AZToken on chain ${chainId} from ${addresses.deployer}`);
  console.log(`Initial admin: ${addresses.admin}`);
  console.log(`Initial minter: ${addresses.minter}`);
  console.log(`Initial supply recipient: ${addresses.recipient}`);

  const token = await hre.ethers.deployContract("AZToken", [
    addresses.admin,
    addresses.minter,
    addresses.recipient,
  ]);
  await token.waitForDeployment();

  console.log(`AZToken deployed at ${await token.getAddress()}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
