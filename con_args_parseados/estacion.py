import argparse
import json
from json.decoder import JSONDecodeError
import socket
import threading
import select
import os
import shutil
import atexit
import time

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet



HOST = "127.0.0.1"
DRONE_PORT = 65300

CONNECTED = False

private_key = None


descripcion = "Estacion de tierra"

def exit_handler(args):
    print("Borrando estacion y saliendo.")
    # TODO: borrar todo rastro de esta ET en drones.json
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)
        new_data = []
        for et in data:
            if et["id"] != args:
                new_data.append(et)
    
    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(new_data, jsonFile)
    exit()


def main():
    global CONNECTED

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPCIONES] [MENSAJE]...",
        description = descripcion,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Funciones
    parser.add_argument('--register', action='store_true', dest='register', default=False, help='REGISTRO estacion de tierra')
    parser.add_argument('--link', action='store_true', dest='link', default=False, help='LINK dron -/-> estacion de tierra')
    parser.add_argument('--unlink', action='store_true', dest='unlink', default=False, help='UNLINK dron -/-> estacion de tierra')
    parser.add_argument('--send_msg', action='store_true', dest='send_msg', default=False, help='Envio de mensaje')
    parser.add_argument('--send_file', action='store_true', dest='send_file', default=False, help='Envio de fichero')
    parser.add_argument('--info_to_bo', action='store_true', dest='bo', default=False, help='Enviar mensaje/fichero a BO')
    parser.add_argument('--fly', action='store_true', dest='fly', default=False, help='Indicar a un drone que incie el vuelo')
    parser.add_argument('--land', action='store_true', dest='land', default=False, help='Indicar a un drone que aterrice')
    parser.add_argument('--disconnect', action='store_true', dest='disconnect', default=False, help='Indicar a un drone que se desconecte')

    # INFO
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')
    parser.add_argument('--msg', dest='msg', default=False, help='Mensaje a enviar')
    parser.add_argument('--file', dest='file', default=False, help='Fichero a enviar')

    args = parser.parse_args()

    atexit.register(exit_handler, args=args.et_id)

    if args.register:
        print("REGISTER")
        if args.et_id:
            # Comprobar si la BO está conectada
            try:
                open("db/base.json", "r")
            except:
                print("ERROR: no hay base de datos")
                return

            et_id = args.et_id
            register_estacion(args.et_id)
        else:
            print("ERROR: Debes proporcionar un et_id")

    else:
        print("ERROR: primero debes registrar la estacion")
        return

    # Poner a la ET a escuchar a drones
    x = threading.Thread(target=recv_thread_drone, args=(args.et_id,))
    x.daemon = True
    x.start()

    # Poner a la ET a escuchar a la BO
    y = threading.Thread(target=recv_thread_bo, args=(args.et_id,))
    y.daemon = True
    y.start()

    # Poner a la ET a escuchar a la consola
    command = input("Comando: ")
    while True:
        try:
            # Para que el mensaje pueda contener espacios lo recogemos como todo el texto entre comillas, suponiendo que no habra otro texto entre comillas
            try:
                i = command.index('"')
                j = command.index('"', i+1)
                args = parser.parse_args(command.split()) 
                args.msg = command[i+1,j]
            except ValueError:
                args = parser.parse_args(command.split()) 
        except:
            print("ERROR: Comando no reconocido")
            parser.print_help()
            command = input("Comando: ")
            continue

        if args.send_msg:
            print("SEND MESSAGE")
            if (args.et_id or args.bo) and args.msg:
                send_msg(args.bo, args.et_id, args.msg)
            else:
                print("ERROR: Debes proporcionar un mensaje y si el mensaje va a otra ET o la BO")

        elif args.send_file:
            print("SEND FILE")
            if (args.et_id or args.bo) and args.file:
                send_file(args.bo, args.et_id, args.file)
            else:
                print("ERROR: Debes proporcionar la ruta del archivo y si va dirigido a otra ET o la BO")

        elif args.link:
            print("LINK")
            #if args.drone_id:
            #    link_drone_et(args.drone_id, et_id)
            #else:
            #    print("ERROR: Debes proporcionar un drone_id")
            link_et(et_id)
            
        elif args.unlink:
            print("UNLINK")
            #if args.drone_id:
            #    unlink_drone_et(args.drone_id, et_id)
            #else:
            #    print("ERROR: Debes proporcionar un drone_id")
            unlink_et(et_id)

        elif args.fly:
            print("FLY")
            if args.drone_id:
                send_to_drone(args.drone_id, "FLY")
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.land:
            print("LAND")
            if args.drone_id:
                send_to_drone(args.drone_id, "LAND")
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.disconnect:
            print("DISCONNECT")
            if args.drone_id:
                send_to_drone(args.drone_id, "DISCONNECT")
                CONNECTED = False
            else:
                print("ERROR: Debes proporcionar un drone_id")

        else:
           print("ERROR: Debes proporcionar un tipo de mensaje a enviar")
           parser.print_help()

        print(CONNECTED)
        command = input("Comando: ")

           

