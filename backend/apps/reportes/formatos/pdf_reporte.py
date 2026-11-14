"""
Membrete compartido de los PDF de la panadería.

Producción diaria y el cierre de ventas usan la misma hoja: logo, título
naranja, tarjetas de cifras y una tabla. Cada reporte pone su propio título.
El logo vive junto a este módulo porque el contenedor del backend no ve
la carpeta frontend.
"""
import io
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ANCHO, ALTO = A4
MARGEN = 36
UTIL = ANCHO - (MARGEN * 2)

# El marrón y la crema salen de la paleta de panadería.
# El naranja del título es #C2410C: se lee como naranja y, en negrita
# sobre blanco, supera el contraste 4.5:1.
NARANJA = HexColor('#C2410C')
MARRON = HexColor('#92400E')
CREMA = HexColor('#FEF3C7')
BORDE = HexColor('#FDE68A')
TINTA = HexColor('#1C1917')
GRIS = HexColor('#475569')
CEBRA = HexColor('#FFFBEB')

LOGO = Path(__file__).resolve().parent / 'assets' / 'circle-logo-panaderia.png'
ALTO_LOGO = 86


def fecha_visible(valor) -> str:
    """Pasa 2026-09-08 a 08/09/2026. Si no es una fecha, lo deja igual."""
    if valor in (None, ''):
        return 'Todas'
    texto = valor.isoformat() if hasattr(valor, 'isoformat') else str(valor)
    anio, separador, resto = texto.partition('-')
    if not separador:
        return 'Todas' if texto == 'todas' else texto
    mes, separador_dia, dia = resto.partition('-')
    if (
        separador_dia
        and len(anio) == 4
        and len(mes) == 2
        and len(dia) == 2
        and anio.isdigit()
        and mes.isdigit()
        and dia.isdigit()
    ):
        return f'{dia}/{mes}/{anio}'
    return texto


def anchos_de(*partes: int) -> list[int]:
    """Reparte el ancho útil de la hoja según proporciones enteras."""
    total = sum(partes)
    columnas = [int(UTIL * parte / total) for parte in partes]
    columnas[-1] += int(UTIL) - sum(columnas)
    return columnas


