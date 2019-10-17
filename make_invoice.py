from charge import getinfo, invoice, register_webhook

nodeinfo = getinfo()
print('using node: ' + nodeinfo['alias'] + '(' + str(nodeinfo['blockheight']) + ', peers: ' + str(
    nodeinfo['num_peers']) + ')')
inv = invoice(amount=1, desc='testing charge')
print("\n\n==== INVOICE =====\n\n" + inv['payreq'] + "\n\n===================\n")
print("==== URL ====")
print('https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=lightning:'+inv['payreq'])
print("=============")


if register_webhook(inv['id'], 'https://cb.yaya.cf/charge'):
    print('registered webhook for ' + inv['id'])
else:
    print('failed to register webhook for ' + inv['id'])