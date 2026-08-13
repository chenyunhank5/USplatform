# AZToken — Phase 1

This isolated package contains the testnet-only Phase 1 implementation of AZToken. It does not contain an exchange, USDC integration, staff trading, a Reown transaction flow, or any real-fund functionality.

## Agreed token configuration

| Property | Value |
|---|---|
| Name | AZToken |
| Symbol | AZT |
| Decimals | 18 |
| Initial supply | 10,000,000 AZT |
| Maximum outstanding supply | 100,000,000 AZT |
| Minting | Restricted to `MINTER_ROLE` |
| Burning | Holders may burn their tokens; approved spenders may use `burnFrom` |
| Upgradeability | None |
| Allowed deployment networks | Hardhat local chain and Ethereum Sepolia only |

The initial admin, initial minter, and initial supply recipient are constructor arguments. The admin and minter must be different, and all three addresses must be non-zero.

## Selected Sepolia accounts

| Purpose | Public address |
|---|---|
| Deployer and initial recipient | `0xed36412d2183014fB9A355F1880DB9A4102b683a` |
| Admin | `0xb1ba83c74940A4077C85025d88e42211443bA685` |
| Minter | `0x5decc0fD8EffC851A04D720e82D255cDEA9CB93C` |

Only public addresses are recorded here. Recovery phrases and private keys must never be committed or shared.

## Structure

```text
blockchain/aztoken/
├── contracts/AZToken.sol
├── scripts/deploy-aztoken.js
├── scripts/deployment-safety.js
├── test/AZToken.test.js
├── test/deployment-safety.test.js
├── FUNCTIONS.md
├── hardhat.config.js
└── package.json
```

## Local commands

From this directory:

```bash
pnpm install
pnpm compile
pnpm test
pnpm test:coverage
pnpm deploy:local
```

`deploy:local` deploys only to an ephemeral Hardhat chain. It neither persists a network nor uses funds.

## Optional Sepolia preparation

Copy `.env.example` to `.env` inside this directory and replace every placeholder. Do not commit `.env` or a private key.

Required variables:

- `SEPOLIA_RPC_URL`
- `SEPOLIA_PRIVATE_KEY`
- `ADMIN_ADDRESS`
- `MINTER_ADDRESS`
- `INITIAL_RECIPIENT_ADDRESS`

The Sepolia deployer needs testnet ETH for gas. Phase 1 deliberately has no mainnet network entry, and the deployment script independently rejects chain ID `1` and all chains other than Hardhat (`31337`) and Sepolia (`11155111`).

Do not deploy until the test output and [function documentation](./FUNCTIONS.md) have been reviewed.

## Security boundary

- No contract function can transfer tokens from a holder without the holder initiating a transfer or explicitly approving an allowance.
- `MINTER_ROLE` can create new AZT but cannot move existing holder balances.
- `DEFAULT_ADMIN_ROLE` can grant and revoke roles but cannot move holder balances.
- The contract enforces ongoing separation of duties: one address cannot hold both `DEFAULT_ADMIN_ROLE` and `MINTER_ROLE`.
- Burning another holder's tokens requires that holder's explicit ERC-20 allowance.
- The cap limits outstanding supply to 100,000,000 AZT. Burning reduces supply and therefore creates room below the cap that an authorized minter can later mint again.
- There is no proxy, upgrade hook, arbitrary call, blacklist, tax, pause, rescue, or hidden balance-editing function.

This code is not an audit and is not approved for real funds or mainnet deployment.

## Development dependency audit

The lockfile is checked with `pnpm audit --audit-level high`. Patched transitive versions are forced for the high-severity findings present in Hardhat 2's permitted dependency ranges. The remaining reported findings are low/moderate and exist only in local development and coverage tooling; none is imported into, linked with, or deployed as AZToken bytecode. They must be reviewed again before changing toolchain versions or preparing any production release.
