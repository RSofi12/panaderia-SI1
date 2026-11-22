"""Texto del asistente listo para PDF/pantalla sin Markdown visible."""
from __future__ import annotations

import re


def sin_markdown(texto: str) -> str:
    """Quita **negritas**, viñetas con * y encabezados # para informes formales."""
    if not texto:
        return ''
    lineas = []
    for linea in str(texto).splitlines():
        frag = linea.strip()
        if not frag:
            lineas.append('')
            continue
        frag = re.sub(r'^#{1,6}\s*', '', frag)
        frag = re.sub(r'\*\*([^*]+)\*\*', r'\1', frag)
        frag = re.sub(r'__([^_]+)__', r'\1', frag)
        frag = re.sub(r'\*([^*]+)\*', r'\1', frag)
        frag = re.sub(r'\*\*', '', frag)
        if re.match(r'^[\*\-]\s+', frag):
            frag = re.sub(r'^[\*\-]\s+', '• ', frag, count=1)
        lineas.append(frag)
    bloque = '\n'.join(lineas)
    bloque = re.sub(r'\n{3,}', '\n\n', bloque)
    return bloque.strip()