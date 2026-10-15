# interfaz.py
# Menus, validaciones y mensajes de Viajes Aventura.
# Aqui no hay SQL: todo lo que toca la base pasa por los gestores.

import getpass
from datetime import date

from modelos import Destino, Paquete, Cliente, Administrador

MENSAJE_ERROR = "No se pudo completar la operacion. Intente mas tarde."


# ---------------------------------------------------------------- validaciones

def pedir_texto(mensaje):
    # Un campo vacio nunca se acepta.
    while True:
        texto = input(mensaje).strip()
        if texto != "":
            return texto
        print("El campo no puede quedar vacio.")


def pedir_entero(mensaje, minimo):
    while True:
        try:
            numero = int(input(mensaje))
        except ValueError:
            print("Debe escribir un numero entero.")
            continue
        if numero < minimo:
            print("El numero debe ser", minimo, "o mayor.")
            continue
        return numero


def pedir_fecha(mensaje):
    # Se pide en formato AAAA-MM-DD y se revisa que sea una fecha real.
    while True:
        texto = input(mensaje).strip()
        try:
            date.fromisoformat(texto)
            return texto
        except ValueError:
            print("Fecha no valida. Use el formato AAAA-MM-DD, por ejemplo 2026-12-15.")


def pedir_rut():
    # Formato simple: numeros, guion y digito verificador (ej. 12345678-5).
    while True:
        rut = input("RUT (ej. 12345678-5): ").strip().upper()
        partes = rut.split("-")
        if len(partes) == 2 and partes[0].isdigit() and len(partes[1]) == 1:
            return rut
        print("RUT no valido. Escribalo sin puntos y con guion.")


def leer_clave(mensaje):
    # getpass esconde la clave mientras se escribe. Si el editor no lo soporta,
    # se usa input para que el programa igual funcione.
    try:
        return getpass.getpass(mensaje)
    except Exception:
        return input(mensaje)


def pedir_clave_nueva():
    while True:
        clave = leer_clave("Clave (minimo 8 caracteres): ")
        if len(clave) < 8:
            print("La clave debe tener al menos 8 caracteres.")
            continue
        if leer_clave("Repita la clave: ") != clave:
            print("Las claves no coinciden.")
            continue
        return clave


# ---------------------------------------------------------------- permisos

def tiene_permiso(usuario):
    # Segunda barrera: la funcion revisa el rol aunque la opcion no se vea en el menu.
    if usuario.puede_administrar():
        return True
    print("No tiene permiso para esta opcion.")
    return False


def es_cliente(usuario):
    if usuario.puede_administrar():
        print("Esta opcion es solo para clientes.")
        return False
    return True


# ---------------------------------------------------------------- mostrar

def mostrar_destinos(destinos):
    if len(destinos) == 0:
        print("No hay destinos registrados.")
    for destino in destinos:
        print(destino.id, "-", destino.nombre, "(" + destino.pais + ") |",
              destino.dias(), "dias | $", destino.precio())


def mostrar_paquete(paquete):
    print(paquete.id, "-", paquete.nombre, "| del", paquete.fecha_inicio, "al", paquete.fecha_termino)
    for destino in paquete.destinos():
        print("     ", destino.nombre, "$", destino.precio())
    print("     Costo total: $", paquete.costo())
    if paquete.tiene_cupo():
        print("     Cupos disponibles:", paquete.cupos_disponibles(), "de", paquete.cupos)
    else:
        print("     SIN CUPOS")


# ---------------------------------------------------------------- destinos

def registrar_destino(usuario, destinos):
    if not tiene_permiso(usuario):
        return
    print("\n-- REGISTRAR DESTINO --")
    nombre = pedir_texto("Nombre: ")
    # Se busca antes de guardar para no repetir destinos.
    if destinos.existe_nombre(nombre):
        print("Ya existe un destino con ese nombre.")
        return
    pais = pedir_texto("Pais: ")
    dias = pedir_entero("Dias de estadia: ", 1)
    precio = pedir_entero("Precio: ", 1)
    if destinos.crear(Destino(nombre, pais, dias, precio)):
        print("Destino registrado.")
    else:
        print(MENSAJE_ERROR)


def listar_destinos(usuario, destinos):
    if not tiene_permiso(usuario):
        return
    print("\n-- DESTINOS --")
    lista = destinos.listar()
    if lista == None:
        print(MENSAJE_ERROR)
        return
    mostrar_destinos(lista)


