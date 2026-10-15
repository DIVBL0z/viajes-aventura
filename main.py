# main.py
# Crea la base y los gestores, y arranca la interfaz.

from datos import BaseDeDatos, GestorDestinos, GestorPaquetes, GestorUsuarios, GestorReservas
from interfaz import iniciar


def main():
    base = BaseDeDatos("viajes_aventura.db")
    # Todos los gestores comparten la misma conexion: eso es composicion.
    destinos = GestorDestinos(base)
    paquetes = GestorPaquetes(base)
    usuarios = GestorUsuarios(base)
    reservas = GestorReservas(base, paquetes)
    iniciar(base, destinos, paquetes, usuarios, reservas)
    base.cerrar()


if __name__ == "__main__":
    main()
