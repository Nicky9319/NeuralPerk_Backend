import sqlite3


localconnection = sqlite3.connect('LoginCredentials.db')
cursor = localconnection.cursor()

cursor.execute("update users set balance = earned - payout where email = ?" , ('paarthsaxena2005@gmail.com',))
