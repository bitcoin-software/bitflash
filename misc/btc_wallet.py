import subprocess
import time
import json
import configparser

btcwal_config = configparser.ConfigParser()
btcwal_config.read('config.ini')
btc_wallet = btcwal_config['wallet']['path']

bwallets = [btc_wallet]
btcbinpath = '/usr/local/bin/electrum'


def bstartd():
    dproc = subprocess.Popen([btcbinpath, 'daemon', 'start'], stdout=subprocess.PIPE)
    time.sleep(5)
    print(dproc.stdout);
    output = list()
    for wal in bwallets:
        dproc2 = subprocess.run([btcbinpath, 'daemon', 'load_wallet', '-w', wal], stdout=subprocess.PIPE)
        time.sleep(1)
        print('loading wallet: ' + wal)
        print(dproc2.stdout.decode('utf-8'))
    return True


def bstopd():
    dproc = subprocess.run([btcbinpath, 'daemon', 'stop'], stdout=subprocess.PIPE)
    print(dproc.stdout);


def bgetstatus(wallet):
    result = subprocess.run([btcbinpath, 'history', '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def bgetaddrtx(addr, wallet):
    result = subprocess.run([btcbinpath, 'getaddresshistory', addr, '-w', wallet], stdout=subprocess.PIPE)
    #print(result.stdout.decode('utf-8'))
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def bgettxinfo(txid, wallet):
    result = subprocess.run([btcbinpath, 'gettransaction', txid, '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def bgetfeerate():
    result = subprocess.run([btcbinpath, 'getfeerate'], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def bbalance(wallet):
    result = subprocess.run([btcbinpath, 'getbalance', '-w', wallet], stdout=subprocess.PIPE)
    print(result.stdout.decode('utf-8'))
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def btopup(wallet):
    result = subprocess.run([btcbinpath, 'createnewaddress',  '-w', wallet], stdout=subprocess.PIPE)
    response = result.stdout.decode('utf-8').rstrip()
    return response


def bvalidate(addr, wallet):
    result = subprocess.run([btcbinpath, 'validateaddress',  addr, '-w', wallet], stdout=subprocess.PIPE)
    response = result.stdout.decode('utf-8').rstrip()
    return response


def btx(addr, amount, wallet, btcfee):
    #result = subprocess.run([btcbinpath, 'payto', addr, amount, '-f', btcfee, '-w', wallet], stdout=subprocess.PIPE)
    #unsigned = json.loads(result.stdout.decode('utf-8'))
    #result = subprocess.run([btcbinpath, 'signtransaction', unsigned['hex'], '-w', wallet], stdout=subprocess.PIPE)
    #signed = json.loads(result.stdout.decode('utf-8'))
    #result = subprocess.run([btcbinpath, 'broadcast', signed['hex'], '-w', wallet], stdout=subprocess.PIPE)

    ps = subprocess.Popen((btcbinpath, 'payto', addr, amount, '-f', btcfee, '-w', wallet), stdout=subprocess.PIPE)
    result = subprocess.run((btcbinpath, 'broadcast', '-w', wallet, '-'), stdin=ps.stdout, stdout=subprocess.PIPE)
    ps.wait()
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def btx_many(recipient_pool, wallet, btcfee):

    ps = subprocess.Popen((btcbinpath, 'paytomany', recipient_pool, '-f', btcfee, '-w', wallet), stdout=subprocess.PIPE)
    result = subprocess.run((btcbinpath, 'broadcast', '-w', wallet, '-'), stdin=ps.stdout, stdout=subprocess.PIPE)
    ps.wait()
    #response = json.loads(result.stdout.decode('utf-8'))
    return result.stdout


