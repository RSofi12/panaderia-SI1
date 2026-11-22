# Revisión de Ciclo 3 — Backend (CU14, CU15, CU17, CU19)

**Fecha de revisión:** 2026-10-29  
**Rama revisada:** `prueba` (merge de `feature/cu19-historial-precios` incluido)  
**Revisor:** Antigravity (code review automatizado)  
**Alcance:** Solo backend. Frontend pendiente de revisión separada.

---

## Resultado General

| CU | Nombre | Arquitectura | Tests | Auditoría | Validaciones | RBAC |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| CU14 | Registrar pedido | ✅ | ✅ | ⚠️ Parcial | ⚠️ Mejorable | ✅ |
| CU15 | Consultar estado de pedido | ✅ | ✅ | ❌ Ausente | ✅ | ✅ |
| CU17 | Consultar disponibilidad | ✅ | ❌ Sin tests | ❌ Ausente | ⚠️ Mejorable | ✅ |
| CU19 | Historial de precios | ✅ | ✅ Excelente | ❌ Ausente | ✅ | ✅ |

---

## CU14 — Registrar Pedido (`apps.comercializacion.pedidos`)

### ✅ Lo que está bien
- Estructura modular correcta: `models.py`, `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `selectors.py`, capa `services/` con archivos separados por caso de uso (`registrar_pedido.py`, `cambiar_estado_pedido.py`, `entregar_pedido.py`). Sigue exactamente el patrón de `ventas/`.
- El servicio `registrar_pedido.py` usa `@transaction.atomic` — correcto para una operación que escribe múltiples tablas.
- La validación de cliente en `ClienteEntradaSerializer` es correcta: exige `id_cliente` existente **o** nombre nuevo.
- `CambiarEstadoPedidoSerializer.update()` delega correctamente a `cambiar_estado_pedido()` en lugar de hacer lógica inline.
- `PedidoCreateView.get()` devuelve solo pedidos abiertos (estado pendiente/en preparación) — semánticamente correcto para el mostrador.

### ⚠️ Mejoras recomendadas

**1. Auditoría incompleta en `registrar_pedido.py`**

El CU14 no registra en la `Bitacora`. Todos los CU de escritura del proyecto usan `Bitacora.registrar(...)`. El estándar del equipo lo exige.

```python
# Agregar al final de registrar_pedido(), dentro del bloque @transaction.atomic:
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

Bitacora.registrar(
    usuario=usuario,
    accion=AccionBitacora.ALTA_PEDIDO,       # agregar esta acción al enum
    tabla_afectada='pedido',
    descripcion=(
        f'Pedido #{pedido.id_pedido} registrado para cliente '
        f'{pedido.id_cliente.nombre} — total Bs {pedido.total}'
    ),
    agente_usuario=agente_usuario,
)
```

> También agregar `ALTA_PEDIDO`, `CAMBIO_ESTADO_PEDIDO` y `ENTREGA_PEDIDO` al enum `AccionBitacora` en `bitacora/models.py`.

**2. Auditoría ausente en `cambiar_estado_pedido.py`**

Los cambios de estado de un pedido (pendiente → en_preparacion → listo → entregado / cancelado) son acciones de negocio relevantes que deben quedar trazadas. Sin registro, el propietario no puede auditar qué operador canceló un pedido ni cuándo se marcó como listo.

```python
# Dentro de cambiar_estado_pedido(), en @transaction.atomic:
Bitacora.registrar(
    usuario=usuario,
    accion=AccionBitacora.CAMBIO_ESTADO_PEDIDO,
    tabla_afectada='pedido',
    descripcion=(
        f'Pedido #{pedido_id} cambió de {estado_anterior} '
        f'a {estado_nuevo}'
    ),
    agente_usuario=agente_usuario,
)
```

**3. Sin validación de `fecha_entrega` futura**

`PedidoRegistroSerializer` acepta cualquier `DateTimeField` incluyendo fechas pasadas. Un pedido con fecha de entrega anterior a hoy es un dato inválido de negocio.

```python
def validate_fecha_entrega(self, value):
    from django.utils import timezone
    if value <= timezone.now():
        raise serializers.ValidationError(
            'La fecha de entrega debe ser posterior a la fecha y hora actual.'
        )
    return value
