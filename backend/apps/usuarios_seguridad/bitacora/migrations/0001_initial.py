# Generated for Panaderia Santiago
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bitacora',
            fields=[
                ('id_bitacora', models.BigAutoField(primary_key=True, serialize=False)),
                ('accion', models.CharField(max_length=50, verbose_name='Acción realizada')),
                ('tabla_afectada', models.CharField(blank=True, max_length=50, null=True, verbose_name='Tabla o Módulo afectado')),
                ('descripcion', models.TextField(blank=True, null=True, verbose_name='Detalle de la acción')),
                ('fecha_hora', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha y hora')),
                ('usuario', models.ForeignKey(db_column='id_usuario', on_delete=django.db.models.deletion.CASCADE, related_name='bitacoras', to=settings.AUTH_USER_MODEL, verbose_name='Usuario responsable')),
            ],
            options={
                'verbose_name': 'Bitácora de Auditoría',
                'verbose_name_plural': 'Bitácoras de Auditoría',
                'db_table': 'bitacora',
                'ordering': ['-fecha_hora'],
            },
        ),
    ]
