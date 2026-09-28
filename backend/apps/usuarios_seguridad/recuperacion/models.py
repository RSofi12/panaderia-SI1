import hashlib
import secrets

from django.db import models
from django.db.models import Q
from django.utils import timezone

# Alfabeto del token: dígitos + mayúsculas, sin los caracteres que se confunden
# entre sí en un texto (0/O, 1/I/l). El token viaja dentro de una URL que pasa por
# un cliente de correo, y hay clientes que recortan o reconstruyen el enlace al
# previsualizarlo: un token válido dejaría de funcionar por un cambio de
# tipografía. Un alfabeto más chico NO baja la seguridad: 32 símbolos y 20
# posiciones son 1,1 x 10^30 combinaciones, muy por encima de lo que el límite de
# intentos por token deja probar.
ALFABETO_TOKEN = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

# Entropía: 20 posiciones de un alfabeto de 32 símbolos => 20 * log2(32) = 100
# bits. Es la misma idea de las contraseñas pero al revés: aquí la longitud es lo
# que protege, porque el atacante no elige el valor ni dispone de un diccionario.
LONGITUD_TOKEN = 20


class TokenRecuperacion(models.Model):
    """
    Token temporal de un solo uso para restablecer la contraseña (CU2).

    Reglas de seguridad que esta tabla materializa:

    1. UN SOLO USO. `usado_en` es NULL mientras el token sirve. En cuanto se
       confirma una contraseña se escribe la fecha y el token muere para siempre.
       Aunque el atacante fotografíe el correo, no le sirve dos veces.

    2. EXPIRACIÓN. `expira_en` acota la ventana de vida (por defecto 15 minutos,
       gobernado por `ConfiguracionSeguridad.minutos_expiracion_token`).
       La expiración se resuelve de forma PEREZOSA, sin cron: cada validación
       pregunta si la ventana ya venció. Es la misma decisión que tomó
       `auth_app.services.politica_bloqueo` para el bloqueo de CU1.

    3. NUNCA SE GUARDA EN CLARO. `token_hash` es el SHA-256 del token. Aunque
       alguien lea la tabla completa no puede construir un enlace válido, ni
       aunque se lleve la base de datos. El token en claro solo existe en el
       correo del usuario, que es el único lugar donde tiene que estar.

    4. LÍMITE DE INTENTOS. `intentos` cuenta cuántas veces se confirmó con este
       token. Al superar `ConfiguracionSeguridad.max_intentos_token` el token se
       invalida por completo. Sin este campo, un atacante con el enlace podría
       pedir confirmaciones indefinidamente; con él, la búsqueda exhaustiva queda
       acotada.

    Por qué `usado_en` e `invalidado_en` son columnas separadas: si al pedir un
    token nuevo se marcaran los anteriores como "usados", la base de datos
    estaría mintiendo, porque no fueron usados sino CANCELADOS. Con dos columnas
    el dato es fiel y el reporte de la bitácora (CU26) puede distinguir "recuperó
    su contraseña" de "pidió el enlace tres veces y nunca lo abrió".
    """

    id_token = models.BigAutoField(
        primary_key=True,
        verbose_name='ID del token'
    )
    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        related_name='tokens_recuperacion',
        verbose_name='Usuario'
    )
    # SHA-256 en hexadecimal: 64 caracteres exactos. Es `unique` porque el token
    # es la clave con la que se busca; el índice único hace ese trabajo.
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Hash del token',
        help_text='SHA-256 del token. El token en claro nunca se almacena.'
    )
    # Se guarda a quién se envió, y no solo "el correo del usuario". Si el
    # administrador cambia el correo entre la solicitud y el clic, la bitácora
    # sigue reflejando dónde salió el enlace.
    email_destino = models.EmailField(
        max_length=150,
        verbose_name='Correo de destino',
        help_text='Correo al que se envió el enlace en el momento de la solicitud.'
    )
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Creado en'
    )
    expira_en = models.DateTimeField(
        verbose_name='Expira en'
    )
    usado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Usado en',
        help_text='Instante en que se confirmó una contraseña con este token. NULL = sin usar.'
    )
    invalidado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Invalidado en',
        help_text='Instante en que se canceló: por pedir otro token o por agotar los intentos.'
    )
    intentos = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Intentos de confirmación',
        help_text='Confirmaciones fallidas con este token. Al superar el máximo se invalida.'
    )
    ip_origen = models.CharField(
        max_length=45,
        blank=True,
        null=True,
        verbose_name='IP de origen',
        help_text='Máx. 45 = longitud máxima de una IPv6.'
    )
    agente_usuario = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Agente de usuario'
    )

    class Meta:
        db_table = 'token_recuperacion'
        verbose_name = 'Token de Recuperación'
        verbose_name_plural = 'Tokens de Recuperación'
        ordering = ['-creado_en']
        indexes = [
            # Django limita a 30 caracteres el nombre de un índice, por
            # compatibilidad con Oracle. La consulta de la política por cuenta
            # (cuántas solicitudes hizo en la última hora) siempre filtra por
            # usuario y ordena por fecha.
            models.Index(
                fields=['usuario', '-creado_en'],
                name='token_recuperacion_usuario_idx'
            ),
        ]
        constraints = [
            # Una ventana de expiración negativa o nula haría que el token
            # naciera muerto; la base de datos lo impide en lugar de confiar en
            # que el servicio siempre calcule bien.
            models.CheckConstraint(
                condition=Q(expira_en__gt=models.F('creado_en')),
                name='token_recuperacion_expiracion_positiva',
            ),
            models.CheckConstraint(
                condition=Q(intentos__gte=0),
                name='token_recuperacion_intentos_no_negativos',
            ),
            models.CheckConstraint(
                condition=Q(usado_en__isnull=True) | Q(usado_en__gte=models.F('creado_en')),
                name='token_recuperacion_uso_coherente',
            ),
        ]

    def __str__(self):
        if self.esta_usado:
            estado = 'usado'
        elif self.esta_invalidado:
            estado = 'invalidado'
        else:
            estado = 'pendiente'
        return f'Token #{self.id_token} de {self.usuario_id} ({estado})'

    @staticmethod
    def generar_token():
        """
        Devuelve un token aleatorio criptográficamente seguro.

        `secrets.choice` usa el generador del sistema operativo (os.urandom en
        Linux, BCryptGenRandom en Windows), que a diferencia de `random.choice` no
        es predecible a partir de una semilla previa.
        """
        return ''.join(secrets.choice(ALFABETO_TOKEN) for _ in range(LONGITUD_TOKEN))

    @staticmethod
    def hashear_token(token):
        """
        Devuelve el SHA-256 hexadecimal del token, que es lo que se guarda.

        ¿Por qué SHA-256 y no bcrypt como en las contraseñas? Porque bcrypt está
        pensado para valores de BAJA entropía, que son atacables por diccionario y
        necesitan que el hasher sea lento para encarecer cada intento. Un token
        de 100 bits de entropía no se puede bruteforcear ni juntando todos los
        servidores del mundo, así que el costo de bcrypt solo aportaría una
        denegación de servicio: convertir el endpoint de confirmación en un alto
        costo de CPU por petición sería un regalo para quien quisiera tumbarlo.
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    # --- Estado derivado (solo lectura, sin tocar la base de datos) ---

    @property
    def esta_usado(self):
        return self.usado_en is not None

    @property
    def esta_invalidado(self):
        return self.invalidado_en is not None

    @property
    def esta_expirado(self):
        return self.expira_en <= timezone.now()

    @property
    def segundos_restantes(self):
        """Segundos que faltan para expirar. 0 si ya expiró."""
        return max(0, int((self.expira_en - timezone.now()).total_seconds()))

    def es_valido(self, max_intentos):
        """
        Regla de vigencia completa, reunida en un solo lugar.

        Recibe el máximo de intentos desde la configuración en vez de leerlo aquí,
        para que esta comprobación no dependa de una consulta extra a la base de
        datos en cada validación.
        """
        if self.esta_usado or self.esta_invalidado or self.esta_expirado:
            return False
        return self.intentos < max_intentos
