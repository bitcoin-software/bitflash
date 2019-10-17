import sqlite3

dbpath='rail.db'

def create_db():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute('CREATE TABLE invoices(timestamp TEXT, id TEXT, addr TEXT, satoshi INT, chargeid TEXT, status TEXT, bolt11 TEXT)')
    conn.commit()
    conn.close()

def create_txs():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute('CREATE TABLE invoices(timestamp TEXT, txid TEXT, pool TEXT, status TEXT, currency TEXT)')
    conn.commit()
    conn.close()

def new_invoice(dtime, id, addr, satoshi, charge_id, bolt11):
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    status = 'new'
    c.execute("INSERT INTO invoices VALUES ('"+dtime+"','"+id+"','"+addr+"',"+str(satoshi)+",'"+charge_id+"','"+status+"','"+bolt11+"')")
    conn.commit()
    conn.close()

def record_tx(dtime, txid, pool, status, currency):
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute("INSERT INTO txs VALUES ('"+dtime+"','"+txid+"','"+pool+"','"+status+"','"+currency+"')")
    conn.commit()
    conn.close()


def get_status(charge_id):
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = (charge_id,)
    c.execute('SELECT * FROM invoices WHERE chargeid=?', t)
    data = c.fetchone()
    conn.commit()
    conn.close()
    #('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data

def get_paid():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = ('paid',)
    c.execute('SELECT * FROM invoices WHERE status=?', t)
    data = c.fetchall()
    conn.commit()
    conn.close()
    #list of tuples ('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data

def get_new():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = ('new',)
    c.execute('SELECT * FROM invoices WHERE status=?', t)
    data = c.fetchall()
    conn.commit()
    conn.close()
    #list of tuples ('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data

def get_processing():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = ('processing',)
    c.execute('SELECT * FROM invoices WHERE status=?', t)
    data = c.fetchall()
    conn.commit()
    conn.close()
    #list of tuples ('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data

def get_errored():
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = ('error',)
    c.execute('SELECT * FROM invoices WHERE status=?', t)
    data = c.fetchall()
    conn.commit()
    conn.close()
    #list of tuples ('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data


def new_status(charge_id, newstatus):
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    t = (charge_id,)
    c.execute("UPDATE invoices SET status='"+newstatus+"' WHERE chargeid=?", t)
    data = c.fetchone()
    conn.commit()
    conn.close()
    #('2019-06-16 21:09:08', 'ee49e', 'bc1q5tjkt26e00mdxxeytvwnccvw0n3urrpgpwv8k5', 10, 'V~DdJZDkvxCg1~rA_A0bj', 'new', 'lnbc100n1pwsdpwxpp5dvgm7k8rnwc94rwdtnm9nsapqayn77dald9r4ymqu3s90krgzd0qdragfhk7um5yp68sgr0vcsrqt3sxqcrqvpsxyczqar0yp3xxvt3x46x56m5xgmx2vpsd4j8s7r90968vamwvd3hvaesdceh2unjwpnhqamk8p4n22rfvsax2ef589jjjxqyjw5qcqp2rzjqwjs8k8rpuhlgpcfd534khdk8d8u70uf5ef6edh585lufy48vaqpjzxwcqqqvqcqqyqqqqlgqqqqqqgq9qzsjl67z0tq9zhhfp6d59wdnq4l355ky2q7wupcmxc2kx8483tp6kkznr0kchcs9y0eka782s9l5sp63vnrkqcjrur0jy4jwjyajwa6qpe9f275')
    return data

