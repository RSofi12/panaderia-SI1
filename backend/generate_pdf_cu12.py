"""
Script para generar la Guía Completa de Implementación y Defensa del CU12 para Roberto.
Genera un documento PDF académico, didáctico y exhaustivo con ReportLab.
"""
import os
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
        self.drawString(54, 755, "Panadería Santiago (SI-1) — Guía Completa de Implementación CU12")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 755, "Caso de Uso: Roberto")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)

        # Pie de página
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Ciclo #2 · PUDS + UML · Sub-app: productos_terminados")
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

    # Paleta de colores institucional
    c_primary = colors.HexColor("#78350F")    # Amber-900 (Marrón panadería)
    c_secondary = colors.HexColor("#B45309")  # Amber-700
    c_dark = colors.HexColor("#0F172A")       # Slate-900
    c_body = colors.HexColor("#334155")       # Slate-700
    c_bg_light = colors.HexColor("#FFFBEB")   # Amber-50
    c_border = colors.HexColor("#CBD5E1")     # Slate-300
    c_emerald = colors.HexColor("#065F46")    # Verde
    c_blue = colors.HexColor("#1E40AF")       # Azul

    # Tipografías y jerarquías
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
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
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_secondary,
        spaceBefore=9,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_body,
        spaceAfter=4,
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
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=3,
        spaceAfter=4,
    )

    nota_box = ParagraphStyle(
        'NotaBox',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#92400E"),
        backColor=c_bg_light,
        borderPadding=6,
        spaceAfter=6,
    )

    story = []

    # ==========================================
    # 1. PORTADA
    # ==========================================
    story.append(Spacer(1, 35))
    story.append(Paragraph("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO", ParagraphStyle('Univ', parent=subtitle_style, fontSize=11, textColor=colors.HexColor("#475569"))))
    story.append(Paragraph("FACULTAD DE CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES", ParagraphStyle('Fac', parent=subtitle_style, fontSize=9, textColor=colors.HexColor("#64748B"))))
    story.append(Paragraph("SISTEMAS DE INFORMACIÓN I (SI-1) — PROYECTO MRP", ParagraphStyle('Mat', parent=subtitle_style, fontSize=9.5, textColor=c_secondary)))
    story.append(Spacer(1, 35))

    story.append(Paragraph("GUÍA COMPLETA DE IMPLEMENTACIÓN, FUNCIONAMIENTO Y DEFENSA TÉCNICA", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("CASO DE USO 12 (CU12):<br/><b>CONSULTAR EXISTENCIAS DE PRODUCTOS TERMINADOS</b>", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="70%", thickness=2, color=c_secondary, spaceBefore=4, spaceAfter=20))

    story.append(Paragraph("Sistema de Información Web para la Panadería <b>'Santiago'</b>", ParagraphStyle('Sub', parent=subtitle_style, fontSize=10, textColor=c_dark)))
    story.append(Spacer(1, 40))

    datos_portada = [
        [Paragraph("<b>Caso de Uso:</b>", body_style), Paragraph("CU12 — Consultar existencias de productos terminados", body_style)],
        [Paragraph("<b>Integrante Responsable:</b>", body_style), Paragraph("<b>Roberto</b>", body_style)],
        [Paragraph("<b>Ciclo PUDS:</b>", body_style), Paragraph("Ciclo #2 (Abastecimiento, Producción y Existencias)", body_style)],
        [Paragraph("<b>Rama de Git:</b>", body_style), Paragraph("<code>feature/cu12-consultar-existencias-roberto</code> (100% Local)", code_style)],
        [Paragraph("<b>Sub-app Backend:</b>", body_style), Paragraph("<code>backend/apps/productos_inventario/productos_terminados/</code>", code_style)],
        [Paragraph("<b>Módulo Frontend:</b>", body_style), Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/</code>", code_style)],
        [Paragraph("<b>Fecha de Entrega:</b>", body_style), Paragraph("15 de Octubre de 2026", body_style)],
        [Paragraph("<b>Estado del Caso de Uso:</b>", body_style), Paragraph("<b>100% Desarrollado, Probado y Verificado (0 Errores)</b>", ParagraphStyle('Ok', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold'))],
    ]
    t_portada = Table(datos_portada, colWidths=[140, 290])
    t_portada.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_portada)

    story.append(PageBreak())

    # ==========================================
    # 2. ACLARACIÓN IMPORTANTE: LA BASE DE DATOS
    # ==========================================
    story.append(Paragraph("1. Aclaración Importante: ¿Qué pasó con la Base de Datos?", h1_style))
    story.append(Paragraph(
        "Es muy normal que al ver mensajes de consola te surjan dudas como: <i>¿Se crearon bases de datos nuevas? ¿Se modificó la base de datos de mis compañeros?</i>. "
        "A continuación se explica con total transparencia técnica qué ocurrió y por qué tu proyecto está completamente seguro:",
        body_style
    ))

    story.append(Paragraph(
        "<b>A. NO se creó ninguna base de datos nueva permanente ni se alteró PostgreSQL:</b><br/>"
        "La base de datos oficial del proyecto sigue siendo <b>PostgreSQL 14+</b> definida por el script maestro <code>Database_Panaderia_Santiago.sql</code>. "
        "Las tablas que utiliza tu CU12 (<code>inventario_producto_terminado</code> y <code>movimiento_producto_terminado</code>) ya fueron diseñadas previamente por el equipo.",
        body_style
    ))

    story.append(Paragraph(
        "<b>B. ¿Por qué la consola dijo <i>'Creating test database for alias default...'</i>?</b><br/>"
        "Cuando ejecutamos las pruebas automatizadas (<code>manage.py test</code>), Django crea por seguridad una <b>base de datos temporal desechable</b> en la memoria RAM de tu computadora. "
        "Allí ejecuta las 9 pruebas para comprobar que todo funcione y, en cuanto terminan con éxito, Django la destruye de inmediato (<i>'Destroying test database...'</i>). "
        "Esto garantiza que las pruebas nunca ensucien ni borren los datos reales de la panadería.",
        body_style
    ))

    story.append(Paragraph(
        "<b>C. Compatibilidad de entorno local sin Docker:</b><br/>"
        "Se agregó en <code>settings.py</code> un ajuste para que, si alguien no tiene Docker o PostgreSQL corriendo en su máquina, pueda probar el backend localmente usando SQLite sin que el sistema falle. Cuando el proyecto se levanta en Docker, automáticamente usa PostgreSQL.",
        body_style
    ))

    story.append(Paragraph(
        "<b>D. Los cambios están ÚNICAMENTE en tu PC:</b><br/>"
        "Todo se encuentra en tu rama local <code>feature/cu12-consultar-existencias-roberto</code>. No se ha ejecutado ningún <code>git push</code> hacia GitHub. Tu equipo en <code>main</code> no ha recibido ninguna alteración.",
        nota_box
    ))

    story.append(Spacer(1, 5))

    # ==========================================
    # 3. ¿QUÉ ES EL CU12 Y QUÉ PROBLEMA RESUELVE?
    # ==========================================
    story.append(Paragraph("2. ¿Qué es el Caso de Uso 12 (CU12)?", h1_style))
    story.append(Paragraph(
        "El <b>CU12: Consultar existencias de productos terminados</b> tiene como objetivo permitir al <b>Propietario</b> y al <b>Personal de Ventas</b> conocer en cualquier momento qué panes están listos para la venta en el mostrador, cuántas piezas hay disponibles de cada uno, cuál es su valorización total en dinero (Bs.) y qué panes están por agotarse o ya se terminaron.",
        body_style
    ))

    story.append(Paragraph(
        "<b>¿Por qué es importante en la Panadería Santiago?</b><br/>"
        "En una panadería tradicional, el personal de mostrador no tiene tiempo de contar panes mientras atiende a los clientes. "
        "El CU12 conecta la producción con las ventas: cuando producción termina de hornear (CU10), el stock de pan sube; cuando se atiende en mostrador (CU13), el stock disminuye. "
        "El CU12 muestra la verdad de la vitrina en tiempo real con semáforos de advertencia visuales.",
        body_style
    ))

    story.append(Spacer(1, 5))

    # ==========================================
    # 4. MAPA DE ARCHIVOS: DÓNDE ESTÁ TODO LO NUEVO
    # ==========================================
    story.append(Paragraph("3. Mapa Completo de Archivos: Dónde está cada cosa", h1_style))
    story.append(Paragraph(
        "Todo el código nuevo se ubicó exactamente dentro de las carpetas que corresponden a la arquitectura del proyecto:",
        body_style
    ))

    mapa_archivos = [
        [Paragraph("<b>Capa</b>", body_style), Paragraph("<b>Ruta del Archivo</b>", body_style), Paragraph("<b>Estado</b>", body_style), Paragraph("<b>¿Qué contiene?</b>", body_style)],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/permissions.py</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N1', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Control de acceso RBAC. Valida que solo roles con permiso de inventario/ventas puedan consultar.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/serializers.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('N2', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Serializadores JSON. Contiene la matemática que calcula el valor en Bs. (<code>stock * precio</code>) y clasifica el estado (disponible/bajo/agotado).", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/views.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('N3', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Vistas de la API: <code>ExistenciasListView</code> (lista con filtros), <code>ResumenExistenciasView</code> (tarjetas KPI) y <code>KardexProductoTerminadoView</code> (historial).", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/urls.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('N4', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Rutas de la API bajo <code>/api/productos-terminados/existencias/</code>.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/management/commands/seed_existencias.py</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N5', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Comando seeder: llena datos realistas de los 12 tipos de pan para probar y demostrar el sistema.", body_style)
        ],
        [
            Paragraph("<b>Backend</b>", body_style),
            Paragraph("<code>backend/apps/productos_inventario/productos_terminados/tests.py</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('N6', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("9 pruebas unitarias que verifican permisos, cálculos matemáticos, filtros y kardex.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/types/existencias.ts</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N7', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Tipos e interfaces TypeScript para garantizar que los datos no tengan errores.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/services/existenciasService.ts</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N8', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Cliente Axios que pide los datos al backend y tiene datos de respaldo si estás desconectado.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/ExistenciasTab.tsx</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N9', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Pantalla completa con las 4 tarjetas KPI, buscador en vivo, filtros de categoría y tabla con barras de nivel.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/existencias/components/KardexProductoModal.tsx</code>", code_style),
            Paragraph("NUEVO", ParagraphStyle('N10', parent=body_style, textColor=c_emerald, fontName='Helvetica-Bold')),
            Paragraph("Modal emergente que muestra el historial de movimientos de un pan al hacer clic en 'Kardex'.", body_style)
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("<code>frontend/src/apps/dashboard/productos/ProductosPage.tsx</code>", code_style),
            Paragraph("MODIFICADO", ParagraphStyle('N11', parent=body_style, textColor=c_blue, fontName='Helvetica-Bold')),
            Paragraph("Página principal donde se agregó la pestaña <b>'Existencias (CU12)'</b> junto al catálogo y producción.", body_style)
        ],
    ]
    t_mapa = Table(mapa_archivos, colWidths=[65, 175, 74, 190])
    t_mapa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_mapa)

    story.append(PageBreak())

    # ==========================================
    # 5. CÓMO FUNCIONA DE PUNTA A PUNTA
    # ==========================================
    story.append(Paragraph("4. ¿Cómo Funciona la Solución de Punta a Punta?", h1_style))
    story.append(Paragraph(
        "A continuación se explica el ciclo de vida completo de una consulta en el sistema, desde que el usuario interactúa hasta que se consulta la base de datos:",
        body_style
    ))

    pasos_flujo = [
        Paragraph("<b>1. Autenticación y Autorización (Seguridad RBAC):</b><br/>"
                  "El usuario inicia sesión en <code>/login</code> con sus credenciales (por ejemplo, María Elena Gonzales del Personal de Ventas). "
                  "El backend emite un token JWT que contiene los permisos del rol. Al ingresar a <i>Productos e Inventario</i>, el sistema detecta que el usuario tiene el permiso <code>gestionar_inventario</code> y abre automáticamente la pestaña <b>Existencias (CU12)</b>.", body_style),
        Paragraph("<b>2. Carga de Métricas en Tiempo Real (KPIs):</b><br/>"
                  "El frontend solicita al endpoint <code>GET /api/productos-terminados/existencias/resumen/</code> los totales globales. "
                  "El servidor calcula la suma de unidades disponibles, el valor monetario total en bolivianos (Bs.) y cuenta cuántos panes están con stock crítico o agotados.", body_style),
        Paragraph("<b>3. Listado Dinámico con Filtros y Optimización:</b><br/>"
                  "El frontend solicita <code>GET /api/productos-terminados/existencias/</code>. La vista en Django utiliza <code>select_related('id_producto__id_categoria')</code> "
                  "para traer en una única consulta SQL de alta velocidad toda la información del pan, su categoría y su inventario, evitando sobrecargar el servidor.", body_style),
        Paragraph("<b>4. Cálculos Matemáticos en el Servidor:</b><br/>"
                  "Para cada pan devuelto, el serializador de Django calcula:<br/>"
                  "• <code>valor_total_stock = stock_actual * precio_venta</code> (ej. 140 marraquetas a Bs. 0.80 = Bs. 112.00).<br/>"
                  "• <code>estado_stock</code>: Si tiene 0 unidades es <code>'agotado'</code>; si tiene entre 1 y 20 es <code>'critico'</code>; si tiene más de 20 es <code>'disponible'</code>.", body_style),
        Paragraph("<b>5. Visualización Accesible y Amigable en Pantalla:</b><br/>"
                  "El usuario ve la tabla con una barra de progreso que representa la capacidad de la vitrina (de 0 a 150 unidades) y un badge de color intuitivo (verde para normal, amarillo para alerta, rojo para agotado).", body_style),
        Paragraph("<b>6. Auditoría y Kardex Detallado:</b><br/>"
                  "Si el usuario desea saber por qué hay cierta cantidad de pan, presiona el botón <b>'Kardex'</b>. "
                  "Se abre un modal interactivo que consulta <code>/api/productos-terminados/existencias/&lt;id&gt;/movimientos/</code> y muestra cuándo ingresó pan por producción horneada (+) y cuándo salió por ventas (-).", body_style),
    ]

    for p in pasos_flujo:
        story.append(p)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 5))

    # ==========================================
    # 6. GUÍA DE ELEMENTOS DE LA PANTALLA
    # ==========================================
    story.append(Paragraph("5. Guía Visual de la Pantalla (Lo que ve el Usuario)", h1_style))
    story.append(Paragraph(
        "Cuando el docente te pida mostrar la pantalla, esto es exactamente lo que tienes y lo que debes señalar:",
        body_style
    ))

    elementos_ui = [
        [Paragraph("<b>Elemento en Pantalla</b>", body_style), Paragraph("<b>Ubicación</b>", body_style), Paragraph("<b>Función / Qué hace</b>", body_style)],
        [
            Paragraph("<b>4 Tarjetas KPI Superiores</b>", body_style),
            Paragraph("Parte superior", body_style),
            Paragraph("• <b>Variedad en vitrina:</b> Número de tipos de pan activos.<br/>• <b>Stock total listo:</b> Total de piezas de pan listas en mostrador.<br/>• <b>Valor en mostrador:</b> Valor monetario total en Bs. a precio de venta.<br/>• <b>Alertas:</b> Conteo de panes que están por agotarse o ya en 0.", body_style)
        ],
        [
            Paragraph("<b>Buscador en Vivo</b>", body_style),
            Paragraph("Barra de herramientas", body_style),
            Paragraph("Permite tipear cualquier nombre (ej. 'marraqueta') y filtra la tabla en tiempo real sin recargar la página.", body_style)
        ],
        [
            Paragraph("<b>Selector de Categorías</b>", body_style),
            Paragraph("Filtro desplegable", body_style),
            Paragraph("Permite ver solo panes tradicionales, especiales o dulces.", body_style)
        ],
        [
            Paragraph("<b>Filtro de Estado de Stock</b>", body_style),
            Paragraph("Filtro desplegable", body_style),
            Paragraph("Permite filtrar solo los panes 'Normales', solo los 'Bajos (1 a 20 un)' o solo los 'Agotados'.", body_style)
        ],
        [
            Paragraph("<b>Barra Visual de Stock</b>", body_style),
            Paragraph("Columna de la tabla", body_style),
            Paragraph("Muestra una barra de color verde, amarilla o roja que indica el porcentaje de llenado de la canasta/vitrina.", body_style)
        ],
        [
            Paragraph("<b>Badges Semánticos</b>", body_style),
            Paragraph("Columna de estado", body_style),
            Paragraph("Pastillas de color con texto e icono: 'Disponible' (verde), 'Stock bajo' (amarillo) y 'Agotado' (rojo).", body_style)
        ],
        [
            Paragraph("<b>Botón 'Kardex'</b>", body_style),
            Paragraph("Columna acciones", body_style),
            Paragraph("Abre el modal con el historial cronológico de entradas y salidas de ese pan específico.", body_style)
        ],
    ]
    t_ui = Table(elementos_ui, colWidths=[120, 100, 284])
    t_ui.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_ui)

    story.append(PageBreak())

    # ==========================================
    # 7. CÓMO PROBARLO Y DEFENDERLO
    # ==========================================
    story.append(Paragraph("6. Cómo Probar el Sistema en tu Computadora", h1_style))
    story.append(Paragraph(
        "Para levantar y probar todo lo que implementaste, sigue estos sencillos pasos en tu terminal de PowerShell:",
        body_style
    ))

    comandos_pasos = [
        Paragraph("<b>Paso 1: Activar entorno virtual y poblar datos de prueba:</b><br/>"
                  "En la carpeta <code>backend</code> ejecuta el seeder creado para el CU12:", body_style),
        Paragraph("<code>cd \"d:\\Proyecto SI\\backend\"<br/>.\\venv\\Scripts\\Activate.ps1<br/>python manage.py seed_existencias</code>", code_style),
        Paragraph("<b>Paso 2: Correr las pruebas automatizadas (Test suite):</b><br/>"
                  "Demuestra que las 9 pruebas de CU12 pasan al 100% en verde:", body_style),
        Paragraph("<code>$env:DB_ENGINE=\"sqlite3\"; python manage.py test apps.productos_inventario.productos_terminados.tests</code>", code_style),
        Paragraph("<b>Paso 3: Iniciar el servidor backend:</b>", body_style),
        Paragraph("<code>python manage.py runserver</code>", code_style),
        Paragraph("<b>Paso 4: Iniciar el frontend en otra terminal:</b>", body_style),
        Paragraph("<code>cd \"d:\\Proyecto SI\\frontend\"<br/>npm run dev</code>", code_style),
        Paragraph("Abre tu navegador en <code>http://localhost:5173</code> e inicia sesión con el usuario de Personal de Ventas: <b>mgonzales</b> / contraseña: <b>Admin123!</b>.", body_style),
    ]

    for p in comandos_pasos:
        story.append(p)
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 10))

    # ==========================================
    # 8. GUIÓN DE EXPOSICIÓN ORAL PARA ROBERTO
    # ==========================================
    story.append(Paragraph("7. Guión de Exposición Oral para Roberto", h1_style))
    story.append(Paragraph(
        "Lee y practica este guión para cuando te toque hablar en la presentación ante el docente:",
        body_style
    ))

    story.append(Paragraph(
        "<b>Palabras de apertura:</b><br/>"
        "<i>«Docente, compañeros, mi nombre es Roberto y me correspondió desarrollar el <b>Caso de Uso 12: Consultar existencias de productos terminados</b>. "
        "Este caso de uso es fundamental en el ciclo operativo de la panadería porque conecta la producción con las ventas en mostrador. "
        "Permite que tanto el Propietario como el Personal de Ventas conozcan en tiempo real el stock físico disponible en vitrina, su valorización monetaria total y las alertas tempranas de reposición.»</i>",
        ParagraphStyle('G1', parent=body_style, fontName='Helvetica-Oblique', backColor=colors.HexColor("#F8FAFC"), borderPadding=6)
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Al mostrar la pantalla:</b><br/>"
        "<i>«Como pueden observar en la pantalla, al ingresar con el rol de Personal de Ventas, el sistema abre directamente la pestaña de Existencias. "
        "En la parte superior tenemos 4 tarjetas de métricas clave: total de variedades horneadas, unidades disponibles, el valor total del inventario en bolivianos calculado automáticamente, y los panes que están por agotarse.<br/>"
        "En la tabla principal, cada pan tiene su precio unitario, una barra visual de capacidad y un semáforo de disponibilidad. Además, contamos con un botón de Kardex que permite auditar las entradas por producción y las salidas por ventas.»</i>",
        ParagraphStyle('G2', parent=body_style, fontName='Helvetica-Oblique', backColor=colors.HexColor("#F8FAFC"), borderPadding=6)
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Respuestas a posibles preguntas del docente:", h2_style))

    story.append(Paragraph("• <b>Si el docente pregunta:</b> <i>¿Por qué no pusiste un botón para editar el número de stock en esta pantalla?</i><br/>"
                           "<b>Tu respuesta:</b> <i>«Porque en un sistema de información formal con arquitectura PUDS, el inventario no se altera manualmente con un formulario arbitrario. El stock aumenta de manera atómica cuando el horneador registra la producción (CU10) y disminuye cuando se registra una venta (CU13) o una pérdida (CU18). El CU12 es de supervisión y consulta fidedigna.»</i>", body_style))

    story.append(Paragraph("• <b>Si el docente pregunta:</b> <i>¿Cómo controlaste la seguridad y permisos?</i><br/>"
                           "<b>Tu respuesta:</b> <i>«Se implementó la clase de permiso <code>PuedeConsultarExistenciasTerminados</code> en Django REST Framework. El backend evalúa si el usuario cuenta con el permiso <code>gestionar_inventario</code> o <code>registrar_ventas</code>. Si un usuario sin permiso o un atacante intenta consumir el endpoint, el servidor rechaza la petición con código HTTP 403 Forbidden.»</i>", body_style))

    story.append(Paragraph("• <b>Si el docente pregunta:</b> <i>¿Cómo trabajaron en Git?</i><br/>"
                           "<b>Tu respuesta:</b> <i>«Siguiendo la política de nuestro equipo, nadie sube cambios directo a la rama main. Todo mi caso de uso fue desarrollado en mi rama de trabajo <code>feature/cu12-consultar-existencias-roberto</code> con sus pruebas unitarias en verde, garantizando cero conflictos al momento del merge.»</i>", body_style))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    generar_pdf()
