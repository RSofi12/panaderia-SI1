from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0001_initial'),
    ]

    operations = [
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
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]