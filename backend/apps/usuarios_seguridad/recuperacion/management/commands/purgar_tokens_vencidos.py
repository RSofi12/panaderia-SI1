"""
Comando `manage.py purgar_tokens_vencidos` (CU2).

QUÉ HACE
    Marca como `invalidado` los tokens de recuperación que ya vencieron y que
    siguen con estado "pendiente" en la tabla.

POR QUÉ EXISTE, Y POR QUÉ NO ES UNA TARGA PROGRAMADA
    Esto NO es una necesidad de seguridad. Un token vencido ya no se puede usar:
    `TokenRecuperacion.esta_expirado` lo rechaza en la validación, y
    `es_valido()` devuelve False por ese motivo. Un token vencido NO puede
    cambiar la contraseña de nadie, esté en la tabla o no.

    El único efecto de purgar es de ORDEN VISUAL: el panel del Administrador
    lista los tokens, y sin esta limpieza seguiría mostrando enlaces que en
    realidad están muertos como si fueran "pendientes", lo cual invite a pensar
    que hay recuperaciones en curso que no existen.

    Por eso se decidió NO meter Celery ni un broker de por medio. Para ejecutar
    un UPDATE de una sola línea no vale la pena levantar un worker, un beat y un
    Redis (que además no tiene versión oficial para Windows). Este comando se
    ejecuta a mano, o se agenda desde el Programador de tareas de Windows, que
    para un proyecto de esta escala cumple lo mismo con cero infraestructura.

    Si algún día el proyecto necesita trabajo en segundo plano de verdad (por
    ejemplo, no bloquear la vista mientras se manda un correo lento), ahí Celery
    sí se justifica, pero por el motivo contrario a este comando.

CÓMO SE USA
    python manage.py purgar_tokens_vencidos            # modo normal
    python manage.py purgar_tokens_vencidos --dry-run  # solo cuenta, no escribe
    python manage.py purgar_tokens_vencidos --verbose  # lista los tokens

Sobre `--dry-run`: es importante en la primera ejecución. El comando corre un
UPDATE en masa, y aunque solo toque filas vencidas, en una base real conviene
saber cuántas son antes de tocar.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.usuarios_seguridad.recuperacion.models import TokenRecuperacion
from apps.usuarios_seguridad.recuperacion.services import confirmacion


class Command(BaseCommand):
    help = (
        'Cancela los tokens de recuperacion vencidos que siguen pendientes. '
        'Es cosmetico: un token vencido ya no sirve para nada.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Cuenta los tokens que se cancelarian sin escribir en la base.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra el detalle de cada token que se cancela.',
        )

    def handle(self, *args, **options):
        ahora = timezone.now()
        # El mismo criterio que usa `confirmacion.purgar_vencidos`, replicado acá
        # solo para poder mostrar el detalle con --verbose. La escritura real la
        # sigue haciendo el servicio, para que no haya dos definiciones de "vencido"
        # que puedan divergir con el tiempo.
        pendientes = TokenRecuperacion.objects.filter(
            usado_en__isnull=True,
            invalidado_en__isnull=True,
            expira_en__lte=ahora,
        )

        total = pendientes.count()
        modo = 'DRY-RUN' if options['dry_run'] else 'EJECUCION'

        # Se escribe en ASCII puro a proposito: la consola de Windows trabaja en
        # cp1252 y revienta con UnicodeEncodeError al imprimir certaines simbolos.
        # Mismo criterio que usa `seed_usuarios`.
        self.stdout.write(
            self.style.NOTICE(
                f'[CU2] Purga de tokens vencidos ({modo})...'
            )
        )
        self.stdout.write(
            f'  Tokens pendientes y vencidos a las {ahora:%Y-%m-%d %H:%M:%S}: {total}'
        )

        if total == 0:
            self.stdout.write(self.style.SUCCESS('  Nada que purgar.'))
            return

        if options['verbose']:
            for fila in pendientes.order_by('expira_en').select_related('usuario'):
                etiqueta = fila.usuario.nombre_usuario if fila.usuario else '(sin usuario)'
                self.stdout.write(
                    f'    #{fila.id_token}  {etiqueta}  '
                    f'vencio {fila.expira_en:%Y-%m-%d %H:%M:%S}'
                )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'  [DRY-RUN] Se habrian cancelado {total} token(s). '
                    'Sin cambios en la base.'
                )
            )
            return

        cancelados = confirmacion.purgar_vencidos(ahora=ahora)
        self.stdout.write(
            self.style.SUCCESS(f'  Tokens cancelados: {cancelados}')
        )
        self.stdout.write(
            '  Recordatorio: esto es cosmetico, no una medida de seguridad. '
            'Un token vencido ya no cambiaba ninguna contrasena.'
        )
