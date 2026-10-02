import sqlite3

# Nos conectamos a tu base de datos
conn = sqlite3.connect('forrajeria.db')
cursor = conn.cursor()

# Primero, insertamos un par de categorías para respetar las claves foráneas
cursor.execute("INSERT INTO CATEGORIA (Nombre_Categoria) VALUES ('Alimento Balanceado')")
cursor.execute("INSERT INTO CATEGORIA (Nombre_Categoria) VALUES ('Cereales y Granos')")

# Ahora, insertamos 3 productos de prueba típicos de forrajería
productos_prueba = [
    ('Alimento Perro Adulto 20kg', 15000.0, 10, 'Pedigree', 1),
    ('Maíz Quebrado x 50kg', 12000.0, 15, 'Granja Local', 2),
    ('Alimento Gato 3kg', 4500.0, 20, 'Whiskas', 1)
]

# Ejecutamos la inserción múltiple
cursor.executemany('''
    INSERT INTO PRODUCTO (Nombre, Precio, Stock_Actual, Marca, ID_Categoria) 
    VALUES (?, ?, ?, ?, ?)
''', productos_prueba)

# Guardamos los cambios y cerramos
conn.commit()
conn.close()

print("¡Productos de prueba cargados con éxito en la base de datos!")