Estas son las distintas operaciones posibles con este módulo:

## Grabar servicios

> 1.  Al confirmar el albarán, el servicio se grabará en Correos
>     Express.
> 2.  Con la respuesta, se registrará en el chatter la referencia de
>     envío y las etiquetas correspondientes.
> 3.  Para gestionar los bultos del envío, se puede utilizar el campo de
>     número de bultos que añade delivery_package_number (ver el README
>     para mayor información) o bien el flujo nativo de Odoo con
>     paquetes de envío. El módulo mandará a la API de Correos Express
>     el número correspondiente y podremos descargar las etiquetas con
>     su correspondiente numeración.

## Cancelar servicios

> 1.  Correos Express no dispone de un servicio para cancelar los
>     envíos.
> 2.  Si se ha de corregir algún dato, hay que grabar un nuevo envío con
>     una nueva etiqueta. Esto no hace que dicho envío se facture,
>     solamente sucede si el paquete es recogido y entra en reparto

## Obtener etiquetas

> 1.  Si por error hubiésemos eliminado el adjunto de las etiquetas que
>     obtuvimos en la grabación del servicio, podemos obtenerlas de
>     nuevo pulsando en el botón "Etiqueta Correos Express" que tenemos
>     en la parte superior de la vista formulario del albarán.

## Seguimiento de envíos

> 1.  El módulo está integrado con delivery_state para poder recabar la
>     información de seguimiento de nuestros envíos directamente desde
>     la API de Correos Express.
> 2.  Para ello, vaya al albarán con un envío Correos Express ya grabado
>     y en la pestaña de *Información adicional* verá el botón
>     *Actualizar seguimiento* para pedir a la API que actualice el
>     estado de este envío en Odoo.

## Manifiesto

> 1.  Correos Express no dispone de un servicio para sacar el manifiesto
>     Por lo tanto se tiene que sacar desde su interfaz web

## Depuración de errores

> 1.  Se puede activar Odoo con --log-level=debug para registrar las
>     peticiones y las respuestas en el log.
