# Videos de appClub

Cómo se hacen los videos cortos de la app: se graban en el celular, se les pone voz de locutora y se editan con `editar.py`, siempre con el mismo estilo. Los dos primeros (pago y cobro, en el sitio desde el 20/10/2026) son la referencia: `clips/337-pago.json` y `clips/341-cobro.json`.

El plan de todos los clips, con qué muestra cada uno y dónde se usa, está en `NicoPelos/appcarc-backend#335`.

## El estilo

| | |
|---|---|
| Formato | Horizontal **1920×1080**, 30 fps, con voz |
| Duración | **Entre 30 y 45 segundos**, ni menos ni más. El editor avisa si un clip queda afuera |
| Composición | Texto a la izquierda, celular con marco a la derecha, fondo `#14122E` |
| Arriba del texto | Etiqueta de la función en mayúsculas, amarillo `#FDE68A` (por ejemplo, "PAGOS DESDE EL CELULAR") |
| Texto en pantalla | Una frase corta por tramo, Manrope 800, `#EEF2FF`, que acompaña lo que dice la voz |
| Pie | `appclub.net.ar` en `#A5B4FC` |
| Placas | Cuando la voz dice algo que no tiene pantalla ("sin planillas…"): solo texto, las líneas aparecen de a una |
| Apertura | La pantalla de carga de la app (A → C) y el login del club demo |
| Cierre | La animación de appClub y "Más info en **appclub.net.ar**" |
| Sonido | La voz, normalizada a -16 LUFS. Sin música |

## Guion

- Explica **qué puede hacer la persona** con la función, no cómo está hecha. "El socio elige qué pagar y lo paga todo junto", no "se genera una preferencia de Mercado Pago".
- En **voseo** rioplatense, frases cortas, un tema por frase.
- Unas 80 a 110 palabras, para que la voz dure entre 27 y 40 segundos.
- Siempre termina con: **"Más info en app club punto net punto ar."** Escrito así, separado, para que la voz lo pronuncie bien. Lo mismo con "app club" en el resto del texto.
- **No prometer lo que no está.** Si el sitio dice que algo está "en desarrollo", el video no lo muestra como hecho.

## Voz

- **Locutora argentina**, voz femenina, tono claro y cálido, ritmo tranquilo.
- Generada en ElevenLabs (o grabada por una persona) a partir del guion, en mp3. El archivo se llama igual que el clip: `337-pago.mp3`.
- Revisar que pronuncie bien "app club", "DNI" y "Mercado Pago".

## Grabación (en el celular)

- **Siempre con el club demo** (usuarios `@demo.appclub.ar`; las contraseñas están en el manual público). Nunca con datos reales.
- Antes de grabar: **"No molestar"** activado, batería cargada y **"Mostrar toques"** en las opciones de desarrollador.
- Grabadora de pantalla del sistema, sin sonido, en la máxima resolución. Un archivo por clip, con el número del issue: `338-credencial.mp4`.
- Tocar con calma y dejar un segundo quieto al principio y al final de cada paso. Las esperas se aceleran en la edición.
- El pago y el cobro cambian los datos del demo, que se restablece a las 5 de la mañana: grabarlos una sola vez por día.

### Lo que nunca puede salir (revisar cada grabación)

- **Datos personales de quien graba**: el email en el aviso de Google Password Manager y en la barra de sugerencias del teclado, la pantalla de inicio del celular, las notificaciones.
- **La cuenta de Mercado Pago de quien graba**: el checkout muestra el límite disponible. El video corta en la pantalla amarilla del candado, antes de que cargue la cuenta.
- **Errores de la app que aparezcan en la toma**: se dejan afuera y se abre un issue (así salieron `appCARC-mobile#226` y `#227`).

## Edición

1. Pasar las grabaciones y la voz a una carpeta propia, por ejemplo `~/videos-appclub/`.
2. Ver la grabación cuadro por cuadro y medir las pausas de la voz:
   ```bash
   ffmpeg -i 337-pago.mp3 -af silencedetect=noise=-35dB:d=0.3 -f null - 2>&1 | grep silence_
   ```
   Cada frase del guion queda entre dos pausas. Si una frase no tiene pausa propia, se reparte por la cantidad de caracteres.
3. Escribir `clips/<clip>.json` copiando uno de los de referencia:
   - `tramos`: en orden. Un tramo `src` es un pedazo de una grabación (`archivo`, `ini` y `fin` en segundos) que dura `dur` segundos en el video final, con su `texto`. La velocidad sale sola de esos números. Los otros dos tipos de tramo son `placa` (con sus `lineas`) y `cierre`.
   - La suma de `dur` tiene que coincidir con la voz y quedar entre 30 y 45 s. El cierre arranca cuando la voz dice "Más info en…".
   - `subtitulos`: las frases del guion con sus tiempos, para el `.vtt` del sitio.
   - `recorte`: solo si se graba con otro celular. El de por defecto es el del POCO 7 Pro (1224×2712), sin la barra de estado ni la de navegación.
4. Editar:
   ```bash
   pip install fonttools pillow
   python3 brand/videos/editar.py 337-pago --fuentes ~/videos-appclub --salida ~/appclub-media
   ```
5. Revisar el resultado cuadro por cuadro (sobre todo los cortes y que no se cuele nada de la lista de arriba) y mostrarlo antes de publicar.

## Publicación

- **LinkedIn**: el `<clip>-narrado.mp4` tal cual.
- **Sitio**: agregar `--web assets/videos/<nombre>` desde la raíz del repo. Genera `.mp4`, `.webm`, la portada `-portada.webp` y los subtítulos `.vtt`, de menos de 1 MB cada video. Después, sumar el `<figure>` en "En video" de `index.html`, igual que los dos primeros (`preload="none"`, `poster`, las dos `<source>` y el `<track>`).
- Las grabaciones originales y los mp4 de LinkedIn no entran a git.
