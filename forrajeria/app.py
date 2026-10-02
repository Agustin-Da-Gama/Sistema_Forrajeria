from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from functools import wraps  #que es wraps?   es una funcion que permite envolver funciones
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# ---> NUEVO (SEGURIDAD): Llave secreta obligatoria para que Flask encripte las sesiones
app.secret_key = 'forrajeria_clave_super_secreta'
# =======================================================
# ---> NUEVO: OBLIGAR AL NAVEGADOR A NO GUARDAR CACHÉ
# =======================================================
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
# =======================================================

# Función para conectar a la base de datos en cada petición
def get_db_connection():
    # Asegúrate de haber ejecutado el script SQL que te pasé antes para crear este archivo
    conn = sqlite3.connect('forrajeria.db')
    # Esto permite acceder a las columnas por su nombre (ej: fila['Nombre'])
    conn.row_factory = sqlite3.Row 
    return conn

# =======================================================
# ---> NUEVO (SEGURIDAD): CREAMOS EL CANDADO
# =======================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si el usuario no tiene su ticket en la sesión...
        if 'usuario_id' not in session:
            # Lo pateamos a la pantalla de login
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
# =======================================================

# Ruta principal (Ejemplo: Login del sistema - RF01)
@app.route('/')
def index():
    return render_template('login.html')

