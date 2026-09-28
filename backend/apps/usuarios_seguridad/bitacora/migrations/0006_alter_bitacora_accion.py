"""
CU3 — Vocabulario de auditoría para la gestión de cuentas.

Agrega cuatro acciones al enum `AccionBitacora`:

    ALTA_USUARIO              alta de una cuenta
    EDICION_USUARIO           modificación de datos
    CAMBIAR_ESTADO_USUARIO    activación o inactivación
    RESTABLECER_CONTRASENA    reset administrativo de clave

QUÉ CAMBIA EN LA BASE Y QUÉ NO

`accion` es un `CharField` con `choices`, no un enum de PostgreSQL ni una tabla
de lookup. Por eso esta migración no altera la columna ni un solo byte de los
registros que ya existen: los valores siguen siendo cadenas de texto, y lo único
que cambia es la lista de claves que el código Python acepta. `DESBLOQUEO_CUENTA`
ya existía desde CU1 y se reutiliza tal cual.

Esto es exactamente lo que la nota de diseño de `AccionBitacora` promete: un
enum de Python da control de claves sin acoplar el esquema físico. Si en el
futuro se quisiera consultar "acciones válidas" desde SQL, el cambio sería
migrar la columna a un `EnumField` de Django, que tampoco toca los datos.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitacora', '0005_alter_bitacora_accion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitacora',
            name='accion',
            field=models.CharField(choices=[('INICIO_SESION', 'Inicio de sesión'), ('LOGIN_FALLIDO', 'Intento de acceso fallido'), ('ACCESO_BLOQUEADO', 'Acceso rechazado por bloqueo'), ('ACCESO_DENEGADO', 'Acceso denegado por cuenta inactiva'), ('CIERRE_SESION', 'Cierre de sesión'), ('DESBLOQUEO_CUENTA', 'Desbloqueo manual de cuenta'), ('SOLICITUD_RECUPERACION', 'Solicitud de recuperación de contraseña'), ('RECUPERACION_CONFIRMADA', 'Contraseña restablecida por recuperación'), ('RECUPERACION_INVALIDADA', 'Enlace de recuperación rechazado'), ('ALTA_USUARIO', 'Alta de usuario'), ('EDICION_USUARIO', 'Modificación de usuario'), ('CAMBIAR_ESTADO_USUARIO', 'Activación o inactivación de usuario'), ('RESTABLECER_CONTRASENA', 'Restablecimiento administrativo de contraseña')], max_length=50, verbose_name='Acción realizada'),
        ),
    ]
