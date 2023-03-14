# Ciberseguridad P1 - Centro de mando
----------

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



## Comunicaciones seguras

