from flask import Flask
from flask_restful import Resource, Api, reqparse, request
import datetime
from hashlib import blake2b
from db import get_status, new_invoice
from charge import invoice, register_webhook, get_invoice
from btc_wallet import bvalidate, bgetfeerate
from ltc_wallet import lvalidate, lgetfeerate
import requests
from requests.auth import HTTPBasicAuth
import configparser
import threading
import time
import base64
from rail import executing, processing, processing_ltc, current_orders

app = Flask(__name__)
api = Api(app)

rates = {
    'btcusd': 0,
    'btceur': 0,
    'ltcbtc': 0,
}

api_config = configparser.ConfigParser()
api_config.read('config.ini')
fees = dict()
fees['service'] = api_config['fees']['service']

charge_callbacks = api_config['charge']['callback_url']
paylightning_url = api_config['paylightning']['url']
paylightning_login = api_config['paylightning']['login']
paylightning_password = api_config['paylightning']['password']

btc_wallet = api_config['wallet']['path']
ltc_wallet = api_config['wallet']['ltc_path']
bw_wallet = api_config['wallet']['bluewallet']
lntxbot_url = api_config['wallet']['lntxbot_url']

max_amount_sat = 1000000


def rate_check():
    threading.Timer(95.0, rate_check).start()
    #print('refreshing rates...')
    btcusd_get = requests.get('https://www.bitstamp.net/api/v2/ticker/btcusd')
    time.sleep(1)
    btceur_get = requests.get('https://www.bitstamp.net/api/v2/ticker/btceur')
    time.sleep(1)
    ltcbtc_get = requests.get('https://www.bitstamp.net/api/v2/ticker/ltcbtc')
    if (btcusd_get.status_code == 200) and (btceur_get.status_code == 200) and (ltcbtc_get.status_code == 200):
        dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        #print(dtime)
        #print('renewing BTC/USD:' + "{:.2f}".format(rates['btcusd']) + ' -> ' + str(btcusd_get.json()['last']))
        rates['btcusd'] = float(btcusd_get.json()['last'])
        #print('renewing BTC/EUR:' + "{:.2f}".format(rates['btceur']) + ' -> ' + str(btceur_get.json()['last']))
        rates['btceur'] = float(btceur_get.json()['last'])
        #print('renewing LTC/BTC:' + "{:.8f}".format(rates['ltcbtc']) + ' -> ' + str(ltcbtc_get.json()['last']))
        rates['ltcbtc'] = float(ltcbtc_get.json()['last'])
        #print('new rates saved!')
    else:
        print('api: error saving rates!')

    print("api: updating fees")
    #c-lightning fee estimate
    fees_get = requests.get(paylightning_url + '/rateinfo', auth=HTTPBasicAuth(paylightning_login, paylightning_password))
    if fees_get.status_code == 200:
        newfees = fees_get.json()
        btc_fee = int(newfees['btc']['onchain_fee_estimates']['opening_channel_satoshis'])
        try:
            ltc_fee = int(newfees['ltc']['onchain_fee_estimates']['opening_channel_satoshis'])
        except Exception as e:
            ltc_fee = int(newfees['ltc']['perkb']['min_acceptable'])

    else:
        #electrum fee estimate
        btc_fee = 1000
        ltc_fee = 1000
        newfees = {
            'btc': fees['btc_full'],
            'ltc': fees['ltc_full']
        }

    #print('btc fee: ' + str(btc_fee))
    #print('ltc fee: ' + str(ltc_fee))
    #fee per user
    fees['btc'] = int(btc_fee / 2.7)
    fees['btc_full'] = newfees['btc']
    fees['ltc'] = int(ltc_fee / 2.7)
    fees['ltc_full'] = newfees['ltc']
    #print(fees)


