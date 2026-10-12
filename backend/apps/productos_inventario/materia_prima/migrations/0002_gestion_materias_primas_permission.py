from django.db import migrations


def assign_management_permission(apps, schema_editor):
    Permiso = apps.get_model('permisos', 'Permiso')
    Rol = apps.get_model('roles', 'Rol')
    RolPermiso = apps.get_model('roles', 'RolPermiso')

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
