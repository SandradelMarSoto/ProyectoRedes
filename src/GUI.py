import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk
from cliente import Cliente
import threading
import time
import os
from proyectoDAO import DAO

class ManejadorSesion:
    """
     Clase ManejadorSesion que funciona como controlador conectando la vista de la aplicación con el modelo

        Atributos
        ---------
        self.builder = builder
            constructor que se conectará con la vista
        self.cliente = cliente
            objeto cliente
        self.dao = dao
            controlador de la base de dato
        Elementos del glade gtk que serán llamados para que la interfaz gráfica responda a la aplicación:
            self.ventanaIS
            self.ventanaReg
            self.dialogoIS
            self.dialogoReg
            self.dialogoRegExt
            self.dialogoDesc
            self.ventanaEPerf
            self.ventanaMenu
            self.ventanaImag
            self.imagenUsuario
            self.treeView
            self.selected
            self.file_list
        self.id_usuario = -1
            identificador del usuario
    """
    def __init__(self, builder, cliente, dao):
        self.builder = builder
        self.cliente = cliente
        self.dao = dao
        self.ventanaIS = self.builder.get_object("IniciaS")
        self.ventanaReg = builder.get_object("Registro")
        self.dialogoIS = builder.get_object("DialogoUsuario")
        self.dialogoReg = builder.get_object("DialogoRegistro")
        self.dialogoRegExt = builder.get_object("DialogoRegExt")
        self.dialogoDesc = builder.get_object("DialogoDescarga")
        self.ventanaEPerf = builder.get_object("EditaPerfil")
        self.ventanaMenu = builder.get_object("MenuUsuario")
        self.ventanaImag = builder.get_object("VisualizaImagen")
        self.imagenUsuario = builder.get_object("imagenUser")
        self.treeView = builder.get_object("imagesTreeView")
        self.selected = None
        self.file_list = Gtk.ListStore(str)
        self.id_usuario = -1
        self.setupTreeView()

    def cierra(self, *args):
        """
         Cierra la sesión del usuario
        """
        self.cliente.enviaMensaje(100, "")
        Gtk.main_quit()

    def iniciaSesion(self, *args):
        """
         Se mandan a llamar a las ventanas correspondientes a iniciar sesión, se envía la información
         introducida por el usuario al servidor y se interpreta su respuesta
        """
        usuario = self.builder.get_object("entradaUs")  # id de la entrada donde se pone el nombre de usuario
        contrasena = self.builder.get_object("entradaCont")  # id de la entrada para la contraseña
        codigo, m, valido = self.cliente.preparaMensaje("10|" + usuario.get_text() + "|" + contrasena.get_text())
        if valido:
            self.cliente.enviaMensaje(codigo, m)

        respuesta = self.cliente.mensajes.get()

        if respuesta[0] == 20:
            if respuesta[1] == 1:
                self.dialogoIS.run()
            else:
                nombre=respuesta[1:].decode()
                print("EXITO")
                self.ventanaIS.hide()
                usuario.set_text("")
                contrasena.set_text("")
                self.muestraMenu(nombre)
        else:
            print("ERROR")

    def ventanaRegistro(self, *args):
        """
            Mostramos la ventana de registro y cerramos la de inicio de sesión
        """
        self.ventanaIS.hide()
        self.ventanaReg.show()

    def ventanaInicio(self, *args):
        """
            Mostramos la ventana de inicio de sesión y cerramos la de registro
        """
        self.ventanaReg.hide()
        self.ventanaIS.show()

    def cierraDialogoIS(self, *args):
        """
            Cerramos el dialogo enviado cuando se introducen datos erróneos en el inicio de sesión
        """
        self.dialogoIS.hide()
        return True

    def cierraDialogoReg(self, *args):
        """
            Cerramos el dialogo enviado cuando se realiza un registro exitoso
        """
        self.dialogoReg.hide()
        return True

    def cierraDialogoExt(self, *args):
        """
            Cerramos el dialogo enviado cuando se intenta registrar el usuario con un nombre ya existente
        """
        self.dialogoRegExt.hide()
        return True

    def cierraDialogoDesc(self,*args):
        """
            Cerramos el dialogo enviado cuando se realiza una descarga de forma exitosa
        """
        self.dialogoDesc.hide()
        return True

    def registraUsuario(self, *args):
        """
         Se mandan a llamar a las ventanas correspondientes a registrar usuario, se envía la información
         introducida por el usuario al servidor y se interpreta su respuesta
        """
        usuario = self.builder.get_object("regUs")  # id de la entrada donde se pone el nombre de usuario
        contrasena = self.builder.get_object("regCont")  # id de la entrada para la contraseña
        codigo, m, valido = self.cliente.preparaMensaje("12|" + usuario.get_text() + "|" + contrasena.get_text())
        if valido:
            self.cliente.enviaMensaje(codigo, m)

        respuesta = self.cliente.mensajes.get()

        if respuesta[0] == 11:
            if respuesta[1] == 0:
                self.dialogoRegExt.run()
                usuario.set_text("")
                contrasena.set_text("")
            else:
                usuario.set_text("")
                self.dialogoReg.run()
        else:
            print("ERROR")

    def muestraMenu(self,nombre):
        """
            Se muestra el perfil del usuario así como su lista de archivos y se envía la información
            introducida por el usuario al servidor y se interpreta su respuesta
        """
        bienvenida = self.builder.get_object("bienvenida")
        bienvenida.set_text(bienvenida.get_text() + " " + nombre)
        obj_im_perfil = self.builder.get_object("imagenUser")
        self.id_usuario = self.dao.checaUsuario(nombre)
        imagen_perfil = self.dao.imagenPerfil(self.id_usuario)
        if(imagen_perfil != -1):
            loader = GdkPixbuf.PixbufLoader()
            loader.write(imagen_perfil)
            loader.close()
            nb_imagen_perfil = loader.get_pixbuf()
            nb_imagen_perfil = nb_imagen_perfil.scale_simple(360, 360, GdkPixbuf.InterpType.BILINEAR)
            obj_im_perfil.set_from_pixbuf(nb_imagen_perfil)
        self.ventanaMenu.show()
        self.muestraImagenes()
        self.muestraRestante()

    def muestraRestante(self, *args):
        """
            Busca la memoria restante del usuario y se la muestra en el menú
        """
        codigo, m, valido = self.cliente.preparaMensaje("31")
        if valido:
            self.cliente.enviaMensaje(codigo, m)
        respuesta = self.cliente.mensajes.get()
        label = self.builder.get_object("memoriaRestante")
        if respuesta[0] == 33:
            if respuesta[1] == 1:
                pass
            else:
                restante = int.from_bytes(respuesta[1:], 'big')
                label.set_text( "Su memoria restante es de: " + str(restante) + " MB")
        else:
            print("ERROR")


    def muestraImagenes(self, *args):
        """
            Se obtienen todas las imagenes que ha subido el usuario y se muestran en el menú
        """
        codigo, m, valido = self.cliente.preparaMensaje("41")
        if valido:
            self.cliente.enviaMensaje(codigo, m)

        respuesta = self.cliente.mensajes.get()
        if(respuesta[1] != 1):
            for imagen in respuesta[1]:
                self.file_list.append([imagen])

    def setupTreeView(self):
        """
            Llena el tree view donde se mostrarán los nombres de las imagenes
        """
        renderer = Gtk.CellRendererText()
        pathColumn = Gtk.TreeViewColumn(title='Nombre Imagen', cell_renderer=renderer, text=0)
        self.treeView.append_column(pathColumn)
        self.treeView.set_model(self.file_list)

    def set_selected(self, user_data):
        """
           Se guarda la imagen seleccionada en ese momento
        """
        selected = user_data.get_selected()[1]
        if selected:
            self.selected = selected

    def cambiarPerfil(self, *args):
        """
         Se mandan a llamar a las ventanas correspondientes a editar el perfil, se envía la información
         introducida por el usuario al servidor y se interpreta su respuesta
        """
        nuevoNombre = self.builder.get_object("regPerf").get_text()
        imagenPerfil = self.builder.get_object("escogePerf")
        rutaImagen = imagenPerfil.get_filename()
        codigo, m, valido = self.cliente.preparaMensaje("15|" + str(nuevoNombre) + "|" + str(rutaImagen))
        if valido:
            self.cliente.enviaArchivo(codigo, m)
        m = self.cliente.mensajes.get()
        print(m)
        if m[1] == 0:
            obj_im_perfil = self.builder.get_object("imagenUser")
            nuevaImagen = GdkPixbuf.Pixbuf.new_from_file(rutaImagen)
            nuevaImagen = nuevaImagen.scale_simple(360, 360, GdkPixbuf.InterpType.BILINEAR)
            obj_im_perfil.set_from_pixbuf(nuevaImagen)
            bienvenida = self.builder.get_object("bienvenida")
            bienvenida.set_text("Bienvenido a la aplicación " + nuevoNombre)
            self.cierraPerfil()

    def subirImagen(self, *args):
        """
         Se mandan a llamar a las ventanas correspondientes para subir una imagen, se envía la información
         introducida por el usuario al servidor y se interpreta su respuesta
        """
        nuevaImagen = self.builder.get_object("escogeImagen")
        rutaImagen = nuevaImagen.get_filename()
        nombre = os.path.basename(rutaImagen)
        nombre = os.path.splitext(nombre)[0]
        codigo, m, valido = self.cliente.preparaMensaje("32|"+str(nombre)+"|"+str(rutaImagen))
        if valido:
            self.cliente.enviaArchivo(codigo, m)
        exito = self.cliente.mensajes.get()
        if exito[1] == 0:
            self.file_list.append([nombre])
            self.muestraRestante()
        else:
            print("ERROR")

    def descargarImagen(self, *args):
        """
         Se manda a descargar el nombre de la imagen seleccionada
        """
        if self.selected is not None:
            nombre = self.file_list.get_value(self.selected, 0)
            codigo, m, valido = self.cliente.preparaMensaje("43|" + str(nombre))
            if valido:
                self.cliente.enviaMensaje(codigo, m)
            self.dialogoDesc.run()


    def verImagen(self, *args):
        """
         Se mandan a llamar al visualizador de imagenes para que se puedan mostrar las imagenes subidas por el cliente
        """
        self.ventanaImag.show()
        if self.selected is not None:
            nombre = self.file_list.get_value(self.selected, 0)
            codigo, m, valido = self.cliente.preparaMensaje("46|" + nombre)
            if valido:
                self.cliente.enviaMensaje(codigo, m)

        imagenIndividual = self.builder.get_object("imagenIndiv")
        respuesta = self.cliente.mensajes.get()
        imagen_res = respuesta[1:]
        loader = GdkPixbuf.PixbufLoader()
        loader.write(imagen_res)
        loader.close()
        imagen = loader.get_pixbuf()
        imagenIndividual.set_from_pixbuf(imagen)

    def cierraImag(self, *args):
        """
            Cierra el visualizador de imágenes
        """
        self.ventanaImag.hide()
        return True

    def ventanaPerfil(self, *args):
        """
            Abre la ventana para editar el perfil
        """
        self.ventanaEPerf.show()

    def cierraPerfil(self, *args):
        """
            Cierra el editor de perfil
        """
        self.ventanaEPerf.hide()
        return True

    def cierraSesion(self, *args):
        """
            Cierra la sesión del usuario
        """
        self.ventanaMenu.hide()
        self.builder.get_object("bienvenida").set_text("Bienvenido a la aplicación")
        self.ventanaIS.show()
        self.cliente.enviaMensaje(100, "")
        self.file_list.clear()
        self


if __name__ == '__main__':
    dao = DAO()
    cliente = Cliente('127.0.0.1', 9999)
    cliente.conectaServidor()
    t1 = threading.Thread(target=cliente.recibeMensaje)
    t1.setDaemon(True)
    t1.start()
    time.sleep(0.001)
    builder = Gtk.Builder()
    builder.add_from_file("../GUI/inicio_sesion.glade")
    m = ManejadorSesion(builder, cliente, dao)
    builder.connect_signals(m)
    m.ventanaIS.show_all()
    Gtk.main()
