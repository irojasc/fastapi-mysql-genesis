from passlib.context import CryptContext
import bcrypt

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    """
    Esta función toma una contraseña y la codifica utilizando bcrypt.

    :param password: La contraseña que se quiere codificar.
    :return: El hash de la contraseña codificada en bcrypt.
    """
    # Generar un salt de bcrypt
    salt = bcrypt.gensalt()

    # Codificar la contraseña con el salt generado
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Retornar el hash como una cadena
    return hashed_password.decode('utf-8')