"""
CU2 — `usuario.email` pasa a ser OBLIGATORIO y ÚNICO.

Esta migración está escrita a mano y no generada, porque Django no sabe resolver
sola el paso de NULL a NOT NULL sobre una tabla con datos: necesita que alguien
decida qué valor poner en las filas que ya existen, y esa decisión no puede ser
un default inventado en el código.

Por eso la migración hace tres cosas, EN ESTE ORDEN:

  1. `comprobar_correos` (RunPython): verifica que no quede ningún `email` vacío
     ni ninguna diferencia entre dos correos. Si encuentra algo, ABORTA con un
     mensaje que dice exactamente qué usuario falta. Es preferible a que la
     sentencia `SET NOT NULL` reviente con un error de violación de null que no
     explica qué fila es la culpable.

  2. `AlterField`: aplica el NOT NULL y el NOT NULL de verdad.

  3. `AddConstraint`: agrega la unicidad sobre `Lower('email')`.

El orden importa: el chequeo tiene que correr ANTES del AlterField. Si fuera al
reverso, el ALTER fallaría primero y nunca sabríamos qué usuario estaba sin
correo.

Sobre por qué la unicidad es sobre `Lower('email')` y no sobre `email`: en
PostgreSQL la comparación de texto distingue mayúsculas, así que sin esto
'Admin@mail.com' y 'admin@mail.com' serían dos cuentas diferentes. Con dos
cuentas que en realidad son la misma, la pantalla de recuperación quedaría
ambigua: ¿a cuál de las dos le mando el enlace?
"""
from django.db import migrations, models
from django.db.models.functions import Lower


def comprobar_correos(apps, schema_editor):
    """
    Verifica que se pueda aplicar el NOT NULL y la unicidad.

    Se trabaja en Python y no con un `UPDATE` o un `GROUP BY` a propósito: la
    tabla `usuario` tiene seis filas en un proyecto académico, y un chequeo
    legible que diga "el usuario 'vendedor' no tiene correo" vale más que una
    sentencia de agregación que solo serviría para una tabla de un millón de
    filas que aquí no existe.
    """
    Usuario = apps.get_model('users', 'Usuario')
    alias = schema_editor.connection.alias

    usuarios = list(
        Usuario.objects.using(alias).values('id_usuario', 'nombre_usuario', 'email')
    )

    sin_correo = [
        f"  - id={u['id_usuario']} nombre_usuario='{u['nombre_usuario']}'"
        for u in usuarios
        if not (u['email'] or '').strip()
    ]
    if sin_correo:
        raise RuntimeError(
            'No se puede hacer `usuario.email` obligatorio: hay usuarios sin '
            'correo electrónico, y el CU2 los necesita para poder recuperar su '
            'contraseña. Asignales un correo y volvé a correr `migrate`:\n'
            + '\n'.join(sin_correo)
        )

    vistos = {}
    for u in usuarios:
        clave = u['email'].strip().lower()
        if clave in vistos:
            raise RuntimeError(
                'No se puede hacer `usuario.email` único: dos usuarios comparten '
                'el mismo correo sin distinguir mayúsculas, y con dos cuentas '
                f"para la misma persona la recuperación sería ambigua:\n"
                f"  - '{vistos[clave]}' y '{u['nombre_usuario']}' usan {clave}"
            )
        vistos[clave] = u['nombre_usuario']


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_usuario_intentos_fallidos'),
    ]

    operations = [
        migrations.RunPython(comprobar_correos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='usuario',
            name='email',
            field=models.EmailField(max_length=150, verbose_name='Correo electrónico'),
        ),
        migrations.AddConstraint(
            model_name='usuario',
            constraint=models.UniqueConstraint(
                Lower('email'),
                name='usuario_email_unico_ci',
            ),
        ),
    ]
