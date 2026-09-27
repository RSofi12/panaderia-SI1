from django.db import models
from django.utils import timezone


class Bitacora(models.Model):
    """
    Modelo de Auditoría del Sistema para Panadería Santiago.
    Registra todas las acciones críticas (CU26).
    """
    id_bitacora = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='bitacoras',
        verbose_name='Usuario responsable'
    )
    accion = models.CharField(
        max_length=50,
        verbose_name='Acción realizada'
    )
    tabla_afectada = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tabla o Módulo afectado'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Detalle de la acción'
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora'
    )

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Bitácora de Auditoría'
        verbose_name_plural = 'Bitácoras de Auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f'[{self.fecha_hora.strftime("%Y-%m-%d %H:%M")}] {self.usuario.nombre_usuario} - {self.accion}'

    @classmethod
    def registrar(cls, usuario, accion, tabla_afectada=None, descripcion=None):
        """
        Método utilitario para registrar un evento en la bitácora desde cualquier vista o servicio.
        """
        if not usuario or not usuario.is_authenticated:
            return None
        return cls.objects.create(
            usuario=usuario,
            accion=accion,
            tabla_afectada=tabla_afectada,
            descripcion=descripcion
        )