def registered(et_id):
    """
    Comprueba si una estacion de tierra esta registrada
    et_id: id de la estacion de tierra
    """
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que existe
            ids = [et["id"] for et in data]
            if et_id in ids:
                return True

        except JSONDecodeError:
            print("ERROR: no hay entradas registradas")
    
    return False


def register_estacion(et_id):
    """
    Registra una estacion de tierra
    et_id: id de la estacion de tierra a registrar
    """
    global private_key

    # Crear clave publica y privada
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')

    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            if data:
                # Comprobar que no existe
                ids = [et["id"] for et in data]
                if et_id in ids:
                    print("ERROR: La estacion con ID", et_id, "ya existe")
                    os._exit(1)

                # Añadir nueva estacion con puertos libres
                maxPort = max([et["listens_bo"] for et in data])
                data.append({"id": et_id, "linked": False, "listens_bo": maxPort+1, "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")})
        
            else: # Caso en que en el json hay una lista vacia
                data = [{"id": et_id, "linked": False, "listens_bo": 64000,  "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")}]

        except JSONDecodeError: # Primera entrada del json
            data = [{"id": et_id, "linked": False, "listens_bo": 64000,  "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")}]

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("REGISTER completado con exito: estacion de tierra registrada con ID:", et_id)


def link_et(et_id):
    """
    Enlaza una estacion de tierra con la base de operaciones
    et_id: id de la estacion de tierra a enlazar
    """
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for et in data:
                if et["id"] == et_id:
                    et["linked"] = True
                    break
        except JSONDecodeError:
            print("ERROR al abrir la base de datos de ET")
            return
        
    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    print("LINK completado con exito: ET con ID", et_id, "enlazada con la BO")
        

def unlink_et(et_id):
    """
    Desenlaza una estacion de tierra con la base de operaciones
    et_id: id de la estacion de tierra a desenlazar
    """
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for et in data:
                if et["id"] == et_id:
                    et["linked"] = False
                    break
        except JSONDecodeError:
            print("ERROR al abrir la base de datos de ET")
            return
    
    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("UNLINK completado con exito: ET con ID", et_id, "desenlazada con la BO")


def get_drone_id(et_id):
    """
    Devuelve el id del drone conectado a una estacion de tierra
    et_id: id de la estacion de tierra
    """
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for et in data:
            if et["id"] == et_id:
                try:
                    drone_id = et["connected"]
                except:
                    print("ET y drone no estaban conectados")
                    return False
    return drone_id


def get_et_port(et_id):
    """
    Devuelve el puerto en el que la ET con id et_id escucha a la BO
    et_id: id de la estacion de tierra
    """
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            et_port = 0
            for el in data:
                if el['id'] == et_id:
                    et_port = el['listens_bo']
            if not et_port:
                print("ERROR: la estacion de tierra con ID: " + et_id + " no está registrada")

        except JSONDecodeError:
            print("ERROR: No hay estaciones de tierra")
            return
    return et_port


def recv_thread_bo(et_id):
    """
    Thread que escucha a la base de operaciones
    et_id: id de la estacion de tierra que escucha
    """
    et_port = get_et_port(et_id)
    print("thread bo iniciado")

    # escuchar a la BO
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, et_port + 100))
            s.listen(1)
            while True:
                #time.sleep(0.5)
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    
                    while True:
                        # recibir clave de session
                        data = conn.recv(4096)
                        if not data: break

                        # descifrar clave de sesion con clave privada de la ET
                        cipher = PKCS1_OAEP.new(RSA.import_key(private_key))
                        session_key = cipher.decrypt(data)
                        print("Clave de sesion recibida:")
                        print(session_key)

                        # descifrar mensaje recibido con clave de sesion
                        data = conn.recv(4096)
                        if not data: break
                        fernet = Fernet(session_key)
                        msg = fernet.decrypt(data).decode()
                        print("Mensaje recibido: ", msg)

                        drone_id = get_drone_id(et_id)
                        if msg == 'FLY':
                            send_to_drone(drone_id, "FLY")
                        elif msg == 'LAND':
                            send_to_drone(drone_id, "LAND")
                        elif msg == 'kill':
                            if drone_id:
                                kill_drone(et_id)
                            exit_handler(et_id)


def recv_thread_drone(et_id):
    """
    Thread que escucha a un drone
    et_id: id de la estacion de tierra que escucha
    """
    global CONNECTED
    et_port = get_et_port(et_id)

    while True:
        print("thread drone iniciado")
        # recibir clave de session cifrada
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, et_port))
                s.listen(1)
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    cipher = PKCS1_OAEP.new(RSA.import_key(private_key))
                    session_key = cipher.decrypt(data)
                    print("Clave de sesion de conexion con dron recibida")
                    print(session_key)
        
        CONNECTED = True

        # escuchar telemetry         
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, et_port))
                print("Escuchando a dron en puerto", et_port)
                s.listen(1)
                print("Escuchando a dron fen puerto", et_port)
                while CONNECTED:
                    r, _, _ = select.select([s, CONNECTED], [], [], None)
                    if s in r:
                        conn, addr = s.accept()
                        print(HOST, et_port)
                        with conn:
                            print('Connected by', addr)
                            while True:
                                data = conn.recv(4096)
                                if not data: break

                                # descifrar mensaje recibido con clave de sesion
                                fernet = Fernet(session_key)
                                msg = fernet.decrypt(data).decode()
                                print("Telemetry: " + msg)

                                # parar el thread 
                                with open("db/estaciones.json", "r") as jsonFile:
                                    try:
                                        data = json.load(jsonFile)
                                        if not data:
                                            return

                                    except JSONDecodeError:
                                        print("Matando thread")
                                        return
                    if not CONNECTED:
                        break
        print("fin de escucha de dron, pero me pongo a esperar otra vez")
                            




