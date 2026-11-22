"""Servicios de inventario de producto terminado."""
from .descontar_stock import descontar_por_venta
from .registrar_baja import registrar_baja_producto

__all__ = ['descontar_por_venta', 'registrar_baja_producto']
