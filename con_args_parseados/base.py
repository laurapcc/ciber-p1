import argparse
import json
from json.decoder import JSONDecodeError
import socket

HOST = "127.0.0.1"
PORT = 65300



descripcion = "Envia un comando a una base"



def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPCIONES] [MENSAJE]...",
        description = descripcion,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Funciones
    parser.add_argument('--send_msg', action='store_true', dest='send_msg', default=False, help='Envio de mensaje')
    parser.add_argument('--send_file', action='store_true', dest='send_file', default=False, help='Envio de fichero')
    parser.add_argument('--FLY', action='store_true', dest='fly', default=False, help='Despegar dron')
    parser.add_argument('--LAND', action='store_true', dest='land', default=False, help='Aterrizar dron')
    parser.add_argument('--get_status', action='store_true', dest='get_status', default=False, help='Obtener estado de todos los sistemas')
    parser.add_argument('--shutdown', action='store_true', dest='shutdown', default=False, help='Apagar el sistema por completo')

    # IDs
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')
    parser.add_argument('--msg', dest='msg', default=False, help='Mensaje a enviar')
    parser.add_argument('--file', dest='file', default=False, help='Fichero a enviar')

    ## Alguna estrucura especial para los IDs?? Regex???

    args = parser.parse_args()

    if args.send_msg:
        print("SEND MESSAGE")
        if args.et_id and args.msg:
            send_msg(args.et_id, args.msg)
        else:
            print("ERROR: Debes proporcionar un et_id")

    elif args.send_file:
        print("SEND FILE")
        if args.et_id:
            print("et_id:", args.et_id)
            send_file(args.et_id)
            # FIN
        else:
            print("ERROR: Debes proporcionar un et_id")
        
    elif args.fly:
        print("FLY")
        if args.drone_id:
            print("drone_id:", args.drone_id)
            fly(args.drone_id)
        else:
            print("ERROR: Debes proporcionar un drone_id")

    elif args.land:
        print("LAND")
        if args.drone_id:
            print("drone_id:", args.drone_id)
            land(args.drone_id)
        else:
            print("ERROR: Debes proporcionar un drone_id")

    elif args.get_status:
        print("GET_STATUS")
        get_status()
    
    elif args.shutdown:
        print("SHUTDOWN")
        shutdown()
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



def send_msg(et_id, msg):
    print('TODO: send_msg')
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
                    ET_PORT = el['listens_bo']

        except JSONDecodeError:
            # Primera entrada del json
            print("ERROR: No hay estaciones registradas")
            return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, ET_PORT))
        s.sendall(msg)
        print("Mensaje enviado")
    return

def send_file(et_id):
    print('TODO: send_file')

def fly(drone_id):
    print('TODO: fly')

def land(drone_id):
    print('TODO: land')

def get_status():
    print('TODO: get_status')

def shutdown():
    print('TODO: shutdown')

if __name__ == "__main__":
    main()