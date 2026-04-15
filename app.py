from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave123"

# Carpeta de uploads
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ✅ BASE DE DATOS (UNA SOLA RUTA FIJA)
def get_db_path():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, "darfum.db")


# Crear base de datos si no existe
def init_db():

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abonos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    monto REAL,
    fecha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ajustes_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,  -- ingreso / egreso
    monto REAL,
    motivo TEXT,
    fecha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,   -- ingreso / egreso / ajuste
    monto REAL,
    descripcion TEXT,
    fecha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia TEXT,
        nombre TEXT,
        cantidad INTEGER,
        costo REAL,
        total REAL,
        fecha TEXT
    )
    """)

    # TABLA GASTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT,
        monto REAL,
        fecha TEXT,
        categoria TEXT
    )
    """)

    # TABLA COMPRAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT,
        cantidad INTEGER,
        costo REAL,
        total REAL,
        fecha TEXT
    )
    """)

    # TABLA ABONOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abonos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        monto REAL,
        fecha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        celular TEXT,
        cedula TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        cliente TEXT,
        total REAL,
        tipo_venta TEXT,
        metodo_pago TEXT,
        fecha_limite TEXT,
        cuotas INTEGER
    )
    """)

    cursor.execute("UPDATE ventas SET metodo_pago = 'efectivo' WHERE metodo_pago IS NULL")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto_id INTEGER,
        referencia TEXT,
        producto TEXT,
        precio REAL,
        cantidad INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula TEXT UNIQUE,
        nombre TEXT,
        telefono TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    tipo TEXT,
    cantidad INTEGER,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    rol TEXT
    )
    """)

    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    admin = cursor.fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol)
            VALUES (?, ?, ?)
        """, ("admin", "1234", "admin"))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia TEXT UNIQUE,
        nombre TEXT,
        precio REAL,
        precio_compra REAL,
        stock INTEGER,
        categoria TEXT,
        genero TEXT,
        imagen TEXT
    )
    """)

    # 🔥 AGREGAR COLUMNA SI NO EXISTE
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN precio_compra REAL")
    except:
        pass

    # 🔥 ESTE ES EL PASO 7 (AQUÍ 👇)
    cursor.execute("UPDATE productos SET precio_compra = 0 WHERE precio_compra IS NULL")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        cantidad INTEGER,
        total REAL
    )
    """)

        # 🧠 AGREGAR COLUMNA metodo_pago SI NO EXISTE
    try:
        cursor.execute("ALTER TABLE abonos ADD COLUMN metodo_pago TEXT")
    except:
        pass

        # 🔥 agregar metodo_pago a ventas
    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE caja ADD COLUMN metodo_pago TEXT")
    except:
        pass

        

    conn.commit()
    conn.close()

init_db()

@app.route("/cierres")
def cierres():
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    hoy = datetime.now().strftime("%Y-%m-%d")

    # 📅 HOY
    cursor.execute("""
    SELECT SUM(total) FROM ventas
    WHERE DATE(fecha) = DATE('now')
    """)
    hoy_total = cursor.fetchone()[0] or 0

    # 📆 ESTA SEMANA
    cursor.execute("""
    SELECT SUM(total) FROM ventas
    WHERE strftime('%W', fecha) = strftime('%W', 'now')
    """)
    semana_total = cursor.fetchone()[0] or 0

    # 📅 ESTE MES
    cursor.execute("""
    SELECT SUM(total) FROM ventas
    WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
    """)
    mes_total = cursor.fetchone()[0] or 0

    # 📅 ESTE AÑO
    cursor.execute("""
    SELECT SUM(total) FROM ventas
    WHERE strftime('%Y', fecha) = strftime('%Y', 'now')
    """)
    año_total = cursor.fetchone()[0] or 0

    fecha = request.args.get("fecha")

    cursor.execute("""
    SELECT SUM(total) FROM ventas
    WHERE DATE(fecha) = ?
    """, (fecha,))

    conn.close()

    return render_template(
        "cierres.html",
        hoy=hoy_total,
        semana=semana_total,
        mes=mes_total,
        año=año_total
    )

