# Marca appClub

Fuente única de los archivos de marca. La web, la app, la PWA, los paneles y los videos toman los archivos de acá y no los redibujan. Se generan con `generar.py` (ver al final). Para verlos todos juntos, en los dos temas, abrir `muestra.html` en el navegador.

La marca appClub es la de la **plataforma**: pantalla de carga, "Powered by", paneles, web y videos. La app de cada club muestra el logo del club; en el CARC, el del Club Andino Río Cuarto.

## Archivos

| Archivo | Para qué |
|---|---|
| `icono.svg` | Ícono principal: cuadrado índigo, C blanca, punto amarillo. Sobre fondos claros. |
| `icono-oscuro.svg` | Ícono para fondos oscuros: cuadrado `#818CF8` con la C en `#14122E`. El índigo de marca sobre `#14122E` da 2,3:1 y se pierde. |
| `icono-sin-fondo.svg` | Solo la C y el punto, en índigo, para usar sobre una superficie de color propia. |
| `icono-sin-fondo-oscuro.svg` | La C clara con el punto amarillo, para fondos oscuros. |
| `icono-mono.svg` | Una sola tinta (`currentColor`), con la C y el punto calados. |
| `wordmark.svg`, `wordmark-oscuro.svg`, `wordmark-mono.svg` | "appClub" en trazos: "app" en Manrope 500 y "Club" en Manrope 800. |
| `lockup.svg`, `lockup-oscuro.svg`, `lockup-mono.svg` | Ícono + wordmark en horizontal. |
| `favicon.svg` | Ícono que cambia solo con el tema del sistema (`prefers-color-scheme`). |
| `tokens.css` | Colores de la web y los paneles, en tema claro y oscuro, con sus contrastes. |
| `png/` | PNG para los usos que no aceptan SVG (ver abajo). |
| `fuentes/` | Manrope 500 y 800 (licencia OFL, en `fuentes/OFL.txt`). Solo las usa el generador. |

Las versiones `-mono` usan `currentColor`: insertadas inline en el HTML toman el color del texto. Como `<img>`, salen negras.

## Colores

| | Claro | Oscuro |
|---|---|---|
| Marca | índigo `#4338CA` + amarillo `#FDE68A` | |
| "app" en el wordmark | `#4338CA` | `#A5B4FC` |
| "Club" en el wordmark | `#1E1B4B` | `#EEF2FF` |

Los colores de interfaz están en `tokens.css`. El amarillo es resalte: en tema claro va como fondo o decoración, nunca como texto (1,2:1). En tema oscuro también sirve como texto (14,6:1).

## Tipografía

El wordmark usa **Manrope** (500 y 800), convertida a trazos: los SVG no dependen de ninguna fuente instalada. La web sigue usando Archivo y Public Sans para los textos; el wordmark es un dibujo, no texto.

## Zona de respeto y tamaño mínimo

- **Zona de respeto**: alrededor del ícono o del lockup, dejar libre al menos **un cuarto del lado del ícono** (30 sobre 120). Nada de texto ni bordes ahí.
- **Tamaño mínimo**: ícono de **16 px** (favicon; a ese tamaño el punto casi no se ve, y está bien) y lockup de **24 px de alto**. Debajo de 24 px, usar solo el ícono.
- No estirar, no rotar (salvo la animación A → C, ver issue #3), no cambiar los colores fuera de las variantes de esta carpeta, no ponerle sombra ni contorno.

## PNG

| Archivo | Uso |
|---|---|
| `png/icono-16.png` a `icono-64.png` | Favicon de respaldo, accesos directos |
| `png/apple-touch-icon-180.png` | `apple-touch-icon`: cuadrado lleno, sin transparencia (iOS rellena de negro las esquinas transparentes) |
| `png/icono-192.png`, `icono-512.png` | Manifest de la PWA |
| `png/icono-oscuro-192.png`, `icono-oscuro-512.png` | Variante oscura para la PWA o fondos oscuros |
| `png/icono-1024.png` | Original grande, con esquinas redondeadas |
| `png/icono-ios-1024.png` | iOS: cuadrado lleno, sin transparencia ni esquinas (iOS aplica la máscara) |
| `png/lockup-alto240.png`, `lockup-oscuro-alto240.png` | Documentos, presentaciones y redes |

Los íconos adaptativos de Android (primer plano de 432 px dentro del círculo central, monocromo, notificaciones) dependen de la configuración de build de la app y se arman en el issue #5.

## Regenerar

```bash
pip install fonttools uharfbuzz cairosvg
python3 brand/generar.py
```

Colores, medidas del ícono, pesos de la fuente y separación del lockup son constantes al principio de `generar.py`. Para cambiar algo, cambiarlo ahí y volver a generar; no editar los SVG a mano.

## Publicación

La carpeta está en `.assetsignore`: no se publica en appclub.net.ar. Lo que la web necesite (favicon, `apple-touch-icon`, imagen para compartir) se copia a la raíz del sitio en el issue #4.