# =======================================================
# ESTÁ ES LA RUTA PARA EL LOGIN
# =======================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        
        # 1. Buscamos SOLO por el nombre de usuario
        usuario = conn.execute('SELECT * FROM USUARIO WHERE Nombre_Usuario = ?', (username,)).fetchone()
        conn.close()
        
        # 2. Verificamos si el usuario existe Y si la contraseña coincide con el hash
        if usuario and check_password_hash(usuario['Contrasena'], password):
            session['usuario_id'] = usuario['ID_Usuario'] 
            return redirect(url_for('listar_productos'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos.")
    
    return render_template('login.html')

# =======================================================
#      RUTA PARA REGISTRAR NUEVO ADMINISTRADOR
# =======================================================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nuevo_usuario = request.form['username'].strip()
        nueva_password = request.form['password']
        confirmar_password = request.form['confirm_password']

        # 1. Verificamos que ambas contraseñas coincidan
        if nueva_password != confirmar_password:
            return render_template('registro.html', error="Las contraseñas no coinciden.")

        conn = get_db_connection()
        
        # Detectamos automáticamente los nombres de las columnas de tu tabla USUARIO
        columnas_info = conn.execute('PRAGMA table_info(USUARIO)').fetchall()
        nombres_col = [col[1] for col in columnas_info]
        col_usuario = nombres_col[1]
        col_password = nombres_col[2]

        # 2. Verificamos si el nombre de usuario ya existe
        usuario_existente = conn.execute(
            f'SELECT * FROM USUARIO WHERE {col_usuario} = ?', (nuevo_usuario,)
        ).fetchone()

        if usuario_existente:
            conn.close()
            return render_template('registro.html', error="Ese nombre de usuario ya está registrado.")

        # Generamos el hash de la contraseña de forma segura
        password_hasheada = generate_password_hash(nueva_password)

        # 3. Guardamos el nuevo administrador en la base de datos (USAMOS EL HASH)
        if len(nombres_col) == 3:
            conn.execute(
                f'INSERT INTO USUARIO ({col_usuario}, {col_password}) VALUES (?, ?)',
                (nuevo_usuario, password_hasheada)
            )
        elif len(nombres_col) >= 4:
            col_extra = nombres_col[3]
            conn.execute(
                f'INSERT INTO USUARIO ({col_usuario}, {col_password}, {col_extra}) VALUES (?, ?, ?)',
                (nuevo_usuario, password_hasheada, 'Administrador')
            )

        conn.commit()
        conn.close()

        # Redirigimos al login con un mensaje de éxito
        return render_template('login.html', exito="Administrador registrado con éxito. Ya podés iniciar sesión.")

    return render_template('registro.html')
# =======================================================


@app.route('/productos')
def listar_productos():
    # 1. Abrimos conexión
    conn = get_db_connection()
    
    # 2. Hacemos la consulta SQL a la tabla PRODUCTO
    productos = conn.execute('SELECT * FROM PRODUCTO').fetchall()
    
    # 3. Cerramos conexión
    conn.close()
    
    # 4. Enviamos los datos al archivo HTML llamado 'productos.html'
    return render_template('productos.html', productos=productos)

# =======================================================
#      AQUÍ ESTÁ LA RUTA DE VENTAS  (CARGA CLIENTES)
# =======================================================
@app.route('/registrar_venta', methods=['GET', 'POST'])
@login_required
def registrar_venta():
    conn = get_db_connection()
    
    if request.method == 'POST':
        id_cliente = request.form['id_cliente']
        ids_productos = request.form.getlist('id_producto[]')
        cantidades = request.form.getlist('cantidad[]')
        
        items_venta = []
        importe_total_venta = 0
        stock_acumulado = {}

        for id_prod, cant_str in zip(ids_productos, cantidades):
            cantidad = int(cant_str)
            stock_acumulado[id_prod] = stock_acumulado.get(id_prod, 0) + cantidad
            
            producto = conn.execute('SELECT * FROM PRODUCTO WHERE ID_Producto = ?', (id_prod,)).fetchone()
            
            if producto['Stock_Actual'] < stock_acumulado[id_prod]:
                error = f"Error: Stock insuficiente para '{producto['Nombre']}'. Solo quedan {producto['Stock_Actual']} unidades."
                productos_disponibles = conn.execute('SELECT * FROM PRODUCTO WHERE Stock_Actual > 0').fetchall()
                clientes = conn.execute('SELECT * FROM CLIENTE').fetchall()
                conn.close()
                return render_template('registrar_venta.html', productos=productos_disponibles, clientes=clientes, error=error)
            
            subtotal = producto['Precio'] * cantidad
            importe_total_venta += subtotal
            
            items_venta.append({
                'id_producto': id_prod,
                'nombre': producto['Nombre'],
                'precio': producto['Precio'],
                'cantidad': cantidad,
                'subtotal': subtotal
            })

        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO VENTA (Fecha_Hora, Importe_Total, ID_Usuario, ID_Cliente)
            VALUES (?, ?, 1, ?)
        ''', (fecha_hora_actual, importe_total_venta, id_cliente))
        
        id_nueva_venta = cursor.lastrowid 
        
        for item in items_venta:
            cursor.execute('''
                INSERT INTO DETALLE_VENTA (Cantidad_Vendida, Subtotal, ID_Venta, ID_Producto)
                VALUES (?, ?, ?, ?)
            ''', (item['cantidad'], item['subtotal'], id_nueva_venta, item['id_producto']))
            
            cursor.execute('''
                UPDATE PRODUCTO SET Stock_Actual = Stock_Actual - ? WHERE ID_Producto = ?
            ''', (item['cantidad'], item['id_producto']))

        # =========================================================================
        # ---> NUEVO (TICKET): Buscamos los datos del cliente para el comprobante
        # =========================================================================
        cliente = conn.execute('SELECT * FROM CLIENTE WHERE ID_Cliente = ?', (id_cliente,)).fetchone()
        
        conn.commit()
        conn.close()
        
        # ---> NUEVO (TICKET): Cargamos la pantalla del ticket en lugar de ir al inventario
        return render_template('ticket.html', 
                               id_venta=id_nueva_venta, 
                               fecha=fecha_hora_actual, 
                               items=items_venta, 
                               total=importe_total_venta, 
                               producto=producto, 
                               cantidad=cantidad, 
                               subtotal=subtotal, 
                               cliente=cliente)
        # =========================================================================
        
        return redirect(url_for('listar_productos'))

    else:
        productos_disponibles = conn.execute('SELECT * FROM PRODUCTO WHERE Stock_Actual > 0').fetchall()
        
        # ---> NUEVO: Cuando entramos a la pantalla por primera vez, buscamos a los clientes en la base de datos
        clientes = conn.execute('SELECT * FROM CLIENTE').fetchall()
        
        conn.close()
        
        # ---> NUEVO: Le enviamos la lista de "clientes" al HTML para que llene el menú desplegable
        return render_template('registrar_venta.html', productos=productos_disponibles, clientes=clientes)
#================================================================================================================

# =======================================================
#          NUEVA RUTA PARA AGREGAR PRODUCTOS
# =======================================================
@app.route('/nuevo_producto', methods=['GET', 'POST'])
def nuevo_producto():
    conn = get_db_connection()
    
    # Si el Administrador envía el formulario para guardar el producto
    if request.method == 'POST':
        nombre = request.form['nombre']
        marca = request.form['marca']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        id_categoria = request.form['id_categoria']
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO PRODUCTO (Nombre, Precio, Stock_Actual, Marca, ID_Categoria)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, precio, stock, marca, id_categoria))
        
        conn.commit()
        conn.close()
        
        # Lo devolvemos al panel de control para que vea su nuevo producto
        return redirect(url_for('listar_productos'))

    # Si solo está entrando a la pantalla para ver el formulario
    else:
        # Buscamos las categorías para mostrarlas en una lista desplegable
        categorias = conn.execute('SELECT * FROM CATEGORIA').fetchall()
        conn.close()
        return render_template('nuevo_producto.html', categorias=categorias)
# =======================================================


# =======================================================
#           RUTA PARA ELIMINAR PRODUCTOS
# =======================================================
@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscamos el producto por su ID y lo borramos de la base de datos
    cursor.execute('DELETE FROM PRODUCTO WHERE ID_Producto = ?', (id,))
    
    conn.commit()
    conn.close()
    
    # Recargamos la tabla de inventario
    return redirect(url_for('listar_productos'))
# =======================================================

# =======================================================
#                    EDITAR PRODUCTO 
# =======================================================
@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Si envían el formulario, actualizamos la base de datos
        nombre = request.form['nombre']
        marca = request.form['marca']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        id_categoria = request.form['id_categoria']
        
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE PRODUCTO 
            SET Nombre = ?, Precio = ?, Stock_Actual = ?, Marca = ?, ID_Categoria = ?
            WHERE ID_Producto = ?
        ''', (nombre, precio, stock, marca, id_categoria, id))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('listar_productos'))

    else:
        # Si entran por primera vez, buscamos los datos para llenar el formulario
        producto = conn.execute('SELECT * FROM PRODUCTO WHERE ID_Producto = ?', (id,)).fetchone()
        categorias = conn.execute('SELECT * FROM CATEGORIA').fetchall()
        conn.close()
        
        return render_template('editar_producto.html', producto=producto, categorias=categorias)
