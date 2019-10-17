amount = 6300000
max_amount = 1000000

dm = divmod(amount, max_amount)

inv_count = dm[0]
left = dm[1]

if left > 0:
    inv_count += 1


print('total invoices: ' + str(inv_count))

i = 1
while i <= inv_count:
    i += 1
    print(max_amount)
print(left)