def create_invoice(addr, amount, fast=False):
    dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    hash = blake2b(digest_size=8)
    hash.update(str.encode(dtime + addr + str(amount)))
    order_id = hash.hexdigest()[:5]

    fee_sat = int(fees['service'])
    ltc_network_fee = int(fees['ltc'])

    ### pay for all needed computations

    def getfastfee():
        inv_count = 0
        receiver_dict_optimized = dict()

        for inv in processing:
            inv_count += 1

            order_data = processing[inv]
            try:
                receiver_dict_optimized[order_data['address']] += order_data['amount_btc']
            except KeyError as e:
                receiver_dict_optimized[order_data['address']] = order_data['amount_btc']

        final_output_count = 0

        for receiver in receiver_dict_optimized:
            final_output_count += 1

        if final_output_count == 0:
            final_output_count = 1

        total_kb = (100 + (final_output_count * 50)) / 1000
        fee_urgent = fees['btc_full']['perkb']['normal']

        per_client_fee = fees['btc']
        expected_tx_fee = fee_urgent * total_kb
        collected_fees = final_output_count * fees['btc']

        fast_fee = expected_tx_fee - (expected_tx_fee - collected_fees)

        return fast_fee

    ####

    #fee per one user
    if not fast:
        btc_network_fee = int(fees['btc'])
    else:
        btc_network_fee = getfastfee()


    if addr.startswith("L") or addr.startswith("M") or addr.startswith("ltc1"):
        fast = True
        #THIS IS FOR LITECOIN

        return {'error': 'litecoin support currently paused due to no demand'}

        valid = lvalidate(addr, ltc_wallet)
        if valid != 'true':
            return {'error': 'wrong address'}

        ltc_price = rates['ltcbtc']*1.005

        satoshis = round((float(ltc_price) * float(amount)) * 100000000)

        if satoshis > max_amount_sat:
            return {'error': 'maximum amount is 1 000 000 satoshi ('+"{:.4f}".format(round(0.01/ltc_price, 4))+' LTC)'}

        lites = round(float(amount)*100000000)
        network_fee_sat = round(float(ltc_network_fee) * ltc_price)
        msat = round(satoshis*1000 + fee_sat*1000 + network_fee_sat*1000)
        currency = 'LTC'
    else:
        #THIS IS FOR BITCOIN
        valid = bvalidate(addr, btc_wallet)
        if valid != 'true':
            return {'error': 'wrong address'}

        satoshis = round(float(amount) * 100000000)

        lites = False

        def split_invoices():
            dm = divmod(satoshis, max_amount_sat)
            modulus = dm[0]
            amount_left = dm[1]
            if amount_left > 0:
                total_invoices = modulus + 1
            else:
                total_invoices = modulus

            result = {
                "total_invoices": total_invoices,
                "amount_left": amount_left
            }

            return result

        network_fee_sat = btc_network_fee

        msat = round(satoshis * 1000 + fee_sat * 1000 + network_fee_sat * 1000)
        currency = 'BTC'

        if satoshis > max_amount_sat:
            # divide large amount into multiple smaller ones

            #return {'error': 'maximum amount is 1 000 000 satoshi (0.01 BTC)'}
            splitted = split_invoices()

            invoice_count = splitted['total_invoices']
            amount_left = splitted['amount_left']

            counter = 1
            invoices_list = list()

            while counter <= invoice_count:
            #while all whole amounts are divided, create invoices
            #as a separate invoice create what left
                dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

                counter += 1
                if counter != invoice_count:
                    msat = round(max_amount_sat * 1000 + fee_sat * 1000 + (network_fee_sat / invoice_count) * 1000) + 3
                    splitted_order_fast = False
                else:
                    msat = round(amount_left * 1000 + fee_sat * 1000 + getfastfee() * 1000) + 3
                    splitted_order_fast = fast

                inv = invoice(msat=msat, desc='Boost tx of ' + str(amount) + ' to ' + addr + '(id:' + order_id + ')')
                if inv:
                    payreq = inv['payreq']
                    id = inv['id']
                    register_webhook(id, charge_callbacks)
                    if counter != invoice_count:
                        new_invoice(dtime, order_id, addr, max_amount_sat, id, payreq)
                    else:
                        new_invoice(dtime, order_id, addr, amount_left, id, payreq)

                    order = {
                        'order_id': order_id,
                        'charge_id': id,
                        'bolt11': payreq,
                        'fee_satoshi': fee_sat,
                        'network_fee_sat': round(network_fee_sat / invoice_count)+3,
                        'tobe_paid_satoshi': str(round(msat / 1000)),
                        'receiver': addr,
                        'fast': fast,
                        'receiver_amount': str(amount),
                        'receiver_currency': currency
                    }
                    invoices_list.append(order)
                    current_orders.append(order)
                else:
                    return {'error': 'something went completely wrong. please contact developer!'}
            #FINALLY, return bunch of invoices
            return {"invoices": invoices_list}

    print('generating invoice for msat:' + str(msat))
    inv = invoice(msat=msat, desc='Boost tx of ' + str(amount) + ' to ' + addr + '(id:' + order_id + ')')
    if inv:
        payreq = inv['payreq']
        id = inv['id']
        register_webhook(id, charge_callbacks)
        if lites:
            satoshis = lites
        new_invoice(dtime, order_id, addr, satoshis, id, payreq)
        order = {
            'order_id': order_id,
            'charge_id': id,
            'bolt11': payreq,
            'fee_satoshi': fee_sat,
            'network_fee_sat': network_fee_sat,
            'tobe_paid_satoshi': str(round(msat / 1000)),
            'receiver':  addr,
            'fast': fast,
            'receiver_amount': str(amount),
            'receiver_currency': currency
        }
        if lites:
            order['exchange_ltcbtc'] = "{:.8f}".format(ltc_price)

        invoices = list()
        invoices.append(order)
        current_orders.append(order)
        return {"invoices": invoices}
    else:
        return False


