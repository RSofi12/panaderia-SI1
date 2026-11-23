from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proveedores', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor',
            name='descripcion',
            field=models.CharField(
                blank=True,
                default='',
                max_length=300,
                verbose_name='Descripción',
            ),
        ),
    ]
