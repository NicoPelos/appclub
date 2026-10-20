#!/usr/bin/env python3
"""Edita los videos de appClub con el estilo de la marca (ver README.md de esta carpeta).

    python3 brand/videos/editar.py 337-pago --fuentes ~/videos-appclub --salida ~/appclub-media
    python3 brand/videos/editar.py 337-pago --fuentes ~/videos-appclub --salida ~/appclub-media --web assets/videos/pago

Cada clip se define en clips/<clip>.json: qué tramos de qué grabación, cuánto dura cada
tramo (lo que dura su frase en la voz), el texto en pantalla, las placas, el cierre y los
subtítulos. Salida: <clip>-narrado.mp4 (1920x1080, con voz). Con --web, además, la versión
liviana para el sitio: .mp4, .webm, portada .webp y subtítulos .vtt.

Requiere ffmpeg, fonttools y Pillow (pip install fonttools pillow).
"""
import argparse
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
BRAND = AQUI.parent
CIERRE = BRAND / 'animacion' / 'video' / 'appclub-una-vez-oscuro.mp4'

# Estilo (no cambiar por clip: es lo que hace que todos se vean iguales)
FONDO, TEXTO, SUAVE, AMARILLO = '0x14122E', '0xEEF2FF', '0xA5B4FC', '0xFDE68A'
ANCHO, ALTO, FPS = 1920, 1080, 30
ALTO_PANTALLA, BISEL = 900, 18           # celular: alto de pantalla y bisel del marco
MARGEN = 150                              # margen izquierdo del texto y derecho del celular
TEXTO_Y, ETIQUETA_Y, ETIQUETA_PLACA_Y, PIE_Y = 360, 300, 330, 960
TAM_TEXTO, TAM_ETIQUETA, TAM_PLACA = 70, 30, 84
CORTE_TEXTO = 22                          # caracteres por línea del texto en pantalla
RECORTE_POCO = [1224, 2470, 0, 110]       # POCO 7 Pro: sin barra de estado ni de navegación


def run(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *map(str, args)], check=True)


