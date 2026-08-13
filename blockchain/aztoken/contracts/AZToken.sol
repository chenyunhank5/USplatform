// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {ERC20Capped} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol";

/// @title AZToken
/// @notice A capped, burnable ERC-20 with a separately administered minting role.
/// @dev Phase 1 contains no exchange, USDC, tax, pause, blacklist, or upgrade logic.
contract AZToken is ERC20, ERC20Burnable, ERC20Capped, AccessControl {
    /// @notice Role permitted to mint AZT while the maximum supply is not exceeded.
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /// @notice Amount minted once during construction: 10,000,000 AZT.
    uint256 public constant INITIAL_SUPPLY = 10_000_000 ether;

    /// @notice Absolute lifetime ceiling on simultaneously outstanding supply: 100,000,000 AZT.
    uint256 public constant MAX_SUPPLY = 100_000_000 ether;

    error ZeroAddress();
    error AdminAndMinterMustDiffer();
    error AdminAndMinterRolesMustBeSeparate(address account);

    /// @param initialAdmin Address receiving DEFAULT_ADMIN_ROLE and permission to manage roles.
    /// @param initialMinter Address receiving MINTER_ROLE. It must differ from initialAdmin.
    /// @param initialRecipient Address receiving the complete initial supply.
    constructor(address initialAdmin, address initialMinter, address initialRecipient)
        ERC20("AZToken", "AZT")
        ERC20Capped(MAX_SUPPLY)
    {
        if (initialAdmin == address(0) || initialMinter == address(0) || initialRecipient == address(0)) {
            revert ZeroAddress();
        }
        if (initialAdmin == initialMinter) {
            revert AdminAndMinterMustDiffer();
        }

        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(MINTER_ROLE, initialMinter);
        _mint(initialRecipient, INITIAL_SUPPLY);
    }

    /// @notice Creates new AZT for `recipient`.
    /// @dev Restricted to MINTER_ROLE and automatically bounded by ERC20Capped.
    /// @param recipient Address receiving newly minted AZT.
    /// @param amount Token amount in 18-decimal base units.
    function mint(address recipient, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(recipient, amount);
    }

    /// @dev Preserves least privilege by preventing an account from holding both
    /// DEFAULT_ADMIN_ROLE and MINTER_ROLE at the same time.
    function _grantRole(bytes32 role, address account) internal override returns (bool) {
        if (
            (role == MINTER_ROLE && hasRole(DEFAULT_ADMIN_ROLE, account))
                || (role == DEFAULT_ADMIN_ROLE && hasRole(MINTER_ROLE, account))
        ) {
            revert AdminAndMinterRolesMustBeSeparate(account);
        }

        return super._grantRole(role, account);
    }

    /// @dev Resolves ERC20Capped's supply check in the inheritance graph.
    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Capped) {
        super._update(from, to, value);
    }
}