def modificar_destino(usuario, destinos):
    if not tiene_permiso(usuario):
        return
    print("\n-- MODIFICAR DESTINO --")
    # Se busca antes de modificar: si no existe, no hay nada que cambiar.
    destino = destinos.buscar(pedir_entero("ID del destino: ", 1))
    if destino == None:
        print("No existe un destino con ese ID.")
        return
    print("Datos actuales:", destino.nombre, "(" + destino.pais + ") |",
          destino.dias(), "dias | $", destino.precio())
    nuevo_nombre = pedir_texto("Nuevo nombre: ")
    if nuevo_nombre != destino.nombre and destinos.existe_nombre(nuevo_nombre):
        print("Ya existe un destino con ese nombre.")
        return
    destino.nombre = nuevo_nombre
    destino.pais = pedir_texto("Nuevo pais: ")
    destino.cambiar_dias(pedir_entero("Nuevos dias: ", 1))
    destino.cambiar_precio(pedir_entero("Nuevo precio: ", 1))
    if destinos.modificar(destino):
        print("Destino actualizado. Los paquetes que lo incluyen ya usan el nuevo precio.")
    else:
        print(MENSAJE_ERROR)


def eliminar_destino(usuario, destinos):
    if not tiene_permiso(usuario):
        return
    print("\n-- ELIMINAR DESTINO --")
    id_destino = pedir_entero("ID del destino: ", 1)
    if destinos.buscar(id_destino) == None:
        print("No existe un destino con ese ID.")
        return
    # Si el destino esta en un paquete, borrarlo cambiaria el costo de ese paquete.
    en_uso = destinos.cantidad_paquetes(id_destino)
    if en_uso == None:
        print(MENSAJE_ERROR)
    elif en_uso > 0:
        print("No se puede eliminar: el destino esta en", en_uso, "paquete(s).")
    elif destinos.eliminar(id_destino):
        print("Destino eliminado.")
    else:
        print(MENSAJE_ERROR)


# ---------------------------------------------------------------- paquetes

def crear_paquete(usuario, destinos, paquetes):
    if not tiene_permiso(usuario):
        return
    print("\n-- CREAR PAQUETE --")
    nombre = pedir_texto("Nombre del paquete: ")
    inicio = pedir_fecha("Fecha de inicio (AAAA-MM-DD): ")
    termino = pedir_fecha("Fecha de termino (AAAA-MM-DD): ")
    cupos = pedir_entero("Cupos: ", 1)
    paquete = Paquete(nombre, inicio, termino, cupos)
    if not paquete.fechas_validas():
        print("La fecha de termino debe ser posterior a la de inicio.")
        return
    if not paquete.inicia_despues_de(date.today().isoformat()):
        print("La fecha de inicio no puede ser anterior a hoy.")
        return
    lista = destinos.listar()
    if lista == None:
        print(MENSAJE_ERROR)
        return
    mostrar_destinos(lista)
    while True:
        id_destino = pedir_entero("ID del destino a agregar (0 para terminar): ", 0)
        if id_destino == 0:
            break
        destino = destinos.buscar(id_destino)
        if destino == None:
            print("No existe un destino con ese ID.")
        elif paquete.agregar_destino(destino):
            print("Agregado. Costo hasta ahora: $", paquete.costo())
        else:
            print("Ese destino ya esta en el paquete.")
    # Un paquete combina destinos: con uno solo no es un paquete.
    if len(paquete.destinos()) < 2:
        print("Un paquete necesita al menos 2 destinos. No se guardo.")
        return
    if paquetes.crear(paquete):
        print("Paquete creado. Costo: $", paquete.costo())
    else:
        print("No se pudo crear el paquete. Revise que el nombre no este repetido.")


def ver_paquetes(paquetes):
    # La ven los dos roles: el cliente la necesita para elegir.
    print("\n-- PAQUETES --")
    lista = paquetes.listar()
    if lista == None:
        print(MENSAJE_ERROR)
        return
    if len(lista) == 0:
        print("No hay paquetes.")
    for paquete in lista:
        mostrar_paquete(paquete)


def ver_clientes_paquete(usuario, paquetes, reservas):
    if not tiene_permiso(usuario):
        return
    print("\n-- CLIENTES DE UN PAQUETE --")
    paquete = paquetes.buscar(pedir_entero("ID del paquete: ", 1))
    if paquete == None:
        print("No existe un paquete con ese ID.")
        return
    clientes = reservas.clientes_de(paquete.id)
    if clientes == None:
        print(MENSAJE_ERROR)
        return
    print(paquete.nombre, "-", len(clientes), "de", paquete.cupos, "cupos ocupados")
    # Solo el nombre: el RUT no hace falta para esta lista.
    for cliente in clientes:
        print("  ", cliente.nombre)


# ---------------------------------------------------------------- reservas

def reservar_paquete(usuario, paquetes, reservas):
    if not es_cliente(usuario):
        return
    print("\n-- RESERVAR PAQUETE --")
    # Se busca el paquete justo antes, para contar los cupos del momento.
    paquete = paquetes.buscar(pedir_entero("ID del paquete: ", 1))
    if paquete == None:
        print("No existe un paquete con ese ID.")
    elif reservas.ya_reservado(usuario.id, paquete.id):
        print("Usted ya tiene una reserva en ese paquete.")
    elif not paquete.tiene_cupo():
        print("El paquete no tiene cupos disponibles.")
    elif reservas.reservar(usuario.id, paquete.id):
        print("Reserva registrada en", paquete.nombre)
    else:
        print(MENSAJE_ERROR)


