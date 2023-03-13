import argparse
import json
from json.decoder import JSONDecodeError
import socket
import threading
import os
import shutil
import atexit
import time

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


HOST = "127.0.0.1"
DRONE_PORT = 65300

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
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPCIONES] [MENSAJE]...",
        description = descripcion,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Funciones
    parser.add_argument('--register', action='store_true', dest='register', default=False, help='REGISTRO estacion de tierra')
    parser.add_argument('--link', action='store_true', dest='link', default=False, help='LINK dron -/-> estacion de tierra')
    parser.add_argument('--unlink', action='store_true', dest='unlink', default=False, help='UNLINK dron -/-> estacion de tierra')
    #parser.add_argument('--connect', action='store_true', dest='connect', default=False, help='CONNECT dron -> estacion de tierra')
    parser.add_argument('--send_msg', action='store_true', dest='send_msg', default=False, help='Envio de mensaje')
    parser.add_argument('--send_file', action='store_true', dest='send_file', default=False, help='Envio de fichero')
    parser.add_argument('--info_to_bo', action='store_true', dest='bo', default=False, help='Enviar mensaje/fichero a BO')
    parser.add_argument('--fly', action='store_true', dest='fly', default=False, help='Indicar a un drone que incie el vuelo')
    parser.add_argument('--land', action='store_true', dest='land', default=False, help='Indicar a un drone que aterrice')
    parser.add_argument('--disconnect', action='store_true', dest='disconnect', default=False, help='Indicar a un drone que se desconecte')

    # IDs 
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')
    parser.add_argument('--msg', dest='msg', default=False, help='Mensaje a enviar')
    parser.add_argument('--file', dest='file', default=False, help='Fichero a enviar')

    ## Alguna estrucura especial para los IDs?? Regex???

    args = parser.parse_args()

    atexit.register(exit_handler, args=args.et_id)

    ##Cada vez que se inicie el programa habrá que registrar la estacion y al cerrarlo se borra
    if args.register:
        print("REGISTER")
        if args.et_id:
            # Comprobar si la BO está conectada
            try:
                jsonFile = open("db/base.json", "r")
            except:
                print("ERROR: no hay base de datos")
                return

            print("et_id:", args.et_id)
            et_id = args.et_id
            register_estacion(args.et_id)
        else:
            print("ERROR: Debes proporcionar un et_id")

    else:
        print("ERROR: primero debes registrar la estacion")
        return

    x = threading.Thread(target=recv_thread_et, args=(args.et_id,))
    x.daemon = True
    x.start()
    y = threading.Thread(target=recv_thread_bo, args=(args.et_id,))
    y.daemon = True
    y.start()


    command = input("Comando: ")
    while True:
        try:
            #Para que el mensaje pueda contener espacios lo recogemos como todo el texto entre comillas, suponiendo que no habra otro texto entre comillas
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
            if args.drone_id:
                print("drone_id:", args.drone_id)
                link_drone_et(args.drone_id, et_id)
            else:
                print("ERROR: Debes proporcionar un drone_id")
            
        elif args.unlink:
            print("UNLINK")
            if args.drone_id:
                print("drone_id:", args.drone_id)
                unlink_drone_et(args.drone_id, et_id)
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.fly:
            print("FLY")
            if args.drone_id:
                print("drone_id:", args.drone_id)
                send_fly(args.drone_id)
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.land:
            print("LAND")
            if args.drone_id:
                print("drone_id:", args.drone_id)
                send_land(args.drone_id)
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.disconnect:
            print("DISCONNECT")
            if args.drone_id:
                print("drone_id:", args.drone_id)
                send_disconnect(args.drone_id)
            else:
                print("ERROR: Debes proporcionar un drone_id")

        else:
           print("ERROR: Debes proporcionar un tipo de mensaje a enviar")
           parser.print_help()

        command = input("Comando: ")

           



def registered(et_id):
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