```

**4. Sin validación de stock al registrar el pedido**

`registrar_pedido.py` no verifica si hay stock suficiente de `InventarioProductoTerminado` al momento de crear el pedido. Actualmente el sistema acepta pedidos de productos sin existencias.

Considera al menos emitir una advertencia en la respuesta (sin bloquear) cuando el stock actual sea insuficiente para la cantidad pedida, dado que el pedido puede ser anticipado a la producción.

**5. `PedidoDetailView` usa `permission_classes = [PuedeRegistrarPedidos]` como default innecesario**

La clase base define `permission_classes` que se pisa inmediatamente con `get_permissions()`. La línea `permission_classes = [PuedeRegistrarPedidos]` en el cuerpo de clase es código muerto — confunde y puede causar bugs si alguien elimina `get_permissions()` en el futuro.

```python
# Eliminar esta línea (es el default de clase pero nunca se usa):
permission_classes = [PuedeRegistrarPedidos]  # ← redundante, quitar
```

---

## CU15 — Consultar Estado de Pedido (`apps.comercializacion.pedidos`)

### ✅ Lo que está bien
- `PedidoEstadoListView` y `PedidoEstadoDetailView` son vistas de solo lectura — correcto.
- Separación de permisos: `PuedeConsultarPedidos` para GET, `PuedeRegistrarPedidos` para PATCH.
- Filtros por `estado`, `q` (búsqueda por nombre de cliente) y `fecha_entrega` implementados en `selectors.py` — respeta la separación de responsabilidades.
- `listar_pedidos()` en `selectors.py` evita lógica de queries en la vista.

### ⚠️ Mejoras recomendadas

**1. Sin auditoría de consultas sensibles**

Si bien CU15 es de consulta, el PACKAGE_CU_MAP indica que `Personal de Producción` también puede consultar el estado de pedidos. Un Producción que consulta pedidos frecuentemente podría ser un indicio de acceso indebido. Evaluar si conviene registrar accesos a este endpoint con `AccionBitacora.CONSULTA_PEDIDOS` (nivel informativo, no obligatorio para la defensa).

**2. Filtro `fecha_entrega` acepta strings inválidos sin respuesta clara**

En `listar_pedidos(estado, q, fecha_entrega)`, si `fecha_entrega` no es una fecha ISO válida, el filtro probablemente falla silenciosamente o lanza una excepción no controlada. Agregar validación explícita:

```python
# En selectors.py — listar_pedidos()
from datetime import date
try:
    fecha = date.fromisoformat(fecha_entrega) if fecha_entrega else None
except ValueError:
    raise ValidationError({'fecha_entrega': 'Formato de fecha inválido. Use YYYY-MM-DD.'})
```

**3. No hay endpoint de paginación**

`listar_pedidos()` devuelve todos los pedidos sin paginación. Si el sistema tiene pedidos de semanas anteriores, el endpoint puede volverse lento. Agregar `PageNumberPagination` como se hizo en CU19.

---

## CU17 — Consultar Disponibilidad de Productos (`apps.comercializacion`)

### ✅ Lo que está bien
- Reutiliza `InventarioProductoTerminado` de `productos_terminados` sin duplicar modelos — correcto.
- `DisponibilidadProductoSerializer` calcula `valor_disponible` en Python con `Decimal` — preciso.
- Filtros por `q` y `categoria` funcionan correctamente.
- Usa el permiso `PuedeConsultarExistenciasTerminados` de `productos_terminados` — RBAC correcto sin duplicar permisos.

### ⚠️ Mejoras recomendadas

**1. Sin tests**

Este es el único endpoint del Ciclo 3 sin ninguna prueba. Mínimo recomendado:
- Test que devuelve solo productos activos con `stock_actual > 0`.
- Test de filtro por `q` (búsqueda por nombre).
- Test de filtro por `categoria`.
- Test que usuario sin permiso recibe 403.
- Test que usuario no autenticado recibe 401.

**2. No filtra por `activo=True` en la categoría**

El filtro `id_producto__id_categoria_id=int(categoria)` no excluye categorías inactivas si existieran. Actualmente `CategoriaProducto` no tiene campo `activo`, pero es una deuda de diseño a considerar en futuras iteraciones.

**3. `DisponibilidadProductoSerializer` está en el namespace raíz de `comercializacion/`**

El serializer y su view correspondiente están en `comercializacion/serializers.py` y `comercializacion/views.py`. Aunque es funcional, **no sigue la convención de sub-apps** establecida por el equipo (cada CU/grupo en su propia sub-app con archivos propios). El equipo decidió dejarlo así por ahora — documentar como deuda técnica conocida.

**4. `valor_disponible` como `str` en la respuesta**

Se devuelve como `str` (resultado de `.quantize()`) pero el serializer lo declara como `SerializerMethodField` sin tipo explícito. Considerar usar `DecimalField` con `coerce_to_string=True` para consistencia con el resto de campos monetarios del proyecto.

---

## CU19 — Historial de Precios (`apps.productos_inventario.productos`)

### ✅ Lo que está bien — Implementación de referencia

Esta es la implementación más completa y bien estructurada del Ciclo 3. Sirve como referencia para el equipo.

- **Ubicación correcta:** dentro de `productos/` sub-app de `productos_inventario`, tal como dicta `PACKAGE_CU_MAP.md`.
- **RBAC estricto:** `EsPropietarioCU19` verifica el rol de negocio explícitamente, sin bypass de superusuario — decisión arquitectónica deliberada y correcta para este CU.
- **`FiltrosHistorialPreciosSerializer`:** valida todos los filtros de entrada (`id_producto`, `fecha_desde`, `fecha_hasta`) con tipos, rangos y coherencia de rango de fechas — ningún valor inválido llega al queryset.
- **`selectors.py`:** manejo correcto de zonas horarias (`America/La_Paz`) con `datetime.combine + make_aware`. El test `test_fechas_incluyen_dia_completo_de_bolivia` verifica esto explícitamente — muy maduro.
- **Solo lectura real:** `http_method_names = ['get', 'head', 'options']` en la vista — 405 garantizado para POST/PUT/PATCH/DELETE sin lógica adicional.
- **Sin N+1:** `select_related('id_producto')` en el queryset; el test `test_lectura_precarga_productos_sin_consultas_por_fila` lo verifica con `assertNumQueries(1)`.
- **Suite de tests:** 20 pruebas unitarias que cubren RBAC, filtros, paginación, zona horaria, precisión decimal, inmutabilidad de datos y resolución de rutas. El test `test_get_no_modifica_precios_productos_inventarios_ni_compras` es especialmente valioso — verifica que el endpoint no emite ninguna escritura a la BD.

### ⚠️ Mejoras recomendadas

**1. Sin auditoría de consulta**

CU19 expone información financiera sensible (historial de precios de todos los productos). El Propietario es el único actor autorizado, pero no queda registro en la `Bitacora` de cuándo consultó ni con qué filtros.

Recomendación: agregar `AccionBitacora.CONSULTA_HISTORIAL_PRECIOS` (acción informativa) y registrar la consulta en `HistorialPreciosListView.get_queryset()` o en un override de `list()`:

```python
def list(self, request, *args, **kwargs):
    respuesta = super().list(request, *args, **kwargs)
    Bitacora.registrar(
        usuario=request.user,
        accion=AccionBitacora.CONSULTA_HISTORIAL_PRECIOS,
        tabla_afectada='historial_precio_producto',
        descripcion='Consulta de historial de precios',
        agente_usuario=request.META.get('HTTP_USER_AGENT'),
    )
    return respuesta
