import socket
import threading
import time
from usuario import Usuario
from proyectoDAO import DAO
from usuario import Usuario


class Servidor():
    """
        Clase Servidor, recibe las peticiones del cliente y responde de acuerdo
        a estas.

        Atributos
        ---------
        self.host: str
            La dirección IP del cliente.
        self.port: int
            Puerto en el que se establecerá la comunicación.
        self.s : socket
            Socket a través del cual se hara la conexión.
        self.usuarios: diccionario
            Tendrá la información del usuario y su respectiva conexión.
            La llave será su id de acuerdo a la bd y el contenido es una tupla
            (usuario, con) donde usuario es objeto Usuario y con : socket
    """

    def __init__(self, host, port,bd):
        self.host = host
        self.port = port
        self.bd = bd
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usuarios = {}

    def conectaCliente(self):
        """
            Se inicia el servidor haciendo bind con el puerto y host
        """
        try:
            self.s.bind((self.host, self.port))
            print("Se ha iniciado el servidor")
        except socket.error:
            return False

    def hilo_cliente(self,con, dir):
        """
            Por cada cliente que se conecte, se crea este hilo, que tendrá
            información para que se procese el mensaje.
            ----
            parámetros
            ----
            con: socket
                conexión del cliente
            dir: (str, int)
                dirección del cliente
        """
        codigo = 0
        mensaje = ""
        id_usuario = -1
        while True:
            try:
                mensaje = con.recv(1024)
                if mensaje:
                    codigo = mensaje[0]
                    if codigo == 32:
                        if id_usuario != -1:
                            self.acumulaArchivo(mensaje[1:], id_usuario, con)
                        else:
                            con.send("No has iniciado sesión".encode())
                        #time.sleep(10)
                    elif codigo == 15:
                        if id_usuario != -1:
                            self.actualizaPerfil(mensaje[1:], id_usuario, con)
                        else:
                            con.send("No has iniciado sesión".encode())

                    else:
                        mensaje = mensaje.decode()
                        id_usuario=self.procesaMensaje(codigo, mensaje[1:], id_usuario, con)
            except:
                continue
        con.close()



    def estableceConexion(self):
        """
            Se crea un hilo por cada cliente que se conecta
        """
        self.s.listen(100)
        while True:
            con, dir = self.s.accept()
            print("conectado a "+ dir[0]+":"+str(dir[1]))
            hilo= threading.Thread(target = self.hilo_cliente, args = (con, dir))
            hilo.start()

    def procesaMensaje(self, codigo, mensaje, id_usuario, con):
        """
            Por cada mensaje que se reciba, se obtendrá el codigo de la solicitud y
            si es válida se mandará a los métodos correspondientes
            ----
            parámetros
            ----
            codigo: byte
                el código de la solicitud
            mensaje: bytes
                resto del mensaje enviado por el cliente
            id_usuario: int
                identificador del usuario
        """
        if codigo == 10:
            if id_usuario != -1:
                con.send("Ya estás identificado".encode())
            else:
                respuesta = "Revisando la base de datos\n"
                con.send(respuesta.encode())
                id_usuario = self.iniciaSesion(con,mensaje)

        elif id_usuario == -1 and codigo != 12 :
            respuesta = "Bienvenida/o a ALGISA, por favor identifícate \n"
            con.send(respuesta.encode())

        elif id_usuario == -1 and codigo == 12:
            id_usuario = self.registraCliente(con, mensaje)

        elif codigo == 31:
            self.revisaDisponible(con, id_usuario)

        elif codigo == 41:
            self.getNombresArchivos(con, id_usuario)

        elif codigo == 43 or codigo == 46:
            self.muestraArchivo(con, id_usuario, mensaje,codigo)

        elif codigo == 100:
            respuesta = "Hasta pronto, "+ self.usuarios[id_usuario][0].nombre_usuario + "\n \n \n"
            con.send(respuesta.encode())
            del self.usuarios[id_usuario]
            id_usuario = -1

        else:
            respuesta = "No es un código válido"
            con.send(respuesta.encode())

        return id_usuario

    def iniciaSesion(self,con,mensaje):
        """
            Se revisa en la base de datos si existe el usuario y se checa
            si introdujo su contraseña, se envia una respuesta de acuerdo al resultado
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            mensaje: bytes
                resto del mensaje enviado por el cliente
        """
        respuesta=bytearray(bytes([20]))
        partes = mensaje.split("|")
        partes = partes[1:]
        id_usuario = -1

        if len(partes) == 2:
            id_usuario=self.bd.checaUsuario(partes[0],partes[1])
            if id_usuario != -1: #checa si existe el usuario
                usuario = Usuario( partes[0], partes[1])
                #imagen= self.bd.imagenPerfil(id_usuario)
                self.usuarios[id_usuario] = (usuario, con)
                respuesta.extend(bytes(usuario.nombre_usuario,'utf-8'))
                print("Exito")
            else:
                respuesta.extend(bytes([1]))
                error = "Nombre de usuario o contraseña incorrecto"
                print(error)
                #con.send(error.encode())
        else: #No existe el usuario solicitado
            respuesta.extend(bytes([1]))
            print("Por favor ingresa formato correcto : 10|user|password \n")

        con.send(respuesta)
        return id_usuario

    def registraCliente(self, con, mensaje):
        """
            Se registra al cliente y se envia una respuesta de acuerdo al resultado
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            mensaje: bytes
                resto del mensaje enviado por el cliente
        """

        respuesta=bytearray(bytes([11]))
        partes = mensaje.split("|")
        partes = partes[1:]
        if len(partes) == 2:
            id_usuario = self.bd.registraUsuario(partes[0],partes[1])
            if id_usuario != -1:
                print("Exito")
                respuesta.extend(bytes([0]))
            else:
                print("Fallo")
                respuesta.extend(bytes([1]))
        else:
            print("Fallo")
            respuesta.extend(bytes([1]))

        con.send(respuesta)
        return -1 #porque después de registrarse tiene que iniciar sesión

    def revisaDisponible(self, con, id_usuario):
        """
            Verifica en la Base de Datos cuántos MB ha utilizado, si
            este es igual a 1024 Megabytes (1 GB) entonces responderá
            al cliente que ya no puede almacenar más archivos. En caso
            contrario dirá que la longitud máxima del archivo a subir
            es lo que le queda de capacidad.
            -------
            parámetros
            ------
            con: socket
                conexión con el usuario
            id_usuario: int
                identificador del usuario
        """
        cap_consumida = self.bd.getMBConsumidos(id_usuario)
        restante = 100000000 - cap_consumida
        respuesta =bytearray(bytes([33])) #checa luego
        if restante >= 10000:
            restante = restante / 1000000
            respuesta.extend(int(restante).to_bytes(4,'big'))
            print("Exito")
        else:
            print("Fallo")
            respuesta.extend(bytes([1]))

        con.send(respuesta)

    def getNombresArchivos(self, con, id_usuario):
        """
            Se obtiene una lista de todos los archivos asociados con un usuario
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            mensaje: id_usuario
                identificador del usuario
        """
        archivos = self.bd.getTodosArchivos(id_usuario)
        respuesta = bytearray(bytes([42]))
        delimitador = bytes("|",'utf-8')
        if len(archivos) != 0:
            for archivo in archivos:
                respuesta.extend(delimitador)
                id = archivo[0]
                respuesta.extend(id.to_bytes(4,'big'))
                respuesta.extend(delimitador)
                nombre = bytes(archivo[1], 'utf-8')
                respuesta.extend(nombre)
                print("Exito")
        else:
            print("Fallo")
            respuesta.extend(bytes([1]))
        con.send(respuesta)

    def actualizaPerfil(self,mensaje,id_usuario, con):
        """
            Se actualizan los datos del usuario, su nombre e imagen de perfil
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            mensaje: bytes
                resto del mensaje enviado por el cliente
            id_usuario: int
                identificador del usuario
        """
        longAcc = 0
        indx = []
        i = 1
        k = 0
        if mensaje[0] == 124:
            for b in mensaje[1:]:
                if k == 2:
                    break
                if b == 124:
                    indx.append(i)
                    k = k + 1
                i = i + 1

            nombre_nuevo = bytearray(mensaje[1:indx[0]]).decode()
            longitud = int.from_bytes(mensaje[indx[0] + 1:indx[1]], 'big')

            archivo = bytearray(mensaje[indx[1] + 1:])
            longAcc = len(archivo)

            while longAcc < longitud:
                m = con.recv(1024)
                archivo.extend(m)
                longAcc = len(archivo)

            exito=self.bd.actualizaPerfil(id_usuario, nombre_nuevo, archivo)
            print("Éxito")
            respuesta = bytearray(bytes([16]))
            respuesta.extend(bytes([exito]))
        else:
            respuesta = bytearray(bytes([16]))
            respuesta.extend(bytes([1]))
            print("Fallo")
        con.send(respuesta)

    def acumulaArchivo(self, mensaje, id_usuario, con):
        """
        Verifica que el archivo enviado tenga el formato correcto, si es así
        recibe mensajes y los va reconstruyendo en el archivo original hasta
        que la longitud acumulada sea igual a la longitud del archivo
        -------
        parámetros
        ------
        mensaje: bytes
            mensaje enviado por el cliente
        id_usuario: int
            identificador del usuario
        con: socket
            conexión con el cliente
        """
        longAcc=0
        indx=[]
        i=1
        k=0

        if mensaje[0] == 124:
            for b in mensaje[1:]:
                if k == 2:
                    break
                if b == 124:
                    indx.append(i)
                    k=k+1
                i=i+1

            nombre_archivo=bytearray(mensaje[1:indx[0]]).decode()
            longitud=int.from_bytes(mensaje[indx[0]+1:indx[1]],'big')
            cap_consumida = self.bd.getMBConsumidos(id_usuario)
            diferencia = 100000000 - (cap_consumida + longitud)

            if diferencia >10000:
                archivo=bytearray(mensaje[indx[1]+1:])
                longAcc=len(archivo)

                while longAcc < longitud:
                    m=con.recv(1024)
                    archivo.extend(m)
                    longAcc=len(archivo)

                id_archivo = self.bd.guardaArchivo(id_usuario,nombre_archivo,archivo,longitud)

                if id_archivo != -1 : #si el nombre del archivo no se repite entonces se guarda
                    respuesta = bytearray(bytes([33]))
                    respuesta.extend(bytes([0]))
                    print("Exito")
                else:
                    print("Fallo")
                    respuesta = bytearray(bytes([33]))
                    respuesta.extend(bytes([1]))

            else:
                print("Fallo")
                respuesta = bytearray(bytes([33]))
                respuesta.extend(bytes([1]))

        else:
            print("Fallo")
            respuesta = bytearray(bytes([33]))
            respuesta.extend(bytes([1]))

        con.send(respuesta)

    def muestraArchivo(self, con, id_usuario, mensaje,codigo):
        """
            Se obtiene un archivo de la base de datos y se le responde al cliente
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            id_usuario: int
                identificador del usuario
            mensaje: bytes
                resto del mensaje enviado por el cliente
            codigo: byte
                de acuerdo a este codigo sabremos si devolver el blob o todas las características
                de la imagen
        """
        partes = mensaje.split("|")
        partes = partes[1:]
        if codigo == 43:
            cd=bytes([44])
        else:
            cd=bytes([47])
        respuesta = bytearray(cd)
        if len(partes) == 1:
            id_archivo = self.bd.checaArchivo(partes[0], id_usuario)
            if id_archivo != -1:
                archivo = self.bd.getArchivo(id_archivo, id_usuario)
                self.enviaArchivo(cd,con,archivo[0], archivo[1], archivo[2])
            else:
                print("Fallo")
                respuesta.extend(bytes([1]))
                con.send(respuesta)
        else:
            print("Fallo")
            respuesta.extend(bytes([1]))
            con.send(respuesta)

    def enviaArchivo(self,codigo,con, nombre_archivo, longitud, archivo):
        """
            Se descarga una imagen
            ----
            parámetros
            ----
            con: socket
                conexión con el cliente
            mensaje: bytes
                resto del mensaje enviado por el cliente
            nombre_archivo: str
                nombre de la imagen
            longitud: int
                tamaño de la imagen
            archivo: bytes
                la imagen codificada en bytes
        """
        mensaje_b = bytearray(codigo) #44
        delimitador = bytes("|", 'utf-8')
        nombre = bytes(nombre_archivo, 'utf-8')

        mensaje_b.extend(delimitador)
        mensaje_b.extend(nombre)
        mensaje_b.extend(delimitador)
        mensaje_b.extend(longitud.to_bytes(4,'big'))
        mensaje_b.extend(delimitador)
        mensaje_b.extend(archivo)
        print("Exito")
        con.sendall(mensaje_b)

if __name__ == '__main__':
    serv = Servidor('127.0.0.1', 9999,DAO())
    serv.conectaCliente()
    serv.estableceConexion()
