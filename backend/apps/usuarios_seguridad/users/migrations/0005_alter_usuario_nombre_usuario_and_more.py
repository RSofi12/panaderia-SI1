"""
CU3 — Unicidad real del nombre de usuario, sin distinguir mayúsculas.

QUÉ HACE ESTA MIGRACIÓN

Agrega la restricción `usuario_username_unico_ci` sobre `Lower(nombre_usuario)`.
Hasta acá el campo ya era `unique=True`, pero en PostgreSQL eso significa
"único Y DISTINTO DE MAYÚSCULAS": las cuentas 'Admin' y 'admin' podían coexistir.
Como el login resuelve con coincidencia exacta (`nombre_usuario=...`), una de las
dos quedaba permanentemente inaccesible y el Administrador veía una cuenta
"creada correctamente" que nadie podía usar. Esta restricción cierra ese hueco.

POR QUÉ SE CONSERVA EL `unique=True` DEL CAMPO

Django exige por contrato (auth.E003) que el campo `USERNAME_FIELD` sea único.
Quitarlo rompería el sistema de autenticación, y silenciar la verificación con
`SILENCED_SYSTEM_CHECKS` sería tapar un problema real en vez de resolverlo. El
índice por defecto queda como el índice que usa la búsqueda del login; este es
el que realmente decide quién puede repetirse.

POR QUÉ HAY UN RunPython ANTES DEL AddConstraint

`AddConstraint` sobre una tabla que ya tiene datos duplicados falla con un error
de PostgreSQL que no dice qué filas son las culpable: algo así como
`duplicate key value violates unique constraint`. Para una defense, o para
cualquiera que lea el log, eso es indescifrable.

`_detectar_duplicados_por_mayusculas` convierte ese fallo en un mensaje que
enlaza la cuenta repetida con lamigration pendiente. No corrige los datos a
propósito: renombrar cuentas es una decisión de negocio, no una tarea que un
script deba tomar solo. Falla ruidosamente para que la resuelva una persona.
"""
import django.db.models.functions.text
from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower


def _detectar_duplicados_por_mayusculas(apps, schema_editor):
    """
    Aborta con un mensaje legible si ya hay nombres de usuario que solo difieren
    en mayúsculas o minúsculas.
    """
    Usuario = apps.get_model('users', 'Usuario')

    repetidos = list(
        Usuario.objects.annotate(clave=Lower('nombre_usuario'))
        .values('clave')
        .annotate(total=Count('id_usuario'))
        .filter(total__gt=1)
    )

    if repetidos:
        detalle = ', '.join(
            f'"{fila["clave"]}" ({fila["total"]} cuentas)'
            for fila in repetidos
        )
        raise RuntimeError(
            'No se puede crear el índice único de nombre de usuario porque ya '
            'existen cuentas que solo difieren en mayúsculas o minúsculas: '
            f'{detalle}. Renombrá esas cuentas en el panel y volvé a correr la '
            'migración. La migración NO las modifica por su cuenta porque '
            'cambiar el nombre de acceso de una cuenta es una decisión de negocio.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('roles', '0001_initial'),
        ('users', '0004_usuario_email_obligatorio'),
    ]

    operations = [
        # El AlterField solo cambia `help_text`; en la base no altera nada, pero
        # Django necesita la operación para dejar el estado del modelo al día.
        migrations.AlterField(
            model_name='usuario',
            name='nombre_usuario',
            field=models.CharField(
                help_text=(
                    'Con este nombre inicia sesión la persona. No distingue '
                    'mayúsculas de minúsculas al validar que sea único.'
                ),
                max_length=50,
                unique=True,
                verbose_name='Nombre de usuario',
            ),
        ),
        migrations.RunPython(_detectar_duplicados_por_mayusculas, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='usuario',
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower('nombre_usuario'),
                name='usuario_username_unico_ci',
            ),
        ),
    ]
