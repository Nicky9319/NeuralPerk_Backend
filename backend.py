import sqlite3


connection = sqlite3.connect('LoginCredentials.db')
cursor = connection.cursor()

email = 'djnwdw@gmail.com'
password = '21121'

credVal = (email, password)

cursor.execute("select * from customers")
d1 = cursor.fetchall()
print(len(d1))
print(d1)

print()

for tup in d1:
    if(tup == credVal):
        print("Found")

