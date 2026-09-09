// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {EIP712} from "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Permit.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @notice Test payment collector: explicit signed terms, fixed treasury, 100 USDC total.
contract USDCCollections is AccessControl, EIP712, ReentrancyGuard {
    using SafeERC20 for IERC20;
    bytes32 public constant COLLECTOR_ROLE = keccak256("COLLECTOR_ROLE");
    uint256 public constant CAP = 100_000_000;
    bytes32 private constant TERMS_TYPEHASH = keccak256("Authorization(address owner,address treasury,uint256 cap,uint256 nonce,uint256 expiresAt)");
    IERC20 public immutable token;
    mapping(address => uint256) public nonces;
    struct Plan { uint256 remaining; uint256 expiresAt; uint256 nonce; address treasury; }
    mapping(address => Plan) public plans;
    mapping(bytes32 => bool) public collectedPayments;
    event Activated(address indexed owner, uint256 nonce, uint256 expiresAt);
    event Collected(address indexed owner, bytes32 indexed paymentId, uint256 amount, uint256 remaining);
    event Cancelled(address indexed owner);

    constructor(address token_, address admin_, address collector_)
        EIP712("USDC Collections", "1")
    {
        require(token_.code.length > 0 && admin_ != address(0) && collector_ != address(0), "Invalid configuration");
        token = IERC20(token_);
        _grantRole(DEFAULT_ADMIN_ROLE, admin_);
        _grantRole(COLLECTOR_ROLE, collector_);
    }

    function activateAndCollect(address owner, address treasury, uint256 nonce, uint256 expiresAt, bytes calldata authorization,
        uint256 permitDeadline, uint8 v, bytes32 r, bytes32 s, uint256 amount, bytes32 paymentId)
        external onlyRole(COLLECTOR_ROLE) nonReentrant
    {
        require(nonce == nonces[owner], "Stale authorization");
        require(treasury != address(0), "Invalid treasury");
        require(expiresAt > block.timestamp && expiresAt <= block.timestamp + 365 days, "Invalid expiry");
        Plan memory previous = plans[owner];
        require(previous.remaining == 0 || previous.expiresAt <= block.timestamp, "Plan still active");
        bytes32 digest = _hashTypedDataV4(keccak256(abi.encode(TERMS_TYPEHASH, owner, treasury, CAP, nonce, expiresAt)));
        require(owner != address(0) && ECDSA.recover(digest, authorization) == owner, "Invalid authorization");
        nonces[owner]++;
        plans[owner] = Plan(CAP, expiresAt, nonce, treasury);
        // A permit may already have been relayed. Only the independently signed
        // collection terms permit spending, and the allowance is checked below.
        try IERC20Permit(address(token)).permit(owner, address(this), CAP, permitDeadline, v, r, s) {} catch {}
        require(token.allowance(owner, address(this)) >= amount, "Insufficient allowance");
        emit Activated(owner, nonce, expiresAt);
        _collect(owner, amount, paymentId);
    }

    function collect(address owner, uint256 amount, bytes32 paymentId)
        external onlyRole(COLLECTOR_ROLE) nonReentrant
    { _collect(owner, amount, paymentId); }

    function _collect(address owner, uint256 amount, bytes32 paymentId) private {
        Plan storage plan = plans[owner];
        require(block.timestamp < plan.expiresAt, "Authorization expired");
        require(amount > 0 && amount <= plan.remaining, "Exceeds remaining cap");
        require(paymentId != bytes32(0) && !collectedPayments[paymentId], "Duplicate payment");
        collectedPayments[paymentId] = true;
        plan.remaining -= amount;
        token.safeTransferFrom(owner, plan.treasury, amount);
        emit Collected(owner, paymentId, amount, plan.remaining);
    }

    /// @notice Invalidates active and currently pending authorizations on-chain.
    function cancel() external {
        nonces[msg.sender]++;
        delete plans[msg.sender];
        emit Cancelled(msg.sender);
    }
}
