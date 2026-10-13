from django.db.models import Count
from django.utils import timezone

from apps.comercializacion.ventas.models import Venta


def listar_ventas(*, fecha=None):
    dia = fecha or timezone.localdate()
    return (
        Venta.objects.select_related('id_usuario')
        .annotate(cantidad_lineas=Count('detalles'))
        .filter(fecha_hora__date=dia)
        .order_by('-fecha_hora', '-id_venta')
    )
