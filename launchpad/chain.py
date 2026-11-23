import json
from urllib.request import Request, urlopen

from django.conf import settings
from eth_abi import encode
from eth_utils import keccak

TERMS_TYPE = "(string,string,uint256,uint256,uint256,uint256)"


def campaign_is_deployed(campaign):
    if not settings.SEPOLIA_RPC_URL or not settings.FEE_FACTORY_ADDRESS:
        return False
    args = encode(
        ["bytes32", "address"], [campaign.reference.int.to_bytes(32, "big"), campaign.company.wallet]
    )

    def rpc(method, params):
        request = Request(
            settings.SEPOLIA_RPC_URL,
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=8) as response:
            return json.load(response)["result"]

    def read(signature, address, arguments=b""):
        selector = keccak(text=signature)[:4]
        return bytes.fromhex(rpc("eth_call", [{"to": address, "data": "0x" + (selector + arguments).hex()}, "latest"])[2:])

    if rpc("eth_chainId", []) != "0xaa36a7":
        return False
    factory = settings.FEE_FACTORY_ADDRESS
    address = read("campaigns(bytes32,address)", factory, args)
    if len(address) != 32 or not any(address):
        return False
    terms = (
        campaign.token_name, campaign.symbol, price_in_wei(campaign.price),
        price_in_wei(campaign.goal), campaign.cap, campaign.duration_minutes * 60,
    )
    return read("approvals(bytes32,address)", factory, args) == keccak(
        encode([TERMS_TYPE, "uint16"], [terms, campaign.commission])
    )


def price_in_wei(amount):
    return int(amount * 10**18)
