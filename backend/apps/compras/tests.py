"""
Pruebas del módulo compras. Re-exporta las pruebas del CU7 desde compra_materia_prima.
"""
from apps.compras.compra_materia_prima.tests import (  # noqa: F401
    BasePruebaCU7,
    PruebasAccesoCompra,
    PruebasDatosInvalidos,
    PruebasRegistroCompra,
)
