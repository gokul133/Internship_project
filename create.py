import sqlite3

connection = sqlite3.connect("instance/data.db")
cursor = connection.cursor()

cursor.execute("INSERT INTO username VALUES('Gokul', '1234')")
cursor.execute("INSERT INTO username VALUES('qwerty', 'qwerty')")
cursor.execute("INSERT INTO username VALUES('nogod', '1234')")

connection.commit()