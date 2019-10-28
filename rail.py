import threading
import datetime
import requests
import time
import traceback
import os
import configparser
from requests.auth import HTTPBasicAuth
from db import get_paid, new_status, get_new, get_processing, get_errored, record_tx
from btc_wallet import bstartd, bstopd, btx_many
from ltc_wallet import lstartd, lstopd, ltx_many

processing = dict()
processing_ltc = dict()

current_orders = list()

executing = {
    'btc': dict(),
    'ltc': dict()
}

wallet_btc = '/home/bitrail/.electrum/wallets/segwit'
wallet_ltc = '/home/bitrail/.electrum-ltc/wallets/segwit'

rail_config = configparser.ConfigParser()
rail_config.read('config.ini')

#fees total per tx
fees = {
    'btc': 1200,
    'ltc': 1200
}

rates = {
    'btcusd': 0,
    'btceur': 0,
    'ltcbtc': 0,
}

pay_for_all = False


def rate_check():
    threading.Timer(180.0, rate_check).start()
    print('refreshing rates...')
    btcusd_get = requests.get('https://www.bitstamp.net/api/v2/ticker/btcusd')
    time.sleep(1)
    btceur_get = requests.get('https://www.bitstamp.net/api/v2/ticker/btceur')
    time.sleep(1)
    ltcbtc_get = requests.get('https://www.bitstamp.net/api/v2/ticker/ltcbtc')
    if (btcusd_get.status_code == 200) and (btceur_get.status_code == 200) and (ltcbtc_get.status_code == 200):
        print('renewing BTC/USD:' + "{:.2f}".format(rates['btcusd']) + ' -> ' + str(btcusd_get.json()['last']))
        rates['btcusd'] = float(btcusd_get.json()['last'])
        print('renewing BTC/EUR:' + "{:.2f}".format(rates['btceur']) + ' -> ' + str(btceur_get.json()['last']))
        rates['btceur'] = float(btceur_get.json()['last'])
        print('renewing LTC/BTC:' + "{:.8f}".format(rates['ltcbtc']) + ' -> ' + str(ltcbtc_get.json()['last']))
        rates['ltcbtc'] = float(ltcbtc_get.json()['last'])
        print('new rates saved!')
    else:
        print('error saving rates!')

    print("updating fees")
    # c-lightning fee estimate
    fees_get = requests.get('http://145.239.239.40:5000/rateinfo',
                            auth=HTTPBasicAuth('ohr7zoh8Ogei7ze', 'Ophu0shohX3zie4'))
    if fees_get.status_code == 200:
        newfees = fees_get.json()
        btc_fee = int(newfees['btc']['onchain_fee_estimates']['opening_channel_satoshis'])
        try:
            ltc_fee = int(newfees['ltc']['onchain_fee_estimates']['opening_channel_satoshis'])
        except Exception as e:
            ltc_fee = int(newfees['ltc']['perkb']['min_acceptable'])

        print('btc fee: ' + str(btc_fee))
        print('ltc fee: ' + str(ltc_fee))
        print('full: ' + str(newfees))
        fees['btc'] = int(btc_fee / 2.7)
        fees['btc_full'] = newfees['btc']
        fees['ltc'] = int(ltc_fee / 2.7)
        fees['ltc_full'] = newfees['ltc']

    else:
        print('fee estimation failed: code + ' + str(fees_get.status_code))


def txcheck():
    threading.Timer(9.0, txcheck).start()
    invoices = get_paid()

    inv_count = 0

    for inv in invoices:
        inv_count += 1
        addr = inv[2]
        satoshi = inv[3]
        charge_id = inv[4]
        status = inv[5]
        dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        amount = satoshi / 100000000
        if addr.startswith("L") or addr.startswith("M") or addr.startswith("ltc1"):
            print(dtime + ': (LTC) found ' + status + ' invoice ' + charge_id + ', sat: ' + str(satoshi))
            print(charge_id + 'mark as in progress')
            order_data = {
                'address': addr,
                'amount_ltc': amount
            }
            processing_ltc[charge_id] = order_data
            new_status(charge_id, 'processing')
        else:
            print(dtime+': found ' + status + ' invoice ' + charge_id + ', sat: ' + str(satoshi))
            print(charge_id + 'mark as in progress')
            order_data = {
                'address': addr,
                'amount_btc': amount
            }
            processing[charge_id] = order_data
            new_status(charge_id, 'processing')

            for order in current_orders:
                if order['charge_id'] == charge_id:
                    if order['fast']:
                        global pay_for_all
                        pay_for_all = True


    print('========= stats =========')
    print('paid orders: ' + str(inv_count))
    newlist = get_new()
    print('new orders: ' + str(len(newlist)))
    processinglist = get_processing()
    print('orders in process: ' + str(len(processinglist)))
    errorlist = get_errored()
    print('orders with error: ' + str(len(errorlist)))
    print('========== queue ========')
    for inv in processing:
        inv_count += 1
        order_data = processing[inv]
        amount = '%.8f' % float(order_data['amount_btc'])
        print(amount + ' btc >> ' + order_data['address'])

    for inv in processing_ltc:
        inv_count += 1
        order_data = processing_ltc[inv]
        amount = '%.8f' % float(order_data['amount_ltc'])
        print(amount + ' ltc >> ' + order_data['address'])
    print('=========== * * * ========')