# =======================================================

# =======================================================
#                  REPORTE DE VENTAS
# =======================================================
@app.route('/reporte_ventas')
@login_required
def reporte_ventas():
    conn = get_db_connection()
    
    # Traemos las ventas junto con el nombre del cliente y el resumen de productos vendidos
    ventas = conn.execute('''
        SELECT 
            V.ID_Venta, 
            V.Fecha_Hora, 
            V.Importe_Total,
            C.Nombre_Completo AS Cliente,
            GROUP_CONCAT(D.Cantidad_Vendida || 'x ' || P.Nombre, ', ') AS Detalle_Productos
        FROM VENTA V
        LEFT JOIN CLIENTE C ON V.ID_Cliente = C.ID_Cliente
        LEFT JOIN DETALLE_VENTA D ON V.ID_Venta = D.ID_Venta
        LEFT JOIN PRODUCTO P ON D.ID_Producto = P.ID_Producto
        GROUP BY V.ID_Venta
        ORDER BY V.Fecha_Hora DESC
    ''').fetchall()
    
    ahora = datetime.now()
    hoy_str = ahora.strftime('%Y-%m-%d')
    inicio_semana = (ahora - timedelta(days=ahora.weekday())).strftime('%Y-%m-%d')
    mes_str = ahora.strftime('%Y-%m')
    anio_str = ahora.strftime('%Y')

    total_dia = 0
    total_semana = 0
    total_mes = 0
    total_anio = 0
    total_historico = 0

    for venta in ventas:
        fecha_venta = venta['Fecha_Hora']
        importe = venta['Importe_Total']
        total_historico += importe

        if fecha_venta.startswith(hoy_str):
            total_dia += importe
        if fecha_venta[:10] >= inicio_semana:
            total_semana += importe
        if fecha_venta.startswith(mes_str):
            total_mes += importe
        if fecha_venta.startswith(anio_str):
            total_anio += importe

    conn.close()
    
    return render_template('reporte_ventas.html', 
                           ventas=ventas,
                           total_dia=total_dia,
                           total_semana=total_semana,
                           total_mes=total_mes,
                           total_anio=total_anio,
                           total_historico=total_historico)


# ---> NUEVA RUTA: Permite abrir y reimprimir cualquier ticket desde el historial
@app.route('/ver_ticket/<int:id_venta>')
@login_required
def ver_ticket(id_venta):
    conn = get_db_connection()
    
    venta = conn.execute('SELECT * FROM VENTA WHERE ID_Venta = ?', (id_venta,)).fetchone()
    cliente = conn.execute('SELECT * FROM CLIENTE WHERE ID_Cliente = ?', (venta['ID_Cliente'],)).fetchone()
    
    detalles = conn.execute('''
        SELECT D.Cantidad_Vendida, D.Subtotal, P.Nombre, P.Precio
        FROM DETALLE_VENTA D
        JOIN PRODUCTO P ON D.ID_Producto = P.ID_Producto
        WHERE D.ID_Venta = ?
    ''', (id_venta,)).fetchall()
    
    items_venta = []
    for d in detalles:
        # Calculamos el precio unitario al que se vendió en ese momento
        precio_unitario = d['Subtotal'] / d['Cantidad_Vendida'] if d['Cantidad_Vendida'] else d['Precio']
        items_venta.append({
            'nombre': d['Nombre'],
            'precio': precio_unitario,
            'cantidad': d['Cantidad_Vendida'],
            'subtotal': d['Subtotal']
        })
        
    conn.close()
    
    return render_template('ticket.html',
                           id_venta=venta['ID_Venta'],
                           fecha=venta['Fecha_Hora'],
                           items=items_venta,
                           total=venta['Importe_Total'],
                           cliente=cliente)
