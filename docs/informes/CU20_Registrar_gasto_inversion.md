# CU20 Registrar gasto/inversión: guía de implementación

**Proyecto:** Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo — Panadería Santiago
**Ciclo:** 4 · **Paquete:** `apps.compras` · **Actor principal:** Propietario

---

## 1. Qué es un gasto y qué es una inversión

Gasto e inversión son **egresos del negocio que no son compra de materia prima**. La compra de insumos (harina, azúcar, etc.) ya la cubre CU07, que alimenta el inventario.

| | **Gasto** | **Inversión** |
|---|---|---|
| Qué es | Pago que se consume en el periodo | Compra que dura años y aumenta la capacidad del negocio |
| Ejemplos | Alquiler, luz, agua, mantenimiento del horno, gas, sueldos | Horno industrial, refrigerador, mesas de acero, mejoras del local |
| En los datos de ejemplo | Alquiler Bs 1.500, energía Bs 350, agua Bs 120, mantenimiento Bs 200 | Horno industrial Bs 8.000 |

**Aclaración sobre "inventario de inmuebles":** el sistema solo **registra el dinero gastado**. No lleva un inventario de activos (no hay tabla de maquinaria, ni vida útil o depreciación). El perfil solo pide registrar gastos e inversiones y relacionarlos con los ingresos, así que un control de activos queda fuera del alcance.

**Regla para no duplicar:** si es materia prima, va por CU07; si es cualquier otro egreso, va por CU20. Si algo se registra en ambos lados, CU24 y CU25 lo contarán dos veces.

---

## 2. Flujo completo

```
React (formulario) → POST /api/compras/gastos/ → views.py → serializers.py (valida)
   → services.py (transaction.atomic: crea el movimiento + escribe la bitácora)
   → models.py → PostgreSQL (movimiento_economico, bitacora)
```

Es un CU de **una sola tabla de negocio** (más la bitácora). No toca inventario, así que no necesita `select_for_update()`. Sí conviene `transaction.atomic()`, porque se escriben dos tablas (el movimiento y la bitácora) y deben guardarse juntas.

---

## 3. Base de datos

La tabla ya existe en el DDL:

| Columna | Tipo | Uso |
|---|---|---|
| `id_movimiento` | bigint PK | Debe ser autoincremental en Django (`BigAutoField`) |
| `id_usuario` | bigint FK | Quién lo registró (viene de la sesión) |
| `tipo` | varchar(20) | `gasto` o `inversion` |
| `categoria` | varchar(20) | `alquiler`, `servicios`, `mantenimiento`, `equipos`, `otros` (por defecto `otros`) |
| `concepto` | varchar(100) | Título corto ("Alquiler del local") |
| `descripcion` | text | Detalle opcional |
| `monto` | decimal(10,2) | Importe en Bs, mayor a 0 (`CHECK`) |
| `fecha_hora` | timestamp | Por defecto `now()`; editable, nunca futura |
| `anulado` | boolean | `false` por defecto; anular conserva la fila |

### Decisiones tomadas (implementadas en el backend)

| Tema | Decisión |
|---|---|
| **Corrección de errores** | `anulado` + `POST /api/gastos/{id}/anular/`. No se borra: se conserva la fila y la bitácora. Doble anulación → 400. |
| **Agrupar en reportes** | `categoria` con `choices`. Sin ella, "Luz" y "Energía eléctrica" quedarían como dos grupos distintos en CU24/CU25. |
| **Fecha del gasto** | `fecha_hora` opcional en el POST y validada contra `timezone.now()`; se permite registrar hoy un pago hecho ayer. |

Integridad declarada en el modelo (migración `gastos.0002`), replicada en el DDL:
`CHECK (monto > 0)`, `CHECK (tipo IN ('gasto','inversion'))`,
`CHECK (categoria IN (...))` e índice sobre `fecha_hora` para los reportes por período.

---

## 4. Archivos del backend