#TODO: añadir puerto para escuchar a la bo
def register_estacion(et_id):
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
                data.append({"id": et_id, "listens_bo": maxPort+1, "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")})
            # Caso en que en el json hay una lista vacia
            else:
                data = [{"id": et_id, "listens_bo": 64000,  "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")}]
        except JSONDecodeError:
            # Primera entrada del json
            data = [{"id": et_id, "listens_bo": 64000,  "linked_drones": [], "files": "ets/" + et_id + "/files/", "public_key": key.publickey().export_key().decode("utf-8")}]

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("REGISTER completado con exito: estacion de tierra registrada con ID:", et_id)



def link_drone_et(drone_id, et_id):
    # Dron existe
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que existe
            ids = [drone["id"] for drone in data]
            if drone_id not in ids:
                print("ERROR: El dron con ID", drone_id, "no existe")
                return

        except JSONDecodeError:
            print("ERROR: El dron con ID", drone_id, "no existe")
            return
    
    # Estacion de tierra existe
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que existe
            ids = [et["id"] for et in data]
            if et_id not in ids:
                print("ERROR: La estacion de tierra con ID", et_id, "no existe")
                return

        except JSONDecodeError:
            print("ERROR: La estacion de tierra con ID", et_id, "no existe")
            return
        
    # Si ambos existen, añadir a la lista de linked_ets del dron
    with open("db/drones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for drone in data:
            if drone["id"] == drone_id:
                drone["linked_ets"].append(et_id) if et_id not in drone["linked_ets"] else drone["linked_ets"]

    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    # Si ambos existen, añadir a la lista de linked_drones de la estacion
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for et in data:
            if et["id"] == et_id:
                try:
                    et["linked_drones"].append(drone_id) if drone_id not in et["linked_drones"] else et["linked_drones"]
                except:
                    et["linked_drones"] = [drone_id]
                break

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    
    print("LINK completado con exito: dron", drone_id, "ahora esta linkeado a la estacion de tierra", et_id)


def unlink_drone_et(drone_id, et_id):
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone["id"] == drone_id:
                    try:
                        drone["linked_ets"].remove(et_id)
                    except:
                        print("ET y drone no estaban linkeados")
                    break

        except JSONDecodeError:
            print("ERROR")
            return
    
    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for et in data:
            if et["id"] == et_id:
                try:
                    et["linked_drones"].remove(drone_id)
                except:
                    print("ET y drone no estaban linkeados")
                break

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    

    print("UNLINK completado con exito: dron", drone_id, "ahora ya no esta linkeado a la estacion de tierra", et_id)

def get_drone_id(et_id):
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
    et_port = get_et_port(et_id)
    print("thread bo iniciado")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, et_port + 100))
            print("Escuchando en puerto", et_port+100)
            s.listen(1)
            print("Escuchando en puerto", et_port+100)
            while True:
                time.sleep(0.5)
                conn, addr = s.accept()
                print(HOST, et_port)
                with conn:
                    print('Connected by', addr)
                    while True:
                        data = conn.recv(1024)
                        if not data: break
                        msg = data.decode(errors='ignore')
                        print(msg)
                        drone_id = get_drone_id(et_id)
                        if msg == 'fly':
                            send_fly(drone_id)
                        elif msg == 'land':
                            print(1)
                            send_land(drone_id)
                        elif msg == 'kill':
                            if drone_id:
                                kill_drone(et_id)
                            exit_handler(et_id)


