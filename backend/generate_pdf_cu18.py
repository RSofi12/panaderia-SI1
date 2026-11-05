"""
Script para generar la Guía Completa de Implementación y Defensa Técnica del CU18 para Roberto.
Genera un documento PDF académico, didáctico y exhaustivo con ReportLab.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numerar páginas 'Página X de Y' con encabezado y pie."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # No numerar portada

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))  # Slate-500

        # Encabezado
        self.drawString(54, 755, "Panadería Santiago (SI-1) — Guía de Implementación y Defensa Técnica CU18")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 755, "Autor: Roberto")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)

        # Pie de página
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Ciclo #3 · PUDS + UML · Módulo: Productos e Inventario (Bajas / Mermas)")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def generar_pdf():
    output_dir = os.path.abspath(r"d:\Proyecto SI\docs\informes")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "Guia_Defensa_CU18_Roberto.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Paleta de colores institucional
    c_primary = colors.HexColor("#78350F")    # Amber-900 (Marrón panadería)
    c_secondary = colors.HexColor("#B45309")  # Amber-700
    c_dark = colors.HexColor("#0F172A")       # Slate-900
    c_body = colors.HexColor("#334155")       # Slate-700
    c_bg_light = colors.HexColor("#FFFBEB")   # Amber-50
    c_border = colors.HexColor("#CBD5E1")     # Slate-300
    c_emerald = colors.HexColor("#065F46")    # Verde éxito
    c_blue = colors.HexColor("#1E40AF")       # Azul técnico
    c_rose = colors.HexColor("#9F1239")       # Rojo / merma

    # Tipografías y jerarquías
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=21,
        leading=25,
        textColor=c_primary,
        alignment=1,
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        alignment=1,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_dark,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_body,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
    )

    story = []

    # =========================================================================
    # PORTADA ACADÉMICA
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO", ParagraphStyle('Univ', parent=subtitle_style, fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor("#475569"))))
    story.append(Paragraph("FACULTAD DE CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES", ParagraphStyle('Fac', parent=subtitle_style, fontSize=9, textColor=colors.HexColor("#64748B"))))
    story.append(Paragraph("SISTEMAS DE INFORMACIÓN I (SI-1) — GRUPO #3", ParagraphStyle('Mat', parent=subtitle_style, fontSize=9.5, textColor=c_secondary)))
    story.append(Spacer(1, 25))

    story.append(Paragraph("GUÍA INTEGRAL DE IMPLEMENTACIÓN Y DEFENSA TÉCNICA", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("CASO DE USO 18 (CU18):<br/><b>REGISTRAR BAJA DE PRODUCTOS TERMINADOS (MERMAS Y PÉRDIDAS)</b>", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="70%", thickness=2, color=c_secondary, spaceBefore=4, spaceAfter=16))

    story.append(Paragraph("Sistema de Información Web para la Panadería <b>'Santiago'</b>", ParagraphStyle('Sub', parent=subtitle_style, fontSize=10, textColor=c_dark)))
    story.append(Spacer(1, 25))

    datos_portada = [
        [Paragraph("<b>Caso de Uso (PUDS):</b>", body_style), Paragraph("CU18: Registrar baja de productos terminados", body_style)],
        [Paragraph("<b>Autor / Desarrollador:</b>", body_style), Paragraph("<b>Roberto</b> (Equipo Panadería Santiago)", body_style)],
        [Paragraph("<b>Ciclo de Desarrollo:</b>", body_style), Paragraph("Ciclo #3 (Comercialización y Control de Pérdidas)", body_style)],
        [Paragraph("<b>Rama Git Activa:</b>", body_style), Paragraph("<code>robert-dev</code> (sincronizada con <code>origin/prueba</code>)", code_style)],
        [Paragraph("<b>Sub-app Backend:</b>", body_style), Paragraph("<code>backend/apps/productos_inventario/productos_terminados/</code>", code_style)],
        [Paragraph("<b>Módulo Frontend:</b>", body_style), Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/</code>", code_style)],
        [Paragraph("<b>Estado de Implementación:</b>", body_style), Paragraph("<b>100% Funcional, Probado y Verificado (16 Tests en Verde)</b>", ParagraphStyle('Ok', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold'))],
        [Paragraph("<b>Objetivo del Documento:</b>", body_style), Paragraph("Brindar el mapa de código, flujo transaccional, guión oral de defensa, respuestas a preguntas de tribunal y resolución de modificaciones en vivo.", body_style)],
    ]
    t_portada = Table(datos_portada, colWidths=[150, 350])
    t_portada.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 1, c_secondary),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_portada)
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 1: MAPA DE RUTAS DEL CÓDIGO
    # =========================================================================
    story.append(Paragraph("1. Mapa de Rutas del Código (Dónde está situado el CU18)", h1_style))
    story.append(Paragraph(
        "El caso de uso 18 se diseñó siguiendo la arquitectura modular de 5 paquetes de Django y componentes limpios en React. "
        "A continuación se detallan todos los archivos creados e intervenidos en el proyecto:",
        body_style
    ))
    story.append(Spacer(1, 4))

    rutas_data = [
        [Paragraph("<b>Capa</b>", body_style), Paragraph("<b>Ruta del Archivo</b>", body_style), Paragraph("<b>Estado</b>", body_style), Paragraph("<b>Responsabilidad Técnica</b>", body_style)],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/services/registrar_baja.py</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('st1', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Servicio de dominio transaccional (<code>@transaction.atomic</code>). Aplica <code>select_for_update()</code>, descuenta stock, crea Nota de Pérdida, movimiento Kardex y audita en Bitácora.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/permissions.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st2', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Guardia RBAC <code>PuedeRegistrarBajaProducto</code>. Autoriza exclusivamente a Propietario, Personal de Producción y Administrador.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/serializers.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st3', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Serializadores <code>NotaPerdidaProductoCreateSerializer</code> y <code>NotaPerdidaProductoSerializer</code> para validación de entrada y payload JSON.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/views.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st4', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Controlador <code>NotaPerdidaProductoListCreateView</code>. Expone <code>POST</code> (crear merma) y <code>GET</code> (historial filtrable).", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/urls.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st5', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Ruta REST oficial: <code>/api/productos-terminados/mermas/</code>.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/usuarios_seguridad/bitacora/models.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st6', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Adición del enumerador <code>AccionBitacora.REGISTRO_BAJA_PRODUCTO</code> para trazabilidad en CU26.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>apps/productos_inventario/productos_terminados/tests.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st7', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Suite automatizada con 7 pruebas unitarias específicas de CU18 (descuento, stock insuficiente, concurrencia, permisos).", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/components/RegistrarBajaModal.tsx</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('st8', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Modal interactivo con selector reactivo de panes, validación de stock disponible en vitrina y cálculo en vivo del valor monetario de pérdida.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/components/HistorialMermasModal.tsx</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('st9', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Modal de consulta de auditoría de mermas con métricas KPI (total bajas, unidades perdidas, valor económico acumulado).", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/ExistenciasTab.tsx</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st10', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Integración de botones 'Registrar Baja' en barra superior y acción rápida de merma por fila en la tabla de existencias.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/services/existenciasService.ts</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st11', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Métodos Axios <code>registrarBaja(payload)</code> y <code>listarMermas(filtros)</code>.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/types/existencias.ts</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('st12', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Contratos TypeScript: <code>NotaPerdida</code>, <code>RegistrarBajaPayload</code> y <code>FiltrosMermas</code>.", body_style)
        ],
    ]

    t_rutas = Table(rutas_data, colWidths=[55, 175, 60, 215])
    t_rutas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_rutas)
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 2: ARQUITECTURA Y CÓMO FUNCIONA (LÓGICA INTERNA)
    # =========================================================================
    story.append(Paragraph("2. Arquitectura y Funcionamiento Interno del CU18", h1_style))
    story.append(Paragraph(
        "En un negocio tradicional de panadería, las mermas (panes quemados en horno, caídos al piso, deformados o vencidos) "
        "solían desecharse sin registro alguno, generando un desfase invisible entre lo horneado y el dinero en caja. "
        "El CU18 resuelve este problema garantizando una <b>transacción contable cerrada</b> que afecta 4 entidades en un solo paso atómico:",
        body_style
    ))
    story.append(Spacer(1, 4))

    pasos_transaccionales = [
        [Paragraph("<b>Paso</b>", body_style), Paragraph("<b>Mecanismo de Software</b>", body_style), Paragraph("<b>Impacto en la Base de Datos (PostgreSQL)</b>", body_style)],
        [
            Paragraph("<b>1. Concurrencia</b>", body_style),
            Paragraph("<code>select_for_update()</code>", code_style),
            Paragraph("Bloquea la fila del producto en <code>inventario_producto_terminado</code>. Evita condiciones de carrera si dos panaderos o cajeros intentan descontar stock simultáneamente.", body_style)
        ],
        [
            Paragraph("<b>2. Validación</b>", body_style),
            Paragraph("Validación de Stock Remanente", body_style),
            Paragraph("Verifica que <code>stock_actual >= cantidad</code>. Si hay 15 marraquetas en vitrina, el sistema impide dar de baja 20, arrojando un HTTP 400 con mensaje semántico claro.", body_style)
        ],
        [
            Paragraph("<b>3. Valorización</b>", body_style),
            Paragraph("Cálculo Económico del Costo", body_style),
            Paragraph("Recupera el costo de producción unitario desde <code>DetalleProduccion</code> (o costo base del catálogo). Multiplica <code>cantidad * costo_unitario</code> para determinar la pérdida monetaria en Bs.", body_style)
        ],
        [
            Paragraph("<b>4. Descuento</b>", body_style),
            Paragraph("Descuento Físico", body_style),
            Paragraph("Actualiza <code>stock_actual = stock_actual - cantidad</code> en <code>inventario_producto_terminado</code> de forma atómica.", body_style)
        ],
        [
            Paragraph("<b>5. Comprobante</b>", body_style),
            Paragraph("Generación de Nota", body_style),
            Paragraph("Inserta un registro en <code>nota_perdida_producto</code> vinculado al lote de producción y al usuario responsable.", body_style)
        ],
        [
            Paragraph("<b>6. Kardex</b>", body_style),
            Paragraph("Movimiento de Inventario", body_style),
            Paragraph("Crea un movimiento de tipo <code>SALIDA</code> en <code>movimiento_producto_terminado</code>, dejando trazabilidad en el kardex físico del producto.", body_style)
        ],
        [
            Paragraph("<b>7. Auditoría</b>", body_style),
            Paragraph("Bitácora General (CU26)", body_style),
            Paragraph("Inserta en <code>bitacora</code> la acción <code>REGISTRO_BAJA_PRODUCTO</code> con usuario, fecha, motivo y valor monetario exacto.", body_style)
        ],
    ]
    t_pasos = Table(pasos_transaccionales, colWidths=[80, 140, 280])
    t_pasos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_pasos)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Principio ACID y Atomicidad:", h2_style))
    story.append(Paragraph(
        "Todo este proceso se encuentra envuelto dentro del context manager <code>with transaction.atomic():</code> de Django. "
        "Si por cualquier motivo falla la inserción en la bitácora o en el kardex, <b>toda la operación se revierte automáticamente (ROLLBACK)</b>, "
        "impidiendo que el inventario quede descuadrado.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 3: CÓDIGO CRÍTICO EXPLICADO LÍNEA POR LÍNEA
    # =========================================================================
    story.append(Paragraph("3. Código Crítico de la Lógica Explicado", h1_style))
    story.append(Paragraph(
        "Para defender técnicamente este caso de uso, debes conocer las líneas maestras de su implementación backend y frontend:",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("A. Servicio de Dominio: registrar_baja.py", h2_style))
    codigo_backend = """@transaction.atomic
