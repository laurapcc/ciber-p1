# Ciberseguridad P1 - Centro de mando


- Pedro Sánchez de la Muela Garzón
- Laura de Paz Carbajo

----------



## Descripción del sistema
Este sistema permite establecer comunicaciones seguras entre los diferentes elementos de la UREJ.

Estas comunicaciones se realizan enter tres tipos de elementos:

- Base de operaciones (BO)
- Estaciones de tierra (ET)
- Drones


Existe una única base de operaciones, y ha de estar activa para que las estaciones y los drones se puedan registrar e intercambiar mensajes.

Para iniciar la BO se utilizará el siguiente comando:

```
python3 base.py
```

A partir de este momento ya se podrán registrar estaciones y drones de la siguiente manera:

```
python3 estacion.py --register --et_id <id-de-la-ET>
```

```
python3 drone.py --register --drone_id <id-del-dron>
```

Para que una ET pueda empezar a operar es necesario que esté linkeada a la BO. Esta acción se efectúa de la siguiente manera:

```
--link
```

Y entonces podrá esperar a recibir instrucciones de la BO y peticiones de conexiones de los dronees.

Por otro lado, para que un dron pueda empezar a operar es necesario que esté linkeado a una ET a la que luego podrá conectarse.
El linkeo se realiza indicando el ID de la ET a la que se quiene enlazar:

```
--link --et_id <id-de-la-ET>
```

Un mismo dron puede estar linkeado a varias ETs al mismo tiempo pero solo se puede conectar a una de ellas en casa momento. Por ello, para conectarse también es necesario indicar el ID de la ET:

```
--connect --et_id <id-de-la-ET>
```

En este punto se ha establecido la conexión entre la estación de tierra y el dron, lo que implica las siguientes comunicaciones:

- El dron envía cada 2 segundos el mensaje _telemetry_ que contiene su id, estado (volando o en tierra) y batería restante.
- Tanto la ET como la BO puede ordenar al dron que empiece a volar o que aterrice:
    ```
    --fly --drone_id <id-del-dron>
    --land --drone_id <id-del-dron>
    ```
- Ambos podrán poner fin a esta conexión enviándose el commando disconnect
    ```
    # disconnect enviado por dron
    --disconnect --et_id <id-de-la-ET>

    # disconnect enviado por estacion de tierra
    --diconnect --drone_id <id-del-dron>
    ```

Un aspecto a tener en cuenta es que la batería de un dron dura 60 segundos en vuelo. Cuando esta se acaba y el dron está volando este tomará tierra inmediatamente pero la conexión se mantendrá abierta. Para recargar el dron es necesario enviar disconnect, es decir, cerrar la conexión y volver a establecerla, connect.


## Comunicaciones seguras

-Para asegurar la confidencialidad de las comunicaciones se usa un esquema de clave pública y privada, que se intercambian al realizar la primera conexión, además se crea una clave de sesión para cada comunicación. 

-La clave pública de cada elemento se almacena en la base de datos y la clave privada en memoria, por lo que es diferente para cada ejecución del programa.

## Posibles bugs

-A la hora de ejecutar los programas pueden surgir problemas si no se ejecutan en el orden indicado.
-Si una ET o un Dron se cierran mientras que están conectados puede surgir el problema de que el socket que se utiliza para mandar el mensaje de telemetry se mantenga activo, esto se soluciona esperando a que el propio sistema operativo lo cierre.
-Al acabar cada uno de los tres programas su funcionalidad indica que se borre su parte de información de la base de datos, pero si la salida del programa es "extraña" puede pasar que no se borre, en estos casos recomendamos borrarla manualmente del .json correspondiente.

## Decisiones de diseño

-Vimos más adecuado que cada elemento cuando se finalizase con ctrl-c su programa correspondiente, borrase todos sus rastros de la base de datos, ya que al ser un programa enfocado al ámbito militar, creímos que sería mejor que los datos no fuesen persistentes.
-Para la seguridad de las comunicaciones, decidimos guardar la clave pública en la base de datos para facilitar su acceso y la clave privada en memoria para aumentar su seguridad, al igual que la clave de sesión, ya que al ser los elementos efímeros en nuestro planteamiento entendemos que las claves también debían serlo.