@app.route("/buscar_producto/<ref>")
def buscar_producto(ref):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, categoria, genero
        FROM productos
        WHERE referencia = ?
    """, (ref,))

    producto = cursor.fetchone()
    conn.close()

    if producto:
        return {
            "existe": True,
            "nombre": producto[0],
            "categoria": producto[1],
            "genero": producto[2]
        }
    else:
        return {"existe": False}

@app.route("/eliminar_compra/<int:id>", methods=["POST"])
def eliminar_compra(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 🔥 1. Obtener productos de la compra
    cursor.execute("""
        SELECT referencia, cantidad
        FROM detalle_compras
        WHERE compra_id = ?
    """, (id,))
    productos = cursor.fetchall()

    # 🔥 2. Restar stock
    for ref, cantidad in productos:
        cursor.execute("""
            UPDATE productos
            SET stock = stock - ?
            WHERE referencia = ?
        """, (cantidad, ref))

    # 🔥 3. Eliminar detalle
    cursor.execute("DELETE FROM detalle_compras WHERE compra_id = ?", (id,))

    # 🔥 4. Eliminar compra
    cursor.execute("DELETE FROM compras WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/compras")

@app.route("/detalle_compra/<int:id>")
def detalle_compra(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compras WHERE id=?", (id,))
    compra = cursor.fetchone()

    cursor.execute("SELECT * FROM detalle_compras WHERE compra_id=?", (id,))
    productos = cursor.fetchall()

    conn.close()

    return render_template("detalle_compra.html", compra=compra, productos=productos)

@app.route("/abonar", methods=["POST"])
def abonar():
    cliente = request.form["cliente"]
    monto = request.form["monto"]

    # 👇 ESTA ES LA LÍNEA NUEVA
    metodo_pago = request.form.get("metodo_pago", "efectivo")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO abonos (cliente, monto, fecha, metodo_pago)
        VALUES (?, ?, datetime('now'), ?)
    """, (cliente, monto, metodo_pago))

    conn.commit()
    conn.close()

    return redirect("/cxc")

@app.route("/historial_abonos/<cliente>")
def historial_abonos(cliente):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 🔥 traer abonos del cliente
    cursor.execute("""
        SELECT monto, fecha
        FROM abonos
        WHERE cliente = ?
        ORDER BY id DESC
    """, (cliente,))

    abonos = cursor.fetchall()

    conn.close()

    return render_template("historial_abonos.html", cliente=cliente, abonos=abonos)
    

