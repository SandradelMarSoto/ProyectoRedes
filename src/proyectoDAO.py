import sqlite3

class DAO(object):
    """Clase que controla la conexion con la base de datos, tales como la
       como la creacion de nuevos usuarios y el CRUD de archivos."""

    def __init__(self):
        self.con = sqlite3.connect("../BD/proyecto.bd", check_same_thread=False)
        self.cursor = self.con.cursor()
        self.creaTablas()
        # self.con.close()

    def creaTablas(self):
        """
            Función que genera las tablas de la base de datos
        """
        self.cursor.execute('''SELECT name FROM sqlite_master
                                WHERE type='table' AND name='usuario'; ''')
        if self.cursor.fetchone() == None:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuario (
            id_usuario       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario   VARCHAR(255) UNIQUE NOT NULL,
            contrasena       VARCHAR(255) NOT NULL,
            imagen           BLOB,
            consumida        FLOAT NOT NULL
            );''')

            self.cursor.execute('''CREATE TABLE IF NOT EXISTS archivo (
            id_archivo       INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario       INTEGER NOT NULL,
            nombre_archivo   VARCHAR(255) NOT NULL,
            archivo          BLOB  NOT NULL,
            longitud         INTEGER NOT NULL,
            FOREIGN KEY      (id_usuario) REFERENCES usuario(id_usuario)
            );''')

            self.cursor.execute(''' INSERT INTO usuario (nombre_usuario,contrasena,consumida)
                                VALUES (?,?,?) ''', ('admin', 'contraseñaAdmin', 0.0))

            self.con.commit()

    def imagenPerfil(self, id_usuario):
        """
        Regresa la imagen de perfil del usuario con el id pasado como argumento.
        """
        self.cursor.execute('''SELECT imagen FROM usuario
                               WHERE id_usuario = ?''', (id_usuario,))

        imagen = self.cursor.fetchone()
        if imagen[0] is not None:
            return imagen[0]
        return -1

    def actualizaPerfil(self, id_usuario, nombre, imagen):
        """
        Actualiza los valores del perfil del usuario
        """
        id = self.checaUsuario(nombre, None)
        if id == -1:
            self.cursor.execute('''UPDATE usuario SET nombre_usuario = ?, imagen = ?
            WHERE id_usuario =?''', (nombre, imagen, id_usuario))
            self.con.commit()
            return 0
        else:
            return 1

    def checaUsuario(self, nombre, contrasena=None):
        """
        Verifica si existe el usuario en la base de datos, si existe,
        retorna su id, de lo contrario regresa -1
        ----
        parámetros
        ----
        nombre : string
        contrasena: string

        """
        if contrasena == None:
            self.cursor.execute(''' SELECT * FROM usuario
                             WHERE nombre_usuario = ?''', (nombre,))
        else:
            self.cursor.execute(''' SELECT * FROM usuario
                             WHERE nombre_usuario = ? AND contrasena = ?''', (nombre, contrasena))
        existe = self.cursor.fetchone()
        if existe != None:
            return existe[0]
        return -1

    def checaArchivo(self, nombre_archivo, id_usuario):
        """
            Verifica si el usuario tiene el archivo con nombre_archivo en
            la base de datos. Si existe, retorna su id, de lo contrario regresa -1

        """
        self.cursor.execute(''' SELECT id_archivo FROM archivo
                                WHERE id_usuario= ? and nombre_archivo = ?''', (id_usuario, nombre_archivo))

        id_archivo = self.cursor.fetchone()
        if id_archivo != None:
            return id_archivo[0]
        else:
            return -1

    def getArchivo(self, id_archivo, id_usuario):
        """
            Obtiene información del archivo para que pueda ser enviado
        """
        self.cursor.execute(''' SELECT nombre_archivo,longitud,archivo FROM archivo
                                WHERE id_archivo= ? and id_usuario = ?''', (id_archivo, id_usuario))
        informacion = self.cursor.fetchone()

        return informacion

    def getTodosArchivos(self, id_usuario):
        """
            Obtiene todos los archivos asociados a un usuario
        """
        self.cursor.execute(''' SELECT id_archivo, nombre_archivo FROM archivo
                                WHERE id_usuario = ? ''', (id_usuario,))

        archivos = self.cursor.fetchall()

        return archivos

    def registraUsuario(self, nombre, contrasena):
        """
            Guarda en la base de datos el usuario, verificando que el
            nombre de usuario no está asignado a otro usuario.
        """
        id = self.checaUsuario(nombre, None)
        if id != -1:
            return -1
        # si no existe, entonces lo creamos y devolvemos su id
        self.cursor.execute('INSERT INTO usuario (nombre_usuario,contrasena,consumida) VALUES(?, ?, ?)',
                            (nombre, contrasena, 0.0))
        self.con.commit()
        id = self.checaUsuario(nombre, contrasena)

        return id

    def getMBConsumidos(self, id_usuario):
        """
            Obtiene la cantidad de MB consumidos
        """
        self.cursor.execute('SELECT consumida FROM usuario WHERE id_usuario = ?', (id_usuario,))
        consumida = self.cursor.fetchone()
        if consumida != None:
            return consumida[0]
        return -1

    def guardaArchivo(self, id_usuario, nombre_archivo, archivo, longitud):
        """
            Inserta en la bd el archivo que desea guardar el cliente.
            El archivo es tipo BLOB.
        """
        id = self.checaArchivo(nombre_archivo, id_usuario)
        if id != -1:
            return -1

        self.cursor.execute('''INSERT INTO archivo
                            (id_usuario, nombre_archivo, archivo, longitud)
                            VALUES (?, ?, ?, ?)''',
                            (id_usuario, nombre_archivo, archivo, longitud))
        self.con.commit()

        mb_consumidos = self.getMBConsumidos(id_usuario)
        mb_consumidos += longitud
        self.cursor.execute('''UPDATE usuario SET consumida = ?
                                WHERE id_usuario = ? ''', (mb_consumidos, id_usuario))
        self.con.commit()

        id = self.checaArchivo(nombre_archivo, id_usuario)
        return id
