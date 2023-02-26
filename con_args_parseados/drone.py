import argparse
import json
from json.decoder import JSONDecodeError
import socket

HOST = "127.0.0.1"
PORT = 65300



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
            print("drone_id:", args.drone_id)
            print("et_id:", args.et_id)
            #TODO: registrar en fichero
            link_drone_et(args.drone_id, args.et_id)
            # FIN
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")
        
    elif args.unlink:
        print("UNLINK")
        if args.drone_id:
            print("drone_id:", args.drone_id)
            # TODO: eliminar de fichero
            # FIN
        else:
            print("ERROR: Debes proporcionar un drone_id")

    elif args.connect:
        print("CONNECT")
        if args.drone_id and args.et_id:
            print("drone_id:", args.drone_id)
            print("et_id:", args.et_id)
            # TODO: comprobar en ficher que drone y et estan asociados
            # TODO: ponerse a esuchar a ET: fly / disconnect
            # TODO: si llega FLY de ET activar thread2: telemetry y seguir escuchando hasta LAND  
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
    
    print("Drone registrado correctamente con ID:", drone_id)


def link_drone_et(drone_id, et_id):
    print("TODO: link")


if __name__ == "__main__":
    main()