@app.route("/agregar_abono", methods=["POST"])
def agregar_abono():

    cliente = request.form["cliente"]
    monto = float(request.form["monto"])
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO abonos (cliente, monto, fecha)
        VALUES (?, ?, ?)
    """, (cliente, monto, fecha))

    conn.commit()
    conn.close()

    return redirect ("/cxc")

@app.route("/cxc")
def cuentas_por_cobrar():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 🔥 TRAER VENTAS A CRÉDITO
    cursor.execute("""
        SELECT cliente, SUM(total)
        FROM ventas
        WHERE tipo_venta LIKE '%credito%'
        GROUP BY cliente
    """)
    ventas = cursor.fetchall()

    # 🔥 TRAER ABONOS
    cursor.execute("""
        SELECT cliente, SUM(monto)
        FROM abonos
        GROUP BY cliente
    """)
    abonos = cursor.fetchall()

    conn.close()

    datos = []

    for v in ventas:
        cliente = v[0]
        total_venta = v[1] or 0

        # 🔥 buscar abonos del cliente
        total_abono = 0
        for a in abonos:
            if a[0] == cliente:
                total_abono = a[1] or 0

        deuda = total_venta - total_abono

        datos.append({
            "cliente": cliente,
            "venta": total_venta,
            "abono": total_abono,
            "deuda": deuda,
            "dias": 0,
            "estado": "🟢 Pendiente" if deuda > 0 else "✅ Pagado"
        })

    return render_template("cxc.html", datos=datos)

@app.route("/reportes")
def reportes():

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # VENTAS
    cursor.execute("SELECT SUM(total) FROM ventas")
    ventas = cursor.fetchone()[0] or 0

    # GASTOS
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos = cursor.fetchone()[0] or 0

    # COMPRAS
    cursor.execute("SELECT SUM(total) FROM compras")
    compras = cursor.fetchone()[0] or 0

    # ABONOS
    cursor.execute("SELECT SUM(monto) FROM abonos")
    abonos = cursor.fetchone()[0] or 0

    # GANANCIA
    ganancia = ventas - gastos - compras

    conn.close()

    return render_template(
        "contabilidad.html",
        ventas=ventas_contado,
        credito=cuentas_por_cobrar,
        abonos=abonos,
        gastos=gastos,
        caja=caja,
        ganancia=ganancia,
    )

@app.route("/agregar_ajuste", methods=["POST"])
def agregar_ajuste():

    tipo = request.form["tipo"]
    monto = float(request.form["monto"])
    motivo = request.form["motivo"]

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ajustes_caja (tipo, monto, motivo, fecha)
        VALUES (?, ?, ?, ?)
    """, (tipo, monto, motivo, fecha))

    conn.commit()
    conn.close()

    return redirect("/ajustes")

@app.route("/ajustes")
def ver_ajustes():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ajustes_caja ORDER BY id DESC")
    ajustes = cursor.fetchall()

    conn.close()

    return render_template("ajustes.html", ajustes=ajustes)

@app.route("/caja")
def caja():

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # INGRESOS
    cursor.execute("SELECT SUM(total) FROM ventas")
    ventas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM abonos")
    abonos = cursor.fetchone()[0] or 0

    ingresos = ventas + abonos

    # EGRESOS
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM compras")
    compras = cursor.fetchone()[0] or 0

    egresos = gastos + compras

    # 🔥 AJUSTES
    cursor.execute("SELECT SUM(monto) FROM ajustes_caja WHERE tipo='ingreso'")
    ajustes_ingreso = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM ajustes_caja WHERE tipo='egreso'")
    ajustes_egreso = cursor.fetchone()[0] or 0

    # 💥 TOTAL FINAL
    total = ingresos - egresos + ajustes_ingreso - ajustes_egreso

    conn.close()

    return render_template("caja.html",
        ingresos=ingresos,
        egresos=egresos,
        total=total
    )

@app.route("/compras")
def compras():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compras ORDER BY id DESC")
    compras = cursor.fetchall()

    conn.close()

    return render_template("compras.html", compras=compras)

