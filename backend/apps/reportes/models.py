"""
Modelos para el paquete de Reportes (CU21 - CU25).

En una arquitectura relacional limpia (OLAP), los reportes no requieren
tablas propias: se generan mediante consultas de agregación sobre las tablas de dominio
existentes (ventas, producción, inventario, compras y gastos).
"""
from django.db import models
