from django.db import migrations


def alinear_secuencia_permiso(apps, schema_editor):
    """
    El seed inserta permisos con id fijo (1, 2, 3...). En PostgreSQL eso no
    mueve el contador automático. La siguiente inserción pide el id 1, que ya
    existe, y la base responde: duplicate key permiso_pkey.

    Se deja el contador en el máximo id ya usado. Si la tabla está vacía, el
    próximo id sigue siendo 1. En SQLite (pruebas) no hay esa secuencia.

    NOTA: La creación del permiso 'gestionar_materias_primas' (id=13) y su
    asignación a roles se delega a seed_usuarios, que gestiona todos los
    permisos con IDs fijos. Hacer esa inserción aquí con ID auto-generado
    chocaba con el ID fijo 13 del seeder (UniqueConstraint por nombre).
    """
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('permiso', 'id_permiso'),
            COALESCE((SELECT MAX(id_permiso) FROM permiso), 1),
            (SELECT MAX(id_permiso) FROM permiso) IS NOT NULL
        )
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ('materia_prima', '0001_initial'),
        ('permisos', '0002_permiso_modulo_alter_permiso_nombre_and_more'),
        ('roles', '0002_alter_rolpermiso_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            alinear_secuencia_permiso,
            migrations.RunPython.noop,
        ),
    ]