def registrar_baja_producto(*, id_producto: int, cantidad: int, usuario, ...):
    # 1. Bloqueo de fila para evitar condiciones de carrera concurrentes
    inventario = InventarioProductoTerminado.objects.select_for_update().get(id_producto=producto)

    # 2. Validación de consistencia física
    if inventario.stock_actual < cantidad:
        raise ValidationError({'cantidad': f'Stock insuficiente en vitrina ({inventario.stock_actual})'})

    # 3. Valorización matemática de la pérdida
    costo_unitario = detalle_prod.costo_unitario or producto.costo_produccion
    costo_total = cantidad * costo_unitario

    # 4. Descuento físico en inventario
    inventario.stock_actual -= cantidad
    inventario.save(update_fields=['stock_actual'])

    # 5. Creación de la Nota de Pérdida
    nota = NotaPerdidaProducto.objects.create(
        id_detalle_produccion=detalle_prod, id_usuario=usuario,
        cantidad=cantidad, costo_unitario=costo_unitario
    )

    # 6. Salida en Kardex físico
    MovimientoProductoTerminado.objects.create(
        id_inventario=inventario, id_nota_perdida=nota,
        tipo=TipoMovimientoProductoTerminado.SALIDA, cantidad=cantidad
    )

    # 7. Registro indeleble en la Bitácora de Seguridad
    Bitacora.registrar(usuario=usuario, accion=AccionBitacora.REGISTRO_BAJA_PRODUCTO, ...)
    return nota"""
    t_code = Table([[Paragraph(f"<pre>{codigo_backend}</pre>", code_style)]], colWidths=[500])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_code)
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. Control de Acceso por Roles (RBAC): permissions.py", h2_style))
    story.append(Paragraph(
        "Se implementó la clase de permiso <code>PuedeRegistrarBajaProducto(BasePermission)</code>. "
        "Esta clase evalúa los permisos del JWT y solo autoriza el método <code>POST</code> a usuarios que posean "
        "<code>registrar_produccion</code> (Personal de Producción / Maestro Panadero), <code>gestionar_inventario</code> o <code>gestionar_productos</code> (Propietario y Admin). "
        "Cualquier intento por parte de un Personal de Ventas o usuario no autenticado es rechazado con <b>HTTP 403 Forbidden</b>.",
        body_style
    ))

    story.append(Paragraph("C. Frontend React: RegistrarBajaModal.tsx", h2_style))
    story.append(Paragraph(
        "En el cliente, el modal calcula reactivamente la pérdida monetaria mediante <code>useMemo</code>: "
        "<code>valorPerdidaEstimado = (cantidad * costoUnitarioEstimado).toFixed(2)</code>. "
        "Además, realiza validación inmediata en el cliente: si el usuario tipea una cantidad superior al stock en vitrina, "
        "el botón de confirmación se bloquea y se muestra un banner de advertencia en rojo, previniendo peticiones inválidas hacia la API.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 4: GUIÓN DE EXPOSICIÓN ORAL PARA ROBERTO
    # =========================================================================
    story.append(Paragraph("4. Guión de Exposición Oral para Roberto frente al Tribunal", h1_style))
    story.append(Paragraph(
        "Sigue este guión estructurado cuando el docente o tribunal te pida exponer tu parte:",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Apertura y Contextualización (30 segundos):", h2_style))
    story.append(Paragraph(
        "«Buenas tardes docente y compañeros. Mi nombre es <b>Roberto</b> y dentro del sistema para la Panadería Santiago tuve bajo mi responsabilidad "
        "la implementación integral del <b>Caso de Uso 18: Registrar baja de productos terminados por merma o pérdida</b>.<br/>"
        "En una panadería artesanal, este caso de uso es crítico porque entre el 3% y el 7% de las horneadas sufren mermas por quemado, deformación, rotura o vencimiento. "
        "Si esas unidades no se descuentan formalmente de la vitrina, el sistema mostraría pan inexistente para la venta y descuadraría el balance económico.»",
        callout_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Demostración en Vivo en la Pantalla (1 minuto):", h2_style))
    story.append(Paragraph(
        "«Para demostrar su funcionamiento en vivo:<br/>"
        "1. Ingreso con el usuario del <b>Personal de Producción (Maestro Panadero)</b> o del <b>Propietario</b> y nos dirigimos a la pestaña de <b>Existencias</b>.<br/>"
        "2. Como pueden observar, cada producto tiene su stock en tiempo real. En la fila de <i>'Pan de Batalla'</i> tenemos 50 unidades.<br/>"
        "3. Hago clic en el botón de acción <b>'Registrar Baja'</b>. Se abre un modal reactivo que me muestra el stock disponible en vitrina.<br/>"
        "4. Si intento ingresar 60 unidades, el frontend inmediatamente me advierte en rojo que no puedo superar las 50 disponibles.<br/>"
        "5. Selecciono 5 unidades con el motivo <i>'Defecto de Horneado / Quemado'</i> y agrego una observación. Observen cómo el sistema calcula automáticamente en pantalla la pérdida económica en bolivianos con base en el costo de producción.<br/>"
        "6. Al confirmar, el sistema ejecuta una transacción atómica en Django: el stock en vitrina baja de 50 a 45 unidades al instante, se genera la Nota de Pérdida oficial y queda auditado en el Kardex y en la Bitácora.»",
        callout_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3. Demostración de Auditoría y Kardex (30 segundos):", h2_style))
    story.append(Paragraph(
        "«Si ahora abro el modal de <b>Kardex</b> de ese producto, observamos la nueva fila de tipo <b>SALIDA</b> generada por el CU18 con su respectivo código de nota de pérdida.<br/>"
        "Asimismo, si entramos al botón <b>'Historial de Mermas'</b>, el Propietario tiene un tablero analítico con el acumulado de panes dados de baja y el valor monetario total de pérdidas para tomar decisiones operativas.»",
        callout_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 5: PREGUNTAS DEL DOCENTE Y RESPUESTAS MAESTRAS
    # =========================================================================
    story.append(Paragraph("5. Batería de Preguntas de Defensa y Respuestas Maestras", h1_style))
    story.append(Paragraph(
        "Estas son las preguntas técnicas más probables que te formulará el docente o tribunal, con sus respuestas fundamentadas:",
        body_style
    ))
    story.append(Spacer(1, 4))

    faq_data = [
        [
            Paragraph("<b>Pregunta de la Docente</b>", body_style),
            Paragraph("<b>Tu Respuesta Técnica Maestra</b>", body_style)
        ],
        [
            Paragraph("<b>1. ¿Por qué no pusiste un campo editable directamente en la tabla para cambiar el número de stock cuando hay merma?</b>", body_style),
            Paragraph("«Porque en un sistema de información formal con arquitectura PUDS y principios de auditoría contable, el inventario <b>nunca debe alterarse de forma manual y arbitraria</b>. Cada salida física de producto debe estar justificada por una venta comercial (CU13) o por una nota formal de pérdida (CU18), dejando trazabilidad indeleble en el Kardex con fecha, responsable y motivo para evitar robos hormiga o adulteraciones.»", body_style)
        ],
        [
            Paragraph("<b>2. ¿Por qué utilizaste <code>select_for_update()</code> en la consulta del inventario?</b>", body_style),
            Paragraph("«Para implementar un <b>bloqueo pesimista a nivel de fila (Row-Level Locking)</b> en PostgreSQL. Si dos usuarios intentaran registrar bajas o ventas simultáneas sobre el mismo pan, <code>select_for_update()</code> encola las transacciones, garantizando que el stock se lea y descuente de manera estrictamente secuencial, eliminando el riesgo de <i>condiciones de carrera (Race Conditions)</i> y evitando que el stock termine en números negativos.»", body_style)
        ],
        [
            Paragraph("<b>3. ¿Por qué la pérdida económica se calcula con el costo de producción y no con el precio de venta?</b>", body_style),
            Paragraph("«Por rigor contable y financiero. El precio de venta al público incluye el margen de ganancia proyectado del negocio. Cuando un pan se quema o se echa a perder antes de venderse, la panadería no 'perdió' la ganancia que no llegó a existir, sino el <b>costo real de los insumos y la mano de obra invertidos</b> en producirlo (harina, manteca, gas, etc.).»", body_style)
        ],
        [
            Paragraph("<b>4. ¿Cómo aseguraste que un Personal de Ventas o un cajero no registre bajas fraudulentas?</b>", body_style),
            Paragraph("«Mediante un control estricto de dos capas. En backend, la vista implementa el permiso RBAC <code>PuedeRegistrarBajaProducto</code> que valida en el token JWT los permisos del rol (exclusivo para Maestro Panadero, Propietario y Administrador). En frontend, la interfaz oculta o deshabilita los botones de baja si el rol en sesión no cuenta con los permisos correspondientes.»", body_style)
        ],
        [
            Paragraph("<b>5. ¿Qué sucede si el servidor se apaga o se cae la conexión en mitad del registro?</b>", body_style),
            Paragraph("«El servicio está blindado bajo el decorador <code>@transaction.atomic</code> de Django. Toda la operación (descuento de inventario, inserción en Kardex, creación de nota y bitácora) se ejecuta dentro de un único bloque de transacción de base de datos. Si ocurre un fallo en cualquier punto intermedio, el motor de base de datos ejecuta un <b>ROLLBACK total</b>, garantizando la integridad referencial y el cumplimiento del principio ACID.»", body_style)
        ],
        [
            Paragraph("<b>6. ¿Cómo demostraste la calidad de tu código antes de integrarlo?</b>", body_style),
            Paragraph("«Desarrollé una suite de 7 pruebas unitarias en <code>apps.productos_terminados.tests</code> con casos de prueba positivos y negativos: registro exitoso, rechazo por stock insuficiente, rechazo de cantidades negativas, verificación de permisos RBAC y consistencia de bitácora. Todas las 16 pruebas de la app pasan al 100% en verde.»", body_style)
        ],
    ]
    t_faq = Table(faq_data, colWidths=[180, 320])
    t_faq.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_faq)
    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 6: MODIFICACIONES EN VIVO (LIVE CODING)
    # =========================================================================
    story.append(Paragraph("6. Modificaciones en Vivo (Live Coding) que te puede pedir la Docente", h1_style))
    story.append(Paragraph(
        "Es muy frecuente que la docente te diga: <i>'Muy bien Roberto, ahora hazme esta pequeña modificación en tu código para demostrar que tú lo programaste'</i>. "
        "Aquí tienes preparadas las 4 modificaciones más comunes con la solución exacta:",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Modificación 1: «Agrega una nueva opción de motivo: 'Donación / Acción Social'»", h2_style))
    story.append(Paragraph(
        "<b>Dónde ir:</b> Abre <code>frontend/src/apps/dashboard/productos/existencias/components/RegistrarBajaModal.tsx</code>.<br/>"
        "<b>Qué cambiar:</b> En la constante <code>MOTIVOS_MERMA</code> (línea 13), añade el nuevo texto en el array:",
        body_style
    ))
    mod1_code = """const MOTIVOS_MERMA = [
  'Expiración / Vencimiento',
  'Defecto de Horneado / Quemado',
  'Donación / Acción Social',  // <-- AGREGAR ESTA LÍNEA
  'Daño / Mala manipulación',
  ...
];"""
    story.append(Table([[Paragraph(f"<pre>{mod1_code}</pre>", code_style)]], colWidths=[500], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")), ('BOX', (0,0), (-1,-1), 0.5, c_border)]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Modificación 2: «Haz que la observación sea obligatoria si la cantidad supera 20 unidades»", h2_style))
    story.append(Paragraph(
        "<b>Dónde ir:</b> En <code>backend/apps/productos_inventario/productos_terminados/services/registrar_baja.py</code>.<br/>"
        "<b>Qué cambiar:</b> Justo antes de abrir la transacción (línea 40), añade esta validación de negocio:",
        body_style
    ))
    mod2_code = """if cantidad > 20 and not observaciones.strip():
    raise ValidationError({
        'observaciones': 'Para bajas mayores a 20 unidades es obligatorio detallar el motivo en las observaciones.'
    })"""
    story.append(Table([[Paragraph(f"<pre>{mod2_code}</pre>", code_style)]], colWidths=[500], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")), ('BOX', (0,0), (-1,-1), 0.5, c_border)]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Modificación 3: «Haz que solo el Propietario o Administrador puedan dar de baja más de 50 panes»", h2_style))
    story.append(Paragraph(
        "<b>Dónde ir:</b> En <code>registrar_baja.py</code>.<br/>"
        "<b>Qué cambiar:</b> Evalúa el rol del usuario que ejecuta la acción:",
        body_style
    ))
    mod3_code = """if cantidad > 50 and not (usuario.is_superuser or getattr(usuario, 'rol', None) in ['Propietario', 'Administrador']):
    raise ValidationError({
        'cantidad': 'Las bajas mayores a 50 unidades requieren autorización exclusiva del Propietario.'
    })"""
    story.append(Table([[Paragraph(f"<pre>{mod3_code}</pre>", code_style)]], colWidths=[500], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")), ('BOX', (0,0), (-1,-1), 0.5, c_border)]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Modificación 4: «Muestra una alerta visual si tras la baja el stock queda en nivel crítico (menos de 10)»", h2_style))
    story.append(Paragraph(
        "<b>Dónde ir:</b> En <code>RegistrarBajaModal.tsx</code> dentro del cálculo de stockDisponible.<br/>"
        "<b>Qué cambiar:</b> Agrega una variable calculada y un badge informativo en el modal:",
        body_style
    ))
    mod4_code = """const stockRestante = stockDisponible - cantidad;
// En el JSX del modal debajo de la cantidad:
{stockRestante > 0 && stockRestante < 10 && (
  <div className="p-2 bg-amber-50 text-amber-800 rounded border border-amber-200 text-xs mt-2">
    ⚠️ Atención: Tras esta baja el producto quedará en nivel crítico ({stockRestante} un.)
  </div>
)}"""
    story.append(Table([[Paragraph(f"<pre>{mod4_code}</pre>", code_style)]], colWidths=[500], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")), ('BOX', (0,0), (-1,-1), 0.5, c_border)]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Conclusión de Defensa:", h2_style))
    story.append(Paragraph(
        "Con este dominio técnico y conceptual, tendrás una defensa impecable. "
        "Demuestras que no solo sabes programar pantallas, sino que comprendes los principios de concurrencia, "
        "integridad transaccional ACID, auditoría PUDS y lógica contable del negocio de la Panadería Santiago.",
        body_style
    ))

    # Construir documento con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    generar_pdf()
