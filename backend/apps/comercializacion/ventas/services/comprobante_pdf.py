def generar_ticket_pdf_bytes(comprobante_data: dict) -> bytes:
    """
    Genera un archivo PDF 1.4 binario válido en memoria para el comprobante de venta,
    sin requerir dependencias externas pesadas.
    Dimensiones: 80mm de ancho (226 pt) x altura dinámica según cantidad de líneas.
    """
    numero = comprobante_data.get('numero_comprobante', 0)
    fecha = str(comprobante_data.get('fecha_hora', ''))[:19].replace('T', ' ')
    cajero = comprobante_data.get('cajero', 'Personal de Ventas')
    metodo = str(comprobante_data.get('metodo_pago', 'efectivo')).upper()
    stripe_id = comprobante_data.get('id_transaccion_stripe')
    total = comprobante_data.get('total', '0.00')
    detalles = comprobante_data.get('detalles', [])
    articulos = comprobante_data.get('total_articulos', len(detalles))

    # Construir líneas de texto
    lineas = []
    lineas.append(("PANADERIA SANTIAGO", 14, True))
    lineas.append(("De: Carlos Santiago Vargas", 9, False))
    lineas.append(("Santa Cruz de la Sierra - Bolivia", 8, False))
    lineas.append(("Telf: 3-3456789", 8, False))
    lineas.append(("------------------------------------------------", 8, False))
    lineas.append((f"COMPROBANTE DE VENTA #{numero}", 11, True))
    lineas.append((f"Fecha: {fecha}", 8, False))
    lineas.append((f"Cajero: {cajero}", 8, False))
    lineas.append(("------------------------------------------------", 8, False))
    lineas.append((f"{'CANT':<5} {'DESCRIPCION':<18} {'P.UNIT':<8} {'SUBTOTAL':>8}", 8, True))
    lineas.append(("- - - - - - - - - - - - - - - - - - - - - - - -", 8, False))

    for d in detalles:
        nom = d.get('nombre_producto', '')[:18]
        cant = f"{d.get('cantidad', 1)}x"
        pu = f"{d.get('precio_unitario', '0.00')}"
        sub = f"{d.get('subtotal', '0.00')}"
        lineas.append((f"{cant:<5} {nom:<18} {pu:<8} {sub:>8}", 8, False))

    lineas.append(("------------------------------------------------", 8, False))
    lineas.append((f"TOTAL A PAGAR:        Bs {total:>8}", 11, True))
    lineas.append((f"METODO DE PAGO:       {metodo}", 8, False))
    if stripe_id:
        lineas.append((f"TRANS. STRIPE: {stripe_id[:24]}", 7, False))
    lineas.append((f"TOTAL ARTICULOS:      {articulos}", 8, False))
    lineas.append(("------------------------------------------------", 8, False))
    lineas.append(("¡Gracias por su preferencia!", 9, True))
    lineas.append(("Pan fresco todos los dias", 8, False))

    # Altura del ticket: 14pt por línea + márgenes
    alto_pagina = max(380, len(lineas) * 16 + 80)
    ancho_pagina = 226  # ~80mm

    # Construir contenido del stream PDF
    stream_parts = ["BT"]
    y_pos = alto_pagina - 30

    def escape_pdf(txt: str) -> str:
        return txt.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    for txt, tam, bold in lineas:
        font_ref = "/F2" if bold else "/F1"
        stream_parts.append(f"{font_ref} {tam} Tf")
        # Centrar si es encabezado o pie
        if txt in ["PANADERIA SANTIAGO", "De: Carlos Santiago Vargas", "Santa Cruz de la Sierra - Bolivia", "Telf: 3-3456789", "¡Gracias por su preferencia!", "Pan fresco todos los dias"]:
            # Estimación de ancho: ~tam*0.5 por carácter
            ancho_est = len(txt) * (tam * 0.5)
            x_pos = max(10, (ancho_pagina - ancho_est) / 2)
        else:
            x_pos = 14
        stream_parts.append(f"1 0 0 1 {x_pos:.1f} {y_pos:.1f} Tm")
        stream_parts.append(f"({escape_pdf(txt)}) Tj")
        y_pos -= (tam + 5)

    stream_parts.append("ET")
    stream_content = "\n".join(stream_parts).encode('latin-1', errors='replace')

    # Estructura de objetos PDF
    objetos = []
    # 1: Catalog
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    objetos.append(f"<< /Type /Pages /Kids [3 0 R] /Count 1 >>".encode('ascii'))
    # 3: Page
    objetos.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {ancho_pagina} {alto_pagina}] "
        f"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
        f"/Contents 6 0 R >>".encode('ascii')
    )
    # 4: Regular Font (Helvetica)
    objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    # 5: Bold Font (Helvetica-Bold)
    objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    # 6: Stream Contents
    objetos.append(
        b"<< /Length " + str(len(stream_content)).encode('ascii') + b" >>\nstream\n" +
        stream_content + b"\nendstream"
    )

    # Armar archivo con tabla xref
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = []
    current_pos = len(header)
    body = bytearray()

    for i, obj_data in enumerate(objetos, start=1):
        offsets.append(current_pos)
        obj_header = f"{i} 0 obj\n".encode('ascii')
        obj_footer = b"\nendobj\n"
        chunk = obj_header + obj_data + obj_footer
        body.extend(chunk)
        current_pos += len(chunk)

    xref_pos = current_pos
    xref = [f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode('ascii')]
    for off in offsets:
        xref.append(f"{off:010d} 00000 n \n".encode('ascii'))

    trailer = (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode('ascii')

    return header + bytes(body) + b"".join(xref) + trailer

