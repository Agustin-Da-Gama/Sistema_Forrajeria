import sqlite3

conn = sqlite3.connect('forrajeria.db')
cursor = conn.cursor()

# Insertamos un usuario administrador genérico
cursor.execute('''
    INSERT INTO USUARIO (Nombre_Usuario, Contrasena, Rol) 
    VALUES ('admin', '1234', 'Administrador')
''')

conn.commit()
conn.close()

print("¡Usuario 'admin' con contraseña '1234' creado con éxito!")