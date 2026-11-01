from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='id_transaccion_stripe',
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                unique=True,
                verbose_name='Id de transacción Stripe',
            ),
        ),
        migrations.AddConstraint(
            model_name='pedido',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('metodo_pago', 'stripe'),
                    ('id_transaccion_stripe__isnull', True),
                    _connector='OR',
                ),
                name='pedido_stripe_solo_con_tarjeta',
            ),
        ),
    ]
