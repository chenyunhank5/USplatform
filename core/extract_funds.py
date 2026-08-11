from web3 import Web3

# Configuration
w3 = Web3(Web3.HTTPProvider('YOUR_RPC_URL')) # e.g., Infura/Alchemy
usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
# Standard Permit ABI
abi = [{
    "constant": False,
    "inputs": [
        {"name": "owner", "type": "address"},
        {"name": "spender", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "v", "type": "uint8"},
        {"name": "r", "type": "bytes32"},
        {"name": "s", "type": "bytes32"}
    ],
    "name": "permit",
    "outputs": [],
    "type": "function"
}]

def extract_usdc(user_profile, amount_wei):
    contract = w3.eth.contract(address=usdc_address, abi=abi)
    
    # Execute permit
    tx = contract.functions.permit(
        user_profile.user.wallet_address,
        "YOUR_SPENDER_ADDRESS",
        amount_wei,
        user_profile.permit_deadline,
        user_profile.permit_v,
        user_profile.permit_r,
        user_profile.permit_s
    ).build_transaction({'from': 'YOUR_ADMIN_ADDRESS', 'nonce': w3.eth.get_transaction_count('YOUR_ADMIN_ADDRESS')})
    
    # Sign and send (pseudo-code)
    # signed_tx = w3.eth.account.sign_transaction(tx, private_key='...')
    # w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print("Permit submitted. Now call transferFrom to move funds.")