class HojaReporte:
    """Una hoja A4 con el membrete de la panadería y salto de página."""

    def __init__(self, titulo_documento: str):
        if not LOGO.is_file():
            raise FileNotFoundError(f'No está el logo del reporte: {LOGO}')
        self.buffer = io.BytesIO()
        self.hoja = canvas.Canvas(self.buffer, pagesize=A4, pageCompression=0)
        self.hoja.setTitle(titulo_documento)
        self.hoja.setAuthor('Panadería Santiago')
        self.titulo = titulo_documento
        self.y = ALTO
        self._reponiendo = False

    def abrir(self, titulo: str, detalle: str) -> None:
        self.titulo = titulo
        self._franja()
        techo = ALTO - 22
        self.hoja.drawImage(
            str(LOGO),
            MARGEN,
            techo - ALTO_LOGO,
            width=ALTO_LOGO,
            height=ALTO_LOGO,
            preserveAspectRatio=True,
            mask='auto',
            anchor='c',
        )

        texto_x = MARGEN + ALTO_LOGO + 16
        ancho_texto = ANCHO - MARGEN - texto_x
        self.hoja.setFillColor(MARRON)
        self.hoja.setFont('Helvetica-Bold', 8)
        self.hoja.drawString(texto_x, techo - 14, 'PANADERÍA SANTIAGO  ·  SANTA CRUZ DE LA SIERRA')

        self.hoja.setFillColor(NARANJA)
        self.hoja.setFont('Helvetica-Bold', 18)
        self.hoja.drawString(texto_x, techo - 38, titulo)

        self.y = techo - 56
        self.hoja.setFillColor(GRIS)
        self.hoja.setFont('Helvetica', 9)
        for linea in self._lineas(detalle, 'Helvetica', 9, ancho_texto)[:3]:
            self.hoja.drawString(texto_x, self.y, linea)
            self.y -= 13

        base = min(self.y, techo - ALTO_LOGO) - 12
        self.hoja.setStrokeColor(NARANJA)
        self.hoja.setLineWidth(2)
        self.hoja.line(MARGEN, base, ANCHO - MARGEN, base)
        self.hoja.setStrokeColor(MARRON)
        self.hoja.setLineWidth(0.4)
        self.hoja.line(MARGEN, base - 4, ANCHO - MARGEN, base - 4)
        self.y = base - 22

    def tarjetas(self, items: list[tuple[str, str]]) -> None:
        if not items:
            return
        alto = 50
        if self.y < 64 + alto:
            self._saltar(None)
        espacio = 8
        ancho = (UTIL - espacio * (len(items) - 1)) / len(items)
        base = self.y - alto
        for indice, (etiqueta, valor) in enumerate(items):
            x = MARGEN + indice * (ancho + espacio)
            self.hoja.setFillColor(CREMA)
            self.hoja.roundRect(x, base, ancho, alto, 4, fill=1, stroke=0)
            self.hoja.setFillColor(NARANJA)
            self.hoja.rect(x, base, 3, alto, fill=1, stroke=0)
            self.hoja.setFillColor(MARRON)
            self.hoja.setFont('Helvetica-Bold', 8)
            self.hoja.drawString(x + 12, base + 30, etiqueta.upper())
            self.hoja.setFillColor(TINTA)
            self.hoja.setFont('Helvetica-Bold', 13)
            self.hoja.drawString(x + 12, base + 12, self._cabe(str(valor), ancho - 20, 'Helvetica-Bold', 13))
        self.y = base - 20

    def seccion(self, titulo: str) -> None:
        if self.y < 78:
            self._saltar(None)
        self.hoja.setFillColor(MARRON)
        self.hoja.setFont('Helvetica-Bold', 11)
        self.hoja.drawString(MARGEN, self.y, titulo)
        self.y -= 16

    def fila(
        self,
        celdas: list[tuple[str, str]],
        columnas: list[int],
        encabezado: bool = False,
        cebra: bool = False,
        al_continuar=None,
    ) -> None:
        alto = 18
        if not self._reponiendo and self.y < 52 + alto:
            self._saltar(al_continuar)
        if encabezado:
            self.hoja.setFillColor(MARRON)
            self.hoja.rect(MARGEN, self.y - 5, UTIL, alto, fill=1, stroke=0)
        elif cebra:
            self.hoja.setFillColor(CEBRA)
            self.hoja.rect(MARGEN, self.y - 5, UTIL, alto, fill=1, stroke=0)

        fuente = 'Helvetica-Bold' if encabezado else 'Helvetica'
        tamano = 8
        self.hoja.setFillColor(white if encabezado else TINTA)
        self.hoja.setFont(fuente, tamano)
        x = MARGEN
        for (texto, alineacion), ancho in zip(celdas, columnas):
            visible = self._cabe(str(texto), ancho - 10, fuente, tamano)
            if alineacion == 'der':
                self.hoja.drawRightString(x + ancho - 6, self.y, visible)
            else:
                self.hoja.drawString(x + 6, self.y, visible)
            x += ancho
        if not encabezado:
            self.hoja.setStrokeColor(BORDE)
            self.hoja.setLineWidth(0.3)
            self.hoja.line(MARGEN, self.y - 5, MARGEN + UTIL, self.y - 5)
        self.y -= alto

    def nota(self, texto: str) -> None:
        self.y -= 6
        for linea in self._lineas(texto, 'Helvetica', 8, UTIL):
            if self.y < 58:
                self._saltar(None)
            self.hoja.setFillColor(GRIS)
            self.hoja.setFont('Helvetica', 8)
            self.hoja.drawString(MARGEN, self.y, linea)
            self.y -= 12

    def cerrar(self) -> bytes:
        self._pie()
        self.hoja.save()
        return self.buffer.getvalue()

    def _franja(self) -> None:
        self.hoja.setFillColor(NARANJA)
        self.hoja.rect(0, ALTO - 8, ANCHO, 8, fill=1, stroke=0)

    def _encabezado_compacto(self) -> None:
        self._franja()
        self.hoja.setFillColor(NARANJA)
        self.hoja.setFont('Helvetica-Bold', 11)
        self.hoja.drawString(MARGEN, ALTO - 28, self.titulo)
        self.hoja.setStrokeColor(NARANJA)
        self.hoja.setLineWidth(1.25)
        self.hoja.line(MARGEN, ALTO - 36, ANCHO - MARGEN, ALTO - 36)
        self.y = ALTO - 54

    def _saltar(self, al_continuar) -> None:
        self._pie()
        self.hoja.showPage()
        self._encabezado_compacto()
        if al_continuar is None:
            return
        self._reponiendo = True
        try:
            al_continuar()
        finally:
            self._reponiendo = False

    def _pie(self) -> None:
        self.hoja.setStrokeColor(BORDE)
        self.hoja.setLineWidth(0.6)
        self.hoja.line(MARGEN, 32, ANCHO - MARGEN, 32)
        self.hoja.setFillColor(GRIS)
        self.hoja.setFont('Helvetica', 8)
        self.hoja.drawString(MARGEN, 20, 'Panadería Santiago  ·  Santa Cruz de la Sierra')
        self.hoja.drawRightString(ANCHO - MARGEN, 20, f'Página {self.hoja.getPageNumber()}')

    def _lineas(self, texto: str, fuente: str, tamano: int, ancho: float) -> list[str]:
        lineas = []
        for bloque in str(texto).split('\n'):
            palabras = bloque.split()
            if not palabras:
                continue
            actual = ''
            for palabra in palabras:
                candidato = palabra if not actual else f'{actual} {palabra}'
                if self.hoja.stringWidth(candidato, fuente, tamano) <= ancho:
                    actual = candidato
                else:
                    if actual:
                        lineas.append(actual)
                    actual = palabra
            if actual:
                lineas.append(actual)
        return lineas

    def _cabe(self, texto: str, ancho: float, fuente: str, tamano: int) -> str:
        if self.hoja.stringWidth(texto, fuente, tamano) <= ancho:
            return texto
        while texto and self.hoja.stringWidth(f'{texto}...', fuente, tamano) > ancho:
            texto = texto[:-1]
        return f'{texto}...' if texto else ''
