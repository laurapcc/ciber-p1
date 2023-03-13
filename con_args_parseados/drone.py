import argparse
import json
from json.decoder import JSONDecodeError
import os
import select
import socket
import threading
import time
import atexit

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad



HOST = "127.0.0.1"
PORT = 65300

# FLYING o LAND
STATUS = "LAND"
BATTERY = 100
FLY_START_TIME = -1

CONNECTED = False

private_key = None


descripcion = "Envia un comando a un dron"

def exit_handler(args):
    print("Borrando dron y saliendo.")
    # TODO: borrar todo rastro de este dron en estaciones.json
    with open("db/drones.json", "r") as jsonFile:
        data = json.load(jsonFile)
        new_data = []
        for drone in data:
            if drone["id"] != args:
                new_data.append(drone)

    with open("db/drones.json", "w") as jsonFile:
        json.dump(new_data, jsonFile)
    exit()


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
    parser.add_argument('--disconnect', action='store_true', dest='disconnect', default=False, help='DISCONNECT dron -> estacion de tierra')

    # IDs
    parser.add_argument('--drone_id', dest='drone_id', default=False, help='ID de dron')
    parser.add_argument('--et_id', dest='et_id', default=False, help='ID de estacion de tierra ID')


    args = parser.parse_args()

    atexit.register(exit_handler, args=args.drone_id)

    if args.register:
        print("REGISTER")
        if args.drone_id:
            drone_id = args.drone_id
            register_drone(args.drone_id)
        else:
            print("ERROR: Debes proporcionar un drone_id")
    else:
        print("Debes registrar el dron al iniciar")
        return

    command = input("Comando: ")
    while True:
        try:
            args = parser.parse_args(command.split())
            
        except:
            print("ERROR: Comando no reconocido")
            parser.print_help()
            command = input("Comando: ")
            continue        

        if args.link:
            print("LINK")
            if args.et_id:
                link_drone_et(drone_id, args.et_id)
            else:
                print("ERROR: Debes proporcionar un et_id")
            
        elif args.unlink:
            print("UNLINK")
            if args.et_id:
                unlink_drone_et(drone_id,args. et_id)
            else:
                print("ERROR: Debes proporcionar un et_id")

        elif args.connect:
            print("CONNECT")
            if args.et_id:
                connect_drone_et(drone_id, args.et_id)
            else:
                print("ERROR: Debes proporcionar un et_id")
        
        elif args.disconnect:
            print("DISCONNECT")
            if args.et_id:
                disconnect(drone_id, args.et_id)
            else:
                print("ERROR: Debes proporcionar un et_id")

        # NOTA: que signitica este elif ??
        #elif not args.register:
        else:
            print("ERROR: Debes proporcionar un tipo de mensaje a enviar")
            parser.print_help()

        command = input("Comando: ")



def register_drone(drone_id):
    global private_key

    # Crear clave publica y privada
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')

    with open("db/drones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)

            # Comprobar que no existe
            ids = [drone["id"] for drone in data]
            if drone_id in ids:
                print("ERROR: El dron con ID", drone_id, "ya existe")
                return

            # Añadir nuevo drone con un puerto libre
            if data:
                maxPort = max([drone["listens"] for drone in data])
                data.append({"id": drone_id, "listens": maxPort+2, "linked_ets": [], "public_key": key.publickey().export_key().decode("utf-8")})
            # Caso en que la lista en el json esta vacia pero existe
            else:
                data = [{"id": drone_id, "listens": 64001, "linked_ets": [], "public_key": key.publickey().export_key().decode("utf-8")}]

        except JSONDecodeError:
            # Primera entrada del json
            data = [{"id": drone_id, "listens": 64001, "linked_ets": [], "public_key": key.publickey().export_key().decode("utf-8")}]

    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    
    print("REGISTER completado con exito: drone registrado con ID:", drone_id)

#TODO: comprobar que no estan ya linkeados
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
                break

    with open("db/drones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    # Si ambos existen, añadir a la lista de linked_drones de la estacion
    with open("db/estaciones.json", "r") as jsonFile:
        data = json.load(jsonFile)

        for et in data:
            if et["id"] == et_id:
                et["linked_drones"].append(drone_id) if drone_id not in et["linked_drones"] else et["linked_drones"]
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

def connect_drone_et(drone_id, et_id):
    global CONNECTED

    # comprobar que drone y et estan linkeados
    listen_port = check_linked(drone_id, et_id)
    print("listen_port: ", listen_port)
    if not listen_port:
        print("ERROR: drone con id", drone_id, "y estacion con id", et_id, "no estan linkeados")
        return

    # crear clave de sesion
    session_key = os.urandom(32)
    print("session_key: ", session_key)
    
    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            print(et_id)
            for el in data:
                if el["id"] == et_id:
                    el["connected"] = drone_id
                    et_public_key = el["public_key"]
        except JSONDecodeError:
            print("ERROR")
            return
    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    
    # enviar la clave de sesion encriptada con la clave publica de la ET
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, listen_port-1))
        except:
            print("ERROR: No se pudo conectar con la estacion de tierra")
            return
        
        cipher = PKCS1_OAEP.new(RSA.import_key(et_public_key))
        cipher_msg = cipher.encrypt(session_key)
        try:
            s.sendall(cipher_msg)
        except:
            print("ERROR while sending session key")
            return

    time.sleep(0.1)
    
            
    # Enviar telemetry y escuchar comando de la ET
    telemetry_thread = threading.Thread(target=telemetry, args=(drone_id, listen_port-1,))
    telemetry_thread.daemon = True
    CONNECTED = True
    telemetry_thread.start()

    # thread para escuchar comandos de la ET
    listen_thread = threading.Thread(target=listen_to_et, args=(drone_id, et_id, listen_port,))
    listen_thread.daemon = True
    listen_thread.start()
    #listen_to_et(drone_id, et_id, listen_port)


