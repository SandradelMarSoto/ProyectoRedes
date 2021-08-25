import socket
import sys
import select
import os
import queue

class Cliente():
    """
        Clase Cliente, que envía las peticiones del usuario al servidor

        Atributos
        ---------
        self.host: str
            La dirección IP del cliente.
        self.port: int
            Puerto en el que se establecerá la comunicación.
        self.mensajes : queue
            Cola donde se irán guardando todos los mensajes recibidos por el servidor.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.mensajes=queue.Queue()
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSERROR as error:
            print("Error al crear el socket para el cliente")
            sys.exit()

    def conectaServidor(self):
        """
        Función que conecta al cliente con el servidor
        """
        try:
            self.s.connect((self.host, self.port))
        except socket.timeout:
            print("Timeout :( ")

    def enviaMensaje(self,codigo, mensaje):
        """
        Codifica el mensaje del cliente antes de mandarlo
        """
        codigo_b = bytearray(bytes([codigo]))
        mensaje_b = bytes(mensaje, 'utf-8')
        codigo_b.extend(mensaje_b)
        self.s.sendall(codigo_b)


    def recibeMensaje(self):
        """
            Se mantiene verificando si el servidor envía una respuesta o si el
            cliente desea ingresar un mensaje. En el primer caso, recibe la respuesta
            y la imprime, en el segundo, revisa si el mensaje es válido y lo envía.
        """
        while True:
            sockets_list = [sys.stdin, self.s]
            read_sockets, write_socket, error_socket = select.select(sockets_list,[],[])
            for socket in read_sockets:
                if socket == self.s:
                    mensaje = socket.recv(1024)
                    #mensaje = mensaje.decode()
                    self.checaMensaje(mensaje)
                else:
                    mensaje = sys.stdin.readline()
                    codigo, m, valido = self.preparaMensaje(mensaje)
                    if codigo == 32 and valido:
                        self.enviaArchivo(codigo,m)
                    elif codigo == 15 and valido:
                        self.enviaArchivo(codigo,m)
                    elif valido:
                        self.enviaMensaje(codigo, m)
                    else:
                        print("Por favor ingresa una petición correcta ")

    def preparaMensaje(self,mensaje):
        """
            Verifica que todos los mensajes inicien con un número, que
            será el código de la petición. Prepara el mensaje para que
            sean los parámetros para el método enviaMensaje(int, string)

            ---
            parámetros
            ---
            mensaje : str
        """
        partes = mensaje.split("|")
        codigo = 0
        m = ""
        valido = True
        try:
            codigo = int(partes[0])
            m = mensaje.replace(partes[0],"").replace("\n","")
            if codigo > 256:
                return "","", False
        except ValueError:
            return "","", False

        return codigo, m, valido

    def enviaArchivo(self,codigo,mensaje):
        """
            Convierte el archivo especificado por el usuario en binario,
            también obtiene su tamaño y lo encapsula en un solo mensaje.
            -----
            parámetros
            ------
            mensaje: string
            un mensaje válido debe tener la siguiente estructura:
            nombre(nombre con el que será guardado en la bd)|archivo(path)
            -----
            salida = mensaje con el formato : nombre|longitud|archivo
        """
        mensaje_b=bytearray(bytes([codigo]))
        partes = mensaje.split("|")
        partes = partes[1:]

        try:
            if len(partes) == 2:
                delimitador=bytes("|",'utf-8')
                nombre = bytes(partes[0],'utf-8')
                tam = os.stat(partes[1]).st_size

                archivo = self.convertirABinario(partes[1])
                mensaje_b.extend(delimitador)
                mensaje_b.extend(nombre)
                mensaje_b.extend(delimitador)
                mensaje_b.extend(tam.to_bytes(4,'big'))
                mensaje_b.extend(delimitador)
                mensaje_b.extend(archivo)

            else:
                print("Faltan argumentos")
        except Exception as error:
            raise error

        self.s.sendall(mensaje_b)

    def convertirABinario(self, ruta):
        """
            Convierte el archivo de tal ruta en binario
            -----
            parámetros
            ------
            ruta: str
                la ruta de la imagen
            -----
        """
        with open(ruta,'rb') as file:
            blobData = file.read()
        return blobData

    def escribeArchivo(self, nombre, archivo):
        """
            Toma el contenido en binario del archivo y lo convierte en un archivo nuevo el
            cual guarda en la carpeta archivos
            -----
            parámetros
            ------
            nombre: string
                el nombre del archivo
            archivo: bytes
                el contenido en binario del archivo
        """
        ruta = "../archivos/"+nombre
        with open(ruta, 'wb') as file:
            file.write(archivo)

    def checaMensaje(self,mensaje):
        """
            Revisa que el mensaje recibido del servidor se válido y si lo es,
            procesa su respuesta de acuerdo al código del mensaje
            -----
            parámetros
            ------
            mensaje: bytes
                un mensaje
        """
        if len(mensaje) == 2:
            self.mensajes.put(mensaje)
            print(mensaje[0],mensaje[1])

        elif mensaje[0] == 42:
            idsArch=self.getListaArchivos(mensaje)
            self.mensajes.put(idsArch)

        elif mensaje[0] == 44 or mensaje[0] == 47:
            exito=self.acumulaArchivo(mensaje[0],mensaje[1:])
            #self.mensajes.put(mensaje[0])

        elif mensaje[0] == 20:
            self.mensajes.put(mensaje)
            print("EXITO")
        elif mensaje[0] == 33:
            self.mensajes.put(mensaje)
        else:
            print(mensaje.decode())

    def acumulaArchivo(self,codigo,mensaje):
        """
            Cuando se recibe un archivo se obtiene la longitud del archivo y se va
            juntando el mensaje hasta que se obtiene el archivo completo
            -----
            parámetros
            ------
            codigo: byte
                identificador para saber a que estado cambiaremos
            mensaje: bytes
                Pedazos del archivo
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

            nombre=bytearray(mensaje[1:indx[0]]).decode()
            longitud=int.from_bytes(mensaje[indx[0]+1:indx[1]],'big')
            archivo=bytearray(mensaje[indx[1]+1:])
            longAcc=len(archivo)

            while longAcc < longitud:
                sockets_list = [sys.stdin, self.s]
                read_sockets, _, _ = select.select(sockets_list,[],[])
                for socket in read_sockets:
                    if socket == self.s:
                        msg = socket.recv(1024)
                        archivo.extend(msg)
                        longAcc=longAcc+len(msg)

            if codigo == 44:
                self.escribeArchivo(nombre,archivo)
                self.mensajes.put(codigo)
                #print("Se ha descargado el archivo correctamente")
            else:
                b=bytearray(bytes([codigo]))
                b.extend(archivo)
                self.mensajes.put(b)
                #print("Se ha mandado el archivo correctamente")

    def getListaArchivos(self, mensaje):
        """
            Se obtienen codificados los nombres e ids de todos los archivos y se devuelve la lista
            ya decodificada
            -----
            parámetros
            ------
            mensaje: bytes
        """
        m = mensaje[1:]
        cont = 0
        ids =[]
        nombres = []
        m_c = m.decode()
        partes = m_c.split("|")
        partes = partes[1:]
        #obtenemos los ids
        for i in range(0, len(m)):
            b = m[i]
            if b == 124:
                cont += 1
                if cont % 2 == 1:
                    num = m[i+1:i+5]
                    ids.append(int.from_bytes(num,'big'))
                    i += 4
                else:
                    continue
        #obtenemos los nombres de archivos
        for i in range(0, len(partes)):
            if i % 2 == 1:
                nombres.append(partes[i])
        return [ids, nombres]

if __name__ == '__main__':
    cliente = Cliente('127.0.0.1', 9999)
    cliente.conectaServidor()
    cliente.recibeMensaje()
