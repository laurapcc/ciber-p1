import argparse
import json
from json.decoder import JSONDecodeError
import socket
import shutil
import os
import threading
import atexit
import time

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet



HOST = "127.0.0.1"
PORT = 65300

private_key = None

file_key = b'AOAeQpvbJ0Rl6vz26tjixCrnk0yf0OFNI5aeXOG8MqA='
file_fernet = None

descripcion = "Envia un comando a la base de operaciones"

def exit_handler():
    print("Borrando base de operaciones y saliendo.")
    os.remove("db/base.json")
    exit()


def main():
    global private_key
    global file_fernet

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

    # crear clave publica y privada
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    file_fernet = Fernet(file_key)

    try:
        jsonFile = open("db/base.json", "r+")
        data = json.load(jsonFile)

        if data:
            print("ERROR: ya hay base de operaciones")
            return

    except (JSONDecodeError, OSError):
        # Primera entrada del json
        data = [{"status": "active", "port": PORT, "public_key": key.publickey().export_key().decode("utf-8")}]

        with open("db/base.json", "w+") as jsonFile:
            data_json = json.dumps(data)
            cipher_data = file_fernet.encrypt(data_json.encode('utf-8'))
            jsonFile.write(cipher_data.decode('utf-8'))
            print("Base de operaciones esperando instrucciones")

    args = parser.parse_args()

    atexit.register(exit_handler)

    # poner a escuchar a la BO
    x = threading.Thread(target=recv_thread)
    x.daemon = True
    x.start()

    command = input("Comando: ")
    while True:
        try:
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
                #fly(args.drone_id)
                send_to_drone(args.drone_id, "FLY")
            else:
                print("ERROR: Debes proporcionar un drone_id")

        elif args.land:
            print("LAND")
            if args.drone_id:
                print("drone_id:", args.drone_id)
                #land(args.drone_id)
                send_to_drone(args.drone_id, "LAND")
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

    

def recv_thread():
    # recuperar el puerto en el que la BO escucha
    with open("db/base.json", "r") as jsonFile:
        try:
            #cipher_data = json.load(jsonFile)
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)
            bo_port = data[0]["port"]

        except JSONDecodeError:
            print("ERROR: La base de operaciones no está registrada")
            return

    # escuchar
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, bo_port))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)

                # recibir clave de sesion
                data = conn.recv(4096)
                if not data: break

                # descifrar clave de sesion con clave privada de la BO
                cipher = PKCS1_OAEP.new(RSA.import_key(private_key))
                session_key = cipher.decrypt(data)

                # descifrar mensaje recibido con clave de sesion
                data = conn.recv(4096)
                if not data: break
                fernet = Fernet(session_key)
                msg = fernet.decrypt(data).decode()
                print("Mensaje recibido: ", msg)


def send_msg(et_id, msg):
    # recuperar puerto en el que la ET escucha a la BO
    # recuperar clave publica de la ET
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

            ids = [et["id"] for et in data]
            if et_id not in ids:
                print("ERROR: La ET con ID", et_id, "no existe")
                return

            for el in data:
                if el['id'] == et_id:
                    et_port = el['listens_bo'] + 100
                    et_public_key = el['public_key']

        except JSONDecodeError:
            print("ERROR: No hay estaciones registradas")
            return

    # crear clave de sesion
    session_key = Fernet.generate_key()

    # enviar mensaje cifrado
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, et_port))

        # cifrar clave de sesion con clave publica del dron y enviar
        cipher = PKCS1_OAEP.new(RSA.import_key(et_public_key))
        cipher_msg = cipher.encrypt(session_key)
        s.sendall(cipher_msg)

        # cifrar mensaje con clave de sesion y enviar
        fernet = Fernet(session_key)
        msg_cipher = fernet.encrypt(msg.encode())
        s.sendall(msg_cipher)

        print("Mensaje enviado")
    return


def send_file(et_id, file):
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

            ids = [et["id"] for et in data]
            if et_id not in ids:
                print("ERROR: La ET con ID", et_id, "no existe")
                return

            #a = file.rfind("/")
            #file_name = file[a:]
            file_name = os.path.basename(file)

            for el in data:
                if el['id'] == et_id:
                    et_route = el['files']

        except JSONDecodeError:
            # Primera entrada del json
            print("ERROR: No hay estaciones registradas")
            return
    os.makedirs(os.path.dirname(et_route), exist_ok=True)
    shutil.copyfile(file, et_route + file_name)


def send_to_drone(drone_id, msg):
    # recuperar puerto en el que la ET escucha a la BO
    # recuperar clave publica de la ET
    with open("db/estaciones.json", "r") as jsonFile:
        try: 
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

            for et in data:
                if et["connected"] == drone_id:
                    et_port = et["listens_bo"]    
                    et_public_key = et["public_key"]  
        except JSONDecodeError:
            print("Error")
            return

    # crear clave de sesion
    session_key = Fernet.generate_key()

    # enviar mensaje cifrado
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, et_port + 100))

        # cifrar clave de sesion con clave publica del dron y enviar
        cipher = PKCS1_OAEP.new(RSA.import_key(et_public_key))
        cipher_msg = cipher.encrypt(session_key)
        s.sendall(cipher_msg)

        # cifrar mensaje con clave de sesion y enviar
        fernet = Fernet(session_key)
        msg_cipher = fernet.encrypt(msg.encode())
        s.sendall(msg_cipher)

        print("FLY enviado")
    

def fly(drone_id):
    with open("db/estaciones.json", "r") as jsonFile:
        try: 
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

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
        s.connect((HOST, et_port + 100))
        s.sendall("land".encode())
        print("LAND enviado")
    return


def get_status():
    print("ESTACIONES:")
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

            for el in data:
                for key, value in el.items():
                    if key not in ['public_key']:
                        print(key, value)
                print("-----")
        except JSONDecodeError:
            print("Error en get_status")
    print("DRONES:")
    with open("db/drones.json", "r") as jsonFile:
        try:
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

            for el in data:
                for key, value in el.items():
                    if key not in ['public_key']:
                        print(key, value)
                print("-----")
        except JSONDecodeError:
            print("Error en get_status")


def shutdown():
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            cipher_data = jsonFile.read()
            data_s = file_fernet.decrypt(cipher_data).decode('utf-8')
            data = json.loads(data_s)

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

if __name__ == "__main__":
    main()