La ruta real sigue la convención del repo (servicios en `services/`, lectura en `consulta.py`, vistas `APIView`, listados como arreglo plano):

| Archivo | Responsabilidad |
|---|---|
| `apps/compras/gastos/models.py` | Modelo `MovimientoEconomico` + `TipoMovimientoEconomico` + `CategoriaMovimientoEconomico` |
| `apps/compras/gastos/serializers.py` | Valida la entrada y arma la salida |
| `apps/compras/gastos/services/registrar_movimiento.py` | `registrar_movimiento()` y `anular_movimiento()`: escriben y dejan bitácora |
| `apps/compras/gastos/consulta.py` | `leer_filtros_gasto()` + `gastos_filtrados()`: lectura con filtros |
| `apps/compras/gastos/permissions.py` | `PuedeGestionarGastos` (permiso `registrar_gastos`) |
| `apps/compras/gastos/views.py` | `APIView`: listar/crear, detalle y anular |
| `apps/compras/gastos/urls.py` | Rutas `/api/gastos/` (montadas en `config/urls.py`) |
| `apps/compras/gastos/tests.py` | Pruebas del CU20 |
| `migrations/` | Generadas con `makemigrations` |

### Modelo

```python
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

class MovimientoEconomico(models.Model):
    class Tipo(models.TextChoices):
        GASTO = "gasto", "Gasto"
        INVERSION = "inversion", "Inversión"

    id_movimiento = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="id_usuario", related_name="movimientos_economicos")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    concepto = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_hora = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "movimiento_economico"
        ordering = ["-fecha_hora"]
        indexes = [models.Index(fields=["fecha_hora"])]   # lo usarán CU24 y CU25
        constraints = [models.CheckConstraint(
            check=Q(monto__gt=0),       # en Django 5.1+ el parámetro se llama condition=
            name="ck_mov_economico_monto_positivo")]
```

### Serializer

```python
from rest_framework import serializers
from django.utils import timezone

class MovimientoEconomicoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre_completo", read_only=True)

    class Meta:
        model = MovimientoEconomico
        fields = ["id_movimiento", "tipo", "concepto", "descripcion",
                  "monto", "fecha_hora", "usuario_nombre"]
        read_only_fields = ["id_movimiento", "usuario_nombre"]
        extra_kwargs = {"fecha_hora": {"required": False}}

    def validate_monto(self, valor):
        if valor <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0.")
        return valor

    def validate_fecha_hora(self, valor):
        if valor > timezone.now():
            raise serializers.ValidationError("La fecha no puede ser futura.")
        return valor
```

### Servicio

```python
from django.db import transaction

@transaction.atomic
def registrar_gasto_inversion(*, usuario, tipo, concepto, monto, descripcion="", fecha_hora=None):
    datos = dict(usuario=usuario, tipo=tipo, concepto=concepto,
                 monto=monto, descripcion=descripcion)
    if fecha_hora:
        datos["fecha_hora"] = fecha_hora
    movimiento = MovimientoEconomico.objects.create(**datos)

    registrar_bitacora(      # reutilizar el helper del Ciclo 1 (CU26), no duplicarlo
        usuario=usuario, accion="CREATE", tabla_afectada="movimiento_economico",
        descripcion=f"Registro de {tipo}: {concepto} por Bs {monto}")
    return movimiento
```

### Vista (el "controller")

```python
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

class MovimientoEconomicoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MovimientoEconomicoSerializer
    permission_classes = [IsAuthenticated]   # + permiso "registrar_gastos" (ver sección 6)

    def get_queryset(self):
        p = self.request.query_params
        return listar_movimientos(tipo=p.get("tipo"), desde=p.get("desde"),
                                  hasta=p.get("hasta"), buscar=p.get("q"))

    def perform_create(self, serializer):
        serializer.instance = registrar_gasto_inversion(
            usuario=self.request.user, **serializer.validated_data)
```

**La vista no tiene lógica:** valida con el serializer, llama al servicio y responde. El usuario sale de `request.user`, nunca del formulario.

