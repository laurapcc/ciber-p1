import argparse
import json
from json.decoder import JSONDecodeError
import socket
import shutil
import os
import threading
import atexit
import time

HOST = "127.0.0.1"
PORT = 65300



descripcion = "Envia un comando a la base de operaciones"

def exit_handler():
    print("Borrando base de operaciones y saliendo.")
    os.remove("db/base.json")
    exit()
    # NOTA: si dejamos el archivo luego peta por index out of range al abrir
    #       si lo borramos nos ahorramos ese problem
    ##with open("db/base.json", "r") as jsonFile:
    ##    new_data = []

    ##with open("db/base.json", "w") as jsonFile:
    ##    json.dump(new_data, jsonFile)


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPCIONES] [MENSAJE]...",
        description = descripcion,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Funciones
    parser.add_argument('--send_msg', action='store_true', dest='send_msg', default=False, help='Envio de mensaje')
    parser.add_argument('--send_file', action='store_true', dest='send_file', default=False, help='Envio de fichero')
    parser.add_argument('--fly', action='store_true', dest='fly', default=False, help='Despegar dron')
    parser.add_argument('--land', action='store_true', dest='land', default=False, help='Aterrizar dron')
    parser.add_argument('--get_status', action='store_true', dest='get_status', default=False, help='Obtener estado de todos los sistemas')
    parser.add_argument('--shutdown', action='store_true', dest='shutdown', default=False, help='Apagar el sistema por completo')

    # IDs
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')
    parser.add_argument('--msg', dest='msg', default=False, help='Mensaje a enviar')
    parser.add_argument('--file', dest='file', default=False, help='Fichero a enviar')

    ##TODO: Alguna estrucura especial para los IDs?? Regex???

    try:
        jsonFile = open("db/base.json", "r")
        data = json.load(jsonFile)

        if data:
            print("ERROR: ya hay base de operaciones")
            return

    except (JSONDecodeError, OSError):
        # Primera entrada del json
        data = [{"status": "active", "port": PORT}]

        with open("db/base.json", "w+") as jsonFile:
            json.dump(data, jsonFile)
            print("Base de operaciones esperando instrucciones")

    args = parser.parse_args()

    atexit.register(exit_handler)

    x = threading.Thread(target=recv_thread)
    x.daemon = True
    x.start()

    command = input("Comando: ")
    #TODO: Si llega un comando raro solucionar los except para que no se cierre
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
            if args.et_id and args.msg:
                send_msg(args.et_id, args.msg)
            else:
                print("ERROR: Debes proporcionar un et_id")

        elif args.send_file:
            print("SEND FILE")
            if args.et_id:
                print("et_id:", args.et_id)
                send_file(args.et_id, args.file)
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
            parser.print_help()


        args.fly = False
        args.land = False
        args.get_status = False
        args.sgutdown = False
        args.send_msg = False
        args.send_file = False
        args.drone_id = False
        args.et_id = False
        args.msg = False
        args.file = False

        command = input("Comando: ")
        # args = parser.parse_args(command.split()) 

    

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

def recv_thread():
    with open("db/base.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            bo_port = data[0]["port"]

        except JSONDecodeError:
            print("ERROR: La base de operaciones no está registrada")
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, bo_port))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    if not data: break
                    print(data.decode())



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
        s.sendall(msg.encode())
        print("Mensaje enviado")
    return

def send_file(et_id, file):
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

def fly(drone_id):
    with open("db/estaciones.json", "r") as jsonFile:
        try: 
            data = json.load(jsonFile)

            for et in data:
                if et["connected"] == drone_id:
                    et_port = et["listens_bo"]      
        except JSONDecodeError:
            print("Error")
            return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, et_port + 100))
        s.sendall("fly".encode())
        print("FLY enviado")
    return
    

def land(drone_id):
    with open("db/estaciones.json", "r") as jsonFile:
        try: 
            data = json.load(jsonFile)

            for et in data:
                if et["connected"] == drone_id:
                    et_port = et["listens_bo"]      
        except JSONDecodeError:
            print("Error")
            return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, et_port))
        s.sendall("land".encode())
        print("LAND enviado")
    return

def get_status():
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            for el in data:
                et_port = el["listens"] + 100
        except:
            pass


def shutdown():
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            for el in data:
                et_port = el["listens_bo"] + 100
                send_kill(et_port)
        except JSONDecodeError:
            print("Error en shutdown")
    return


def send_kill(et_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, et_port))
        s.sendall("kill".encode())
        print("SHUTDOWN enviado")
    exit_handler()
    return

if __name__ == "__main__":
    main()