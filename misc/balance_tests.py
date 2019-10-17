from btc_wallet import bbalance, bgetstatus

wallet = '/home/bitrail/.electrum/wallets/segwit'

hist = bgetstatus(wallet)

balance = bbalance(wallet)

last_balance = hist['transactions'][-1]['balance']

print(last_balance)
print(balance)