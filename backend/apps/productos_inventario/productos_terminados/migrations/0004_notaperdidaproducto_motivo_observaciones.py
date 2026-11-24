from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos_terminados', '0003_movimientoproductoterminado_id_pedido'),
    ]

    operations = [
        migrations.AddField(
            model_name='notaperdidaproducto',
            name='motivo',
            field=models.CharField(
                default='Sobrante de mostrador al cierre',
                help_text='Causa de la baja (ej. Sobrante al cierre, Defecto de horneado, etc.)',
                max_length=100,
                verbose_name='Motivo de la merma',
            ),
        ),
        migrations.AddField(
            model_name='notaperdidaproducto',
            name='observaciones',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Observaciones adicionales',
            ),
        ),
    ]
