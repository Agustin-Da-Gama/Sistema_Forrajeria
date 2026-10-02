import sqlite3

def incializar_bd():
    conexion = sqlite3.connect("forrajeria.db")
    cursor = conexion.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
#Es buena práctica habilitar el soporte para claves foráneas en SQLite


#1. TABLAS FUERTES (No tienen claves foráneas)
    cursor.execute('''
    CREATE TABLE CATEGORIA (
        ID_Categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre_Categoria TEXT NOT NULL
    )
''')

    cursor.execute('''
        CREATE TABLE PROVEEDOR (
            ID_Proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre_Proveedor TEXT NOT NULL
)
''')

    cursor.execute('''
    CREATE TABLE USUARIO (
        ID_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre_Usuario TEXT NOT NULL,
        Contrasena TEXT NOT NULL,
        Rol TEXT NOT NULL
    )   
''')

    cursor.execute('''
    CREATE TABLE CLIENTE (
        ID_Cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre_Completo TEXT NOT NULL,
        Lista_Precios TEXT
    )
''')
#2. TABLAS DEPENDIENTES (Tienen claves foráneas)
    cursor.execute('''
    CREATE TABLE PRODUCTO (
        ID_Producto INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        Precio REAL NOT NULL,
        Stock_Actual INTEGER NOT NULL,
        Marca TEXT,
        ID_Categoria INTEGER,
        FOREIGN KEY (ID_Categoria) REFERENCES CATEGORIA(ID_Categoria)
)
''')

    cursor.execute('''
    CREATE TABLE COMPRA_MERCADERIA (
        ID_Compra INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha DATE NOT NULL,
        ID_Proveedor INTEGER,
    FOREIGN KEY (ID_Proveedor) REFERENCES PROVEEDOR(ID_Proveedor)
    )
''')

    cursor.execute('''
    CREATE TABLE VENTA (
        ID_Venta INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha_Hora DATETIME NOT NULL,
        Importe_Total REAL NOT NULL,
        ID_Usuario INTEGER,
        ID_Cliente INTEGER,
        FOREIGN KEY (ID_Usuario) REFERENCES USUARIO(ID_Usuario),
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE(ID_Cliente)
    )
''')
# 3. TABLA DE DETALLE (Depende de VENTA y PRODUCTO)

    cursor.execute('''
    CREATE TABLE DETALLE_VENTA (
        ID_Detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    Cantidad_Vendida INTEGER NOT NULL,
        Subtotal REAL NOT NULL,
        ID_Venta INTEGER,
        ID_Producto INTEGER,
        FOREIGN KEY (ID_Venta) REFERENCES VENTA(ID_Venta),
        FOREIGN KEY (ID_Producto) REFERENCES PRODUCTO(ID_Producto)
    )
''')

    conexion.commit()
    conexion.close()
    print("Base de datos creada exitosamente")

    # Ejecutamos la función
if __name__ == "__main__":
    incializar_bd()