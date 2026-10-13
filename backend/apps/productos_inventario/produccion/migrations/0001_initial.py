from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('productos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Produccion',
                    fields=[
                        ('id_produccion', models.BigAutoField(primary_key=True, serialize=False)),
                        ('fecha', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha de producción')),
                        ('jornada', models.CharField(choices=[('Mañana', 'Mañana'), ('Tarde', 'Tarde'), ('Noche', 'Noche')], default='Mañana', max_length=20, verbose_name='Jornada')),
                        ('id_usuario', models.ForeignKey(db_column='id_usuario', on_delete=django.db.models.deletion.PROTECT, related_name='producciones', to=settings.AUTH_USER_MODEL, verbose_name='Responsable de producción')),
                    ],
                    options={
                        'verbose_name': 'Producción',
                        'verbose_name_plural': 'Producciones',
                        'db_table': 'produccion',
                        'ordering': ['-fecha', '-id_produccion'],
                    },
                ),
                migrations.CreateModel(
                    name='DetalleProduccion',
                    fields=[
                        ('id_detalle_produccion', models.BigAutoField(primary_key=True, serialize=False)),
                        ('cantidad_producida', models.PositiveIntegerField(verbose_name='Cantidad producida (unidades)')),
                        ('costo_unitario', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Costo unitario (Bs)')),
                        ('id_producto', models.ForeignKey(db_column='id_producto', on_delete=django.db.models.deletion.PROTECT, related_name='detalles_produccion', to='productos.producto', verbose_name='Producto elaborado')),
                        ('id_produccion', models.ForeignKey(db_column='id_produccion', on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='produccion.produccion', verbose_name='Producción')),
                    ],
                    options={
                        'verbose_name': 'Detalle de producción',
                        'verbose_name_plural': 'Detalles de producción',
                        'db_table': 'detalle_produccion',
                    },
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS produccion (
                        id_produccion BIGSERIAL PRIMARY KEY,
                        id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario) ON DELETE RESTRICT,
                        fecha DATE NOT NULL,
                        jornada VARCHAR(20) NOT NULL DEFAULT 'Mañana'
                    );

                    CREATE TABLE IF NOT EXISTS detalle_produccion (
                        id_detalle_produccion BIGSERIAL PRIMARY KEY,
                        id_produccion BIGINT NOT NULL REFERENCES produccion(id_produccion) ON DELETE CASCADE,
                        id_producto BIGINT NOT NULL REFERENCES producto(id_producto) ON DELETE RESTRICT,
                        cantidad_producida INTEGER NOT NULL,
                        costo_unitario NUMERIC(10,2) NOT NULL DEFAULT 0.00
                    );
                    """,
                    reverse_sql="""
                    DROP TABLE IF EXISTS detalle_produccion;
                    DROP TABLE IF EXISTS produccion;
                    """,
                ),
            ],
        ),
    ]