# =======================================================

# =======================================================
#                 MÓDULO DE CLIENTES 
# =======================================================
@app.route('/clientes')
@login_required
def listar_clientes():
    conn = get_db_connection()
    clientes = conn.execute('SELECT * FROM CLIENTE').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/nuevo_cliente', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        lista_precios = request.form['lista_precios']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO CLIENTE (Nombre_Completo, Lista_Precios) VALUES (?, ?)', (nombre, lista_precios))
        conn.commit()
        conn.close()
        
        return redirect(url_for('listar_clientes'))
    
    return render_template('nuevo_cliente.html')

@app.route('/eliminar_cliente/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM CLIENTE WHERE ID_Cliente = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_clientes'))
# =======================================================
@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        lista_precios = request.form['lista_precios']
        
        conn.execute('''
            UPDATE CLIENTE 
            SET Nombre_Completo = ?, Lista_Precios = ?
            WHERE ID_Cliente = ?
        ''', (nombre, lista_precios, id))
        
        conn.commit()
        conn.close()
        return redirect(url_for('listar_clientes'))
    else:
        cliente = conn.execute('SELECT * FROM CLIENTE WHERE ID_Cliente = ?', (id,)).fetchone()
        conn.close()
        return render_template('editar_cliente.html', cliente=cliente)

# =======================================================
#           INGRESO DE MERCADERÍA (COMPRAS)
# =======================================================
@app.route('/ingreso_mercaderia', methods=['GET', 'POST'])
@login_required
def ingreso_mercaderia():
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Recibimos los datos del formulario
        id_producto = request.form['id_producto']
        cantidad_ingresada = int(request.form['cantidad'])
        
        # Le sumamos la cantidad nueva al stock que ya existe
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE PRODUCTO 
            SET Stock_Actual = Stock_Actual + ? 
            WHERE ID_Producto = ?
        ''', (cantidad_ingresada, id_producto))
        
        conn.commit()
        conn.close()
        
        # Volvemos al inventario para ver el stock actualizado
        return redirect(url_for('listar_productos'))
        
    else:
        # Buscamos todos los productos para mostrarlos en la lista desplegable
        productos = conn.execute('SELECT * FROM PRODUCTO ORDER BY Nombre').fetchall()
        conn.close()
        return render_template('ingreso_mercaderia.html', productos=productos)
#========================================================

# =======================================================
#                  MÓDULO DE CATEGORÍAS
# =======================================================
@app.route('/categorias')
@login_required
def listar_categorias():
    conn = get_db_connection()
    categorias = conn.execute('SELECT * FROM CATEGORIA').fetchall()
    conn.close()
    return render_template('categorias.html', categorias=categorias)

@app.route('/nueva_categoria', methods=['GET', 'POST'])
@login_required
def nueva_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre']
        
        conn = get_db_connection()
        # Solo insertamos el Nombre_Categoria
        conn.execute('INSERT INTO CATEGORIA (Nombre_Categoria) VALUES (?)', (nombre,))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_categorias'))
        
    return render_template('nueva_categoria.html')

@app.route('/editar_categoria/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    conn = get_db_connection()
    if request.method == 'POST':
        nombre = request.form['nombre']
        
        conn.execute('UPDATE CATEGORIA SET Nombre_Categoria = ? WHERE ID_Categoria = ?', (nombre, id))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_categorias'))
    else:
        categoria = conn.execute('SELECT * FROM CATEGORIA WHERE ID_Categoria = ?', (id,)).fetchone()
        conn.close()
        return render_template('editar_categoria.html', categoria=categoria)

@app.route('/eliminar_categoria/<int:id>', methods=['POST'])
@login_required
def eliminar_categoria(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM CATEGORIA WHERE ID_Categoria = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_categorias'))
# =======================================================


# =======================================================
#        RUTA NUEVA PARA SALIR (CERRAR SESIÓN)
# =======================================================
@app.route('/logout')
def logout():
    # Por ahora simplemente redirige al login
    return redirect(url_for('index'))
# =======================================================

if __name__ == '__main__':
    # debug=True hace que el servidor se reinicie solo si detecta cambios en el código
    app.run(debug=True, port=5000)