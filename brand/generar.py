#!/usr/bin/env python3
"""Genera los archivos de marca de appClub en esta carpeta.

Uso (desde la raíz del repo):
    pip install fonttools uharfbuzz cairosvg
    python3 brand/generar.py

El texto del wordmark se convierte a trazos con las fuentes de brand/fuentes/
(Manrope, licencia OFL), así los SVG no dependen de ninguna fuente instalada.
Todo sale de las constantes de abajo: para cambiar un color o una medida,
cambiarla acá y volver a generar.
"""
from pathlib import Path

import cairosvg
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / 'fuentes'

# --- Paleta (ver tokens.css) -------------------------------------------------
INDIGO = '#4338CA'       # color de marca
INDIGO_CLARO = '#818CF8'  # acento en tema oscuro
INDIGO_TINTA = '#1E1B4B'  # texto en tema claro, superficie en oscuro
NOCHE = '#14122E'         # fondo del tema oscuro
LAVANDA = '#A5B4FC'       # texto suave en tema oscuro
NIEBLA = '#EEF2FF'        # texto en tema oscuro
AMARILLO = '#FDE68A'      # el punto
BLANCO = '#FFFFFF'

# --- Geometría del ícono (viewBox 120) ---------------------------------------
LADO = 120
RADIO = 28
TRAZO = 12
C_PATH = 'M80 38 H48 A12 12 0 0 0 36 50 V70 A12 12 0 0 0 48 82 H80'
PUNTO = (76, 60, 6.5)

# --- Wordmark -----------------------------------------------------------------
PARTES = [('app', 500), ('Club', 800)]
TRACKING = -0.01  # en em


def svg(view_box, cuerpo, titulo):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" role="img" aria-label="{titulo}">'
        f'<title>{titulo}</title>{cuerpo}</svg>\n'
    )


def ico_cuerpo(cuadrado, c, punto, transform=''):
    cx, cy, r = PUNTO
    t = f' transform="{transform}"' if transform else ''
    fondo = f'<rect width="{LADO}" height="{LADO}" rx="{RADIO}" fill="{cuadrado}"/>' if cuadrado else ''
    return (
        f'<g{t}>{fondo}'
        f'<path d="{C_PATH}" fill="none" stroke="{c}" stroke-width="{TRAZO}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{punto}"/></g>'
    )


def ico_mono_cuerpo(id_mask='calado'):
    """Cuadrado de una sola tinta con la C y el punto calados (currentColor)."""
    cx, cy, r = PUNTO
    return (
        f'<defs><mask id="{id_mask}" maskUnits="userSpaceOnUse" x="0" y="0" width="{LADO}" height="{LADO}">'
        f'<rect width="{LADO}" height="{LADO}" fill="#fff"/>'
        f'<path d="{C_PATH}" fill="none" stroke="#000" stroke-width="{TRAZO}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#000"/></mask></defs>'
        f'<rect width="{LADO}" height="{LADO}" rx="{RADIO}" fill="currentColor" mask="url(#{id_mask})"/>'
    )


