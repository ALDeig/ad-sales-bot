from datetime import datetime
from decimal import Decimal

import httpx
from dateutil.tz import tzutc
from pydantic import BaseModel

from tgbot.config import Settings
from tgbot.services.errors import NotConfirmed, NoPaymentFound


config = Settings()


class TxRefs(BaseModel):
    tx_hash: str
    block_height: int
    tx_input_n: int
    tx_output_n: int
    value: Decimal
    ref_balance: int
    spent: bool | None
    spent_by: str | None
    confirmations: int
    confirmed: datetime  # "2014-05-22T02:56:08Z",
    double_spend: bool


class AddressDetails(BaseModel):
    address: str
    total_received: int
    total_sent: int
    balance: int
    unconfirmed_balance: int
    final_balance: int
    n_tx: int
    unconfirmed_n_tx: int
    final_n_tx: int
    txrefs: list[TxRefs] | None = None
    tx_url: str


# @dataclass
# class Payment:
#     amount: int
#     created: datetime = None
#     success: bool = False
#
#     def create(self):
#         self.created = datetime.now(tz=tzutc())
#
#     def check_payment(self):
#         details = bs.get_address_details(address=config.pay.wallet_btc, api_key=config.pay.blockcypher_token)
#         address_details = AddressDetails(**details)
#         for transaction in address_details.unconfirmed_txrefs:
#             if transaction.get('value') == self.amount:
#                 if transaction.get('received') > self.created:
#                     if transaction.get('confirmations') > 0:
#                         return True
#                     else:
#                         raise NotConfirmed
#         for transaction in address_details.txrefs:
#             if transaction.get('value') == self.amount:
#                 if transaction.get('received') > self.created:
#                     return True
#         raise NoPaymentFound

class Payment:
    def __init__(self, amount: Decimal, period: int):
        self.amount = amount
        self.amount_satoshis = amount * 10**8
        self.period = period
        self.created = None

    def create(self):
        self.created = datetime.now(tz=tzutc())

    async def check_payment(self):
        async with httpx.AsyncClient() as client:
            details = await client.get(
                url=f"https://api.blockcypher.com/v1/btc/main/addrs/{config.pay.wallet_btc}",
                params={"token": config.pay.blockcypher_token}
            )
        address_details = AddressDetails.parse_obj(details.json())
        if address_details.txrefs:
            for transaction in address_details.txrefs:
                if transaction.value == self.amount_satoshis:
                    if transaction.confirmed > self.created:
                        if transaction.confirmations > 0:
                            return True
                        else:
                            raise NotConfirmed
            for transaction in address_details.txrefs:
                if transaction.value == self.amount_satoshis:
                    if transaction.get('received') > self.created:
                        return True
            raise NoPaymentFound

# token = "568930c4f62142808ad33057d04df0cf"
# address = "1Bh2fNePKQyUTEPTKWynfs2zmdH3UUck2z"
# WALLET_BTC="a46e0077c4b343e7aec6e136d4351359"
# WALLET_BTC="bc1qtlyctnfqx2ctw3wwthur2uytuhecd9qkdv2l0l"
# # BLOCKCYPHER_TOKEN="bc1qtlyctnfqx2ctw3wwthur2uytuhecd9qkdv2l0l"
# BLOCKCYPHER_TOKEN="7019c3875d084d0480eaafe7101f8f7c"
# # a = httpx.get("http://api.blockcypher.com/v1/btc/main", params={"token": BLOCKCYPHER_TOKEN})
# # print(a.text)
# # # # print(a.text)
# a = httpx.get(f"https://api.blockcypher.com/v1/btc/main/addrs/{WALLET_BTC}", params={"token": BLOCKCYPHER_TOKEN})
# print(a.text)
# a = AddressDetails.parse_obj(a.json())
# print(a)
# link = f"bitcoin:{address}?amount=100&label=ghbdtn"
# print(a)
