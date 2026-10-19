"""Animación de marca A → C ("app" → "appClub"). La llama generar.py.

Produce, dentro de brand/animacion/:
- appclub-loop.svg       spinner: va y vuelve sin parar
- appclub-una-vez.svg    splash o cierre: A → C una vez y queda en C
- trazos.ts              geometría y colores para el componente de React Native
- demo.html              las dos versiones en claro y oscuro, inline (para revisar y para render de video)

Tiempos (en % de un ciclo de 3,6 s; el loop va y vuelve con `alternate`):
   0–35 %  quieto en A: dibujo girado 90° en sentido horario, travesaño visible, "app"
  35–65 %  gira a C en sentido antihorario (gira el dibujo, el cuadrado queda quieto); el travesaño se va hasta el 50 % y el punto
           aparece entre el 50 y el 65 %; "Club" se descubre de izquierda a derecha
  65–100 % quieto en C con "appClub"

"Club" entra desplazado 6 unidades (sobre 120 de alto), no 14 px como el prototipo:
a esta escala 14 lo hacía encimarse con "app" mientras aparecía.
"""

BARRA = 'M64 50 V70'  # travesaño: solo existe en la posición A
BARRA_TRAZO = 10
DURACION = 3.6
FASES = dict(giro=(0.35, 0.65), barra=(0.35, 0.50), punto=(0.50, 0.65), club=(0.35, 0.65))


def _pct(x):
    return f'{round(x * 100)}%'


def _css(modo, colores, alcance=''):
    """alcance: selector que limita el CSS a un SVG (cuando hay varios inline en la misma página)."""
    g0, g1 = FASES['giro']
    b0, b1 = FASES['barra']
    p0, p1 = FASES['punto']
    c0, c1 = FASES['club']
    if modo == 'loop':
        anim = f'{DURACION}s ease-in-out infinite alternate'
    else:
        anim = f'{DURACION}s ease-in-out 1 both'
    cl, os_ = colores['claro'], colores['oscuro']
    css = (
        '.sq{fill:%s}.c,.barra{stroke:%s}.pt{fill:%s}.app{fill:%s}.club{fill:%s}'
        '@media (prefers-color-scheme:dark){.sq{fill:%s}.c,.barra{stroke:%s}.pt{fill:%s}.app{fill:%s}.club{fill:%s}}'
        % (cl['cuadrado'], cl['c'], cl['punto'], cl['app'], cl['club'],
           os_['cuadrado'], os_['c'], os_['punto'], os_['app'], os_['club'])
        + '.giro{transform-box:view-box;transform-origin:60px 60px}'
        f'@keyframes ac-giro{{0%,{_pct(g0)}{{transform:rotate(90deg)}}{_pct(g1)},100%{{transform:rotate(0deg)}}}}'
        f'@keyframes ac-barra{{0%,{_pct(b0)}{{opacity:1}}{_pct(b1)},100%{{opacity:0}}}}'
        f'@keyframes ac-punto{{0%,{_pct(p0)}{{opacity:0}}{_pct(p1)},100%{{opacity:1}}}}'
        f'@keyframes ac-club{{0%,{_pct(c0)}{{clip-path:inset(-10% 100% -10% 0);opacity:0;transform:translateX(-6px)}}'
        f'{_pct(c1)},100%{{clip-path:inset(-10% 0 -10% 0);opacity:1;transform:translateX(0)}}}}'
        f'.giro{{animation:ac-giro {anim}}}.barra{{animation:ac-barra {anim}}}'
        f'.pt{{animation:ac-punto {anim}}}.club{{animation:ac-club {anim}}}'
        '@media (prefers-reduced-motion:reduce){.giro,.barra,.pt,.club{animation:none}'
        '.giro{transform:none}.barra{opacity:0}.pt{opacity:1}.club{clip-path:none;opacity:1;transform:none}}'
    )
    if alcance:
        import re
        css = re.sub(r'(?<![\w-])\.(sq|c|barra|pt|app|club|giro)(?![\w-])', rf'{alcance} .\1', css)
    return css


def _cuerpo(partes, geo):
    cx, cy, r = geo['punto']
    lado, radio, trazo, c_path = geo['lado'], geo['radio'], geo['trazo'], geo['c_path']
    app = ''.join(f'<path class="app" d="{d}"/>' for d, peso in partes if peso == 500)
    club = ''.join(f'<path d="{d}"/>' for d, peso in partes if peso != 500)
    return (
        f'<rect class="sq" width="{lado}" height="{lado}" rx="{radio}"/>'
        f'<g class="giro"><path class="c" d="{c_path}" fill="none" stroke-width="{trazo}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path class="barra" d="{BARRA}" fill="none" stroke-width="{BARRA_TRAZO}" stroke-linecap="round"/>'
        f'<circle class="pt" cx="{cx}" cy="{cy}" r="{r}"/></g>'
        f'{app}<g class="club">{club}</g>'
    )


