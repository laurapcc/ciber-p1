import argparse
import json
from json.decoder import JSONDecodeError
import os
import socket
import threading
import time


HOST = "127.0.0.1"
PORT = 65300

# FLYING o LAND
STATUS = "LAND"
BATTERY = 100
FLY_START_TIME = -1


descripcion = "Envia un comando a un dron"



def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPCIONES] [MENSAJE]...",
        description = descripcion,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Funciones
    parser.add_argument('--register', action='store_true', dest='register', default=False, help='REGISTRO dron')
    parser.add_argument('--link', action='store_true', dest='link', default=False, help='LINK dron -/-> estacion de tierra')
    parser.add_argument('--unlink', action='store_true', dest='unlink', default=False, help='UNLINK dron -/-> estacion de tierra')
    parser.add_argument('--connect', action='store_true', dest='connect', default=False, help='CONNECT dron -> estacion de tierra')

    # IDs
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')

    ## Alguna estrucura especial para los IDs?? Regex???

    args = parser.parse_args()

    if args.register:
        print("REGISTER")
        if args.drone_id:
            register_drone(args.drone_id)
        else:
            print("ERROR: Debes proporcionar un drone_id")

    elif args.link:
        print("LINK")
        if args.drone_id and args.et_id:
            link_drone_et(args.drone_id, args.et_id)
            # FIN
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")
        
    elif args.unlink:
        print("UNLINK")
        if args.drone_id and args.et_id:
            print("drone_id:", args.drone_id)
            print("et_id:", args.et_id)
            # TODO: eliminar de fichero
            unlink_drone_et(args.drone_id,args. et_id)
            # FIN
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")

    elif args.connect:
        print("CONNECT")
        if args.drone_id and args.et_id:
            print("drone_id:", args.drone_id)
            print("et_id:", args.et_id)
            # comprobar que drone y et estan linkeados
            listen_port = check_linked(args.drone_id, args.et_id)
            if not listen_port:
                print("ERROR: drone con id", args.drone_id, "y estacion con id", args.et_id, "no estan linkeados")
                return
            # TODO: ponerse a esuchar a ET: fly / disconnect
            # TODO: activar telemetry y seguir escuchando hasta LAND  
            telemetry_thread = threading.Thread(target=telemetry, args=(args.drone_id, listen_port+1,))
            telemetry_thread.daemon = True
            telemetry_thread.start()
            listen_to_et(listen_port)
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")

    else:
        print("ERROR: Debes proporcionar un tipo de mensaje a enviar")



    # TODO: comprobar que hay base de operaciones

    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #    s.bind((HOST, PORT))
    #    print("Listening on port", PORT)
    #    s.listen()
    #    conn, addr = s.accept()
    #    with conn:
    #        print(f"Connected by {addr}")
    #        while True:
    #            data = conn.recv(1024)
    #            print(f"Received {data!r}")
    #            if not data:
    #                break
    #            conn.sendall("Hello estacion".encode())



def register_drone(drone_id):
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que no existe
            ids = [drone["id"] for drone in data]
            if drone_id in ids:
                print("ERROR: El dron con ID", drone_id, "ya existe")
                return

            # Añadir nuevo drone con un puerto libre
            maxPort = max([drone["listens"] for drone in data])
            data.append({"id": drone_id, "listens": maxPort+2, "linked_ets": []})

        except JSONDecodeError:
            # Primera entrada del json
            data = [{"id": drone_id, "listens": 64001, "linked_ets": []}]

    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("REGISTEER completado con exito: drone registrado con ID:", drone_id)


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
                et["linked_drones"].append(drone_id)
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


def check_linked(drone_id, et_id):
    # Comprobar que drone y et estan linkeados
    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for drone in data:
                if drone["id"] == drone_id and et_id in drone["linked_ets"]:
                    return drone["listens"]
        except JSONDecodeError:
            print("ERROR")

    return False
        

def listen_to_et(listen_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, listen_port))
        print("Drone listening on port", listen_port)
        s.listen()
        conn, addr = s.accept()
        while True:
            data = recvall(conn)
            print(data)
            if data == "FLY":
                # TODO
                print("a volar")
                # FLY_START_TIME = time.time()
            elif data == "DISCONNECT":
                # TODO
                print("disconnect")
            elif data == "LAND":
                # TODO
                print("land")


def recvall(conn, buff_size=4096):
    data = b''
    while True:
        data += conn.recv(buff_size)
        if len(data) < buff_size:
            break
    return data.decode()


def telemetry(drone_id, et_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, et_port))
        except:
            print("ERROR: No se pudo conectar con la estacion de tierra")
            os._exit(1)

        while True:
            msg = telemetry_msg(drone_id)
            print(msg)
            try:
                s.sendall(msg.encode())
            except:
                print("ERROR while sending telemetry")
                return
            time.sleep(2)


def telemetry_msg(drone_id):
    global STATUS
    global BATTERY
    if STATUS == "FLYING":
        time_elapsed = time.time() - FLY_START_TIME
        BATTERY = round(time_elapsed*100/60, 2)
        if BATTERY == 0:
            # TODO: hacer land
            STATUS = "LAND"

    msg = {
        "drone_id": drone_id,
        "status": STATUS,
        "battery": BATTERY
    }

    return json.dumps(msg)

if __name__ == "__main__":
    main()