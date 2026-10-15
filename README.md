# viajes-aventura
Sistema en Python con SQLite para gestionar destinos, paquetes turísticos y reservas de una agencia de viajes. Incluye autenticación segura con PBKDF2 y roles.

Viajes Aventura es un sistema de consola desarrollado en Python con SQLite para gestionar una agencia de viajes. Permite administrar destinos, armar paquetes con costo calculado y cupos, y registrar reservas de clientes.

Programación orientada a objetos: encapsulamiento, herencia y polimorfismo (Usuario, Cliente, Administrador).
Persistencia: SQLite con claves foráneas, transacciones con rollback y consultas parametrizadas.
Seguridad: claves con PBKDF2-HMAC-SHA256 (200.000 iteraciones) y sal única por usuario, comparación con compare_digest, tres intentos de acceso y mensajes de error que no revelan información técnica.
Roles: el administrador gestiona destinos y paquetes; el cliente se registra, reserva y consulta su historial.
Arquitectura: modelos.py (negocio), datos.py (SQL), interfaz.py (menús y validaciones) y main.py (arranque).

Ejecución: python main.py. La primera vez pide crear la cuenta del administrador.

Proyecto de la Evaluación Sumativa 3 de Programación Orientada a Objeto Seguro (INACAP).


Requisito: Python 3.7 o superior (usa date.fromisoformat) y ninguna librería externa, porque todo es de la biblioteca estándar.


Los integrantes con sus roles: José (Product Owner), Denisse (Scrum Master y Líder de Proyecto) y Daniel (desarrollo).

LINK DEL VIDEO: https://youtu.be/2AfCdHKQmIE