def listen_to_et(drone_id, et_id, listen_port):    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, listen_port))
        s.listen(1)
        while CONNECTED:
            r, _, _ = select.select([s, CONNECTED], [], [], None)
            if s in r:
                conn, addr = s.accept()
                with conn:
                    msg = b''
                    while True:
                        data = conn.recv(1024)
                        if not data: break
                        msg += data

                    msg = msg.decode()
                    if msg == "FLY":
                        fly()

                    elif msg == "LAND":
                        print("land recibido")
                        land()
                    
                    elif msg == "DISCONNECT":
                        disconnect(et_id, drone_id)
                    
                    elif msg == "kill":
                        exit_handler(drone_id)

            if not CONNECTED:
                break
                
        print("Conexion con ET", et_id, "finalizada")


def fly():
    global BATTERY
    global LAST_TELEMETRY
    global STATUS
    if STATUS == "FLYING":
        print("Dron en vuelo")
        return

    if BATTERY <= 0:
        print("Dron sin bateria")
        return

    print("Dron volando")
    STATUS = "FLYING"
    LAST_TELEMETRY = time.time()


def land():
    global BATTERY
    global LAST_TELEMETRY
    global STATUS
    if STATUS == "LAND":
        print("Dron en tierra")
        return

    print("Dron aterrizando")
    BATTERY = round(BATTERY - (time.time()-LAST_TELEMETRY)*100/60, 2)
    STATUS = "LAND"


def disconnect(et_id, drone_id):
    global CONNECTED
    global BATTERY

    with open("db/estaciones.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
            for et in data:
                if et["id"] == et_id:
                    print("Disconnect tag:", et["connected"])
                    del et["connected"]
                    break

        except JSONDecodeError:
            print("ERROR")
            return
        
    with open("db/estaciones.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    if STATUS != "LAND":
        land()

    CONNECTED = False
    BATTERY = 100
    


def telemetry(drone_id, et_port):
    global CONNECTED

    print("Telemetry thread started")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, et_port))
            print(HOST, et_port)
        except:
            print("ERROR: No se pudo conectar con la estacion de tierra")
            return
            
        while CONNECTED:
            msg = telemetry_msg(drone_id)
            print(msg)
            try:
                s.sendall(msg.encode(errors='ignore'))
            except Exception as e:
                print("ERROR while sending telemetry")
                print(e)
                return
            time.sleep(2)
            with open("db/estaciones.json", "r") as jsonFile:
                try:
                    data = json.load(jsonFile)
                    if not data:
                        print("llegue")
                        return

                except JSONDecodeError:
                    print("Matando thread")
                    return
        s.shutdown(socket.SHUT_RDWR)
        print("Telemetry thread finished")


def telemetry_msg(drone_id):
    global BATTERY
    global LAST_TELEMETRY
    global STATUS

    if STATUS == "FLYING":
        time_elapsed = time.time() - LAST_TELEMETRY
        LAST_TELEMETRY = time.time()
        BATTERY = round(BATTERY - time_elapsed*100/60, 2)
        if BATTERY <= 0:
            BATTERY = 0.0
            land()


    msg = {
        "drone_id": drone_id,
        "status": STATUS,
        "battery": BATTERY
    }
    return json.dumps(msg)
    

if __name__ == "__main__":
    main()