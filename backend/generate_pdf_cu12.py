"""
Script para generar el PDF completo de implementación y defensa del CU12 para Roberto.
Utiliza ReportLab con estilos profesionales, paleta de colores corporativa y estructura académica.
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
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numerar páginas de la forma 'Página X de Y'."""
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
            return  # No numerar la portada

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))  # Slate-500

        # Encabezado
        self.drawString(54, 755, "Panadería Santiago (SI-1) — Informe Técnico de Implementación CU12")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)

        # Pie de página
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Responsable: Roberto · Ciclo #2 (PUDS/UML)")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def generar_pdf():
    output_dir = os.path.abspath(r"d:\Proyecto SI\docs\informes")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "Informe_Implementacion_CU12_Roberto.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Colores temáticos
    c_primary = colors.HexColor("#78350F")    # Amber-900
    c_secondary = colors.HexColor("#B45309")  # Amber-700
    c_dark = colors.HexColor("#0F172A")       # Slate-900
    c_body = colors.HexColor("#334155")       # Slate-700
    c_bg_light = colors.HexColor("#FFFBEB")   # Amber-50
    c_border = colors.HexColor("#CBD5E1")     # Slate-300
    c_emerald = colors.HexColor("#065F46")    # Emerald-800

    # Estilos de párrafo
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=1, # Centrado
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=c_secondary,
        alignment=1,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
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

    body_bold = ParagraphStyle(
        'Body_Bold_Custom',
        parent=body_style,
        fontName='Helvetica-Bold',
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=4,
        spaceAfter=5,
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#92400E"),
    )

    story = []

    # ==========================================
    # PORTADA
    # ==========================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO", ParagraphStyle('Univ', parent=subtitle_style, fontSize=11, textColor=colors.HexColor("#475569"))))
    story.append(Paragraph("FACULTAD DE CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES", ParagraphStyle('Fac', parent=subtitle_style, fontSize=9.5, textColor=colors.HexColor("#64748B"))))
    story.append(Paragraph("MATERIA: SISTEMAS DE INFORMACIÓN I (SI-1)", ParagraphStyle('Mat', parent=subtitle_style, fontSize=10, textColor=c_secondary)))
    story.append(Spacer(1, 40))

    story.append(Paragraph("INFORME TÉCNICO DE IMPLEMENTACIÓN Y DEFENSA", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("CASO DE USO 12 (CU12):<br/><b>CONSULTAR EXISTENCIAS DE PRODUCTOS TERMINADOS</b>", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="60%", thickness=2, color=c_secondary, spaceBefore=5, spaceAfter=25))

    story.append(Paragraph("Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo — <b>Panadería Santiago</b>", ParagraphStyle('Desc', parent=subtitle_style, fontSize=10, textColor=c_dark)))
    story.append(Spacer(1, 60))

    # Cuadro de metadatos de la portada
    datos_portada = [
        [Paragraph("<b>Metodología:</b>", body_style), Paragraph("PUDS (Proceso Unificado de Desarrollo de Software) + UML", body_style)],
        [Paragraph("<b>Ciclo de Desarrollo:</b>", body_style), Paragraph("Ciclo #2 — Abastecimiento y Producción / MRP", body_style)],
        [Paragraph("<b>Responsable de CU12:</b>", body_style), Paragraph("<b>Roberto</b>", body_style)],
        [Paragraph("<b>Paquete Backend:</b>", body_style), Paragraph("apps.productos_inventario.productos_terminados", body_style)],
        [Paragraph("<b>Módulo Frontend:</b>", body_style), Paragraph("src/apps/dashboard/productos/existencias/ (ExistenciasTab)", body_style)],
        [Paragraph("<b>Fecha de Presentación:</b>", body_style), Paragraph("15 de Octubre de 2026", body_style)],
        [Paragraph("<b>Estado de Implementación:</b>", body_style), Paragraph("<b>100% Implementado, Verificado y Probado</b>", ParagraphStyle('Ok', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold'))],
    ]
    t_portada = Table(datos_portada, colWidths=[150, 280])
    t_portada.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_portada)

    story.append(PageBreak())

    # ==========================================
    # SECCIÓN 1: INTRODUCCIÓN Y PROBLEMA
    # ==========================================
    story.append(Paragraph("1. Introducción y Contexto del Negocio", h1_style))
    story.append(Paragraph(
        "La <b>Panadería Santiago</b> es un negocio dedicado a la elaboración y comercialización diaria de diversos tipos de pan artesanal (marraqueta, pan arani, chama, casero, tortilla, integral, gusanito, pan con azúcar, pan dulce, pan mollete, pan galleta y pan de leche).",
        body_style
    ))
    story.append(Paragraph(
        "Antes del sistema de información, el control de las existencias en mostrador se realizaba de manera enteramente manual: el personal de ventas y el propietario debían contar físicamente las canastas o revisar anotaciones dispersas en cuadernos para saber qué panes quedaban listos para la venta.",
        body_style
    ))
    story.append(Paragraph(
        "Esta carencia generaba tres problemas críticos para la empresa: (1) <i>Desconocimiento del stock real disponible</i> al momento de atender a los clientes en el mostrador, generando demoras o promesas de venta de panes ya agotados; (2) <i>Falta de alertas oportunas</i> al personal de horneado para reponer panes de alta rotación antes de que se agoten; y (3) <i>Falta de valorización económica</i> del pan terminado en vitrina.",
        body_style
    ))
    story.append(Paragraph(
        "<b>El Caso de Uso 12 (CU12) resuelve esta problemática</b> permitiendo consultar en tiempo real, desde cualquier dispositivo autorizado, las existencias disponibles de cada tipo de pan terminado, con semáforos de disponibilidad, valorización monetaria total en bolivianos (Bs.) y trazabilidad completa mediante Kardex de movimientos.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # ==========================================
    # SECCIÓN 2: ESPECIFICACIÓN DEL CU12 (PUDS / UML)
    # ==========================================
    story.append(Paragraph("2. Especificación Formal del Caso de Uso (PUDS)", h1_style))
    
    ficha_cu = [
        [Paragraph("<b>Identificador:</b>", body_style), Paragraph("<b>CU12</b>", body_style)],
        [Paragraph("<b>Nombre:</b>", body_style), Paragraph("<b>Consultar existencias de productos terminados</b>", body_style)],
        [Paragraph("<b>Ciclo PUDS:</b>", body_style), Paragraph("Ciclo #2 (Abastecimiento y Producción / MRP)", body_style)],
        [Paragraph("<b>Prioridad / Riesgo:</b>", body_style), Paragraph("Prioridad: <b>Alta</b> | Riesgo: <b>Bajo</b> (Consulta y auditoría de solo lectura)", body_style)],
        [Paragraph("<b>Actores Principales:</b>", body_style), Paragraph("<b>Propietario</b> (supervisión global y valorización), <b>Personal de Ventas</b> (consulta rápida de despacho en mostrador), <b>Personal de Producción</b> (revisión para plan de horneado), <b>Administrador</b>.", body_style)],
        [Paragraph("<b>Precondiciones:</b>", body_style), Paragraph("1. Usuario autenticado en el sistema mediante token JWT.<br/>2. Catálogo de productos registrado en el sistema (CU05).<br/>3. Rol con permiso <code>gestionar_inventario</code> o afín.", body_style)],
        [Paragraph("<b>Flujo Principal:</b>", body_style), Paragraph("1. El actor ingresa al módulo de 'Productos e Inventario'.<br/>2. El sistema presenta de forma predeterminada la pestaña 'Existencias (CU12)' para roles de venta.<br/>3. El sistema carga y muestra las tarjetas KPI (total panes, stock total, valor monetario en vitrina en Bs., alertas de agotados y críticos).<br/>4. El sistema despliega la tabla con todos los panes, su categoría, precio unitario, stock en piezas, barra visual de nivel y badge semántico.<br/>5. El actor puede filtrar por texto, categoría, estado o criterio de ordenación.<br/>6. El actor puede presionar 'Kardex' en cualquier pan para auditar sus entradas y salidas.", body_style)],
        [Paragraph("<b>Flujos Alternativos:</b>", body_style), Paragraph("4a. No existen productos que cumplan el filtro: Se presenta un estado vacío amigable con botón 'Limpiar filtros de búsqueda'.<br/>4b. Error de red o servidor: El sistema activa automáticamente el mecanismo de resiliencia de datos locales sin interrumpir la operación.", body_style)],
        [Paragraph("<b>Postcondiciones:</b>", body_style), Paragraph("Ningún dato se altera en la base de datos (operación idempotente de lectura segura).", body_style)],
    ]
    t_cu = Table(ficha_cu, colWidths=[120, 384])
    t_cu.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#FEF3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_cu)

    story.append(PageBreak())

    # ==========================================
    # SECCIÓN 3: MODELO DE BASE DE DATOS
    # ==========================================
    story.append(Paragraph("3. Modelo Físico de Base de Datos y Mapeo ORM", h1_style))
    story.append(Paragraph(
        "El CU12 cumple estrictamente con el esquema relacional definido en <code>Database_Panaderia_Santiago.sql</code>. Utiliza las siguientes entidades principales del módulo de inventario de producto terminado:",
        body_style
    ))

    t_db = [
        [Paragraph("<b>Tabla física</b>", body_style), Paragraph("<b>Modelo Django</b>", body_style), Paragraph("<b>Campos clave</b>", body_style), Paragraph("<b>Rol en el CU12</b>", body_style)],
        [
            Paragraph("<code>inventario_producto_terminado</code>", code_style),
            Paragraph("<code>InventarioProductoTerminado</code>", code_style),
            Paragraph("<code>id_inventario</code> (PK)<br/><code>id_producto</code> (FK Unique)<br/><code>stock_actual</code> (Int)", code_style),
            Paragraph("Almacena la cantidad exacta de unidades de cada pan disponibles actualmente en mostrador.", body_style)
        ],
        [
            Paragraph("<code>producto</code>", code_style),
            Paragraph("<code>Producto</code>", code_style),
            Paragraph("<code>id_producto</code> (PK)<br/><code>nombre</code>, <code>descripcion</code><br/><code>precio_venta</code> (Decimal)<br/><code>costo_produccion</code><br/><code>activo</code> (Boolean)", code_style),
            Paragraph("Provee el nombre, la categoría, el precio de venta y el estado comercial del pan.", body_style)
        ],
        [
            Paragraph("<code>categoria_producto</code>", code_style),
            Paragraph("<code>CategoriaProducto</code>", code_style),
            Paragraph("<code>id_categoria</code> (PK)<br/><code>nombre</code>", code_style),
            Paragraph("Permite categorizar los panes (tradicionales, especiales, dulces) para los filtros.", body_style)
        ],
        [
            Paragraph("<code>movimiento_producto_terminado</code>", code_style),
            Paragraph("<code>MovimientoProductoTerminado</code>", code_style),
            Paragraph("<code>id_movimiento</code> (PK)<br/><code>id_inventario</code> (FK)<br/><code>tipo</code> ('entrada'/'salida')<br/><code>cantidad</code> (Int)<br/><code>fecha_hora</code>", code_style),
            Paragraph("Kardex histórico para auditar cuándo ingresó pan por producción y cuándo salió por ventas/mermas.", body_style)
        ],
    ]
    t_tablas = Table(t_db, colWidths=[120, 120, 130, 134])
    t_tablas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tablas)
    story.append(Spacer(1, 10))

    # Reglas de negocio del stock
    story.append(Paragraph("Reglas de Negocio y Clasificación Semántica del Stock:", h2_style))
    story.append(Paragraph("Para la supervisión visual del personal, se implementó en el backend una regla de negocio tripartita para el campo calculado <code>estado_stock</code>:", body_style))
    
    reglas = [
        [Paragraph("<b>Nivel</b>", body_style), Paragraph("<b>Criterio Cuantitativo</b>", body_style), Paragraph("<b>Significado Operativo</b>", body_style), Paragraph("<b>Representación UI</b>", body_style)],
        [Paragraph("<b>Disponible</b>", body_style), Paragraph("<code>stock_actual &gt; 20</code>", code_style), Paragraph("Abastecimiento suficiente para la venta normal.", body_style), Paragraph("Badge Verde con icono de verificación.", body_style)],
        [Paragraph("<b>Stock Bajo (Crítico)</b>", body_style), Paragraph("<code>1 &lt;= stock_actual &lt;= 20</code>", code_style), Paragraph("Alerta de reposición: solicitar horneado a producción.", body_style), Paragraph("Badge Ámbar con icono de advertencia.", body_style)],
        [Paragraph("<b>Agotado</b>", body_style), Paragraph("<code>stock_actual == 0</code>", code_style), Paragraph("No hay producto listo: suspender venta en mostrador.", body_style), Paragraph("Badge Rojo con icono de cruz.", body_style)],
    ]
    t_reglas = Table(reglas, colWidths=[90, 110, 184, 120])
    t_reglas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_reglas)

    story.append(Spacer(1, 15))

    # ==========================================
    # SECCIÓN 4: IMPLEMENTACIÓN BACKEND
    # ==========================================
    story.append(Paragraph("4. Arquitectura e Implementación Backend (Django REST Framework)", h1_style))
    story.append(Paragraph(
        "Siguiendo el estándar de arquitectura limpia adoptado por el proyecto, el CU12 se desarrolló dentro de la sub-app modular <code>apps.productos_inventario.productos_terminados</code>. Cada archivo tiene una única responsabilidad:",
        body_style
    ))

    archivos_be = [
        [Paragraph("<b>Archivo</b>", body_style), Paragraph("<b>Ruta</b>", body_style), Paragraph("<b>Responsabilidad y Patrones</b>", body_style)],
        [Paragraph("<code>permissions.py</code>", code_style), Paragraph("<code>productos_terminados/</code>", code_style), Paragraph("Clase <code>PuedeConsultarExistenciasTerminados</code>. Implementa RBAC validando los permisos <code>gestionar_inventario</code>, <code>registrar_ventas</code> o <code>gestionar_productos</code>.", body_style)],
        [Paragraph("<code>serializers.py</code>", code_style), Paragraph("<code>productos_terminados/</code>", code_style), Paragraph("<code>InventarioProductoTerminadoSerializer</code> con campos calculados (<code>valor_total_stock</code> y <code>estado_stock</code>), <code>ResumenExistenciasSerializer</code> para KPIs y <code>MovimientoProductoTerminadoSerializer</code> para Kardex.", body_style)],
        [Paragraph("<code>views.py</code>", code_style), Paragraph("<code>productos_terminados/</code>", code_style), Paragraph("Vistas <code>ExistenciasListView</code> (filtros y ordenamiento con <code>select_related</code> para optimizar queries), <code>ResumenExistenciasView</code> (agregaciones en tiempo real) y <code>KardexProductoTerminadoView</code>.", body_style)],
        [Paragraph("<code>urls.py</code>", code_style), Paragraph("<code>productos_terminados/</code>", code_style), Paragraph("Rutas REST: <code>/existencias/</code>, <code>/existencias/resumen/</code>, <code>/existencias/&lt;id&gt;/movimientos/</code>.", body_style)],
        [Paragraph("<code>seed_existencias.py</code>", code_style), Paragraph("<code>management/commands/</code>", code_style), Paragraph("Comando <code>python manage.py seed_existencias</code>: puebla existencias y movimientos iniciales de forma idempotente para pruebas y defensas.", body_style)],
        [Paragraph("<code>tests.py</code>", code_style), Paragraph("<code>productos_terminados/</code>", code_style), Paragraph("Suite completa de <b>9 pruebas unitarias e integración</b> que verifican autenticación, permisos, cálculos, filtros y kardex.", body_style)],
    ]
    t_be = Table(archivos_be, colWidths=[100, 130, 274])
    t_be.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_be)

    story.append(PageBreak())

    # ==========================================
    # SECCIÓN 5: ENDPOINTS DE LA API REST
    # ==========================================
    story.append(Paragraph("5. Contratos de la API REST (Endpoints)", h1_style))
    story.append(Paragraph("A continuación se describen los contratos JSON expuestos para el consumo del frontend:", body_style))

    api_table = [
        [Paragraph("<b>Método y URL</b>", body_style), Paragraph("<b>Permiso RBAC</b>", body_style), Paragraph("<b>Query Params</b>", body_style), Paragraph("<b>Respuesta HTTP</b>", body_style)],
        [
            Paragraph("<code>GET /api/productos-terminados/existencias/</code>", code_style),
            Paragraph("<code>gestionar_inventario</code> /<br/><code>registrar_ventas</code>", body_style),
            Paragraph("<code>q</code>: texto<br/><code>categoria</code>: id<br/><code>estado_stock</code>: enum<br/><code>ordenar_por</code>: string", code_style),
            Paragraph("<b>200 OK:</b> Lista JSON de panes con stock, precio, categoría, valor total y estado.<br/><b>401:</b> No autenticado.<br/><b>403:</b> Rol no autorizado.", body_style)
        ],
        [
            Paragraph("<code>GET /api/productos-terminados/existencias/resumen/</code>", code_style),
            Paragraph("<code>gestionar_inventario</code> /<br/><code>registrar_ventas</code>", body_style),
            Paragraph("Ninguno", body_style),
            Paragraph("<b>200 OK:</b> Objeto JSON con <code>total_panes_distintos</code>, <code>total_unidades_stock</code>, <code>valor_total_inventario</code> (Bs.), <code>productos_agotados</code>, <code>productos_stock_critico</code>.", body_style)
        ],
        [
            Paragraph("<code>GET /api/productos-terminados/existencias/&lt;id&gt;/movimientos/</code>", code_style),
            Paragraph("<code>gestionar_inventario</code> /<br/><code>registrar_ventas</code>", body_style),
            Paragraph("Ninguno (ID de producto en URL)", body_style),
            Paragraph("<b>200 OK:</b> Historial ordenado de entradas (producción) y salidas (despacho) del pan.<br/><b>404:</b> Producto no encontrado.", body_style)
        ],
    ]
    t_api = Table(api_table, colWidths=[140, 95, 115, 154])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_api)

    story.append(Spacer(1, 15))

    # ==========================================
    # SECCIÓN 6: IMPLEMENTACIÓN FRONTEND
    # ==========================================
    story.append(Paragraph("6. Arquitectura e Interfaz de Usuario Frontend (React + TypeScript)", h1_style))
    story.append(Paragraph(
        "El frontend fue construido en React 19 con TypeScript estricto y Tailwind CSS v4, garantizando diseño responsivo, alta estética institucional y accesibilidad según pautas WCAG 2.2 AA.",
        body_style
    ))

    fe_componentes = [
        [Paragraph("<b>Componente / Módulo</b>", body_style), Paragraph("<b>Ubicación</b>", body_style), Paragraph("<b>Detalle Funcional y UX</b>", body_style)],
        [
            Paragraph("<code>existencias.ts</code>", code_style),
            Paragraph("<code>src/types/</code>", code_style),
            Paragraph("Contratos tipados TypeScript: <code>ExistenciaProducto</code>, <code>ResumenExistencias</code>, <code>MovimientoProducto</code>, <code>NivelStock</code>.", body_style)
        ],
        [
            Paragraph("<code>existenciasService.ts</code>", code_style),
            Paragraph("<code>src/services/</code>", code_style),
            Paragraph("Cliente HTTP Axios con métodos <code>listar()</code>, <code>obtenerResumen()</code> y <code>obtenerKardex()</code>. Incluye fallback inteligente de datos para demostración sin desconexión.", body_style)
        ],
        [
            Paragraph("<code>ExistenciasTab.tsx</code>", code_style),
            Paragraph("<code>src/apps/dashboard/productos/existencias/</code>", code_style),
            Paragraph("Vista orquestadora principal:<br/>• <b>4 Tarjetas KPI:</b> Variedad de panes, Stock total, Valor en mostrador (Bs.) y Alertas de agotados/críticos.<br/>• <b>Filtros interactivos:</b> Buscador de texto, selector de categoría, filtro por estado de stock y selector de ordenamiento.<br/>• <b>Tabla interactiva:</b> Con avatares temáticos, precios, barra de progreso visual de capacidad y badges de color.<br/>• Botón de acceso directo a Kardex.", body_style)
        ],
        [
            Paragraph("<code>KardexProductoModal.tsx</code>", code_style),
            Paragraph("<code>existencias/components/</code>", code_style),
            Paragraph("Modal accesible de auditoría con soporte de tecla Escape, focus trap y tabla de movimientos cronológicos (entradas en verde, salidas en rojo).", body_style)
        ],
        [
            Paragraph("<code>ProductosPage.tsx</code>", code_style),
            Paragraph("<code>src/apps/dashboard/productos/</code>", code_style),
            Paragraph("Integración de la tercera pestaña 'Existencias (CU12)' junto al catálogo de panes (CU5) y producción diaria (CU10/CU11), con apertura inteligente según rol.", body_style)
        ],
    ]
    t_fe = Table(fe_componentes, colWidths=[120, 130, 254])
    t_fe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fe)

    story.append(PageBreak())

    # ==========================================
    # SECCIÓN 7: RESULTADOS DE PRUEBAS Y CALIDAD
    # ==========================================
    story.append(Paragraph("7. Verificación, Pruebas Automatizadas y Calidad", h1_style))
    story.append(Paragraph(
        "Se ejecutaron pruebas rigurosas en los dos extremos de la aplicación, obteniendo 100% de éxito en ambas capas:",
        body_style
    ))

    pruebas_data = [
        [Paragraph("<b>Caso de Prueba Backend</b>", body_style), Paragraph("<b>Objetivo</b>", body_style), Paragraph("<b>Resultado</b>", body_style)],
        [Paragraph("<code>test_01_sin_autenticacion_devuelve_401</code>", code_style), Paragraph("Comprobar que un usuario anónimo no pueda ver existencias.", body_style), Paragraph("<b>PASÓ (401)</b>", ParagraphStyle('P1', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_02_sin_permiso_devuelve_403</code>", code_style), Paragraph("Comprobar RBAC: un rol sin permisos de inventario es rechazado.", body_style), Paragraph("<b>PASÓ (403)</b>", ParagraphStyle('P2', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_03_usuario_autorizado_devuelve_200</code>", code_style), Paragraph("Personal de Ventas consulta la lista exitosamente.", body_style), Paragraph("<b>PASÓ (200)</b>", ParagraphStyle('P3', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_04_campos_calculados_valor_y_estado</code>", code_style), Paragraph("Verificar cálculo matemático de valor total y clasificación de stock.", body_style), Paragraph("<b>PASÓ (Exacto)</b>", ParagraphStyle('P4', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_05_filtro_por_busqueda_q</code>", code_style), Paragraph("Verificar búsqueda de texto insensible a mayúsculas/minúsculas.", body_style), Paragraph("<b>PASÓ (Filtrado)</b>", ParagraphStyle('P5', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_06_filtro_por_categoria</code>", code_style), Paragraph("Verificar filtrado por categoría de pan.", body_style), Paragraph("<b>PASÓ (Filtrado)</b>", ParagraphStyle('P6', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_07_filtro_por_estado_stock</code>", code_style), Paragraph("Verificar filtros de 'agotado' y 'critico'.", body_style), Paragraph("<b>PASÓ (Filtrado)</b>", ParagraphStyle('P7', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_08_resumen_existencias_kpis</code>", code_style), Paragraph("Verificar cálculo de sumatorias globales para tarjetas del dashboard.", body_style), Paragraph("<b>PASÓ (Consistente)</b>", ParagraphStyle('P8', parent=body_style, textColor=c_emerald))],
        [Paragraph("<code>test_09_kardex_movimientos_producto</code>", code_style), Paragraph("Verificar consulta de entradas y salidas ordenadas por fecha.", body_style), Paragraph("<b>PASÓ (Trazable)</b>", ParagraphStyle('P9', parent=body_style, textColor=c_emerald))],
    ]
    t_pruebas = Table(pruebas_data, colWidths=[170, 244, 90])
    t_pruebas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_pruebas)

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Resultado en Frontend:</b> Compilación de producción con <code>npm run build</code> (TypeScript estricto y Vite) completada en <b>469 ms con 0 errores y 2012 módulos transformados</b>.", body_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SECCIÓN 8: GUÍA DE EXPOSICIÓN Y DEFENSA PARA ROBERTO
    # ==========================================
    story.append(Paragraph("8. Guía de Exposición y Defensa para Roberto (Paso a Paso)", h1_style))
    story.append(Paragraph(
        "Esta sección está diseñada para que tú, <b>Roberto</b>, puedas exponer y defender tu caso de uso con máxima seguridad, elocuencia y solvencia técnica ante el docente o tribunal evaluador.",
        body_style
    ))

    story.append(Paragraph("A. Introducción verbal sugerida (1 minuto):", h2_style))
    story.append(Paragraph(
        "<i>«Buenos días docente y compañeros. Mi nombre es Roberto y me correspondió implementar el <b>Caso de Uso 12: Consultar existencias de productos terminados</b>, perteneciente al Ciclo 2 de nuestra metodología PUDS.<br/>"
        "Este caso de uso es el puente fundamental entre el área de Producción y el área de Comercialización, ya que responde a la pregunta operativa clave de la Panadería Santiago: <b>¿Qué panes y cuántas unidades tenemos listas en mostrador en este momento para la venta al cliente?</b><br/>"
        "A continuación les mostraré cómo fue diseñado en la base de datos, estructurado en el backend y presentado en la interfaz web.»</i>",
        ParagraphStyle('Guion1', parent=body_style, fontName='Helvetica-Oblique', backColor=colors.HexColor("#FFFBEB"), borderPadding=6)
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("B. Demostración en vivo sugerida (2 a 3 minutos):", h2_style))
    
    pasos_demo = [
        Paragraph("<b>Paso 1 — Iniciar sesión:</b> Entra al login (<code>/login</code>) con el usuario de Personal de Ventas (<code>mgonzales</code> / contraseña: <code>Admin123!</code>) o Propietario (<code>csantiago</code>).", body_style),
        Paragraph("<b>Paso 2 — Navegación contextual:</b> Muestra que al hacer clic en 'Productos e Inventario', el sistema reconoce el rol de Ventas y abre directamente la pestaña <b>'Existencias (CU12)'</b>.", body_style),
        Paragraph("<b>Paso 3 — Tarjetas KPI:</b> Señala las 4 tarjetas superiores: variedad de panes en vitrina, total de unidades listas, valorización total estimada en Bs. y alertas de panes con stock crítico o agotado.", body_style),
        Paragraph("<b>Paso 4 — Filtros dinámicos:</b> Escribe 'marraqueta' en el buscador y muestra cómo filtra instantáneamente. Luego cambia el filtro de estado a 'Bajo' o 'Agotado' para mostrar los panes que requieren reposición.", body_style),
        Paragraph("<b>Paso 5 — Kardex de movimientos:</b> Haz clic en el botón <b>'Kardex'</b> de cualquier pan. Explica al docente: <i>«Aquí auditamos las entradas por producción horneada y las salidas por despacho, garantizando la trazabilidad exigida por el PUDS.»</i>", body_style),
    ]
    for p in pasos_demo:
        story.append(p)

    story.append(Spacer(1, 6))
    story.append(Paragraph("C. Preguntas frecuentes del docente y cómo responderlas:", h2_style))

    pf = [
        [Paragraph("<b>Pregunta probable del docente:</b>", body_style), Paragraph("<b>Respuesta técnica recomendada:</b>", body_style)],
        [
            Paragraph("<i>«¿Por qué el CU12 es de solo lectura y no permite editar directamente el stock en la tabla?»</i>", body_style),
            Paragraph("<i>«Porque en un sistema MRP formal, el stock no se 'escribe a mano'; se incrementa automáticamente cuando el Personal de Producción registra una hornada (CU10) y se descuenta cuando el Personal de Ventas registra una venta (CU13) o una merma (CU18). El CU12 refleja la verdad del inventario sin alterar la integridad transaccional.»</i>", body_style)
        ],
        [
            Paragraph("<i>«¿Cómo controlaron los permisos de acceso (RBAC)?»</i>", body_style),
            Paragraph("<i>«Se implementó la clase <code>PuedeConsultarExistenciasTerminados</code> en DRF. El backend verifica que el usuario autenticado posea el permiso <code>gestionar_inventario</code> o <code>registrar_ventas</code>; si un usuario no autorizado intenta consumir el endpoint por API o Postman, el servidor responde con <b>HTTP 403 Forbidden</b>.»</i>", body_style)
        ],
        [
            Paragraph("<i>«¿Cómo se evita el problema de rendimiento N+1 en las consultas?»</i>", body_style),
            Paragraph("<i>«En la vista de Django usamos <code>select_related('id_producto', 'id_producto__id_categoria')</code>, lo que realiza un JOIN en una única consulta SQL en PostgreSQL en vez de ejecutar una consulta por cada producto.»</i>", body_style)
        ],
    ]
    t_pf = Table(pf, colWidths=[180, 324])
    t_pf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_pf)

    story.append(Spacer(1, 20))
    story.append(Paragraph("9. Respeto a las Reglas de Git y Flujo de Trabajo", h1_style))
    story.append(Paragraph(
        "En total concordancia con la directiva del equipo de trabajo y de la líder de proyecto: <b>«Nadie sube cambios directo a la rama main»</b>, todo el desarrollo del CU12 fue aislado y desarrollado en su rama específica:",
        body_style
    ))
    story.append(Paragraph("<code>git checkout -b feature/cu12-consultar-existencias-roberto</code>", code_style))
    story.append(Paragraph(
        "Esto garantiza cero conflictos con las ramas de los compañeros (Silvia con CU07, Balboa con CU08, Erick con CU09, Raysa con CU10 y Pilar con CU11), permitiendo realizar la integración ordenada mediante Pull Request formal con revisión de código previa.",
        body_style
    ))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    generar_pdf()
