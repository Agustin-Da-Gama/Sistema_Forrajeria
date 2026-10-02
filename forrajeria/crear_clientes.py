import sqlite3

conn = sqlite3.connect('forrajeria.db')
cursor = conn.cursor()

# Insertamos clientes usando solo las columnas que existen en tu tabla
clientes = [
    ('Consumidor Final', 'Minorista'),
    ('Juan Pérez', 'Mayorista')
]

cursor.executemany('''
    INSERT INTO CLIENTE (Nombre_Completo, Lista_Precios)
    VALUES (?, ?)
''', clientes)

conn.commit()
conn.close()

print("¡Clientes de prueba cargados con éxito!")