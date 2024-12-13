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


async def sell(contract, tx_hash, ratio, denom, price,tx_number):

    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - dans la fonction sell pour {tx_number} avec le contrat : {contract}")
    # select network: local, testnet, mainnet
    network = Network.mainnet()

    # initialize grpc client
    client = AsyncClient(network)
    composer = await client.composer()
    await client.sync_timeout_height()

    # load account
    priv_key = PrivateKey.from_hex(pv_key)
    pub_key = priv_key.to_public_key()
    address = pub_key.to_address()

    while True:
        try:
            await asyncio.sleep(2)
            tx_logs = await client.fetch_tx(tx_hash)
            wasm_event = next((event for event in tx_logs['txResponse']['logs'][0]['events'] if event['type'] == "wasm"), None)
            break
        except:
            continue

    if denom == None:
        denom = next((attr['value'] for attr in wasm_event['attributes'] if attr['key'] == "ask_asset"), None)
    
    nombre_token = int(next((attr['value'] for attr in wasm_event['attributes'] if attr['key'] == "return_amount"), None))
    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - nombre de tokens achetés : {nombre_token}")

    if denom[:7] == "factory":
        token_type = '"native_token":{"denom"'
    else:
        token_type = '"token":{"contract_addr"'
        nombre_token = int(nombre_token*0.99)
    #nombre_token *= ratio

    # prepare tx msg
    funds = [
        composer.coin(
            amount=nombre_token,
            denom=denom,
        )
    ]

    msg = composer.MsgExecuteContract(
        sender=address.to_acc_bech32(),
        contract=contract,
        msg='{"swap":{"offer_asset":{"info":{'+token_type+':"'+denom+'"}},"amount":"'+str(nombre_token)+'"},"max_spread":"0.5"}}',
        funds=funds,
    )

    i = 0
    dimin_token = 0
    while True:
        await client.fetch_account(address.to_acc_bech32())
            
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
            continue

        if i%1000 == 0:
            try:
                test = 0
                #details = sim_res.details()
                #logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - fonction sell, {i} tx simulées, contrat : {contract} \n {details}")
            except:
                pass

        i+=1

        if i%3000==0:
            price*=0.9
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Baisse du TP à: {price} veuillez vérifier la courbe")
        
        if i>150000:
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Suppression du TP, retrait imminent")
            price = 0
        
        if i>150100:
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - vente impossible, annulation")
            return("",0)

        
        try:    
            wasm_event_sim = next((event for event in sim_res['result']['events'] if event['type'] == "wasm"), None)
            nombre_inj_sim = int(next((attr['value'] for attr in wasm_event_sim['attributes'] if attr['key'] == "return_amount"), None))
        except:
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - EXCEPTION fonction sell, calcul de prix impossible, contrat : {contract} \n {sim_res}")
            '''details = sim_res.details()
            if details[:25] == "account sequence mismatch":
                msg = composer.MsgExecuteContract(
                    sender=address.to_acc_bech32(),
                    contract=contract,
                    msg='{"swap":{"offer_asset":{"info":{'+token_type+':"'+denom+'"}},"amount":"'+str(nombre_token)+'"},"max_spread":"0.05"}}',
                    funds=funds,
                )
                logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - actualisation de l'account sequence, contrat : {contract}")
            if details[:62] == "failed to execute message; message index: 0: spendable balance":

                dimin_token +=1
                if dimin_token>450:#plus que 1% du nombre de token achetés
                    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - balance inférieure à 1% du nombre d'achat annulation de la vente, contrat : {contract}")
                    return ("",0)


                nombre_token = int(nombre_token*0.99)

                funds = [
                    composer.coin(
                        amount=nombre_token,
                        denom=denom,
                    )
                ]

                msg = composer.MsgExecuteContract(
                    sender=address.to_acc_bech32(),
                    contract=contract,
                    msg='{"swap":{"offer_asset":{"info":{'+token_type+':"'+denom+'"}},"amount":"'+str(nombre_token)+'"},"max_spread":"0.05"}}',
                    funds=funds,
                )

                logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - actualisation du nombre de token : {nombre_token}, contrat : {contract}")

            continue'''

        if success and nombre_inj_sim > price:
            # build tx
            gas_price = 500000000
            gas_limit = int(sim_res['gasInfo']['gasUsed']) + 200000  # add 20k for gas, fee computation
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
            await asyncio.sleep(2)

            try:
                res_hash = res['txResponse']['txhash']
                res_logs = await client.fetch_tx(res_hash)
                wasm_event_res = next((event for event in res_logs['txResponse']['logs'][0]['events'] if event['type'] == "wasm"), None)
                nombre_inj_res = next((attr['value'] for attr in wasm_event_res['attributes'] if attr['key'] == "return_amount"), None)

                return (res_hash,nombre_inj_res)
            
            except:
                pass



if __name__ == "__main__":
    contract = input('contract: ')
    tx_hash = input('tx_hash: ')
    ratio = input('ratio vente en %')
    asyncio.run(sell(contract=contract,tx_hash=tx_hash,ratio=ratio,denom=None,price=0,tx_number=0))
