import threading
import ssl
import socket

def server_tls

def drone_function():
    # Conectar con ot y et
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.connect(('ip_bo', puerto_bo))
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock3.connect(('ip_et', puerto_et))

    # Iniciar conexión SSL con actor 2 y actor 3

    # Enviar mensaje a actor 2
    

    # Recibir mensaje de actor 3
    

def bo_function():
    # Cargar certificado y clave privada
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key_bo.pem')

    # Conectar con ot y et
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.connect(('ip_bo', puerto_drone))
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock3.connect(('ip_et', puerto_et))

    # Iniciar conexión SSL con actor 2 y actor 3
    ssl_sock2 = context.wrap_socket(sock2, server_hostname='drone')
    ssl_sock3 = context.wrap_socket(sock3, server_hostname='et')

    # Enviar mensaje a actor 2
    ssl_sock2.send(b'Hola dron!')

    # Recibir mensaje de actor 3
    mensaje = ssl_sock3.recv(1024)
    print(mensaje)

def et_function():
    # Cargar certificado y clave privada
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key_et.pem')

    # Conectar con ot y et
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.connect(('ip_bo', puerto_drone))
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock3.connect(('ip_et', puerto_bo))

    # Iniciar conexión SSL con actor 2 y actor 3
    ssl_sock2 = context.wrap_socket(sock2, server_hostname='drone')
    ssl_sock3 = context.wrap_socket(sock3, server_hostname='bo')

    # Enviar mensaje a actor 2
    ssl_sock2.send(b'Hola base de operaciones!')

    # Recibir mensaje de actor 3
    mensaje = ssl_sock3.recv(1024)
    print(mensaje)


if __name__ == "__main__":

    functions = [drone_function, bo_function, et_function]
    for i in range(3):
        x = threading.Thread(target=functions[i])
        x.start()
