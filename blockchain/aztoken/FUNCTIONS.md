# AZToken function reference

AZToken composes audited OpenZeppelin modules: `ERC20`, `ERC20Burnable`, `ERC20Capped`, and `AccessControl`. This document describes every externally callable contract function in Phase 1.

Amounts are integers expressed in 18-decimal base units. For example, `1 AZT` is `1_000_000_000_000_000_000` base units.

## AZToken-specific functions

### `constructor(initialAdmin, initialMinter, initialRecipient)`

Runs once at deployment. It validates three non-zero addresses, requires the admin and minter to differ, grants their respective roles, and mints 10,000,000 AZT to the recipient. It cannot run again.

### `mint(recipient, amount)`

Creates `amount` AZT for `recipient`. Only an account holding `MINTER_ROLE` can call it. `ERC20Capped` rejects the transaction if the resulting total supply would exceed 100,000,000 AZT. Minting emits `Transfer(address(0), recipient, amount)`.

This permission does not allow the minter to transfer or burn tokens belonging to another account.

### `MINTER_ROLE()`

Returns the fixed `bytes32` role identifier derived from `keccak256("MINTER_ROLE")`. Applications use this value when checking, granting, or revoking mint permission.

### `INITIAL_SUPPLY()`

Returns `10_000_000 * 10^18`, the quantity minted once by the constructor.

### `MAX_SUPPLY()`

Returns `100_000_000 * 10^18`, the configured cap on outstanding supply.

## ERC-20 information functions

### `name()`

Returns `AZToken`.

### `symbol()`

Returns `AZT`.

### `decimals()`

Returns `18`. This affects user-interface display; it does not add floating-point arithmetic to Solidity.

### `totalSupply()`

Returns current outstanding AZT. Minting increases it and burning decreases it.

### `balanceOf(account)`

Returns the AZT owned by `account`.

## ERC-20 transfer and allowance functions

### `transfer(to, value)`

Moves `value` from the caller to `to`. It fails if the caller lacks the balance or `to` is the zero address. It emits `Transfer`.

### `approve(spender, value)`

Explicitly sets `spender`'s allowance over the caller's AZT to `value`. Setting it to zero revokes the allowance. It emits `Approval`.

As with standard ERC-20 tokens, changing a non-zero allowance directly to another non-zero value can create a transaction-ordering race. Wallet interfaces should normally set the old allowance to zero first or approve only the exact amount required.

### `allowance(owner, spender)`

Returns how much of `owner`'s AZT `spender` is currently permitted to use.

### `transferFrom(from, to, value)`

Moves `value` from `from` to `to`, but only when the caller has sufficient allowance from `from`. A finite allowance decreases by the amount spent. The maximum `uint256` allowance is treated as unlimited and is not decreased.

The future exchange contract will rely on this standard explicit-allowance mechanism; Phase 1 contains no exchange.

## Burning functions

### `burn(value)`

Permanently destroys `value` from the caller's balance and reduces total supply. It emits `Transfer(caller, address(0), value)`.

### `burnFrom(account, value)`

Permanently destroys `value` from `account`, but only when `account` has explicitly approved the caller for at least that amount. It consumes allowance and reduces total supply.

## Supply-cap function

### `cap()`

Returns the immutable 100,000,000 AZT maximum outstanding supply. Transfers do not affect the cap. Burns reduce supply and create room under the cap; authorized minting may use that room later.

## Access-control functions

### `DEFAULT_ADMIN_ROLE()`

Returns the all-zero role identifier used as the administrator for `MINTER_ROLE` and itself. This role is powerful because it can grant and revoke roles, so a future mainnet holder should be a secured treasury multisig.

### `hasRole(role, account)`

Returns whether `account` currently holds `role`.

### `getRoleAdmin(role)`

Returns the role allowed to grant and revoke `role`. In this contract, `DEFAULT_ADMIN_ROLE` administers `MINTER_ROLE`.

### `grantRole(role, account)`

Grants `role` to `account`. The caller must hold the role returned by `getRoleAdmin(role)`. AZToken rejects an assignment that would make the same account both an admin and a minter; the old role must be revoked first. It emits `RoleGranted` when a new assignment is made.

### `revokeRole(role, account)`

Removes `role` from `account`. The caller must hold the role's admin role. It emits `RoleRevoked` when an assignment is removed.

### `renounceRole(role, callerConfirmation)`

Allows a role holder to remove its own role. `callerConfirmation` must equal the transaction caller; one account cannot use this function to remove another account's role.

### `supportsInterface(interfaceId)`

Reports ERC-165 interface support. It returns true for ERC-165 and OpenZeppelin's access-control interface and false for unsupported identifiers.

## Emitted events

- `Transfer(from, to, value)` for transfers, minting, and burning.
- `Approval(owner, spender, value)` when an allowance is set.
- `RoleGranted(role, account, sender)` when a role is granted.
- `RoleRevoked(role, account, sender)` when a role is revoked or renounced.
- `RoleAdminChanged(role, previousAdminRole, newAdminRole)` if a derived implementation changes role administration. AZToken itself exposes no function that changes role administrators.

## Deliberately absent functions

There are no functions for USDC exchange, staff-initiated trades, Reown, pausing, blacklisting, taxation, forced approvals, arbitrary calls, recovering user tokens, upgrading the implementation, or deploying to mainnet. Those concerns are outside Phase 1.