def recv_thread_et(et_id):
    def recvall(sock):
        BUFF_SIZE = 4096 # 4 KiB
        fragments = []
        while True: 
            chunk = sock.recv(BUFF_SIZE)
            fragments.append(chunk)
            # if the following line is removed, data is omitted
            time.sleep(0.005)
            if len(chunk) < BUFF_SIZE: 
                break
            
        data = b''.join(fragments)
        return data
        
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            et_port = 0
            for el in data:
                if el['id'] == et_id:
                    et_port = el['listens_bo']
                    print("ET", et_id, "escuchando en puerto", et_port)
            if not et_port:
                print("ERROR: la estacion de tierra con ID: " + et_id + " no está registrada")

        except JSONDecodeError:
            print("ERROR: No hay estaciones de tierra")
            return

    # recibir clave de session cifrada
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, et_port))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                cipher = PKCS1_OAEP.new(RSA.import_key(private_key))
                session_key = cipher.decrypt(data)
                print("Clave de sesion recibida")
                print(session_key)

    # escuchar telemetry         
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, et_port))
            print("Escuchando en puerto", et_port)
            s.listen(1)
            print("Escuchando en puerto", et_port)
            while True:
                time.sleep(0.5)
                conn, addr = s.accept()
                print(HOST, et_port)
                with conn:
                    print('Connected by', addr)
                    while True:
                        data = conn.recv(1024)
                        if not data: break
                        msg = data.decode(errors='ignore')
                        print("Telemetry: " + msg)
                        #Esto es una tremenda ñapa pero no se me ocurre otra cosa para matar el thread
                        with open("db/estaciones.json", "r") as jsonFile:
                            try:
                                data = json.load(jsonFile)
                                if not data:
                                    return

                            except JSONDecodeError:
                                print("Matando thread")
                                return
                        

def send_msg(bo, et_id, msg):
    print('TODO: send_msg con espacios')
    if bo:
        with open("db/base.json", "r") as jsonFile:
            try:
                data = json.load(jsonFile)
                PORT = data[0]["port"]

            
            except (JSONDecodeError, OSError):
                print("ERROR: la base de operaciones no esta activa")
                return

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
                        PORT = el['listens_bo']

            except JSONDecodeError:
                # Primera entrada del json
                print("ERROR: No hay estaciones registradas")
                return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(msg.encode())
        print("Mensaje enviado")
    return

def send_file(bo, et_id, file):
    if bo:
        # enviar file a la BO
        pass
    else:
        with open("db/estaciones.json", "r") as jsonFile:
            try:
                data = json.load(jsonFile)

                ids = [et["id"] for et in data]
                if et_id not in ids:
                    print("ERROR: La ET con ID", et_id, "no existe")
                    return

                a = file.rfind("/")

                file_name = file[a:]

                for el in data:
                    if el['id'] == et_id:
                        et_route = el['files']

            except JSONDecodeError:
                # Primera entrada del json
                print("ERROR: No hay estaciones registradas")
                return
        os.makedirs(os.path.dirname(et_route), exist_ok=True)
        shutil.copyfile(file, et_route + file_name)

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




def send_fly(drone_id):
    #with open("db/estaciones.json", "r") as jsonFile:
    #    try:
    #        data = json.load(jsonFile)
    #        for et in data:
    #            if et['id'] == et_id:
    #                drone_id = drone['connected']
    #                break
    #            return
    #    except:
    #        print("ERROR")


    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone['id'] == drone_id:
                    drone_port = drone['listens']
                    break
                return
        except:
            print("ERRROR")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, drone_port))
            s.sendall("FLY".encode())
            print("FLY enviado")
        except:
            print("ERROR: ET y dron no conectados")

        
def send_land(drone_id):
    #with open("db/estaciones.json", "r") as jsonFile:
    #    try:
    #        data = json.load(jsonFile)
    #        for et in data:
    #            if et['id'] == et_id:
    #                drone_id = drone['connected']
    #                break
    #            return
    #    except:
    #        print("ERROR")

    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone['id'] == drone_id:
                    drone_port = drone['listens']
                    break
                return
        except:
            print("ERRROR")
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, drone_port))
            s.sendall("LAND".encode())
            print("LAND enviado")
        except:
            print("ERROR: ET y dron no conectados")


def send_disconnect(drone_id):
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone['id'] == drone_id:
                    drone_port = drone['listens']
                    break
                return 
        except:
            print("ERRROR")
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, drone_port))
            s.sendall("DISCONNECT".encode())
            print("DISCONNECT enviado")
        except:
            print("ERROR: ET y dron no conectados")
        
       

if __name__ == "__main__":
    main()