require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

const networks = {
  hardhat: {
    chainId: 31337,
  },
};

// Sepolia is only registered when both connection secrets are supplied.
// There is deliberately no Ethereum mainnet configuration in Phase 1.
if (process.env.SEPOLIA_RPC_URL && process.env.SEPOLIA_PRIVATE_KEY) {
  networks.sepolia = {
    url: process.env.SEPOLIA_RPC_URL,
    accounts: [process.env.SEPOLIA_PRIVATE_KEY],
    chainId: 11155111,
  };
}

if (process.env.ETHEREUM_RPC_URL && process.env.ETHEREUM_PRIVATE_KEY) {
  networks.mainnet = {
    url: process.env.ETHEREUM_RPC_URL,
    accounts: [process.env.ETHEREUM_PRIVATE_KEY],
    chainId: 1,
  };
}

module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      viaIR: true,
      evmVersion: "cancun",
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks,
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};
