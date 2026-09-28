"""Sincroniza la FK de bitacora.id_usuario con el on_delete del modelo.

CONTEXTO
--------
0001 creo la FK con on_delete=CASCADE y 0002 la cambio a SET_NULL mas nullable.
En la base de desarrollo, sin embargo, la constraint quedo como ON DELETE NO
ACTION, que es lo que produce el DDL original cuando se escribe la FK sin
clausula ON DELETE.

POR QUE NO LO DETECTO DJANGO
-----------------------------
`manage.py makemigrations --check` compara el estado de los modelos contra el
estado de las migraciones, no contra la base de datos real. Como 0002 ya declara
SET_NULL, Django da el schema por bueno aunque la constraint real diga otra
cosa. Solo un DELETE por SQL directo lo revela.

POR QUE IMPORTA
---------------
Por el ORM no se nota: Django neutraliza la FK en Python y pone la columna en
NULL antes de borrar. Pero un `DELETE FROM usuario` ejecutado en pgAdmin, en un
script de la docente o desde cualquier otra herramienta que no pase por el ORM
falla con "update o delete en usuario viola la llave foranea bitacora_id_usuario",
justo cuando lo que se quiere es conservar la auditoria de ese usuario.

La migracion es defensiva: solo reconstruye la constraint si la regla actual no
es SET NULL, asi que aplicarla sobre una base ya correcta no hace nada.
"""

from django.db import migrations

CONSTRAINT = "bitacora_id_usuario_a86ded91_fk_usuario_id_usuario"

CONSULTA_REGLA = """
    select rc.delete_rule
    from information_schema.referential_constraints rc
    join information_schema.table_constraints tc
      on tc.constraint_name = rc.constraint_name
    where tc.constraint_type = 'FOREIGN KEY'
      and tc.table_name = 'bitacora'
"""


def _reconstruir(schema_editor, regla):
    """Deja la constraint de bitacora en la regla de borrado indicada."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'ALTER TABLE "bitacora" DROP CONSTRAINT IF EXISTS "{CONSTRAINT}"')
        cursor.execute(
            f"""
            ALTER TABLE "bitacora"
            ADD CONSTRAINT "{CONSTRAINT}"
            FOREIGN KEY ("id_usuario") REFERENCES "usuario" ("id_usuario")
            ON DELETE {regla}
            DEFERRABLE INITIALLY DEFERRED
            """
        )


def fijar_set_null(apps, schema_editor):
    # El proyecto es PostgreSQL, pero la suite de pruebas corre sobre SQLite.
    # En SQLite no existe information_schema y la sintaxis no aplica, asi que
    # la migracion se limita a no hacer nada.
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(CONSULTA_REGLA)
        fila = cursor.fetchone()

    if fila and fila[0] == "SET NULL":
        return

    _reconstruir(schema_editor, "SET NULL")


def revertir(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    _reconstruir(schema_editor, "NO ACTION")


class Migration(migrations.Migration):

    dependencies = [
        ("bitacora", "0003_bitacora_agente_usuario_alter_bitacora_accion"),
    ]

    operations = [
        # RunPython y no RunSQL porque hace falta inspeccionar la constraint
        # antes de decidir si se toca, y porque el proyecto tiene una suite que
        # corre sobre SQLite.
        migrations.RunPython(fijar_set_null, revertir),
    ]