@app.route("/agregar_compra", methods=["POST"])
def agregar_compra():
    try:
        import sqlite3
        from datetime import datetime
        from flask import request, redirect

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # 🔹 DATOS PRINCIPALES
        factura = request.form.get("factura")
        metodo_pago = request.form.get("metodo_pago")
        print("METODO RECIBIDO:", metodo_pago)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        referencias = request.form.getlist("referencia[]")
        nombres = request.form.getlist("nombre[]")
        cantidades = request.form.getlist("cantidad[]")
        costos = request.form.getlist("costo[]")
        categorias = request.form.getlist("categoria[]")
        generos = request.form.getlist("genero[]")

        total_factura = 0

        # 🔥 1. CALCULAR TOTAL
        for i in range(len(referencias)):
            cantidad = int(cantidades[i] or 0)
            costo = float(costos[i] or 0)
            total_factura += cantidad * costo

        # 🔥 2. GUARDAR COMPRA
        cursor.execute("""
            INSERT INTO compras (factura, metodo_pago, total, fecha)
            VALUES (?, ?, ?, ?)
        """, (factura, metodo_pago, total_factura, fecha))

        compra_id = cursor.lastrowid

        # 🔥 3. RECORRER PRODUCTOS
        for i in range(len(referencias)):
            ref = referencias[i]
            nombre = nombres[i]
            cantidad = int(cantidades[i] or 0)
            costo = float(costos[i] or 0)
            categoria = categorias[i]
            genero = generos[i]

            # 🔍 BUSCAR PRODUCTO
            cursor.execute("SELECT id, stock FROM productos WHERE referencia = ?", (ref,))
            producto = cursor.fetchone()

            if producto:
                nuevo_stock = producto[1] + cantidad

                cursor.execute("""
                    UPDATE productos
                    SET stock = ?, precio_compra = ?
                    WHERE id = ?
                """, (nuevo_stock, costo, producto[0]))

            else:
                precio = redondear_mil(costo * 1.3)

                cursor.execute("""
                    INSERT INTO productos
                    (referencia, nombre, precio, precio_compra, stock, categoria, genero, imagen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (ref, nombre or "Producto nuevo", precio, costo, cantidad, categoria, genero, ""))

            # 🔥 4. GUARDAR DETALLE
            cursor.execute("""
                INSERT INTO detalle_compras (compra_id, referencia, nombre, cantidad, costo)
                VALUES (?, ?, ?, ?, ?)
            """, (compra_id, ref, nombre, cantidad, costo))

        # 🔥 5. REGISTRAR EN CAJA
        cursor.execute("""
            INSERT INTO caja (tipo, monto, descripcion, fecha)
            VALUES (?, ?, ?, ?)
        """, (
            "egreso",
            total_factura,
            f"Compra factura #{factura} - {metodo_pago}",
            fecha
        ))

        conn.commit()
        conn.close()

        return redirect("/compras")

    except Exception as e:
        print("ERROR:", e)
        return "Error al guardar compra"

@app.route("/eliminar_gasto/<int:id>", methods=["POST"])
def eliminar_gasto(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("DELETE FROM gastos WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/gastos")

@app.route("/gastos")
def ver_gastos():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM gastos ORDER BY id DESC")
    gastos = cursor.fetchall()

    conn.close()

    return render_template("gastos.html", gastos=gastos)

from datetime import datetime

@app.route("/agregar_gasto", methods=["POST"])
def agregar_gasto():
    try:
        descripcion = request.form.get("descripcion")
        monto = float(request.form.get("monto"))
        fecha = request.form.get("fecha")
        categoria = request.form.get("categoria")
        metodo_pago = request.form.get("metodo_pago")

        print("DEBUG ↓↓↓")
        print("descripcion:", descripcion)
        print("monto:", monto)
        print("fecha:", fecha)
        print("categoria:", categoria)
        print("metodo_pago:", metodo_pago)

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # ✅ GUARDAR GASTO (AQUÍ ESTÁ LA CLAVE)
        cursor.execute("""
        INSERT INTO gastos (descripcion, monto, fecha, categoria, metodo_pago)
        VALUES (?, ?, ?, ?, ?)
        """, (descripcion, monto, fecha, categoria, metodo_pago))

        conn.commit()
        conn.close()

        return redirect("/contabilidad")

    except Exception as e:
        print("ERROR:", e)
        return "Error al guardar gasto"

@app.route("/contabilidad")
def contabilidad():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 💰 VENTAS CONTADO (EFECTIVO)
    cursor.execute("""
    SELECT SUM(total)
    FROM ventas
    WHERE LOWER(tipo_venta) = 'contado'
    AND LOWER(metodo_pago) = 'efectivo'
    """)
    ventas_efectivo = cursor.fetchone()[0] or 0

    # 🏦 VENTAS TRANSFERENCIA
    cursor.execute("""
    SELECT SUM(total)
    FROM ventas
    WHERE LOWER(tipo_venta) = 'contado'
    AND LOWER(metodo_pago) = 'transferencia'
    """)
    ventas_banco = cursor.fetchone()[0] or 0

    # 💳 VENTAS CRÉDITO
    cursor.execute("""
    SELECT SUM(total)
    FROM ventas
    WHERE LOWER(tipo_venta) = 'credito'
    """)
    ventas_credito = cursor.fetchone()[0] or 0

    # 💵 ABONOS EFECTIVO
    cursor.execute("""
    SELECT SUM(monto)
    FROM abonos
    WHERE LOWER(metodo_pago) = 'efectivo'
    """)
    abonos_efectivo = cursor.fetchone()[0] or 0

    # 🏦 ABONOS TRANSFERENCIA
    cursor.execute("""
    SELECT SUM(monto)
    FROM abonos
    WHERE LOWER(metodo_pago) = 'transferencia'
    """)
    abonos_banco = cursor.fetchone()[0] or 0

    # 📊 TOTAL ABONOS
    cursor.execute("SELECT SUM(monto) FROM abonos")
    abonos = cursor.fetchone()[0] or 0

    # 📦 COMPRAS (ANTES GASTOS)

    # 💸 COMPRAS EFECTIVO
    cursor.execute("""
    SELECT SUM(total)
    FROM compras
    WHERE LOWER(metodo_pago) = 'efectivo'
    """)
    gasto_efectivo = cursor.fetchone()[0] or 0

    # 🏦 COMPRAS TRANSFERENCIA
    cursor.execute("""
    SELECT SUM(total)
    FROM compras
    WHERE LOWER(metodo_pago) = 'transferencia'
    """)
    gasto_banco = cursor.fetchone()[0] or 0

    # 📊 TOTAL COMPRAS
    cursor.execute("SELECT SUM(total) FROM compras")
    gastos = cursor.fetchone()[0] or 0

    # 📉 CUENTAS POR COBRAR
    cuentas_por_cobrar = max(0, ventas_credito - abonos)

    # 💵 CAJA (EFECTIVO)
    efectivo = ventas_efectivo + abonos_efectivo - gasto_efectivo

    # 🏦 BANCO
    bancos = ventas_banco + abonos_banco - gasto_banco

    # 📈 GANANCIA
    cursor.execute("""
    SELECT d.precio, d.cantidad, p.precio_compra
    FROM detalle_ventas d
    JOIN productos p ON d.producto_id = p.id
    """)
    datos = cursor.fetchall()

    ganancia = 0
    for precio, cantidad, costo in datos:
        precio = precio or 0
        cantidad = cantidad or 0
        costo = costo or 0
        ganancia += (precio - costo) * cantidad

    conn.close()

    # 🧾 CAJA FINAL
    caja = efectivo + bancos

    return render_template(
        "contabilidad.html",
        ventas=ventas_efectivo + ventas_banco,
        credito=cuentas_por_cobrar,
        abonos=abonos,
        gastos=gastos,
        caja=caja,
        ganancia=ganancia,
        efectivo=efectivo,
        bancos=bancos
    )

@app.route("/clientes")
def clientes():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, celular, cedula FROM clientes")
    clientes = cursor.fetchall()

    conn.close()

    return render_template("clientes.html", clientes=clientes)

@app.route("/editar_venta/<int:id>", methods=["POST"])
def editar_venta(id):
    data = request.json

    for v in ventas:
        if v["id"] == id:
            v["cliente"] = data.get("cliente", v["cliente"])
            v["tipo"] = data.get("tipo_venta", v["tipo"])
            v["metodo"] = data.get("metodo_pago", v["metodo"])

    return jsonify({"ok": True})

@app.route("/eliminar_venta/<int:id>", methods=["POST"])
def eliminar_venta(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 🔥 1. OBTENER DETALLE DE LA VENTA
    cursor.execute("""
        SELECT producto, cantidad
        FROM detalle_ventas
        WHERE venta_id = ?
    """, (id,))
    
    detalles = cursor.fetchall()

    # 🔥 2. DEVOLVER STOCK
    for producto, cantidad in detalles:

        cursor.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE nombre = ?
        """, (cantidad, producto))

    # 🔥 3. BORRAR DETALLE
    cursor.execute("DELETE FROM detalle_ventas WHERE venta_id = ?", (id,))

    # 🔥 4. BORRAR VENTA
    cursor.execute("DELETE FROM ventas WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/historial")

