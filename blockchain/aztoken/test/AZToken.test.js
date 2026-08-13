const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AZToken", function () {
  const INITIAL_SUPPLY = ethers.parseEther("10000000");
  const MAX_SUPPLY = ethers.parseEther("100000000");
  const REMAINING_MINTABLE = MAX_SUPPLY - INITIAL_SUPPLY;

  async function deployFixture() {
    const [deployer, admin, minter, recipient, alice, bob, replacementMinter] =
      await ethers.getSigners();
    const token = await ethers.deployContract("AZToken", [
      admin.address,
      minter.address,
      recipient.address,
    ]);
    await token.waitForDeployment();

    return { token, deployer, admin, minter, recipient, alice, bob, replacementMinter };
  }

  describe("deployment", function () {
    it("sets the agreed token metadata and constants", async function () {
      const { token } = await deployFixture();

      expect(await token.name()).to.equal("AZToken");
      expect(await token.symbol()).to.equal("AZT");
      expect(await token.decimals()).to.equal(18n);
      expect(await token.INITIAL_SUPPLY()).to.equal(INITIAL_SUPPLY);
      expect(await token.MAX_SUPPLY()).to.equal(MAX_SUPPLY);
      expect(await token.cap()).to.equal(MAX_SUPPLY);
    });

    it("mints the full initial supply only to the initial recipient", async function () {
      const { token, deployer, recipient } = await deployFixture();

      expect(await token.totalSupply()).to.equal(INITIAL_SUPPLY);
      expect(await token.balanceOf(recipient.address)).to.equal(INITIAL_SUPPLY);
      expect(await token.balanceOf(deployer.address)).to.equal(0n);
    });

    it("separates the admin and minter roles", async function () {
      const { token, admin, minter } = await deployFixture();
      const defaultAdminRole = await token.DEFAULT_ADMIN_ROLE();
      const minterRole = await token.MINTER_ROLE();

      expect(await token.hasRole(defaultAdminRole, admin.address)).to.equal(true);
      expect(await token.hasRole(minterRole, admin.address)).to.equal(false);
      expect(await token.hasRole(defaultAdminRole, minter.address)).to.equal(false);
      expect(await token.hasRole(minterRole, minter.address)).to.equal(true);
    });

    for (const [label, position] of [
      ["admin", 0],
      ["minter", 1],
      ["recipient", 2],
    ]) {
      it(`rejects a zero ${label} address`, async function () {
        const [, admin, minter, recipient] = await ethers.getSigners();
        const addresses = [admin.address, minter.address, recipient.address];
        addresses[position] = ethers.ZeroAddress;
        const factory = await ethers.getContractFactory("AZToken");

        await expect(factory.deploy(...addresses)).to.be.revertedWithCustomError(
          factory,
          "ZeroAddress",
        );
      });
    }

    it("rejects the same address for admin and minter", async function () {
      const [, admin, , recipient] = await ethers.getSigners();
      const factory = await ethers.getContractFactory("AZToken");

      await expect(
        factory.deploy(admin.address, admin.address, recipient.address),
      ).to.be.revertedWithCustomError(factory, "AdminAndMinterMustDiffer");
    });

    it("advertises ERC-165 and AccessControl interface support", async function () {
      const { token } = await deployFixture();

      expect(await token.supportsInterface("0x01ffc9a7")).to.equal(true);
      expect(await token.supportsInterface("0x7965db0b")).to.equal(true);
      expect(await token.supportsInterface("0xffffffff")).to.equal(false);
    });
  });

  describe("restricted minting", function () {
    it("allows the minter to mint and emits a standard Transfer event", async function () {
      const { token, minter, alice } = await deployFixture();
      const amount = ethers.parseEther("125");

      await expect(token.connect(minter).mint(alice.address, amount))
        .to.emit(token, "Transfer")
        .withArgs(ethers.ZeroAddress, alice.address, amount);

      expect(await token.balanceOf(alice.address)).to.equal(amount);
      expect(await token.totalSupply()).to.equal(INITIAL_SUPPLY + amount);
    });

    it("rejects minting by an account without MINTER_ROLE", async function () {
      const { token, alice } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();

      await expect(token.connect(alice).mint(alice.address, 1n))
        .to.be.revertedWithCustomError(token, "AccessControlUnauthorizedAccount")
        .withArgs(alice.address, minterRole);
    });

    it("rejects minting to the zero address", async function () {
      const { token, minter } = await deployFixture();

      await expect(token.connect(minter).mint(ethers.ZeroAddress, 1n))
        .to.be.revertedWithCustomError(token, "ERC20InvalidReceiver")
        .withArgs(ethers.ZeroAddress);
    });

    it("allows minting exactly to the maximum supply", async function () {
      const { token, minter, alice } = await deployFixture();

      await token.connect(minter).mint(alice.address, REMAINING_MINTABLE);

      expect(await token.totalSupply()).to.equal(MAX_SUPPLY);
      expect(await token.balanceOf(alice.address)).to.equal(REMAINING_MINTABLE);
    });

    it("rejects minting even one base unit above the cap", async function () {
      const { token, minter, alice } = await deployFixture();
      const attemptedSupply = MAX_SUPPLY + 1n;

      await expect(token.connect(minter).mint(alice.address, REMAINING_MINTABLE + 1n))
        .to.be.revertedWithCustomError(token, "ERC20ExceededCap")
        .withArgs(attemptedSupply, MAX_SUPPLY);
    });

    it("permits minting again after holders burn below the cap", async function () {
      const { token, minter, recipient, alice } = await deployFixture();
      await token.connect(minter).mint(alice.address, REMAINING_MINTABLE);
      await token.connect(recipient).burn(ethers.parseEther("10"));

      await token.connect(minter).mint(alice.address, ethers.parseEther("10"));

      expect(await token.totalSupply()).to.equal(MAX_SUPPLY);
    });
  });

  describe("role administration", function () {
    it("allows the admin to grant MINTER_ROLE", async function () {
      const { token, admin, replacementMinter, alice } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();

      await expect(token.connect(admin).grantRole(minterRole, replacementMinter.address))
        .to.emit(token, "RoleGranted")
        .withArgs(minterRole, replacementMinter.address, admin.address);
      await token.connect(replacementMinter).mint(alice.address, 50n);

      expect(await token.balanceOf(alice.address)).to.equal(50n);
    });

    it("allows the admin to revoke MINTER_ROLE", async function () {
      const { token, admin, minter, alice } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();

      await expect(token.connect(admin).revokeRole(minterRole, minter.address))
        .to.emit(token, "RoleRevoked")
        .withArgs(minterRole, minter.address, admin.address);

      await expect(token.connect(minter).mint(alice.address, 1n))
        .to.be.revertedWithCustomError(token, "AccessControlUnauthorizedAccount")
        .withArgs(minter.address, minterRole);
    });

    it("prevents non-admin accounts from granting or revoking roles", async function () {
      const { token, alice, minter, replacementMinter } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();
      const defaultAdminRole = await token.DEFAULT_ADMIN_ROLE();

      await expect(token.connect(alice).grantRole(minterRole, replacementMinter.address))
        .to.be.revertedWithCustomError(token, "AccessControlUnauthorizedAccount")
        .withArgs(alice.address, defaultAdminRole);
      await expect(token.connect(alice).revokeRole(minterRole, minter.address))
        .to.be.revertedWithCustomError(token, "AccessControlUnauthorizedAccount")
        .withArgs(alice.address, defaultAdminRole);
    });

    it("never permits the same account to hold admin and minter roles", async function () {
      const { token, admin, minter } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();
      const defaultAdminRole = await token.DEFAULT_ADMIN_ROLE();

      await expect(token.connect(admin).grantRole(minterRole, admin.address))
        .to.be.revertedWithCustomError(token, "AdminAndMinterRolesMustBeSeparate")
        .withArgs(admin.address);
      await expect(token.connect(admin).grantRole(defaultAdminRole, minter.address))
        .to.be.revertedWithCustomError(token, "AdminAndMinterRolesMustBeSeparate")
        .withArgs(minter.address);
    });

    it("allows an account to change roles only after its old role is revoked", async function () {
      const { token, admin, minter } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();
      const defaultAdminRole = await token.DEFAULT_ADMIN_ROLE();

      await token.connect(admin).revokeRole(minterRole, minter.address);
      await token.connect(admin).grantRole(defaultAdminRole, minter.address);

      expect(await token.hasRole(defaultAdminRole, minter.address)).to.equal(true);
      expect(await token.hasRole(minterRole, minter.address)).to.equal(false);
    });

    it("allows a minter to renounce only its own role", async function () {
      const { token, minter, alice } = await deployFixture();
      const minterRole = await token.MINTER_ROLE();

      await token.connect(minter).renounceRole(minterRole, minter.address);
      expect(await token.hasRole(minterRole, minter.address)).to.equal(false);

      await expect(token.connect(alice).renounceRole(minterRole, minter.address))
        .to.be.revertedWithCustomError(token, "AccessControlBadConfirmation");
    });
  });

  describe("transfers and explicit allowances", function () {
    it("transfers only the caller's tokens", async function () {
      const { token, recipient, alice } = await deployFixture();
      const amount = ethers.parseEther("25");

      await expect(token.connect(recipient).transfer(alice.address, amount))
        .to.emit(token, "Transfer")
        .withArgs(recipient.address, alice.address, amount);

      expect(await token.balanceOf(alice.address)).to.equal(amount);
    });

    it("rejects transfers that exceed the caller's balance", async function () {
      const { token, alice, bob } = await deployFixture();

      await expect(token.connect(alice).transfer(bob.address, 1n))
        .to.be.revertedWithCustomError(token, "ERC20InsufficientBalance")
        .withArgs(alice.address, 0n, 1n);
    });

    it("rejects transfers to the zero address", async function () {
      const { token, recipient } = await deployFixture();

      await expect(token.connect(recipient).transfer(ethers.ZeroAddress, 1n))
        .to.be.revertedWithCustomError(token, "ERC20InvalidReceiver")
        .withArgs(ethers.ZeroAddress);
    });

    it("records an allowance only after the holder approves it", async function () {
      const { token, recipient, alice } = await deployFixture();
      const amount = ethers.parseEther("100");

      await expect(token.connect(recipient).approve(alice.address, amount))
        .to.emit(token, "Approval")
        .withArgs(recipient.address, alice.address, amount);

      expect(await token.allowance(recipient.address, alice.address)).to.equal(amount);
    });

    it("lets a spender use only the approved amount", async function () {
      const { token, recipient, alice, bob } = await deployFixture();
      const approved = ethers.parseEther("100");
      const spent = ethers.parseEther("40");
      await token.connect(recipient).approve(alice.address, approved);

      await token.connect(alice).transferFrom(recipient.address, bob.address, spent);

      expect(await token.balanceOf(bob.address)).to.equal(spent);
      expect(await token.allowance(recipient.address, alice.address)).to.equal(approved - spent);
    });

    it("rejects transferFrom without enough allowance", async function () {
      const { token, recipient, alice, bob } = await deployFixture();
      await token.connect(recipient).approve(alice.address, 9n);

      await expect(token.connect(alice).transferFrom(recipient.address, bob.address, 10n))
        .to.be.revertedWithCustomError(token, "ERC20InsufficientAllowance")
        .withArgs(alice.address, 9n, 10n);
    });

    it("lets a holder revoke an allowance by approving zero", async function () {
      const { token, recipient, alice, bob } = await deployFixture();
      await token.connect(recipient).approve(alice.address, 100n);
      await token.connect(recipient).approve(alice.address, 0n);

      expect(await token.allowance(recipient.address, alice.address)).to.equal(0n);
      await expect(token.connect(alice).transferFrom(recipient.address, bob.address, 1n))
        .to.be.revertedWithCustomError(token, "ERC20InsufficientAllowance")
        .withArgs(alice.address, 0n, 1n);
    });

    it("does not reduce an explicitly unlimited allowance", async function () {
      const { token, recipient, alice, bob } = await deployFixture();
      await token.connect(recipient).approve(alice.address, ethers.MaxUint256);

      await token.connect(alice).transferFrom(recipient.address, bob.address, 1n);

      expect(await token.allowance(recipient.address, alice.address)).to.equal(ethers.MaxUint256);
    });
  });

  describe("holder-controlled burning", function () {
    it("allows a holder to burn its own balance", async function () {
      const { token, recipient } = await deployFixture();
      const amount = ethers.parseEther("100");

      await expect(token.connect(recipient).burn(amount))
        .to.emit(token, "Transfer")
        .withArgs(recipient.address, ethers.ZeroAddress, amount);

      expect(await token.balanceOf(recipient.address)).to.equal(INITIAL_SUPPLY - amount);
      expect(await token.totalSupply()).to.equal(INITIAL_SUPPLY - amount);
    });

    it("rejects burning more than the holder owns", async function () {
      const { token, alice } = await deployFixture();

      await expect(token.connect(alice).burn(1n))
        .to.be.revertedWithCustomError(token, "ERC20InsufficientBalance")
        .withArgs(alice.address, 0n, 1n);
    });

    it("allows burnFrom only after an explicit allowance", async function () {
      const { token, recipient, alice } = await deployFixture();
      const amount = ethers.parseEther("25");
      await token.connect(recipient).approve(alice.address, amount);

      await token.connect(alice).burnFrom(recipient.address, amount);

      expect(await token.allowance(recipient.address, alice.address)).to.equal(0n);
      expect(await token.totalSupply()).to.equal(INITIAL_SUPPLY - amount);
    });

    it("rejects burnFrom without enough allowance", async function () {
      const { token, recipient, alice } = await deployFixture();

      await expect(token.connect(alice).burnFrom(recipient.address, 1n))
        .to.be.revertedWithCustomError(token, "ERC20InsufficientAllowance")
        .withArgs(alice.address, 0n, 1n);
    });
  });
});
