// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
contract MockUSDC is ERC20, ERC20Permit {
    constructor() ERC20("Mock USDC", "mUSDC") ERC20Permit("Mock USDC") {
        _mint(msg.sender, 1_000_000 * 10 ** 6);
    }
    function decimals() public pure override returns (uint8) { return 6; }
}