class NewInvoice(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('address')
        parser.add_argument('amount')
        parser.add_argument('fast')
        args = parser.parse_args()
        amount = args['amount']
        address = args['address']

        try:
            too_fast = str(args['fast']).lower()
            if too_fast == 'true':
                fast = True
            else:
                fast = False
        except KeyError as e:
            fast = False

        order = create_invoice(address, amount, fast)

        return order


class InvoiceInfo(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        id = args['id']
        invoice_data = get_invoice(id)
        return invoice_data


class TestEcho(Resource):
    def get(self):
        data = {'echo': 'succesfull'}

        return data


class GetStatus(Resource):
    def get(self):

        inv_count_btc = 0

        for inv in processing:
            inv_count_btc += 1
            print(inv)
        total_kb_btc = (100 + (inv_count_btc * 50)) / 1000
        fee_urgent_btc = fees['btc_full']['perkb']['normal']*total_kb_btc
        percent_btc = (int(fees['btc']) * inv_count_btc) / int(fee_urgent_btc)

        inv_count_ltc = 0
        for inv in processing_ltc:
            inv_count_ltc += 1
            print(inv)
        total_kb_ltc = (100 + (inv_count_ltc * 50)) / 1000
        #ltc_fees = fees['ltc_full']['perkb']['normal']
        ltc_fees = 1000
        fee_urgent_ltc = ltc_fees*total_kb_ltc
        percent_ltc = (int(fees['ltc']) * inv_count_ltc) / int(fee_urgent_ltc)

        data = {'btc': int(percent_btc*100),
                'ltc': int(percent_ltc*100),
                'fee_required': {
                    'btc': fee_urgent_btc,
                    'ltc': fee_urgent_ltc
                },
                'fee_collected': {
                    'btc': fees['btc']*inv_count_btc,
                    'ltc': fees['ltc']*inv_count_ltc
                }
                }

        return data


class GetRates(Resource):
    def get(self):
        return rates


class GetLNDonation(Resource):
    def get(self):
        lntxbot_token = base64.b64encode(bw_wallet).decode("utf-8")

        payload = {
            'memo': 'donate 10k sats to support Bitflash',
            'amt': '10000',
        }

        headers = {
            'Authorization': 'Bearer ' + str(lntxbot_token)
        }

        r = requests.post(lntxbot_url, json=payload, headers=headers)

        # print(r.status_code)
        # print(r.request.headers)
        # print(r.request.body.decode("utf-8"))
        # print("\n\n")
        data = r.json()

        invoice = {
          'bolt': data['pay_req']
        }

        return invoice


class Bitpay(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url')
        args = parser.parse_args()
        url = args['url']

        r = requests.get(url, headers={"Accept": "application/payment-request"})
        data = False
        if r.status_code==200:
            invoice_info = r.json()
            data = {
                "address": invoice_info['outputs'][0]['address'],
                "amount": round(invoice_info['outputs'][0]['amount'] / 100000000, 8)
            }
        return data


rate_check()

api.add_resource(NewInvoice, '/new')
api.add_resource(TestEcho, '/echo')
api.add_resource(GetRates, '/getrates')
api.add_resource(GetStatus, '/getstatus')
api.add_resource(GetLNDonation, '/donate')
api.add_resource(InvoiceInfo, '/invoiceinfo')
api.add_resource(Bitpay, '/bitpay')

if __name__ == '__main__':
    app.run(debug=False, port=7778)