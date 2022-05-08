from datetime import datetime
from decimal import Decimal

import httpx
from dateutil.tz import tzutc
from pydantic import BaseModel

from tgbot.config import Settings
from tgbot.services.errors import NoPaymentFound
from tgbot.services.datatypes import Prices, Currencies


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
    confirmed: datetime
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


class Payment:
    def __init__(self, prices: Prices, period: int, currency: Currencies):
        self.prices = prices
        self.currency = currency
        self.period = period
        self.created = None

    def create(self):
        self.created = datetime.now(tz=tzutc())

    def get_price_in_currency(self) -> Decimal:
        prices = {Currencies.btc: self.prices.btc, Currencies.ltc: self.prices.ltc, Currencies.dash: self.prices.dash}
        return prices[self.currency]

    def _choose_currency_url(self) -> str:
        urls = {
            Currencies.btc: f"https://api.blockcypher.com/v1/btc/main/addrs/{config.pay.wallet_btc}",
            Currencies.ltc: f"https://api.blockcypher.com/v1/ltc/main/addrs/{config.pay.wallet_ltc}",
            Currencies.dash: f"https://api.blockcypher.com/v1/dash/main/addrs/{config.pay.wallet_dash}"
        }
        return urls[self.currency]

    async def check_payment(self):
        url = self._choose_currency_url()
        amount_satoshis = self.get_price_in_currency() * 10**8
        async with httpx.AsyncClient() as client:
            details = await client.get(url=url, params={"token": config.pay.blockcypher_token})
        address_details = AddressDetails.parse_obj(details.json())
        if address_details.txrefs:
            for transaction in address_details.txrefs:
                if transaction.value == amount_satoshis:
                    if transaction.confirmed > self.created:
                        if transaction.confirmations > 0:
                            return True
        raise NoPaymentFound

    def __repr__(self):
        return f"prices={self.prices}\ncurrency={self.currency}\nperiod={self.period}\ncreated={self.created}"


"""
Bitcoin	Main	api.blockcypher.com/v1/btc/main
Bitcoin	Testnet3	api.blockcypher.com/v1/btc/test3
Dash	Main	api.blockcypher.com/v1/dash/main
Dogecoin	Main	api.blockcypher.com/v1/doge/main
Litecoin	Main	api.blockcypher.com/v1/ltc/main
BlockCypher	Test	api.blockcypher.com/v1/bcy/test
"""
