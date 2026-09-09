# USDC payment authorizations

The user wallet page is `/user/usdc/` and the staff dashboard is `/staff/usdc/`.
The existing Trading Account and AZToken deployer routes remain available. The
wallet edit page's Verify action opens the separate USDC page after connection. Legacy
AZToken source is retained; the payment flow does not use or trade AZToken.

## Configure and deploy

1. Install root dependencies with `pnpm install` and contract dependencies with
   `pnpm --dir blockchain/aztoken install`.
2. Compile with `pnpm --dir blockchain/aztoken compile`, then `pnpm build:usdc`.
3. Run `python manage.py migrate`. Keep Node available to Django: it verifies
   typed signatures through `frontend/verify-usdc-record.mjs` using ethers.
   Set `USDC_NODE_EXECUTABLE` if Node is not on the server PATH.
4. Set the existing `REOWN_PROJECT_ID` and register the real application origin
   in the Reown project. Wallet connection uses the website's actual origin.
5. Sign into `/staff/usdc/`. Save the receiving, admin, and collector addresses.
   The initial receiving address is
   `0xb1ba83c74940A4077C85025d88e42211443bA685`.
6. From `blockchain/aztoken`, set `ETHEREUM_RPC_URL`, `ETHEREUM_PRIVATE_KEY`,
   `USDC_ADMIN_ADDRESS`, and `USDC_COLLECTOR_ADDRESS`, then run
   `pnpm deploy:usdc-mainnet`. Review the transaction and fee before submitting.
   After confirmation, save the returned contract address in the dashboard.

No mainnet deployment happens during builds or tests. No wallet keys are held
by Django. New deployments grant collection access only to the specified
collector. Later role changes require the admin to call `grantRole` or
`revokeRole` on the deployed contract; changing dashboard deployment settings
alone does not alter blockchain permissions.

## Payment flow

The user explicitly accepts the visible treasury and 100 USDC aggregate cap.
Two EIP-712 signatures are requested: collection terms (owner, treasury, cap,
authorization nonce, fixed expiry) and USDC's ERC-2612 permit. Both are off-chain.
The expiry is approximately 365 days from signing, not from first collection.
Signing authorizes staff to collect immediately or later within those terms;
there is no additional readiness confirmation.

The server verifies both signatures before storing them. Staff connects a
wallet with `COLLECTOR_ROLE` and enters an amount and invoice reference. The
first transaction activates the authorization and collects atomically. Later
transactions collect the remainder. A stable invoice reference prevents
duplicate collections, including retries after uncertain confirmations.
Use a different reference only for a genuinely different payment.

The contract enforces aggregate spending, expiry, authorized collectors,
signature nonces, a signed recipient, and payment-reference uniqueness.
Changing the receiving wallet affects new signatures only. Active plans pay
their original recipient. The user can cancel pending and active authorizations
on-chain (gas required). Revoking USDC allowance stops spending, but a still-valid
unsubmitted permit could restore it; contract cancellation also invalidates the
collection authorization and is the recommended cancellation action here.

The dashboard reads active remaining balances directly from the contract and
reports a payment confirmed after two confirmations. It does not credit the
project's legacy account balance, and stored signatures are not payment receipts.
USDC balances, allowance revocations, token pauses and freezes may prevent
collection. Avoid logging or exposing saved signatures; they authorize real
spending. Back up and restrict access to the database accordingly.

## Verification

- `pnpm --dir blockchain/aztoken test`
- `python manage.py test core.test_usdc`
- `pnpm build:usdc`

Contract tests use MockUSDC on a local Hardhat chain, never mainnet. They cover
20 + 30 + 40 + 10, cap exhaustion, expiry, replay, altered recipients and domains,
unauthorized collectors, duplicate invoices, cancellation, externally submitted
permits and failed-transfer rollback. These tests are not an independent security
audit, and live Crypto.com Onchain signing requires an actual connected wallet.

Ethereum USDC is fixed to Circle's published address:
https://developers.circle.com/stablecoins/usdc-contract-addresses
The client verifies the token's permit domain before requesting signatures.
