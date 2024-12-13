import asyncio

from pyinjective.async_client import AsyncClient
from pyinjective.core.network import Network
from pyinjective.transaction import Transaction
from pyinjective.wallet import PrivateKey

from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
import os

load_dotenv()

pv_key = os.getenv('PRIVATE_KEY')

utc_1 = timezone(timedelta(hours=1))

file_handler = AsyncFileHandler(filename="app_log.log")
logger = Logger()
logger.add_handler(file_handler)


async def buy(qty_INJ: float, contract: str) -> str:

    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - dans la fonction buy pour {qty_INJ} avec le contrat : {contract}")
    qty_inj = int(qty_INJ*(10**18))
    
    # select network: local, testnet, mainnet
    network = Network.testnet()

    # initialize grpc client
    # set custom cookie location (optional) - defaults to current dir
    client = AsyncClient(network)
    composer = await client.composer()
    await client.sync_timeout_height()

    # load account
    priv_key = PrivateKey.from_hex(pv_key)
    pub_key = priv_key.to_public_key()
    address = pub_key.to_address()


    # prepare tx msg
    # NOTE: COIN MUST BE SORTED IN ALPHABETICAL ORDER BY DENOMS
    funds = [
        composer.coin(
            amount=qty_inj,
            denom="inj",
        )
    ]
    msg = composer.MsgExecuteContract(
        sender=address.to_acc_bech32(),
        contract=contract,
        msg='{"swap":{"offer_asset":{"info":{"native_token":{"denom":"inj"}},"amount":"'+str(qty_inj)+'"},"max_spread":"0.5"}}',
        funds=funds,
    )

    i = -1
    while True:
        await client.fetch_account(address.to_acc_bech32())
        i += 1
        if i>50000:
            return "Pas de liquidité transaction annulée"
        # build sim tx
        tx = (
            Transaction()
            .with_messages(msg)
            .with_sequence(client.get_sequence())
            .with_account_num(client.get_number())
            .with_chain_id(network.chain_id)
        )
        sim_sign_doc = tx.get_sign_doc(pub_key)
        sim_sig = priv_key.sign(sim_sign_doc.SerializeToString())
        sim_tx_raw_bytes = tx.get_tx_data(sim_sig, pub_key)

        # simulate tx
        success = False
        try:
            sim_res = await client.simulate(sim_tx_raw_bytes)
            success = True
        except:
            #logger.exception(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - fonction buy problème simulate_tx, contrat : {contract}")
            continue
        
        if i%1000 == 0:
            try:
                test = 0
                #details = sim_res.details()
                #logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - fonction buy, {i} tx simulées, contrat : {contract} \n {details}")
            except Exception as e:
                print("exception :",e)
                pass
            
        if success:
            # build tx
            gas_price = 500000000
            gas_limit = int(sim_res['gasInfo']['gasUsed']) + 500000
            gas_fee = "{:.18f}".format((gas_price * gas_limit) / pow(10, 18)).rstrip("0")
            fee = [
                composer.coin(
                    amount=gas_price * gas_limit,
                    denom=network.fee_denom,
                )
            ]


            # broadcast tx: send_tx_async_mode, send_tx_sync_mode, send_tx_block_mode
            tx = tx.with_gas(gas_limit).with_fee(fee).with_memo("").with_timeout_height(client.timeout_height)
            sign_doc = tx.get_sign_doc(pub_key)
            sig = priv_key.sign(sign_doc.SerializeToString())
            tx_raw_bytes = tx.get_tx_data(sig, pub_key)

            res = await client.broadcast_tx_sync_mode(tx_raw_bytes)

            tx_hash = res['txResponse']['txhash']
            print(tx_hash)
            return tx_hash
            


if __name__ == "__main__":
    qty_INJ = float(input('quantité de INJ: '))
    contract = input('contract: ')
    asyncio.run(buy(qty_INJ=qty_INJ,contract=contract))