def ver_historial(usuario, reservas):
    if not es_cliente(usuario):
        return
    print("\n-- MI HISTORIAL --")
    historial = reservas.historial(usuario.id)
    if historial == None:
        print(MENSAJE_ERROR)
        return
    if len(historial) == 0:
        print("Todavia no tiene reservas.")
    for reserva in historial:
        print(reserva.fecha, "-", reserva.paquete.nombre, "$", reserva.paquete.costo())


# ---------------------------------------------------------------- cuentas y acceso

def crear_administrador(usuarios):
    print("\n-- NUEVO ADMINISTRADOR --")
    nombre = pedir_texto("Nombre: ")
    nombre_usuario = pedir_texto("Nombre de usuario: ")
    if usuarios.existe_usuario(nombre_usuario):
        print("Ese nombre de usuario ya existe.")
        return
    clave = pedir_clave_nueva()
    if usuarios.registrar(Administrador(nombre, nombre_usuario), clave):
        print("Administrador creado.")
    else:
        print(MENSAJE_ERROR)


def nuevo_administrador(usuario, usuarios):
    # Cada persona que administra tiene su propia cuenta: compartir una clave
    # impediria saber quien hizo cada cambio.
    if tiene_permiso(usuario):
        crear_administrador(usuarios)


def registrarse(usuarios):
    print("\n-- REGISTRO DE CLIENTE --")
    nombre = pedir_texto("Nombre completo: ")
    nombre_usuario = pedir_texto("Nombre de usuario: ")
    if usuarios.existe_usuario(nombre_usuario):
        print("Ese nombre de usuario ya existe.")
        return
    rut = pedir_rut()
    clave = pedir_clave_nueva()
    if usuarios.registrar(Cliente(nombre, nombre_usuario, rut), clave):
        print("Cuenta creada. Ya puede iniciar sesion.")
    else:
        print(MENSAJE_ERROR)


def iniciar_sesion(usuarios):
    for intento in range(3):
        print("\n-- INICIAR SESION --")
        nombre_usuario = input("Usuario: ").strip()
        clave = leer_clave("Clave: ")
        usuario = usuarios.autenticar(nombre_usuario, clave)
        if usuario != None:
            return usuario
        # Un solo mensaje: decir "ese usuario no existe" ayudaria a un atacante.
        print("Usuario o clave incorrectos.")
    print("Se alcanzo el maximo de 3 intentos.")
    return None


# ---------------------------------------------------------------- menus

def menu_usuario(usuario, destinos, paquetes, usuarios, reservas):
    while True:
        print("\n===== VIAJES AVENTURA =====")
        print("Sesion de", usuario.nombre, "(" + usuario.rol() + ")")
        # Primera barrera: cada rol solo ve sus opciones.
        if usuario.puede_administrar():
            print("1 - Registrar destino")
            print("2 - Listar destinos")
            print("3 - Modificar destino")
            print("4 - Eliminar destino")
            print("5 - Crear paquete")
        print("6 - Ver paquetes")
        if usuario.puede_administrar():
            print("7 - Ver clientes de un paquete")
            print("8 - Crear administrador")
        else:
            print("9 - Reservar paquete")
            print("10 - Mi historial")
        print("0 - Cerrar sesion")
        opcion = input("Opcion: ").strip()
        if opcion == "1":
            registrar_destino(usuario, destinos)
        elif opcion == "2":
            listar_destinos(usuario, destinos)
        elif opcion == "3":
            modificar_destino(usuario, destinos)
        elif opcion == "4":
            eliminar_destino(usuario, destinos)
        elif opcion == "5":
            crear_paquete(usuario, destinos, paquetes)
        elif opcion == "6":
            ver_paquetes(paquetes)
        elif opcion == "7":
            ver_clientes_paquete(usuario, paquetes, reservas)
        elif opcion == "8":
            nuevo_administrador(usuario, usuarios)
        elif opcion == "9":
            reservar_paquete(usuario, paquetes, reservas)
        elif opcion == "10":
            ver_historial(usuario, reservas)
        elif opcion == "0":
            break
        else:
            print("Opcion no valida.")


def iniciar(base, destinos, paquetes, usuarios, reservas):
    if not base.crear_tablas():
        print("No se pudo preparar la base de datos.")
        return
    # La primera vez no hay administrador, y su clave no puede venir escrita en el codigo.
    if not usuarios.existe_administrador():
        print("Primera ejecucion: cree la cuenta del administrador.")
        crear_administrador(usuarios)
    while True:
        print("\n===== VIAJES AVENTURA =====")
        print("1 - Iniciar sesion")
        print("2 - Registrarme como cliente")
        print("0 - Salir")
        opcion = input("Opcion: ").strip()
        if opcion == "1":
            usuario = iniciar_sesion(usuarios)
            if usuario == None:
                break
            menu_usuario(usuario, destinos, paquetes, usuarios, reservas)
        elif opcion == "2":
            registrarse(usuarios)
        elif opcion == "0":
            break
        else:
            print("Opcion no valida.")
