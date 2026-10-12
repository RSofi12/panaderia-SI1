"""
Re-exportación del servicio de compra de materia prima (CU7) desde la sub-app compra_materia_prima.
"""
from apps.compras.compra_materia_prima.services.registrar_compra import (  # noqa: F401
    _como_decimal,
    _inventarios_bloqueados,
    _validar_lineas,
    registrar_compra,
)