def send_msg(bo, et_id, msg):
    # TODO: send_msg con espacios

    # enviar mensaje a la BO
    if bo:
        # recuperar puerto en el que la BO escucha a al ET
        # recuperar clave publica de la BO
        with open("db/base.json", "r") as jsonFile:
            try:
                data = json.load(jsonFile)
                port = data[0]["port"]
                public_key = data[0]["public_key"]
            
            except (JSONDecodeError, OSError):
                print("ERROR: la base de operaciones no esta activa")
                return

    # enviar mensaje a otra ET
    else: 
        with open("db/estaciones.json", "r") as jsonFile:
            try:
                data = json.load(jsonFile)

                ids = [et["id"] for et in data]
                if et_id not in ids:
                    print("ERROR: La ET con ID", et_id, "no existe")
                    return

                # Añadir nuevo drone con un puerto libre
                for el in data:
                    if el['id'] == et_id:
                        port = el['listens_bo']
                        public_key = el['public_key']

            except JSONDecodeError:
                # Primera entrada del json
                print("ERROR: No hay estaciones registradas")
                return

    # crear clave de sesion
    session_key = Fernet.generate_key()
    print("session_key: ", session_key)

    # enviar mensaje cifrado
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, port))

            # cifrar clave de sesion con clave publica del dron y enviar
            cipher = PKCS1_OAEP.new(RSA.import_key(public_key))
            cipher_msg = cipher.encrypt(session_key)
            s.sendall(cipher_msg)

            # cifrar mensaje con clave de sesion y enviar
            fernet = Fernet(session_key)
            msg_cipher = fernet.encrypt(msg.encode())
            s.sendall(msg_cipher)

            print("Mensaje enviado")
        except:
            print("ERROR al enviar mensaje")


def send_file(bo, et_id, file):
    if bo: # enviar a la BO
        route = 'bo/files/'
    else: # enviar a otra ET
        with open("db/estaciones.json", "r") as jsonFile:
            try:
                data = json.load(jsonFile)

                ids = [et["id"] for et in data]
                if et_id not in ids:
                    print("ERROR: La ET con ID", et_id, "no existe")
                    return

                for el in data:
                    if el['id'] == et_id:
                        route = el['files']

            except JSONDecodeError:
                # Primera entrada del json
                print("ERROR: No hay estaciones registradas")
                return
            
    #a = file.rfind("/")
    #file_name = file[a:]
    file_name = os.path.basename(file)


    os.makedirs(os.path.dirname(route), exist_ok=True)
    shutil.copyfile(file, route + file_name)


def get_drone_port(drone_id):
    with open("db/drones.json", "r") as jsonFile:
        try: 
            data = json.load(jsonFile)
            for el in data:
                if el["id"] == drone_id:
                    drone_port = el["listens"]
            return drone_port
        except JSONDecodeError:
            print("ERROR buscando puerto de dron")


def kill_drone(et_id):
    drone_id = get_drone_id(et_id)
    drone_port = get_drone_port(drone_id)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, drone_port))
        s.sendall("kill".encode())
        print("SHUTDOWN enviado")
    return



def send_to_drone(drone_id, msg):
    """
    Enviar un mensaje a un dron
    drone_id: id del dron al que se le envia el mensaje
    msg: mensaje a enviar como string
    """
    # recuperar puerto en el que el dron escucha a al ET
    # recuperar clave publica del dron
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone['id'] == drone_id:
                    drone_port = drone['listens']
                    drone_public_key = drone['public_key']
                    break
                return
        except:
            print("ERRROR")
            return

    # crear clave de sesion
    session_key = Fernet.generate_key()
    print("session_key: ", session_key)

    # enviar mensaje cifrado
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, drone_port))

            # cifrar clave de sesion con clave publica del dron y enviar
            cipher = PKCS1_OAEP.new(RSA.import_key(drone_public_key))
            cipher_msg = cipher.encrypt(session_key)
            s.sendall(cipher_msg)

            # cifrar mensaje con clave de sesion y enviar
            fernet = Fernet(session_key)
            msg_cipher = fernet.encrypt(msg.encode())
            s.sendall(msg_cipher)

            print(msg + " enviado")
        except:
            print("ERROR: ET y dron no conectados")

       

if __name__ == "__main__":
    main()