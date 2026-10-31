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

def obtener_comprobante_venta(identificador):
    """
    Recupera una venta optimizada para la emisión de comprobante (CU16).
    Admite id_venta (pk) o numero_comprobante.
    """
    qs = (
        Venta.objects.select_related('id_usuario')
        .prefetch_related('detalles__id_producto')
    )
    venta = qs.filter(pk=identificador).first()
    if not venta:
        venta = qs.filter(numero_comprobante=identificador).first()
    return venta

