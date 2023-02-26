import argparse
import json
from json.decoder import JSONDecodeError
import socket

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
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")
        
    elif args.unlink:
        print("UNLINK")
        if args.drone_id:
            print("drone_id:", args.drone_id)
        else:
            print("ERROR: Debes proporcionar un drone_id")

    elif args.connect:
        print("CONNECT")
        if args.drone_id and args.et_id:
            print("drone_id:", args.drone_id)
            print("et_id:", args.et_id)
        else:
            print("ERROR: Debes proporcionar un drone_id y un et_id")

    else:
        print("ERROR: Debes proporcionar un tipo de mensaje a enviar")
    
    
    
    
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
            data.append({"id": et_id, "listens_bo": maxPort+1})

        except JSONDecodeError:
            # Primera entrada del json
            data = [{"id": et_id, "listens_bo": 66000}]

    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("Estacion de tierra registrada correctamente con ID:", et_id)


if __name__ == "__main__":
    main()