---

## 5. API

| Método | URL | Qué hace | Versión |
|---|---|---|---|
| `POST` | `/api/gastos/` | Registrar gasto o inversión | Implementada |
| `GET` | `/api/gastos/` | Listar con filtros (`tipo`, `categoria`, `fecha_desde`, `fecha_hasta`, `anulado`, `search`) | Implementada |
| `GET` | `/api/gastos/{id}/` | Ver el detalle | Implementada |
| `POST` | `/api/gastos/{id}/anular/` | Anular el movimiento sin borrarlo | Implementada |
| `GET` | `/api/gastos/resumen/` | Totales de gasto e inversión del periodo filtrado | Pendiente (CU24/CU25) |

No exponer `DELETE`: un egreso real no se borra. Por defecto el listado excluye
los anulados; `?anulado=todos` los incluye y `?anulado=true` muestra solo esos.

---

## 6. Permisos

Hay una diferencia entre los documentos que conviene resolver:

- `PACKAGE_CU_MAP.md` dice que el actor de CU20 es el **Propietario**.
- El poblado asigna el permiso `registrar_gastos` al rol **Administrador** y al **Propietario**.

Como el control de acceso se basa en permisos (CU04), lo más coherente es proteger el endpoint con el permiso `registrar_gastos` y que lo reciban los roles que el equipo decida. Verificar cómo se implementó la clase de permisos en el Ciclo 1 y reutilizarla.

**Resuelto:** la API usa `PuedeGestionarGastos`, que exige el permiso `registrar_gastos`; el seeder (`seed_usuarios.py`) y los poblados quedaron alineados con ese nombre. Administrador y Propietario lo reciben.

---

## 7. Frontend

| Archivo (ruta sugerida) | Responsabilidad |
|---|---|
| `types/gasto.ts` | Tipos TypeScript |
| `services/gastosApi.ts` | Llamadas HTTP (`listar`, `crear`) |
| `pages/gastos/GastosPage.tsx` | Pantalla: botón "Nuevo", filtros y tabla |
| `components/gastos/GastoForm.tsx` | Formulario de registro |
| `components/gastos/GastosTable.tsx` | Tabla con paginación |
| Archivo de rutas | Ruta `/gastos`, visible solo para roles con el permiso |

```ts
export type TipoMovimiento = "gasto" | "inversion";

export interface MovimientoEconomico {
  id_movimiento: number;
  tipo: TipoMovimiento;
  concepto: string;
  descripcion: string;
  monto: string;          // DRF envía los decimales como texto: no usar number
  fecha_hora: string;     // ISO 8601
  usuario_nombre: string;
}

export interface MovimientoEconomicoInput {
  tipo: TipoMovimiento;
  concepto: string;
  descripcion?: string;
  monto: string;
  fecha_hora?: string;
}
```

**Estados de la pantalla:** cargando, lista vacía ("Aún no hay registros"), error de red, error de validación (mensajes del backend junto a cada campo) y éxito (cerrar el formulario y refrescar la lista).

**Validaciones del formulario** (para mejorar la experiencia, no para reemplazar al backend): tipo obligatorio, concepto obligatorio (máximo 100 caracteres), monto positivo con máximo 2 decimales, fecha no futura.

---

## 8. Tabla detallada del CU20