class Texto:
    """Convierte 'app' + 'Club' a trazos, con el kerning de la fuente."""

    def __init__(self):
        self.fuentes = {}
        for _, peso in PARTES:
            ruta = FUENTES / f'manrope-latin-{peso}-normal.woff'
            tt = TTFont(ruta)
            # harfbuzz no lee WOFF: se le pasa la misma fuente como TTF en memoria
            from io import BytesIO
            tt.flavor = None
            bio = BytesIO()
            tt.save(bio)
            datos = bio.getvalue()
            tt = TTFont(BytesIO(datos))
            self.fuentes[peso] = (tt, hb.Font(hb.Face(datos)))
        self.upm = next(iter(self.fuentes.values()))[0]['head'].unitsPerEm
        self.cap = next(iter(self.fuentes.values()))[0]['OS/2'].sCapHeight / self.upm

    def trazos(self, tamano, x0=0.0, base=0.0):
        """Devuelve [(d, peso)] y la caja (xmin, ymin, xmax, ymax)."""
        escala = tamano / self.upm
        x = x0
        salida = []
        self.inicios = []  # x donde arranca cada parte (para la animación)
        caja = [float('inf'), float('inf'), float('-inf'), float('-inf')]
        for palabra, peso in PARTES:
            self.inicios.append(x)
            tt, hbfont = self.fuentes[peso]
            buf = hb.Buffer()
            buf.add_str(palabra)
            buf.guess_segment_properties()
            hb.shape(hbfont, buf, {'kern': True, 'liga': False})
            glifos = tt.getGlyphSet()
            orden = tt.getGlyphOrder()
            d_total = []
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
                nombre = orden[info.codepoint]
                gx = x + pos.x_offset * escala
                gy = base - pos.y_offset * escala
                pen = SVGPathPen(glifos)
                glifos[nombre].draw(TransformPen(pen, (escala, 0, 0, -escala, gx, gy)))
                d_total.append(pen.getCommands())
                bp = BoundsPen(glifos)
                glifos[nombre].draw(TransformPen(bp, (escala, 0, 0, -escala, gx, gy)))
                if bp.bounds:
                    a, b, c, d = bp.bounds
                    caja = [min(caja[0], a), min(caja[1], b), max(caja[2], c), max(caja[3], d)]
                x += pos.x_advance * escala + TRACKING * tamano
            salida.append((' '.join(d_total), peso))
        return salida, caja


def redondear(d):
    import re
    return re.sub(r'-?\d+\.\d+', lambda m: f'{float(m.group()):.2f}'.rstrip('0').rstrip('.'), d)


