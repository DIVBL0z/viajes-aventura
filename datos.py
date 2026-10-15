# datos.py
# Conexion, tablas y gestores de Viajes Aventura.
# Aqui vive todo el SQL. Los metodos no imprimen: devuelven True/False,
# un objeto o None, y guardan el detalle tecnico en ultimo_error.

import sqlite3
import hashlib
import hmac
import secrets
from datetime import date

from modelos import Destino, Paquete, Cliente, Administrador, Reserva

# Cuantas veces se repite el calculo del hash. Un numero alto hace que probar
# millones de claves sea lento para un atacante.
ITERACIONES = 200000


def hashear(clave, sal):
    # PBKDF2-HMAC-SHA256 (libreria oficial hashlib). La sal es distinta por
    # usuario: dos usuarios con la misma clave quedan con hashes distintos.
    return hashlib.pbkdf2_hmac(
        "sha256", clave.encode(), bytes.fromhex(sal), ITERACIONES).hex()


class BaseDeDatos:

    def __init__(self, ruta):
        self.ultimo_error = ""
        self.conexion = sqlite3.connect(ruta)
        # SQLite no revisa las FOREIGN KEY si no se le pide.
        self.conexion.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conexion.cursor()

    def crear_tablas(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS destinos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    pais TEXT NOT NULL,
                    dias INTEGER NOT NULL,
                    precio INTEGER NOT NULL
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS paquetes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    fecha_inicio TEXT NOT NULL,
                    fecha_termino TEXT NOT NULL,
                    cupos INTEGER NOT NULL
                )""")
            # Un paquete tiene muchos destinos y un destino puede estar en muchos
            # paquetes: por eso la relacion necesita su propia tabla.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS paquete_destinos (
                    id_paquete INTEGER NOT NULL,
                    id_destino INTEGER NOT NULL,
                    PRIMARY KEY (id_paquete, id_destino),
                    FOREIGN KEY (id_paquete) REFERENCES paquetes(id),
                    FOREIGN KEY (id_destino) REFERENCES destinos(id)
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    nombre_usuario TEXT NOT NULL UNIQUE,
                    rut TEXT,
                    hash TEXT NOT NULL,
                    sal TEXT NOT NULL,
                    rol TEXT NOT NULL
                )""")
            # UNIQUE impide que un cliente ocupe dos cupos del mismo paquete.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cliente INTEGER NOT NULL,
                    id_paquete INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    UNIQUE (id_cliente, id_paquete),
                    FOREIGN KEY (id_cliente) REFERENCES usuarios(id),
                    FOREIGN KEY (id_paquete) REFERENCES paquetes(id)
                )""")
            self.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.ultimo_error = str(error)
            return False

    def cerrar(self):
        self.conexion.close()


class GestorDestinos:

    def __init__(self, base):
        self.base = base

    def crear(self, destino):
        try:
            self.base.cursor.execute(
                "INSERT INTO destinos (nombre, pais, dias, precio) VALUES (?, ?, ?, ?)",
                (destino.nombre, destino.pais, destino.dias(), destino.precio()))
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return False

    def listar(self):
        try:
            self.base.cursor.execute("SELECT id, nombre, pais, dias, precio FROM destinos")
            destinos = []
            for fila in self.base.cursor.fetchall():
                destinos.append(Destino(fila[1], fila[2], fila[3], fila[4], fila[0]))
            return destinos
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def buscar(self, id_destino):
        try:
            self.base.cursor.execute(
                "SELECT id, nombre, pais, dias, precio FROM destinos WHERE id = ?", (id_destino,))
            fila = self.base.cursor.fetchone()
            if fila == None:
                return None
            return Destino(fila[1], fila[2], fila[3], fila[4], fila[0])
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def existe_nombre(self, nombre):
        try:
            self.base.cursor.execute("SELECT COUNT(*) FROM destinos WHERE nombre = ?", (nombre,))
            return self.base.cursor.fetchone()[0] > 0
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def modificar(self, destino):
        try:
            self.base.cursor.execute(
                "UPDATE destinos SET nombre = ?, pais = ?, dias = ?, precio = ? WHERE id = ?",
                (destino.nombre, destino.pais, destino.dias(), destino.precio(), destino.id))
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return False

    def cantidad_paquetes(self, id_destino):
        # Antes de eliminar un destino hay que saber si algun paquete lo usa.
        try:
            self.base.cursor.execute(
                "SELECT COUNT(*) FROM paquete_destinos WHERE id_destino = ?", (id_destino,))
            return self.base.cursor.fetchone()[0]
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def eliminar(self, id_destino):
        try:
            self.base.cursor.execute("DELETE FROM destinos WHERE id = ?", (id_destino,))
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return False


class GestorPaquetes:

    def __init__(self, base):
        self.base = base

    def _armar(self, fila):
        # Convierte una fila en un Paquete con sus destinos y sus reservas.
        paquete = Paquete(fila[1], fila[2], fila[3], fila[4], fila[0])
        self.base.cursor.execute("""
            SELECT destinos.id, destinos.nombre, destinos.pais, destinos.dias, destinos.precio
            FROM paquete_destinos
            JOIN destinos ON paquete_destinos.id_destino = destinos.id
            WHERE paquete_destinos.id_paquete = ?""", (paquete.id,))
        for d in self.base.cursor.fetchall():
            paquete.agregar_destino(Destino(d[1], d[2], d[3], d[4], d[0]))
        self.base.cursor.execute(
            "SELECT COUNT(*) FROM reservas WHERE id_paquete = ?", (paquete.id,))
        paquete.reservados = self.base.cursor.fetchone()[0]
        return paquete

    def crear(self, paquete):
        try:
            self.base.cursor.execute(
                "INSERT INTO paquetes (nombre, fecha_inicio, fecha_termino, cupos) VALUES (?, ?, ?, ?)",
                (paquete.nombre, paquete.fecha_inicio, paquete.fecha_termino, paquete.cupos))
            id_paquete = self.base.cursor.lastrowid
            for destino in paquete.destinos():
                self.base.cursor.execute(
                    "INSERT INTO paquete_destinos (id_paquete, id_destino) VALUES (?, ?)",
                    (id_paquete, destino.id))
            # Un solo commit al final: se guarda el paquete con todos sus
            # destinos, o no se guarda nada.
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.conexion.rollback()
            self.base.ultimo_error = str(error)
            return False

    def listar(self):
        try:
            self.base.cursor.execute(
                "SELECT id, nombre, fecha_inicio, fecha_termino, cupos FROM paquetes")
            paquetes = []
            for fila in self.base.cursor.fetchall():
                paquetes.append(self._armar(fila))
            return paquetes
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def buscar(self, id_paquete):
        try:
            self.base.cursor.execute(
                "SELECT id, nombre, fecha_inicio, fecha_termino, cupos FROM paquetes WHERE id = ?",
                (id_paquete,))
            fila = self.base.cursor.fetchone()
            if fila == None:
                return None
            return self._armar(fila)
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None


class GestorUsuarios:

    def __init__(self, base):
        self.base = base

    def registrar(self, usuario, clave):
        # Cada usuario recibe su propia sal, generada al azar.
        sal = secrets.token_hex(16)
        rut = None
        if usuario.rol() == "cliente":
            rut = usuario.rut
        try:
            self.base.cursor.execute(
                "INSERT INTO usuarios (nombre, nombre_usuario, rut, hash, sal, rol) VALUES (?, ?, ?, ?, ?, ?)",
                (usuario.nombre, usuario.nombre_usuario, rut, hashear(clave, sal), sal, usuario.rol()))
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return False

    def existe_usuario(self, nombre_usuario):
        try:
            self.base.cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
            return self.base.cursor.fetchone()[0] > 0
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def existe_administrador(self):
        try:
            self.base.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'administrador'")
            return self.base.cursor.fetchone()[0] > 0
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def autenticar(self, nombre_usuario, clave):
        # Devuelve el usuario si la clave es correcta; si no, devuelve None.
        try:
            self.base.cursor.execute(
                "SELECT id, nombre, nombre_usuario, rut, rol, hash, sal FROM usuarios WHERE nombre_usuario = ?",
                (nombre_usuario,))
            fila = self.base.cursor.fetchone()
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None
        if fila == None:
            return None
        # Se hashea la clave escrita con la sal guardada y se comparan los hashes:
        # la clave original nunca se guarda. compare_digest compara en tiempo
        # constante, para no filtrar informacion por el tiempo de respuesta.
        if not hmac.compare_digest(hashear(clave, fila[6]), fila[5]):
            return None
        if fila[4] == "administrador":
            return Administrador(fila[1], fila[2], fila[0])
        return Cliente(fila[1], fila[2], fila[3], fila[0])


class GestorReservas:

    def __init__(self, base, paquetes):
        self.base = base
        # Para el historial se necesitan los paquetes completos, con su costo.
        self.paquetes = paquetes

    def ya_reservado(self, id_cliente, id_paquete):
        try:
            self.base.cursor.execute(
                "SELECT COUNT(*) FROM reservas WHERE id_cliente = ? AND id_paquete = ?",
                (id_cliente, id_paquete))
            return self.base.cursor.fetchone()[0] > 0
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None

    def reservar(self, id_cliente, id_paquete):
        try:
            self.base.cursor.execute(
                "INSERT INTO reservas (id_cliente, id_paquete, fecha) VALUES (?, ?, ?)",
                (id_cliente, id_paquete, date.today().isoformat()))
            self.base.conexion.commit()
            return True
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return False

    def historial(self, id_cliente):
        try:
            self.base.cursor.execute(
                "SELECT id, id_paquete, fecha FROM reservas WHERE id_cliente = ?", (id_cliente,))
            filas = self.base.cursor.fetchall()
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None
        reservas = []
        for fila in filas:
            paquete = self.paquetes.buscar(fila[1])
            if paquete != None:
                reservas.append(Reserva(paquete, fila[2], fila[0]))
        return reservas

    def clientes_de(self, id_paquete):
        try:
            self.base.cursor.execute("""
                SELECT usuarios.id, usuarios.nombre, usuarios.nombre_usuario, usuarios.rut
                FROM reservas
                JOIN usuarios ON reservas.id_cliente = usuarios.id
                WHERE reservas.id_paquete = ?""", (id_paquete,))
            clientes = []
            for fila in self.base.cursor.fetchall():
                clientes.append(Cliente(fila[1], fila[2], fila[3], fila[0]))
            return clientes
        except sqlite3.Error as error:
            self.base.ultimo_error = str(error)
            return None
