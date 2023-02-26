import socket
from random import randint
import json
import threading
from json.decoder import JSONDecodeError

HOST = "127.0.0.1"
DRONE_PORT = 65300 #todo: numero aleatorio

def et_listen():
    pass #todo: escuchar a la base de operaciones

def main():
    #todo: comprobar que hay BO
    name = "et1"
    with open("register.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
        except JSONDecodeError:
            data = {"et_names": []}

    arr = data["et_names"] 
    arr.append(name)
    data["et_names"] = arr

    with open("register.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    x = threading.Thread(target=et_listen)
    x.start()

    #do while hast que input sea correcto
    command = input('Esperando instrucciones: ')
    while not command == 'connect to drone':
        command = input('Esperando instrucciones:')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, DRONE_PORT))
        print("Connected to drone")
        s.sendall(b"Hello drone")
        data = s.recv(1024)

    print(f"Received {data!r}")

    with open("register.json", "r") as jsonFile:
        try:
            data = json.load(jsonFile)
        except JSONDecodeError:
            data = {"et_names": []}

    arr = data["et_names"] 
    arr.remove(name)
    data["et_names"] = arr

    with open("register.json", "w") as jsonFile:
        json.dump(data, jsonFile)

if __name__ == "__main__":
    main()