def main():
    texto = Texto()
    archivos = {}

    # Íconos
    temas_ico = {
        'icono': (INDIGO, BLANCO, AMARILLO, 'appClub'),
        'icono-oscuro': (INDIGO_CLARO, NOCHE, AMARILLO, 'appClub'),
    }
    for nombre, (cuad, c, punto, titulo) in temas_ico.items():
        archivos[f'{nombre}.svg'] = svg(f'0 0 {LADO} {LADO}', ico_cuerpo(cuad, c, punto), titulo)
    # Sin fondo: para poner sobre una superficie de color propia
    archivos['icono-sin-fondo.svg'] = svg(f'0 0 {LADO} {LADO}', ico_cuerpo(None, INDIGO, INDIGO), 'appClub')
    archivos['icono-sin-fondo-oscuro.svg'] = svg(f'0 0 {LADO} {LADO}', ico_cuerpo(None, NIEBLA, AMARILLO), 'appClub')
    archivos['icono-mono.svg'] = svg(f'0 0 {LADO} {LADO}', ico_mono_cuerpo(), 'appClub')

    # Favicon: cambia solo con el tema del sistema
    cx, cy, r = PUNTO
    archivos['favicon.svg'] = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LADO} {LADO}">'
        '<style>.f{fill:%s}.c{stroke:%s}'
        '@media (prefers-color-scheme:dark){.f{fill:%s}.c{stroke:%s}}</style>'
        f'<rect class="f" width="{LADO}" height="{LADO}" rx="{RADIO}"/>'
        f'<path class="c" d="{C_PATH}" fill="none" stroke-width="{TRAZO}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{AMARILLO}"/></svg>\n'
    ) % (INDIGO, BLANCO, INDIGO_CLARO, NOCHE)

    # Wordmark (tamaño 100, base en 0; el viewBox se ajusta a la caja con margen)
    partes, caja = texto.trazos(100)
    m = 4
    vb = f'{caja[0]-m:.1f} {caja[1]-m:.1f} {caja[2]-caja[0]+2*m:.1f} {caja[3]-caja[1]+2*m:.1f}'
    colores_wm = {
        'wordmark': (INDIGO, INDIGO_TINTA),
        'wordmark-oscuro': (LAVANDA, NIEBLA),
        'wordmark-mono': ('currentColor', 'currentColor'),
    }
    for nombre, (c_app, c_club) in colores_wm.items():
        cuerpo = ''.join(
            f'<path fill="{c_app if peso == 500 else c_club}" d="{redondear(d)}"/>' for d, peso in partes
        )
        archivos[f'{nombre}.svg'] = svg(vb, cuerpo, 'appClub')

    # Lockup horizontal: alto de mayúscula = alto exterior de la C (56), base alineada con su borde inferior
    alto_c = (82 + TRAZO / 2) - (38 - TRAZO / 2)
    tamano = alto_c / texto.cap
    base = 82 + TRAZO / 2
    separacion = 28
    partes_l, caja_l = texto.trazos(tamano, x0=LADO + separacion, base=base)
    ancho = caja_l[2] + 4
    lockups = {
        'lockup': ((INDIGO, BLANCO, AMARILLO), (INDIGO, INDIGO_TINTA)),
        'lockup-oscuro': ((INDIGO_CLARO, NOCHE, AMARILLO), (LAVANDA, NIEBLA)),
    }
    for nombre, (ico, (c_app, c_club)) in lockups.items():
        cuerpo = ico_cuerpo(*ico) + ''.join(
            f'<path fill="{c_app if peso == 500 else c_club}" d="{redondear(d)}"/>' for d, peso in partes_l
        )
        archivos[f'{nombre}.svg'] = svg(f'0 0 {ancho:.1f} {LADO}', cuerpo, 'appClub')
    cuerpo = ico_mono_cuerpo('calado-lockup') + ''.join(
        f'<path fill="currentColor" d="{redondear(d)}"/>' for d, _ in partes_l
    )
    archivos['lockup-mono.svg'] = svg(f'0 0 {ancho:.1f} {LADO}', cuerpo, 'appClub')

    # Animación A → C (issue #3): mismos trazos que el lockup
    from animacion import generar_animacion
    archivos.update(generar_animacion(
        partes=[(redondear(d), peso) for d, peso in partes_l],
        inicio_club=texto.inicios[1],
        ancho=ancho,
        geo=dict(lado=LADO, radio=RADIO, trazo=TRAZO, c_path=C_PATH, punto=PUNTO),
        colores=dict(
            claro=dict(cuadrado=INDIGO, c=BLANCO, punto=AMARILLO, app=INDIGO, club=INDIGO_TINTA, fondo='#F6F7FB'),
            oscuro=dict(cuadrado=INDIGO_CLARO, c=NOCHE, punto=AMARILLO, app=LAVANDA, club=NIEBLA, fondo=NOCHE),
        ),
    ))
    (AQUI / 'animacion').mkdir(exist_ok=True)

    for nombre, contenido in archivos.items():
        (AQUI / nombre).write_text(contenido, encoding='utf-8')

    # PNG para los usos que no aceptan SVG
    png = AQUI / 'png'
    png.mkdir(exist_ok=True)
    tamanos = {
        'icono': [16, 32, 48, 64, 128, 192, 256, 512, 1024],
        'icono-oscuro': [192, 512],
    }
    for nombre, lista in tamanos.items():
        for t in lista:
            cairosvg.svg2png(bytestring=archivos[f'{nombre}.svg'].encode(), write_to=str(png / f'{nombre}-{t}.png'),
                             output_width=t, output_height=t)
    # iOS: sin transparencia y sin esquinas redondeadas (iOS aplica la máscara)
    ios = svg(f'0 0 {LADO} {LADO}', f'<rect width="{LADO}" height="{LADO}" fill="{INDIGO}"/>' + ico_cuerpo(None, BLANCO, AMARILLO), 'appClub')
    cairosvg.svg2png(bytestring=ios.encode(), write_to=str(png / 'icono-ios-1024.png'), output_width=1024, output_height=1024)
    # apple-touch-icon: mismo criterio (con esquinas transparentes, iOS las rellena de negro)
    cairosvg.svg2png(bytestring=ios.encode(), write_to=str(png / 'apple-touch-icon-180.png'), output_width=180, output_height=180)
    for nombre in ('lockup', 'lockup-oscuro'):
        cairosvg.svg2png(bytestring=archivos[f'{nombre}.svg'].encode(), write_to=str(png / f'{nombre}-alto240.png'),
                         output_height=240)

    print('Generados:', ', '.join(sorted(archivos)), '+', len(list(png.glob('*.png'))), 'PNG')


if __name__ == '__main__':
    main()
