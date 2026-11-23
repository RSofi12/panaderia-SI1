from django.db import models


class PeriodoReporte(models.TextChoices):
    """Etiqueta del cierre; el cálculo siempre usa desde y hasta."""

    DIA = 'dia', 'Día'
    SEMANA = 'semana', 'Semana'
    MES = 'mes', 'Mes'