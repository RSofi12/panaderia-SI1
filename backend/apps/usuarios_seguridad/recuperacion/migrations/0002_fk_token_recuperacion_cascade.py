"""
Pone real el borrado en cascada de `token_recuperacion` al borrar una cuenta.

POR QUE HACE FALTA SQL A MANO
-----------------------------
El modelo declara `on_delete=CASCADE` y `0001_initial` tambien, pero la base de
datos tiene `NO ACTION`. Dos motivos por los que Django no lo solo:

1. `makemigrations` compara el modelo contra el ARCHIVO de migraciones, no
   contra el esquema real. Si el archivo se corrige despues de aplicado, Django
   sigue viendolos de acuerdo y responde "No changes detected". Solo un
   `pg_constraint` lo delata.
2. Aun escribiendo la `AlterField` a mano, Django la emite como **no-op**: para
   el editor de esquemas, `on_delete` es una preocupacion de Python y no un
   parametro de base de datos, asi que no detecta nada que cambiar.

Mientras dure esa diferencia, el borrado en cascada solo ocurre si se borra la
cuenta desde el ORM de Django, que recoge y borra los tokens en Python antes de
emitir el DELETE. Un DELETE por SQL directo o un script de mantenimiento
fallarian con violacion de llave foranea, y un token huerfano apuntando a un
usuario inexistente permitiria reiniciar el reloj de un enlace viejo.

El DROP no fija el nombre de la constraint porque Django la genera con un hash
que depende del entorno: se busca en `pg_constraint` la FK que realmente apunta
a `usuario`. El nombre nuevo si es fijo, para que las migraciones siguientes
puedan referirse a el.

Y POR QUE ES `RunPython` Y NO `RunSQL`
-------------------------------------
El SQL de arriba es de PostgreSQL. La suite de pruebas corre sobre SQLite (el
usuario de PostgreSQL no tiene CREATEDB), y un `RunSQL` a secas reventaria con
`near "DO": syntax error` al construir la base de pruebas. `RunPython` deja
mirar el vendor y no hacer nada en el resto de motores: en SQLite la cascada la
aplica el ORM en Python de todos modos, y SQLite ni siquiera fuerza las llaves
foraneas por omision.

Aun asi, esto deja una trampa: si alguien corre la suite sobre MySQL creyendo
que todo esta verificado, la cascada a nivel de base no existira. El proyecto es
PostgreSQL-only, asi que se acepta.
"""
from django.db import migrations

Soltar_Constraint_Auto = """
DO $$
DECLARE
  nombre text;
BEGIN
  SELECT conname INTO nombre
  FROM pg_constraint
  WHERE conrelid = 'token_recuperacion'::regclass
    AND contype = 'f'
    AND confrelid = 'usuario'::regclass
  LIMIT 1;

  IF nombre IS NOT NULL THEN
    EXECUTE format('ALTER TABLE token_recuperacion DROP CONSTRAINT %I', nombre);
  END IF;
END $$;
"""

Crear_Con_Cascade = """
ALTER TABLE token_recuperacion
  ADD CONSTRAINT "token_recuperacion_usuario_id_fk"
  FOREIGN KEY ("usuario_id") REFERENCES "usuario"("id_usuario")
  ON DELETE CASCADE
  DEFERRABLE INITIALLY DEFERRED;
"""

Crear_Sin_Cascade = """
ALTER TABLE token_recuperacion
  ADD CONSTRAINT "token_recuperacion_usuario_id_fk"
  FOREIGN KEY ("usuario_id") REFERENCES "usuario"("id_usuario")
  DEFERRABLE INITIALLY DEFERRED;
"""


def _es_postgres(schema_editor):
    return schema_editor.connection.vendor == 'postgresql'


def poner_cascade(apps, schema_editor):
    if _es_postgres(schema_editor):
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(Soltar_Constraint_Auto)
            cursor.execute(Crear_Con_Cascade)


def quitar_cascade(apps, schema_editor):
    if _es_postgres(schema_editor):
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                'ALTER TABLE token_recuperacion '
                'DROP CONSTRAINT IF EXISTS "token_recuperacion_usuario_id_fk";'
            )
            cursor.execute(Crear_Sin_Cascade)


class Migration(migrations.Migration):
    dependencies = [
        ('recuperacion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(poner_cascade, quitar_cascade),
    ]
