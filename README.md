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
- La ET puede ordenar al dron que empiece a volar o que aterrice:
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

Un aspecto a tener en cuenta es que la batería de un dron dura 60 segundos en vuelo. Cuando esta se acaba y el dron está volando este tomará tierra inmediatamente pero la conexión se mantendrá abierta. Para recargar el dron es necesario enviar cerrar la conexción y volver a establecerla (disconnect y connect).


## Comunicaciones seguras