def batch():
    threading.Timer(70.0, batch).start()

    inv_count = 0

    btc_addr_str = '['
    rcpts = 0

    ids = list()
    print('starting bitcoin batching..')

    receiver_dict_optimized = dict()

    for inv in processing:
        inv_count += 1
        rcpts += 1
        order_data = processing[inv]
        ids.append(inv)
        try:
            receiver_dict_optimized[order_data['address']] += order_data['amount_btc']
        except KeyError as e:
            receiver_dict_optimized[order_data['address']] = order_data['amount_btc']

    final_output_count = 0

    for receiver in receiver_dict_optimized:
        final_output_count += 1
        btc_addr_str = btc_addr_str + '["' + receiver + '", ' + "{:.8f}".format(receiver_dict_optimized[receiver]) + '],'
    btc_addr_str = btc_addr_str[:-1] + ']'

    # print('chargepool: ' + str(btcchargepool))
    total_kb = (100 + (final_output_count * 50)) / 1000
    fee_urgent = fees['btc_full']['perkb']['normal']
    print('BTC FEE:')
    print('per client: ' + str(fees['btc']))
    print('for tx (est. normal): ' + "{:.1f}".format(fee_urgent*total_kb) + ', absolute fee: ' + "{:.8f}".format(round(int(fee_urgent*total_kb)/100000000,8)))
    print('current kb size: ' + str(total_kb))
    print('currently collected from ' + str(inv_count) + ' users: ' + str(inv_count*fees['btc']))
    print('we need for tx to pay: ' + str(final_output_count*fees['btc']))

    global pay_for_all

    if final_output_count*fees['btc'] > fee_urgent*total_kb or pay_for_all:
        pay_for_all = False
        print('we want to send BTC: ' + btc_addr_str)
        network_fee = round(int(fee_urgent*total_kb)/100000000,8)
        paymentfee = network_fee
        try:
            dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            for id in ids:
                executing['btc'][id] = dtime
                processing.pop(id)
            btc_txstatus = btx_many(btc_addr_str, wallet_btc, "{:.8f}".format(paymentfee))
            status = btc_txstatus.decode('utf-8')
            print("BTC tx status:\n" + str(status))
            print("fee paid: " + "{:.8f}".format(paymentfee))
            os.system("echo '" + dtime + " TX BTC OK:" + str(status) + "' >> /tmp/tx.log")
            record_tx(dtime, status, btc_addr_str, 'ok', 'BTC')
            for id in ids:
                new_status(id, 'completed')
                executing['btc'].pop(id)
        except Exception as e:
            error = traceback.format_exc()
            print('error during btc payment' + ": " + error)
            record_tx(dtime, 'none txid', btc_addr_str, 'error', 'BTC')
            i = 0
            for id in ids:
                new_status(id, 'error')
                executing['btc'].pop(id)
                ids.pop(i)
                i+=1
    else:
        print('fees not enough collected')


def batch_ltc():
    threading.Timer(6000.0, batch_ltc).start()

    inv_count = 0

    ltc_addr_str = '['
    rcpts = 0

    ids = list()
    print('starting litecoin batching..')

    receiver_dict_optimized = dict()

    for inv in processing_ltc:
        inv_count += 1
        rcpts += 1
        order_data = processing_ltc[inv]
        ids.append(inv)
        try:
            receiver_dict_optimized[order_data['address']] += order_data['amount_ltc']
        except KeyError as e:
            receiver_dict_optimized[order_data['address']] = order_data['amount_ltc']

###### JOIN OUTPUTS
    for receiver in receiver_dict_optimized:
        ltc_addr_str = ltc_addr_str + '["' + receiver + '", ' + "{:.8f}".format(receiver_dict_optimized[receiver]) + '],'
    ltc_addr_str = ltc_addr_str[:-1] + ']'

    total_kb = (100 + (inv_count * 50)) / 1000
    try:
        fee_urgent = fees['ltc_full']['perkb']['urgent']
    except Exception as e:
        fee_urgent = 30000
    #print('LTC FEE (lites):')
    #print('per client: ' + str(fees['ltc']))
    #print('for tx (est. urgent): ' + str(fee_urgent * total_kb))
    #print('currently collected from ' + str(inv_count) + ' users: ' + str(inv_count * fees['ltc']))
    # multiply by 10 to make txs less frequently
    if inv_count * fees['ltc'] > 3*fee_urgent*total_kb:
        print('we want to send LTC: ' + ltc_addr_str)
        total_kb = (100 + (inv_count * 50)) / 1000
        network_fee = round(int(fee_urgent*total_kb) / 100000000, 8)
        paymentfee = network_fee

        try:
            dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            for id in ids:
                executing['ltc'][id] = dtime
                processing_ltc.pop(id)
            ltc_txstatus = ltx_many(ltc_addr_str, wallet_ltc, "{:.8f}".format(paymentfee))
            status = ltc_txstatus.decode('utf-8')
            print("LTC tx status:\n" + str(status))
            print("fee paid: " + "{:.8f}".format(paymentfee))
            os.system("echo '"+dtime+" TX LTC OK:" + str(status) + "' >> /tmp/tx.log")
            record_tx(dtime, status, ltc_addr_str, 'ok', 'LTC')
            for id in ids:
                new_status(id, 'completed')
                executing['ltc'].pop(id)
        except Exception as e:
            error = traceback.format_exc()
            print('error during ltc payment' + ": " + error)
            os.system("echo '" + dtime + " TX ERROR:" + error + "' >> /root/tx.log")
            record_tx(dtime, 'none txid', ltc_addr_str, 'error', 'BTC')
            i = 0
            for id in ids:
                new_status(id, 'error')
                executing['ltc'].pop(id)
                ids.pop(i)
                i+=1
    else:
        print('no LTC transactions to be processed, batching canceled')



rate_check()
bstartd()
lstartd()
txcheck()
batch()
batch_ltc()
