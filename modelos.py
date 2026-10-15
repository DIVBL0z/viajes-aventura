# modelos.py
# Clases del problema de Viajes Aventura y sus reglas del negocio.
# Este archivo no usa sqlite3 ni print: solo describe el negocio.


class Destino:

    def __init__(self, nombre, pais, dias, precio, id=None):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self._dias = dias
        self._precio = precio

    def dias(self):
        return self._dias

    def precio(self):
        return self._precio

    def cambiar_dias(self, nuevos):
        # Un destino sin dias de estadia no se puede vender.
        if nuevos <= 0:
            return False
        self._dias = nuevos
        return True

    def cambiar_precio(self, nuevo):
        # Un precio cero o negativo haria que el costo del paquete saliera mal.
        if nuevo <= 0:
            return False
        self._precio = nuevo
        return True


class Paquete:

    def __init__(self, nombre, fecha_inicio, fecha_termino, cupos, id=None):
        self.id = id
        self.nombre = nombre
        # Las fechas se guardan como texto AAAA-MM-DD; asi se pueden comparar.
        self.fecha_inicio = fecha_inicio
        self.fecha_termino = fecha_termino
        self.cupos = cupos
        self.reservados = 0
        self._destinos = []

    def agregar_destino(self, destino):
        # El mismo destino dos veces cobraria su precio dos veces.
        for actual in self._destinos:
            if actual.id == destino.id:
                return False
        self._destinos.append(destino)
        return True

    def destinos(self):
        return self._destinos

    def costo(self):
        # El costo siempre se calcula desde los precios de sus destinos.
        total = 0
        for destino in self._destinos:
            total = total + destino.precio()
        return total

    def fechas_validas(self):
        return self.fecha_termino > self.fecha_inicio

    def inicia_despues_de(self, hoy):
        # No se vende un paquete cuyo viaje ya comenzo.
        return self.fecha_inicio >= hoy

    def cupos_disponibles(self):
        return self.cupos - self.reservados

    def tiene_cupo(self):
        # Esta regla evita que se reserven mas lugares que los cupos.
        return self.cupos_disponibles() > 0


class Usuario:

    def __init__(self, nombre, nombre_usuario, id=None):
        self.id = id
        self.nombre = nombre
        self.nombre_usuario = nombre_usuario

    def puede_administrar(self):
        return False

    def rol(self):
        return "usuario"


class Cliente(Usuario):

    def __init__(self, nombre, nombre_usuario, rut, id=None):
        super().__init__(nombre, nombre_usuario, id)
        self.rut = rut

    def rol(self):
        return "cliente"


class Administrador(Usuario):

    def puede_administrar(self):
        return True

    def rol(self):
        return "administrador"


class Reserva:

    def __init__(self, paquete, fecha, id=None):
        self.id = id
        self.paquete = paquete
        self.fecha = fecha
