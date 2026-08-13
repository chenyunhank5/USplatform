const { expect } = require("chai");
const {
  HARDHAT_CHAIN_ID,
  SEPOLIA_CHAIN_ID,
  assertSeparateAdminAndMinter,
  assertTestnetChain,
  requireDeploymentAddress,
} = require("../scripts/deployment-safety");

describe("Phase 1 deployment safety", function () {
  const admin = "0x0000000000000000000000000000000000000001";
  const minter = "0x0000000000000000000000000000000000000002";

  it("allows the isolated Hardhat development chain", function () {
    expect(() => assertTestnetChain(HARDHAT_CHAIN_ID)).not.to.throw();
  });

  it("allows Ethereum Sepolia", function () {
    expect(() => assertTestnetChain(SEPOLIA_CHAIN_ID)).not.to.throw();
  });

  it("blocks Ethereum mainnet", function () {
    expect(() => assertTestnetChain(1n)).to.throw("Deployment blocked: chain 1");
  });

  it("blocks every other unapproved chain", function () {
    expect(() => assertTestnetChain(8453n)).to.throw("Deployment blocked: chain 8453");
  });

  it("requires a valid non-zero deployment address", function () {
    expect(requireDeploymentAddress(admin, "ADMIN_ADDRESS")).to.equal(admin);
    expect(() => requireDeploymentAddress(undefined, "ADMIN_ADDRESS")).to.throw(
      "ADMIN_ADDRESS must be a valid non-zero address",
    );
    expect(() =>
      requireDeploymentAddress("0x0000000000000000000000000000000000000000", "ADMIN_ADDRESS"),
    ).to.throw("ADMIN_ADDRESS must be a valid non-zero address");
    expect(() => requireDeploymentAddress("not-an-address", "ADMIN_ADDRESS")).to.throw(
      "ADMIN_ADDRESS must be a valid non-zero address",
    );
  });

  it("requires separate admin and minter addresses", function () {
    expect(() => assertSeparateAdminAndMinter(admin, minter)).not.to.throw();
    expect(() => assertSeparateAdminAndMinter(admin, admin)).to.throw(
      "ADMIN_ADDRESS and MINTER_ADDRESS must be different",
    );
  });
});