def duracion(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


class Editor:
    def __init__(self, clip, fuentes, tmp):
        self.c, self.fuentes, self.tmp = clip, fuentes, tmp
        cw, ch, _, _ = clip.get('recorte', RECORTE_POCO)
        self.sh = ALTO_PANTALLA
        self.sw = round(self.sh * cw / ch / 2) * 2
        self.px = ANCHO - MARGEN - (self.sw + 2 * BISEL)
        self.py = (ALTO - (self.sh + 2 * BISEL)) // 2
        self.f800, self.f500 = (self._ttf(p) for p in (800, 500))
        self.marco = self._marco()
        self.n = 0

    def _ttf(self, peso):
        f = TTFont(BRAND / 'fuentes' / f'manrope-latin-{peso}-normal.woff')
        f.flavor = None
        out = self.tmp / f'manrope-{peso}.ttf'
        f.save(out)
        return out

    def _marco(self):
        s, w, h = 4, self.sw + 2 * BISEL, self.sh + 2 * BISEL
        im = Image.new('RGBA', (w * s, h * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=62 * s, fill=(11, 10, 31, 255),
                            outline=(49, 46, 129, 255), width=3 * s)
        d.rounded_rectangle([BISEL * s, BISEL * s, (BISEL + self.sw) * s - 1, (BISEL + self.sh) * s - 1],
                            radius=44 * s, fill=(0, 0, 0, 0))
        cx = w * s // 2
        d.ellipse([cx - 7 * s, (BISEL + 12) * s, cx + 7 * s, (BISEL + 26) * s], fill=(11, 10, 31, 255))
        out = self.tmp / 'marco.png'
        im.resize((w, h), Image.LANCZOS).save(out)
        return out

    def _txt(self, contenido):
        self.n += 1
        p = self.tmp / f't{self.n}.txt'
        p.write_text(contenido, encoding='utf-8')
        return p

    def _comunes(self, y=ETIQUETA_Y):
        e = self._txt(self.c['etiqueta'].upper())
        return (f"drawtext=fontfile={self.f800}:textfile={e}:fontsize={TAM_ETIQUETA}:fontcolor={AMARILLO}:x={MARGEN}:y={y},"
                f"drawtext=fontfile={self.f500}:text='appclub.net.ar':fontsize=32:fontcolor={SUAVE}:x={MARGEN}:y={PIE_Y}")

    def src(self, t, out):
        vel = (t['fin'] - t['ini']) / t['dur']
        cw, ch, cx, cy = t.get('recorte', self.c.get('recorte', RECORTE_POCO))
        texto = self._txt(textwrap.fill(t['texto'], CORTE_TEXTO))
        fc = (
            f"[0:v]trim={t['ini']}:{t['fin']},setpts=(PTS-STARTPTS)/{vel},fps={FPS},crop={cw}:{ch}:{cx}:{cy},"
            f"scale={self.sw}:{self.sh},pad={ANCHO}:{ALTO}:{self.px + BISEL}:{self.py + BISEL}:color={FONDO}[v];"
            f"[v][1:v]overlay={self.px}:{self.py},{self._comunes()},"
            f"drawtext=fontfile={self.f800}:textfile={texto}:fontsize={TAM_TEXTO}:fontcolor={TEXTO}:line_spacing=14:x={MARGEN}:y={TEXTO_Y},"
            f"trim=duration={t['dur']},format=yuv420p,setsar=1[out]"
        )
        run('-i', self.fuentes / t['archivo'], '-i', self.marco, '-filter_complex', fc, '-map', '[out]', '-an',
            '-c:v', 'libx264', '-crf', '18', out)

    def placa(self, t, out):
        paso = t['dur'] / (len(t['lineas']) + 0.5)
        capas = [self._comunes(ETIQUETA_PLACA_Y)]
        for j, linea in enumerate(t['lineas']):
            capas.append(f"drawtext=fontfile={self.f800}:textfile={self._txt(linea)}:fontsize={TAM_PLACA}:"
                         f"fontcolor={TEXTO}:x={MARGEN}:y={400 + j * 120}:enable='gte(t,{j * paso:.2f})'")
        run('-f', 'lavfi', '-i', f"color=c={FONDO}:s={ANCHO}x{ALTO}:r={FPS}:d={t['dur']}",
            '-vf', ','.join(capas) + ',format=yuv420p', '-c:v', 'libx264', '-crf', '18', out)

    def cierre(self, t, out):
        vf = (
            f"setpts=PTS*{t['dur'] / 4.6:.4f},fps={FPS},scale=720:720,pad={ANCHO}:{ALTO}:600:120:color={FONDO},"
            f"drawtext=fontfile={self.f500}:text='Más info en':fontsize=44:fontcolor={SUAVE}:x=(w-text_w)/2:y=830,"
            f"drawtext=fontfile={self.f800}:text='appclub.net.ar':fontsize=64:fontcolor={TEXTO}:x=(w-text_w)/2:y=890,"
            f"tpad=stop_mode=clone:stop_duration=2,trim=duration={t['dur']},format=yuv420p,setsar=1"
        )
        run('-i', CIERRE, '-vf', vf, '-an', '-c:v', 'libx264', '-crf', '18', out)

    def armar(self, voz, final):
        partes = []
        for i, t in enumerate(self.c['tramos']):
            out = self.tmp / f'p{i:02d}.mp4'
            getattr(self, t['tipo'])(t, out)
            partes.append(out)
        lista = self.tmp / 'lista.txt'
        lista.write_text(''.join(f"file '{p}'\n" for p in partes))
        video = self.tmp / 'video.mp4'
        run('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', video)
        # voz normalizada para redes (-16 LUFS); manda la duración del video
        run('-i', video, '-i', voz, '-filter_complex', '[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,apad[a]',
            '-map', '0:v', '-map', '[a]', '-shortest', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
            '-movflags', '+faststart', final)


def vtt(subtitulos, destino):
    lineas = ['WEBVTT', '']
    for ini, fin, texto in subtitulos:
        lineas += [f'{ini} --> {fin}', texto, '']
    destino.write_text('\n'.join(lineas), encoding='utf-8')


def web(final, base, portada_s):
    base.parent.mkdir(parents=True, exist_ok=True)
    run('-i', final, '-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', base.with_suffix('.mp4'))
    run('-i', final, '-vf', 'scale=1280:720', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '36', '-row-mt', '1',
        '-c:a', 'libopus', '-b:a', '80k', base.with_suffix('.webm'))
    run('-ss', portada_s, '-i', final, '-frames:v', '1', '-vf', 'scale=1280:720', '-c:v', 'libwebp', '-quality', '80',
        base.parent / f'{base.name}-portada.webp')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('clip', help='nombre del clip (clips/<clip>.json)')
    ap.add_argument('--fuentes', type=Path, required=True, help='carpeta con las grabaciones y la voz')
    ap.add_argument('--salida', type=Path, required=True, help='carpeta de salida (fuera de git)')
    ap.add_argument('--web', type=Path, help='base de la versión del sitio, ej. assets/videos/pago')
    a = ap.parse_args()

    clip = json.loads((AQUI / 'clips' / f'{a.clip}.json').read_text(encoding='utf-8'))
    total = sum(t['dur'] for t in clip['tramos'])
    if not 30 <= total <= 45:
        print(f'Aviso: dura {total:.1f} s; el estilo pide entre 30 y 45 s.')
    a.salida.mkdir(parents=True, exist_ok=True)
    final = a.salida / f'{a.clip}-narrado.mp4'
    with tempfile.TemporaryDirectory() as tmp:
        Editor(clip, a.fuentes.expanduser(), Path(tmp)).armar(a.fuentes.expanduser() / clip['voz'], final)
    print(f'{final} ({duracion(final):.1f} s)')
    if a.web:
        web(final, a.web, clip.get('portada_s', 8))
        vtt(clip['subtitulos'], a.web.with_suffix('.vtt'))
        print(f'web: {a.web}.mp4 / .webm / -portada.webp / .vtt')


if __name__ == '__main__':
    main()
