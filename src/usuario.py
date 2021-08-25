class Usuario():
    """Clase que crea un objeto para el usuario."""

    def __init__(self, nombre_usuario, password):
        self.nombre_usuario = nombre_usuario
        self.password = password
        self.imagen_perfil = "./path"