```

**2. `get_permissions()` encadena dos permisos que se solapan**

```python
def get_permissions(self):
    return [
        IsAuthenticated(),
        TienePermiso('gestionar_productos'),
        EsPropietarioCU19(),
    ]
```

`EsPropietarioCU19` ya verifica `is_authenticated` internamente. Y `TienePermiso('gestionar_productos')` es redundante: si el Propietario no tuviera ese permiso en el seed, quedaría bloqueado aunque tenga el rol correcto. El permiso `gestionar_productos` es para Administrador y Propietario; el CU19 es exclusivo del Propietario.

Recomendación: simplificar a solo `EsPropietarioCU19()` y que este permiso verifique `is_authenticated` internamente (ya lo hace):

```python
def get_permissions(self):
    return [EsPropietarioCU19()]
```

**3. Paginación usa `PageNumberPagination` global sin `page_size` fijo**

`HistorialPreciosListView` hereda el `page_size` de `DEFAULT_PAGINATION_CLASS` en settings. Si ese valor cambia globalmente, afecta este endpoint. Considerar definir el `page_size` explícitamente en la vista o crear una clase de paginación propia para el módulo.

---

## Resumen de Acciones Prioritarias

| Prioridad | CU | Acción |
|:---:|---|---|
| 🔴 Alta | CU14 | Agregar `Bitacora.registrar()` en `registrar_pedido.py` y `cambiar_estado_pedido.py` |
| 🔴 Alta | CU14 | Agregar validación de `fecha_entrega` futura en el serializer |
| 🟡 Media | CU17 | Escribir tests mínimos (5 casos) |
| 🟡 Media | CU15 | Agregar validación de `fecha_entrega` en `selectors.py` |
| 🟡 Media | CU19 | Simplificar `get_permissions()` a solo `EsPropietarioCU19()` |
| 🟡 Media | CU19 | Agregar auditoría de consulta (informativa) |
| 🟢 Baja | CU14 | Eliminar `permission_classes` redundante en `PedidoDetailView` |
| 🟢 Baja | CU15 | Agregar paginación a `PedidoEstadoListView` |
| 🟢 Baja | CU17 | Mover a sub-app `disponibilidad/` (deuda técnica documentada) |

---

## Estado de Arquitectura General — Ciclo 3

La arquitectura general **respeta los lineamientos del proyecto**:
- Sub-apps por dominio dentro del paquete `comercializacion/` ✅
- Capa de servicios separada de las vistas ✅
- `selectors.py` para queries complejas ✅
- `permissions.py` explícito por sub-app ✅
- Migrations propias por sub-app ✅
- Uso de `@transaction.atomic` en operaciones de escritura ✅

La deuda más importante del ciclo es la **ausencia de auditoría en CU14** — es el único CU de escritura en todo el backend que no registra en Bitácora.
