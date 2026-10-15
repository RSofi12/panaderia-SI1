from django.db import migrations


def alinear_secuencia_permiso(schema_editor):
    """
    El seed inserta permisos con id fijo (1, 2, 3...). En PostgreSQL eso no
    mueve el contador automático. La siguiente inserción pide el id 1, que ya
    existe, y la base responde: duplicate key permiso_pkey.

    Se deja el contador en el máximo id ya usado. Si la tabla está vacía, el
    próximo id sigue siendo 1. En SQLite (pruebas) no hay esa secuencia.
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


def assign_management_permission(apps, schema_editor):
    Permiso = apps.get_model('permisos', 'Permiso')
    Rol = apps.get_model('roles', 'Rol')
    RolPermiso = apps.get_model('roles', 'RolPermiso')

    alinear_secuencia_permiso(schema_editor)
    permiso, _ = Permiso.objects.get_or_create(
        nombre='gestionar_materias_primas',
        defaults={
            'modulo': 'productos_inventario',
            'descripcion': 'Crear, editar y activar o inactivar materias primas',
        },
    )

    for rol in Rol.objects.filter(nombre__in=['Administrador', 'Propietario']):
        RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ('materia_prima', '0001_initial'),
        ('permisos', '0002_permiso_modulo_alter_permiso_nombre_and_more'),
        ('roles', '0002_alter_rolpermiso_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            assign_management_permission,
            migrations.RunPython.noop,
        ),
    ]