def _svg(modo, partes, ancho, geo, colores, id_=''):
    titulo = 'Cargando' if modo == 'loop' else 'appClub'
    rol = 'role="img"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho:.1f} {geo["lado"]}" {rol} aria-label="{titulo}"{id_}>'
        f'<title>{titulo}</title><style>{_css(modo, colores)}</style>{_cuerpo(partes, geo)}</svg>\n'
    )


def _ts(partes, inicio_club, ancho, geo, colores):
    app = ' '.join(d for d, peso in partes if peso == 500)
    club = ' '.join(d for d, peso in partes if peso != 500)
    cx, cy, r = geo['punto']
    lineas = [
        '// Generado por brand/generar.py — no editar a mano.',
        '// Geometría en unidades del lockup (alto 120). Ver brand/README.md, sección Animación.',
        'export const LADO = %d;' % geo['lado'],
        'export const RADIO = %d;' % geo['radio'],
        'export const TRAZO = %d;' % geo['trazo'],
        "export const C_PATH = '%s';" % geo['c_path'],
        'export const PUNTO = { cx: %s, cy: %s, r: %s };' % (cx, cy, r),
        "export const BARRA = '%s';" % BARRA,
        'export const BARRA_TRAZO = %d;' % BARRA_TRAZO,
        'export const SEPARACION = 28;',
        'export const APP_X0 = %d; // la palabra arranca justo después del ícono y la separación' % (geo['lado'] + 28),
        'export const CLUB_X0 = %.2f;' % inicio_club,
        'export const ANCHO = %.2f;' % ancho,
        "export const APP_PATH = '%s';" % app,
        "export const CLUB_PATH = '%s';" % club,
        'export const DURACION_MS = %d;' % round(DURACION * 1000),
        'export const FASES = {',
        *[f'  {k}: [{a}, {b}] as const,' for k, (a, b) in FASES.items()],
        '};',
        'export const COLORES = {',
    ]
    for tema in ('claro', 'oscuro'):
        c = colores[tema]
        lineas.append(f"  {tema}: {{ cuadrado: '{c['cuadrado']}', c: '{c['c']}', punto: '{c['punto']}', app: '{c['app']}', club: '{c['club']}', fondo: '{c['fondo']}' }},")
    lineas.append('} as const;')
    return '\n'.join(lineas) + '\n'


def _demo(partes, ancho, geo, colores):
    bloques = []
    for tema in ('claro', 'oscuro'):
        fondo = colores[tema]['fondo']
        for modo, titulo in (('una-vez', 'Una vez (splash, cierre de video)'), ('loop', 'Loop (cargando)')):
            # Inline, con el tema forzado: cada bloque redefine los colores sin depender del sistema
            id_ = f'ac-{tema}-{modo}'
            css = _css(modo, {'claro': colores[tema], 'oscuro': colores[tema]}, alcance=f'#{id_}')
            svg = (
                f'<svg id="{id_}" viewBox="0 0 {ancho:.1f} {geo["lado"]}" width="{ancho * 1.6:.0f}" height="{geo["lado"] * 1.6:.0f}" '
                f'role="img" aria-label="appClub"><style>{css}</style>{_cuerpo(partes, geo)}</svg>'
            )
            bloques.append(
                f'<section class="b" style="background:{fondo};color:{colores[tema]["club"]}" data-tema="{tema}" data-modo="{modo}">'
                f'<p>{tema} · {titulo}</p>{svg}</section>'
            )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Animación appClub</title><style>body{margin:0;font-family:system-ui,sans-serif}'
        '.b{padding:28px 32px;display:flex;flex-direction:column;gap:12px}.b p{margin:0;font-size:13px;opacity:.75}'
        '.b svg{max-width:100%;height:auto}</style></head><body>'
        + ''.join(bloques)
        + '<p style="padding:16px 32px;font-size:13px">Con "reducir movimiento" activado en el sistema, las dos quedan quietas en C con "appClub".</p>'
        '</body></html>\n'
    )


def generar_animacion(partes, inicio_club, ancho, geo, colores):
    return {
        'animacion/appclub-loop.svg': _svg('loop', partes, ancho, geo, colores),
        'animacion/appclub-una-vez.svg': _svg('una-vez', partes, ancho, geo, colores),
        'animacion/trazos.ts': _ts(partes, inicio_club, ancho, geo, colores),
        'animacion/demo.html': _demo(partes, ancho, geo, colores),
    }
