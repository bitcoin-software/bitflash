import subprocess
import time
import json
import configparser

ltcwal_config = configparser.ConfigParser()
ltcwal_config.read('config.ini')
ltc_wallet = ltcwal_config['wallet']['ltc_path']

lwallets = [ltc_wallet]
ltcbinpath = '/usr/local/bin/electrum-ltc'


def lstartd():
    dproc = subprocess.Popen([ltcbinpath, 'daemon', 'start'], stdout=subprocess.PIPE)
    time.sleep(5)
    print(dproc.stdout)
    output = list()
    for wal in lwallets:
        dproc2 = subprocess.run([ltcbinpath, 'daemon', 'load_wallet', '-w', wal], stdout=subprocess.PIPE)
        time.sleep(1)
        print('loading wallet: ' + wal)
        print(dproc2.stdout.decode('utf-8'))
    return True


def lstopd():
    dproc = subprocess.run([ltcbinpath, 'daemon', 'stop'], stdout=subprocess.PIPE)
    print(dproc.stdout)


def lgetstatus(wallet):
    result = subprocess.run([ltcbinpath, 'history', '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def lgetaddrtx(addr, wallet):
    result = subprocess.run([ltcbinpath, 'getaddresshistory', addr, '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def lgettxinfo(txid, wallet):
    result = subprocess.run([ltcbinpath, 'gettransaction', txid, '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response

def lgetfeerate():
    result = subprocess.run([ltcbinpath, 'getfeerate'], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response

def lbalance(wallet):
    result = subprocess.run([ltcbinpath, 'getbalance', '-w', wallet], stdout=subprocess.PIPE)
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def ltopup(wallet):
    result = subprocess.run([ltcbinpath, 'createnewaddress',  '-w', wallet], stdout=subprocess.PIPE)
    response = result.stdout.decode('utf-8').rstrip()
    return response


def lvalidate(addr, wallet):
    result = subprocess.run([ltcbinpath, 'validateaddress',  addr, '-w', wallet], stdout=subprocess.PIPE)
    response = result.stdout.decode('utf-8').rstrip()
    return response


def ltx(addr, amount, wallet, ltcfee):
    #result = subprocess.run([ltcbinpath, 'payto', addr, amount, '-f', ltcfee, '-w', wallet], stdout=subprocess.PIPE)
    #unsigned = json.loads(result.stdout.decode('utf-8'))
    #result = subprocess.run([ltcbinpath, 'signtransaction', unsigned['hex'], '-w', wallet], stdout=subprocess.PIPE)
    #signed = json.loads(result.stdout.decode('utf-8'))
    #result = subprocess.run([ltcbinpath, 'broadcast', signed['hex'], '-w', wallet], stdout=subprocess.PIPE)
    #response = json.loads(result.stdout.decode('utf-8'))

    ps = subprocess.Popen((ltcbinpath, 'payto', addr, amount, '-f', ltcfee, '-w', wallet), stdout=subprocess.PIPE)
    result = subprocess.run((ltcbinpath, 'broadcast', '-w', wallet, '-'), stdin=ps.stdout, stdout=subprocess.PIPE)
    ps.wait()
    response = json.loads(result.stdout.decode('utf-8'))
    return response


def ltx_many(recipient_pool, wallet, ltcfee):
    ps = subprocess.Popen((ltcbinpath, 'paytomany', recipient_pool, '-f', ltcfee, '-w', wallet), stdout=subprocess.PIPE)
    result = subprocess.run((ltcbinpath, 'broadcast', '-w', wallet, '-'), stdin=ps.stdout, stdout=subprocess.PIPE)
    ps.wait()
    #response = json.loads(result.stdout.decode('utf-8'))
    return result.stdout