import argparse
import json
from json.decoder import JSONDecodeError
import socket
import threading

HOST = "127.0.0.1"
DRONE_PORT = 65300


descripcion = "Estacion de tierra"

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
    parser.add_argument('--connect', action='store_true', dest='connect', default=False, help='CONNECT dron -> estacion de tierra')

    # IDs 
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')

    ## Alguna estrucura especial para los IDs?? Regex???

    args = parser.parse_args()

    x = threading.Thread(target=recv_thread, args=(args.et_id,))
    x.daemon = True
    x.start()

    while True:
        if args.register:
            print("REGISTER")
            if args.et_id:
                print("et_id:", args.et_id)
                register_estacion(args.et_id)
            else:
                print("ERROR: Debes proporcionar un et_id")

        elif args.link:
            print("LINK")
            if args.drone_id and args.et_id:
                print("drone_id:", args.drone_id)
                print("et_id:", args.et_id)
                link_drone_et(args.drone_id, args.et_id)
            else:
                print("ERROR: Debes proporcionar un drone_id y un et_id")
            
        elif args.unlink:
            print("UNLINK")
            if args.drone_id and args.et_id:
                print("drone_id:", args.drone_id)
                print("et_id:", args.et_id)
            else:
                print("ERROR: Debes proporcionar un drone_id y un et_id")

        elif args.connect:
            print("CONNECT")
            if args.drone_id and args.et_id:
                print("drone_id:", args.drone_id)
                print("et_id:", args.et_id)
            else:
                print("ERROR: Debes proporcionar un drone_id y un et_id")

        else:
            print("ERROR: Debes proporcionar un tipo de mensaje a enviar")
            return

        args.connect = False
        args.drone_id = False
        args.et_id = False
        args.register = False
        args.unlink = False

        command = input("Comando: ")
        args = parser.parse_args(command.split())    
        



    
    
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #    s.connect((HOST, DRONE_PORT))
    #    print("Connected to drone")
    #    s.sendall(b"Hello drone")
    #    data = s.recv(1024)
#
    #print(f"Received {data!r}")


def register_estacion(et_id):
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que no existe
            ids = [et["id"] for et in data]
            if et_id in ids:
                print("ERROR: La estacion con ID", et_id, "ya existe")
                return

            # Añadir nueva estacion con puertos libres
            maxPort = max([et["listens_bo"] for et in data])
            data.append({"id": et_id, "listens_bo": maxPort+1, "linked_drones": [], "files": "ets/" + et_id + "/files/"})

        except JSONDecodeError:
            # Primera entrada del json
            data = [{"id": et_id, "listens_bo": 65000,  "linked_drones": [], "files": "ets/" + et_id + "/files/"}]

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("REGISTEER completado con exito: estacion de tierra registrada con ID:", et_id)


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
                drone["linked_ets"].append(et_id)
                break

    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    # Si ambos existen, añadir a la lista de linked_drones de la estacion
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for et in data:
            if et["id"] == et_id:
                try:
                    et["linked_drones"].append(drone_id)
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
                    drone["linked_ets"].remove(et_id)
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
                et["linked_drones"].remove(drone_id)
                break

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    

    print("UNLINK completado con exito: dron", drone_id, "ahora ya no esta linkeado a la estacion de tierra", et_id)


def recv_thread(et_id):
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            for el in data:
                if el['id'] == et_id:
                    et_port = el['listens_bo']
                    print(et_port)

        except JSONDecodeError:
            print("ERROR: La estacion de tierra con ID", et_id, "no existe")
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, et_port))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    if not data: break
                    print(data.decode())


if __name__ == "__main__":
    main()