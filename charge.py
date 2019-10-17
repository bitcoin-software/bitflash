import requests
import datetime
import configparser

charge_config = configparser.ConfigParser()
charge_config.read('config.ini')

charge_url = charge_config['charge']['url']
charge_token = charge_config['charge']['token']


def getinfo():
    node_info_request = requests.get(charge_url + '/info', auth=('api-token', charge_token))

    if node_info_request.status_code == 200:
        node_info = node_info_request.json()
        try:
            #invoice_id = invoice_info['payment_hash']
            # print('sms id: ' + invoice_id)
            # print('info: \n' + str(invoice_info))
            pass
        except KeyError as e:
            print('key error')
        return node_info
    else:
        return False


def invoice(msat=None, amount=0, cur='EUR', desc=False):

    dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

    if not desc:
        desc=dtime+'-invoice-without-description'

    crypto = {
        'msatoshi': msat,
        'description': desc,
        'expiry': 600
    }


    fiat = {
        'amount': amount,
        'currency': cur,
        'description': desc,
        'expiry': 600
    }

    if amount == 0:
        payload = crypto
    else:
        payload = fiat

    invoice_info_request = requests.post(charge_url + '/invoice', auth=('api-token', charge_token), data=payload)

    if invoice_info_request.status_code == 201:
        invoice_info = invoice_info_request.json()
        return invoice_info
    else:
        print('error: ' + str(invoice_info_request.status_code))
        return False


def get_invoice(id=None):
    if id:
        data = requests.get(charge_url + '/invoice/'+id, auth=('api-token', charge_token))
    else:
        data = requests.get(charge_url + '/invoices', auth=('api-token', charge_token))

    if data.status_code == 200:
        invoice_info = data.json()
        return invoice_info
    else:
        return False


def register_webhook(invoice_id, callback_url):
    payload = {
        'url': callback_url
    }

    webhook_info_request = requests.post(charge_url + '/invoice/' + invoice_id + '/webhook',
                                         auth=('api-token', charge_token), data=payload)

    if webhook_info_request.status_code == 201:
        return True
    elif webhook_info_request.status_code == 405:
        print('already paid')
        return False
    elif webhook_info_request.status_code == 410:
        print('invoice expired')
        return False

    return False