| Campo | Detalle |
|---|---|
| **ID / Nombre** | CU20 Registrar gasto/inversión |
| **Paquete / Ciclo** | `apps.compras` (subruta sugerida `gastos`) / Ciclo 4 |
| **Actor principal** | Propietario (el permiso `registrar_gastos` también lo tiene el Administrador en el poblado) |
| **Prioridad / Riesgo** | Media / Bajo (registro simple, sin dependencias complejas) |
| **Objetivo** | Registrar los egresos del negocio que no son compra de materia prima, para calcular el resultado económico |
| **Precondiciones** | Usuario autenticado (CU01) con el permiso `registrar_gastos` |
| **Flujo principal** | 1) El actor abre "Gastos e inversiones". 2) Pulsa "Nuevo". 3) Elige tipo, escribe concepto, monto y (opcional) descripción y fecha. 4) El sistema valida los datos. 5) Guarda el movimiento. 6) Registra la acción en la bitácora. 7) Muestra confirmación y actualiza la lista. |
| **Flujos alternativos / errores** | Monto ≤ 0 o con más de 2 decimales → error junto al campo. Tipo inválido → error. Fecha futura → error. Usuario sin permiso → 403. Sin sesión → 401. Falla al guardar → no queda nada guardado (transacción). |
| **Postcondiciones** | Hay una fila nueva en `movimiento_economico` y otra en `bitacora`. |
| **Tablas** | `movimiento_economico` (escribe), `bitacora` (escribe), `usuario` (lee) |
| **Reglas de negocio** | Solo egresos que no son materia prima. El monto es siempre positivo. El tipo es `gasto` o `inversion`. El usuario sale de la sesión. No se borra. |
| **Relaciones UML** | Sin `<<include>>` ni `<<extend>>`. Es independiente; lo leen CU24 y CU25. |
| **Requisitos no funcionales** | Auditoría (bitácora), control de acceso por rol, precisión decimal. |

---

## 9. Pruebas clave

| Prueba | Resultado esperado |
|---|---|
| Registrar un gasto válido | 201; hay una fila en `movimiento_economico` y otra en `bitacora` |
| Monto `0` o negativo | 400; no se guarda nada |
| Monto con 3 decimales | 400 |
| Tipo distinto de `gasto`/`inversion` | 400 |
| Fecha futura | 400 |
| Usuario sin el permiso | 403 |
| Sin autenticación | 401 |
| Falla la bitácora (simulada) | No queda el movimiento (la transacción se revierte) |
| Listar filtrando por tipo y rango de fechas | Solo devuelve los que corresponden |
| Comparar con el poblado | Los 5 movimientos de ejemplo suman Bs 10.170 (1.500 + 8.000 + 350 + 120 + 200) |

---

## 10. Orden sugerido de implementación

1. Modelo y migración (con la decisión sobre `categoria` y `anulado`).
2. Serializer con sus validaciones.
3. Servicio y su prueba.
4. Vista, rutas y permisos.
5. Listado con filtros y paginación.
6. Frontend: tipos, API, tabla y formulario.
7. Pruebas de extremo a extremo, y recién entonces las mejoras opcionales.

---

## Fuentes

- `Database_Panaderia_Santiago_FINAL.sql`: tabla `movimiento_economico` (columnas, tipos y FK a `usuario`) y tabla `bitacora`.
- `Poblacion_4_Dias_Panaderia_Santiago.sql`: sección 5 (ejemplos de gasto e inversión: alquiler, horno, luz, agua, mantenimiento) y sección 1 (`rol_permiso`: el permiso 9 `registrar_gastos` asignado a los roles 1 y 2).
- `PACKAGE_CU_MAP.md`, secciones 2 y 3 (CU20: actor, paquete, ciclo, prioridad, riesgo) y sección 4 (paquete `apps.compras`).
- `Perfil Proyecto SI-1 grupo3.md`, punto 1.7.6 (Módulo de Compras, Proveedores y Gastos: registro de gastos e inversiones y relación de egresos con ingresos) y punto 1.7.8 (Bitácora).
- Decisiones del proyecto: sin triggers ni PA, lógica en `services.py`, capas `views` → `serializers` → `services` → `models`, IDs autoincrementales.
- Django REST Framework, serializers y validación: https://www.django-rest-framework.org/api-guide/serializers/
- Django REST Framework, ViewSets y mixins: https://www.django-rest-framework.org/api-guide/generic-views/#mixins
- Django, restricciones de modelo (`CheckConstraint`): https://docs.djangoproject.com/en/stable/ref/models/constraints/
- Django, transacciones: https://docs.djangoproject.com/en/stable/topics/db/transactions/
