"""
Envío del correo con el enlace de recuperación (CU2).

Por qué `EmailMultiAlternatives` y no `send_mail`: el mismo correo se envía en
texto plano y en HTML. El texto plano es lo que ven los clientes de correo de
escritorio y las notificaciones de móvil; el HTML es lo que se ve en Gmail,
Outlook y en la vista previa del teléfono. Mandar solo HTML deja usuarios sin
correo legible, y mandar solo texto plano parece un correo de los años 90.

El correo NUNCA lleva la contraseña. Va el enlace con el token: una contraseña en
un correo es una contraseña escrita en un lugar que se archiva, se reenvía y
que el proveedor de correo guarda en claro.

Sobre el SMTP: Django siempre habla SMTP; lo único que cambia es a qué servidor
apunta, y eso se decide con `EMAIL_BACKEND` en settings.py leído del `.env`.
En desarrollo ese servidor es Mailpit (localhost:1025, bandeja en :8025); en
producción, el del proveedor real. Ningún valor está hardcodeado acá, y por eso
este módulo sirve igual en los dos casos sin tocar una línea.
"""
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

NOMBRE_NEGOCIO = 'Panadería Santiago'
ASUNTO = f'{NOMBRE_NEGOCIO}: restablece tu contraseña'
PLANTILLAS = 'emails/recuperacion_contrasena'


def construir_enlace(token):
    """
    Arma el enlace del frontend con el token como parámetro de consulta.

    `PASSWORD_RESET_URL` es la ruta de la SPA que muestra el formulario de nueva
    contraseña, NO una vista de Django. El backend expone el endpoint que esa
    pantalla consume, pero la pantalla vive en el frontend: es la misma división
    que se pidió para el CU1, donde React es el cliente y Django la API.

    `quote(..., safe='')` escapa el token por si acaso. Hoy el alfabeto del token
    (mayúsculas y dígitos) es seguro en una URL, pero dejar el escapado puesto
    evita tener que volver a acordarse de él el día que se cambie el alfabeto.
    """
    base = (settings.PASSWORD_RESET_URL or '').rstrip('/')
    return f'{base}?token={quote(token, safe="")}'


def renderizar_correo(usuario, enlace, minutos_validez):
    """Renderiza las dos versiones del correo con un mismo contexto."""
    contexto = {
        'nombre_negocio': NOMBRE_NEGOCIO,
        'nombre_completo': usuario.nombre_completo,
        'nombre_usuario': usuario.nombre_usuario,
        'enlace': enlace,
        'minutos_validez': minutos_validez,
    }
    return (
        render_to_string(f'{PLANTILLAS}.txt', contexto),
        render_to_string(f'{PLANTILLAS}.html', contexto),
    )


def enviar_enlace_recuperacion(usuario, token, minutos_validez):
    """
    Envía el correo y devuelve cuántos mensajes se enviaron (1 o 0).

    `fail_silently=False` a propósito: si el SMTP está caído queremos que la
    excepción suba y quede registrada. Un error de envío silencioso dejaría al
    usuario con un token vivo en la base de datos del que nunca se enteró, que es
    la peor forma de fallo: silenciosa y sin forma de diagnosticar.
    """
    cuerpo_texto, cuerpo_html = renderizar_correo(
        usuario,
        construir_enlace(token),
        minutos_validez,
    )

    mensaje = EmailMultiAlternatives(
        subject=ASUNTO,
        body=cuerpo_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[usuario.email],
    )
    mensaje.attach_alternative(cuerpo_html, mimetype='text/html')

    return mensaje.send(fail_silently=False)