@app.route("/historial")
def historial():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    fecha = request.args.get("fecha")

    # 🔍 FILTRO POR FECHA
    if fecha:
        cursor.execute("""
            SELECT
                v.id,
                v.fecha,
                v.cliente,
                v.total,
                v.tipo_venta,
                v.metodo_pago
            FROM ventas v
            WHERE DATE(v.fecha) = ?
            ORDER BY v.id DESC
        """, (fecha,))
    else:
        cursor.execute("""
            SELECT
                v.id,
                v.fecha,
                v.cliente,
                v.total,
                v.tipo_venta,
                v.metodo_pago
            FROM ventas v
            ORDER BY v.id DESC
        """)

    ventas = cursor.fetchall()

    # 💰 TOTAL (CIERRE)
    if fecha:
        cursor.execute("""
            SELECT SUM(total) FROM ventas
            WHERE DATE(fecha) = ?
        """, (fecha,))
    else:
        cursor.execute("""
            SELECT SUM(total) FROM ventas
            WHERE DATE(fecha) = DATE('now')
        """)

    total_dia = cursor.fetchone()[0] or 0

    conn.close()

    return render_template(
        "historial.html",
        ventas=ventas,
        total_dia=total_dia,
        fecha=fecha
    )

@app.route("/guardar_venta", methods=["POST"])
def guardar_venta():
    try:
        from datetime import datetime
        import sqlite3

        data = request.get_json()

        # 🔹 fecha actual
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🔹 datos principales
        carrito = data.get("carrito", [])
        cliente = data.get("cliente", "Cliente general")
        total = data.get("total", 0)
        tipo_venta = str(data.get("tipo_venta", "contado")).lower()
        metodo_pago = data.get("metodo_pago", "efectivo")

        fecha_limite = data.get("fecha_limite")
        cuotas = data.get("cuotas")

        # 🔹 si NO es crédito → limpiar
        if tipo_venta != "credito":
            fecha_limite = None
            cuotas = None

        # 🔹 conexión segura
        conn = sqlite3.connect(get_db_path(), timeout=10)
        cursor = conn.cursor()

        # 🔹 guardar cliente si no existe
        cursor.execute(
            "INSERT OR IGNORE INTO clientes (nombre) VALUES (?)",
            (cliente,)
        )

        # 🔹 insertar venta
        cursor.execute("""
            INSERT INTO ventas (
                fecha, cliente, total,
                tipo_venta, metodo_pago,
                fecha_limite, cuotas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha, cliente, total,
            tipo_venta, metodo_pago,
            fecha_limite, cuotas
        ))

        venta_id = cursor.lastrowid

        # 🔹 recorrer carrito
        for item in carrito:
            producto_id = item.get("id")
            referencia = item.get("referencia")
            nombre = item.get("nombre")
            precio = item.get("precio", 0)
            cantidad = item.get("cantidad", 0)

            # 🔹 guardar detalle
            cursor.execute("""
            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio)
            VALUES (?, ?, ?, ?)
            """, (
                venta_id,
                item["id"],
                item["cantidad"],
                item["precio"]  # ESTE DEBE SER PRECIO DE VENTA
            ))

            # 🔹 descontar stock
            cursor.execute("""
                UPDATE productos
                SET stock = stock - ?
                WHERE id = ?
            """, (cantidad, producto_id))

        # 🔹 guardar cambios
        conn.commit()
        conn.close()

        return jsonify({"ok": True})

    except Exception as e:
        print("ERROR REAL:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/buscar_cliente/<dato>")
def buscar_cliente(dato):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, celular, cedula 
        FROM clientes 
        WHERE cedula = ? OR celular = ?
    """, (dato, dato))

    cliente = cursor.fetchone()
    conn.close()

    if cliente:
        return {
            "encontrado": True,
            "nombre": cliente[0],
            "celular": cliente[1]
        }
    else:
        return {"encontrado": False}

