import asyncio
import json
import requests

from pyinjective.async_client import AsyncClient
from pyinjective.core.network import Network
from exec_buy import buy
from exec_sell import sell

from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_AUTH = os.getenv('DISCORD_AUTH')
DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')
DISCORD_MENTION = os.getenv('DISCORD_MENTION')

utc_1 = timezone(timedelta(hours=1))

file_handler = AsyncFileHandler(filename="app_log.log")
logger = Logger()
logger.add_handler(file_handler)

#active_transactions = 0
#transaction_lock = asyncio.Lock()

async def tx_handler(qty_INJ,contract,multiplicateur,denom,tx_number):

    payload = {'content': f'nouveau contrat détecté  {contract} \n denom : {denom} \n {DISCORD_MENTION}'}
    r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
    
    '''global active_transactions
    async with transaction_lock:
        active_transactions += 1'''

    achat_tx_hash = await buy(qty_INJ = qty_INJ,contract = contract)

    if achat_tx_hash == "Pas de liquidité transaction annulée":
        logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - {achat_tx_hash}")
        payload = {'content': f' Pas de liquidité transaction annulée contrat {contract} \n denom : {denom} \n {DISCORD_MENTION}'}
        r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
        c = 0
        while r.status_code != 200:
            c+=1
            r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
            if c == 10:
                logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - erreur message discord : {r.status_code}")
                break
        return

    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Achat Transaction Hash: {achat_tx_hash}")
    

    payload = {'content': f'achat pour {qty_INJ} INJ avec le contrat {contract} \n denom : {denom} \n {DISCORD_MENTION}'}
    r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
    c = 0
    while r.status_code != 200:
        c+=1
        r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
        if c == 10:
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - erreur message discord : {r.status_code}")
            break

    price_sell = int(qty_INJ*(10**18)*multiplicateur)

    (vente_tx_hash,nombre_inj) = await sell(contract=contract,tx_hash=achat_tx_hash,ratio=ratio,denom=denom,price=price_sell,tx_number=tx_number)
    
    if (vente_tx_hash,nombre_inj) == ("",0):
        logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Vente annulée")
        payload = {'content': f'vente annulée pour le contrat {contract} \n denom : {denom} \n {DISCORD_MENTION}'}
        r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
        return
    '''global active_transactions
    async with transaction_lock:
        active_transactions -= 1'''

    INJ_received = float(nombre_inj * (10 ** (-18)))

    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Vente Transaction Hash: {vente_tx_hash}")
    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Quantité de INJ reçue: {INJ_received}")
    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Bénéfice: {INJ_received - qty_INJ} | Ratio: x{INJ_received / qty_INJ}")

    payload = {'content': f'vente pour {INJ_received} INJ avec le contrat {contract} \n denom : {denom} \n {DISCORD_MENTION}'}
    r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
    c = 0
    while r.status_code != 200:
        c+=1
        r = requests.post(f'https://discord.com/api/v9/channels/{DISCORD_CHANNEL}/messages', json=payload, headers={'authorization':DISCORD_AUTH})
        if c == 10:
            logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - erreur message discord : {r.status_code}")
            break

    return

class TxListener:
    def __init__(self, client):
        self.client = client

    async def tx_callback(self,tx):
        try:
            msg_list = json.loads(tx['messages'])
            if msg_list[0]['type'] == "/injective.wasmx.v1.MsgExecuteContractCompat":
                if msg_list[0]['value']['contract'] == "inj19aenkaj6qhymmt746av8ck4r8euthq3zmxr2r6" :#"inj1c4e2787cwawlqslph0yzn62wq4xpzzq9y9kjwj":
                    msg_dic = json.loads(msg_list[0]['value']['msg'])
                    pair = msg_dic["create_pair"]["asset_infos"]
                    if next(iter(pair[0])) == "native_token":
                        if pair[0]["native_token"]["denom"] == "peggy0xdAC17F958D2ee523a2206206994597C13D831ec7":
                            return
                        elif pair[0]["native_token"]["denom"] == "inj":
                            if next(iter(pair[1])) == "native_token":
                                denom = pair[1]["native_token"]["denom"]
                                qty_INJ = qty_INJ_factory
                                multiplicateur = multiplicateur_factory
                            elif next(iter(pair[1])) == "token":
                                denom = pair[1]["token"]["contract_addr"]
                                qty_INJ = qty_INJ_CW20
                                multiplicateur = multiplicateur_CW20
                            else:
                                return                        
                        else:
                            if next(iter(pair[1])) == "native_token":
                                if pair[1]["native_token"]["denom"] == "inj":
                                    denom = pair[0]["native_token"]["denom"]
                                    qty_INJ = qty_INJ_factory
                                    multiplicateur = multiplicateur_factory
                                else:
                                    return
                            else:
                                return
                    elif next(iter(pair[0])) == "token":
                        if pair[1]["native_token"]["denom"] == "inj":
                            denom = msg_dic["create_pair"]["asset_infos"][0]["token"]["contract_addr"]
                            qty_INJ = qty_INJ_CW20
                            multiplicateur = multiplicateur_CW20
                        else:
                            return
                    else:
                        return
                    
                    tx_number = tx['txNumber']
                    tx_logs = await self.client.fetch_tx(tx['hash'][2:])
                    reply_event = next((event for event in tx_logs['txResponse']['logs'][0]['events'] if event['type'] == "reply"), None)
                    contract = next((attr['value'] for attr in reply_event['attributes'] if attr['key'] == "_contract_address"), None)

                    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Contract: {contract}")
                    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Denom: {denom}")
                    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - {tx_number} - Qty INJ: {qty_INJ}")
                   
                    asyncio.create_task(tx_handler(qty_INJ=qty_INJ,contract=contract,multiplicateur=multiplicateur,denom=denom,tx_number=tx_number))
                    
                
        except:
            logger.exception(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - Erreur dans le bloc __main__")
            return


async def main(qty_INJ_factory,qty_INJ_CW20,ratio,multiplicateur_factory,multiplicateur_CW20) -> None:
    logger.info(f"{datetime.now(utc_1).strftime('%D - %H:%M:%S')} - Start")

    # select network: local, testnet, mainnet
    network = Network.testnet()
    client = AsyncClient(network)
    listener = TxListener(client)
    await client.listen_txs_updates(callback=listener.tx_callback)


if __name__ == "__main__":
    qty_INJ_factory = float(input('quantité de INJ token factory: '))
    qty_INJ_CW20 = float(input('quantité de INJ token CW20: '))
    ratio = input('ratio vente en %: ')
    multiplicateur_factory = float(input('objectif de multiplicateur factory: '))
    multiplicateur_CW20 = float(input('objectif de multiplicateur CW20: '))
    asyncio.run(main(qty_INJ_factory=qty_INJ_factory,qty_INJ_CW20=qty_INJ_CW20,ratio=ratio,multiplicateur_factory=multiplicateur_factory,multiplicateur_CW20=multiplicateur_CW20))