@app.route("/crear_cliente", methods=["POST"])
def crear_cliente():
    try:
        data = request.json

        cedula = data.get("cedula")
        nombre = data.get("nombre")
        celular = data.get("celular")

        print("DEBUG:", cedula, nombre, celular)

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clientes (cedula, nombre, celular)
            VALUES (?, ?, ?)
        """, (cedula, nombre, celular))

        conn.commit()
        conn.close()

        return jsonify({"ok": True})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"ok": False, "error": str(e)})

@app.route("/movimientos")
def ver_movimientos():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    SELECT p.nombre, m.tipo, m.cantidad, m.fecha
    FROM movimientos m
    JOIN productos p ON m.producto_id = p.id
    ORDER BY m.fecha DESC
    """)

    movimientos = cursor.fetchall()
    conn.close()

    return render_template("movimientos.html", movimientos=movimientos)

@app.route("/editar_producto/<int:id>", methods=["GET", "POST"])
def editar_producto(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    if request.method == "POST":
        referencia = request.form.get("referencia")
        nombre = request.form.get("nombre")
        precio = float(request.form.get("venta") or 0)
        stock = request.form.get("stock")
        categoria = request.form.get("categoria")
        genero = request.form.get("genero")

        imagen = request.files.get("imagen")

        # Obtener imagen actual
        cursor.execute("SELECT imagen FROM productos WHERE id=?", (id,))
        imagen_actual = cursor.fetchone()[0]

    imagen = request.files.get("imagen")

    nombre_imagen = None

    if imagen and imagen.filename != "":
        # nombre seguro
        nombre_original = secure_filename(imagen.filename)

        # nombre único (IMPORTANTE 🔥)
        nombre_imagen = str(datetime.now().timestamp()).replace(".", "") + "_" + nombre_original

        ruta = os.path.join("static/uploads", nombre_imagen)
        imagen.save(ruta)

        # 🔹 1. Obtener stock anterior
        cursor.execute("SELECT stock FROM productos WHERE id=?", (id,))
        stock_anterior = cursor.fetchone()[0]

        # 🔹 2. Obtener nuevos datos del formulario
        referencia = request.form.get("referencia")
        nombre = request.form.get("nombre")
        precio = request.form.get("venta") or request.form.get("compra")
        stock = request.form.get("stock")
        categoria = request.form.get("categoria")
        genero = request.form.get("genero")

        # 🔹 3. UPDATE producto
        cursor.execute("""
        UPDATE productos
        SET referencia=?, nombre=?, precio=?, stock=?, categoria=?, genero=?, imagen=?
        WHERE id=?
        """, (referencia, nombre, precio, stock, categoria, genero, nombre_imagen, id))

        # 🔹 4. CALCULAR diferencia (🔥 AQUÍ ESTABA TU ERROR)
        diferencia = int(stock) - int(stock_anterior)

        # 🔹 5. Guardar movimiento
        if diferencia != 0:
            tipo = "entrada" if diferencia > 0 else "salida"

            cursor.execute("""
            INSERT INTO movimientos (producto_id, tipo, cantidad)
            VALUES (?, ?, ?)
            """, (id, tipo, abs(diferencia)))

        conn.commit()
        conn.close()

        return redirect("/")

    # GET → cargar datos
    cursor.execute("SELECT * FROM productos WHERE id=?", (id,))
    producto = cursor.fetchone()
    conn.close()

    return render_template("editar_producto.html", p=producto)

@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")
    
@app.route("/usuarios")
def usuarios():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, rol FROM usuarios")
    lista = cursor.fetchall()

    conn.close()
    return render_template("usuarios.html", usuarios=lista)

@app.route("/nuevo_producto")
def nuevo_producto():
    return render_template("nuevo_producto.html")

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/usuarios")

@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        rol = request.form["rol"]

        cursor.execute("""
            UPDATE usuarios 
            SET username=?, password=?, rol=? 
            WHERE id=?
        """, (username, password, rol, id))

        conn.commit()
        conn.close()
        return redirect("/usuarios")

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cursor.fetchone()
    conn.close()

    return render_template("editar_usuario.html", usuario=usuario)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    if session.get("rol") != "admin":
        return "No tienes permiso"

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        rol = request.form["rol"]

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO usuarios (username, password, rol)
        VALUES (?, ?, ?)
        """, (username, password, rol))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("crear_usuario.html")    

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if not usuario or not password:
            return "Faltan datos"

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?",
            (usuario, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario"] = usuario
            return redirect("/")
        else:
            return "Credenciales incorrectas"

    return render_template("login.html")

@app.route("/guardar_producto", methods=["POST"])
def guardar_producto():
    import os

    # 📦 datos
    referencia = request.form.get("referencia")
    nombre = request.form.get("nombre")
    compra = float(request.form.get("compra") or 0)

    # 🔥 ESTE ES EL CAMBIO CLAVE
    venta = float(request.form.get("venta") or 0)

    stock = int(request.form.get("stock") or 0)
    categoria = request.form.get("categoria")
    genero = request.form.get("genero")

    # 🖼️ imagen
    imagen_file = request.files.get("imagen")
    nombre_imagen = "default.png"

    if imagen_file and imagen_file.filename != "":
        nombre_imagen = imagen_file.filename
        ruta = os.path.join("static/uploads", nombre_imagen)
        imagen_file.save(ruta)

    # 💾 guardar en BD
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO productos
        (referencia, nombre, precio_compra, precio, stock, categoria, genero, imagen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            referencia,
            nombre,
            compra,
            venta,
            stock,
            categoria,
            genero,
            nombre_imagen
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return "❌ Ya existe un producto con esa referencia"

    conn.close()
    return redirect("/")

@app.route("/ventas")
def vista_ventas():
    if "usuario" not in session:
        return redirect("/login")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 🔥 IMPORTANTE: ORDEN CONTROLADO
    cursor.execute("""
        SELECT id, referencia, nombre, precio, stock, imagen
        FROM productos
    """)
    productos = cursor.fetchall()

    conn.close()

    return render_template("ventas.html", productos=productos)

@app.route("/vender", methods=["POST"])
def vender():
    producto_id = int(request.form["producto_id"])
    cantidad = int(request.form["cantidad"])

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtener precio y stock
    cursor.execute("SELECT venta, stock FROM productos WHERE id = ?", (producto_id,))
    resultado = cursor.fetchone()

    precio = resultado[0]
    stock_actual = resultado[1]

    # Validar stock
    if cantidad > stock_actual:
        return "No hay suficiente stock"

    total = precio * cantidad

    # Insertar venta
    cursor.execute(
        "INSERT INTO ventas (producto_id, cantidad, total) VALUES (?, ?, ?)",
        (producto_id, cantidad, total)
    )

    # 🔥 DESCONTAR STOCK
    nuevo_stock = stock_actual - cantidad
    cursor.execute(
        "UPDATE productos SET stock = ? WHERE id = ?",
        (nuevo_stock, producto_id)
    )

    conn.commit()
    conn.close()

    return redirect("/ventas")

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect("/login")

    return render_template("home.html")

@app.route("/")
def inicio():
    if "usuario" not in session:
        return redirect("/login")

    db_path = get_db_path()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    # 💰 TOTAL INVENTARIO
    cursor.execute("SELECT SUM(precio * stock) FROM productos")
    total = cursor.fetchone()[0] or 0

    conn.close()

    return render_template("index.html", productos=productos, total=total)

    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
