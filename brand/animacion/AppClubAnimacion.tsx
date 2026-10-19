/**
 * Animación de marca appClub (A → C, "app" → "appClub") para React Native / Expo.
 *
 * Copiar este archivo y trazos.ts a la app. Requiere react-native-svg,
 * react-native-reanimated 4 y react-native-worklets (vienen con Expo SDK 56). Mismos tiempos que
 * appclub-loop.svg y appclub-una-vez.svg: ver brand/README.md, sección Animación.
 *
 *   <AppClubAnimacion modo="una-vez" alto={56} />                  // splash: queda en C
 *   <AppClubAnimacion modo="loop" alto={40} cargando />            // mientras se espera algo
 *   <AppClubAnimacion modo="una-vez" tema="oscuro" onFin={...} />  // avisa al terminar
 *
 * Con "reducir movimiento" activado en el teléfono queda quieta en C con "appClub".
 */
import React, { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  cancelAnimation,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import {
  ANCHO,
  APP_PATH,
  APP_X0,
  BARRA,
  BARRA_TRAZO,
  CLUB_PATH,
  CLUB_X0,
  COLORES,
  C_PATH,
  DURACION_MS,
  FASES,
  LADO,
  PUNTO,
  RADIO,
  TRAZO,
} from './trazos';

type Props = {
  modo?: 'loop' | 'una-vez';
  tema?: 'claro' | 'oscuro';
  /** Alto en puntos; el ancho sale de la proporción del lockup. */
  alto?: number;
  /** Úsalo cuando la animación indica que algo está cargando (lo anuncia el lector de pantalla). */
  cargando?: boolean;
  /** Solo en modo "una-vez": se llama al llegar a C. */
  onFin?: () => void;
};

/** Avance 0..1 dentro de una fase, con la curva ease-in-out de CSS aproximada. */
function fase(p: number, desde: number, hasta: number) {
  'worklet';
  const t = Math.min(1, Math.max(0, (p - desde) / (hasta - desde)));
  return t * t * (3 - 2 * t);
}

export default function AppClubAnimacion({ modo = 'una-vez', tema = 'claro', alto = 48, cargando = false, onFin }: Props) {
  const reducir = useReducedMotion();
  const p = useSharedValue(reducir ? 1 : 0);
  const colores = COLORES[tema];
  const escala = alto / LADO;

  useEffect(() => {
    if (reducir) {
      p.value = 1;
      if (modo === 'una-vez') onFin?.();
      return;
    }
    p.value = 0;
    const lineal = { duration: DURACION_MS, easing: Easing.linear };
    if (modo === 'loop') {
      p.value = withRepeat(withTiming(1, lineal), -1, true);
    } else {
      p.value = withTiming(1, lineal, (terminado) => {
        if (terminado && onFin) scheduleOnRN(onFin);
      });
    }
    return () => cancelAnimation(p);
    // onFin no reinicia la animación a propósito
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modo, reducir]);

  const estiloGiro = useAnimatedStyle(() => ({
    transform: [{ rotate: `${90 * (1 - fase(p.value, ...FASES.giro))}deg` }],
  }));
  const estiloBarra = useAnimatedStyle(() => ({ opacity: 1 - fase(p.value, ...FASES.barra) }));
  const estiloPunto = useAnimatedStyle(() => ({ opacity: fase(p.value, ...FASES.punto) }));

  const anchoApp = (CLUB_X0 - APP_X0) * escala;
  const anchoClub = (ANCHO - CLUB_X0) * escala;
  const estiloClubRecorte = useAnimatedStyle(() => ({ width: anchoClub * fase(p.value, ...FASES.club) }));
  const estiloClub = useAnimatedStyle(() => {
    const t = fase(p.value, ...FASES.club);
    return { opacity: t, transform: [{ translateX: -6 * escala * (1 - t) }] };
  });

  const capa = { width: alto, height: alto };
  return (
    <View
      style={[styles.fila, { height: alto }]}
      accessible
      accessibilityRole={cargando ? 'progressbar' : 'image'}
      accessibilityLabel={cargando ? 'Cargando' : 'appClub'}
      accessibilityState={cargando ? { busy: true } : undefined}
    >
      <View style={capa}>
        <Svg width={alto} height={alto} viewBox={`0 0 ${LADO} ${LADO}`} style={StyleSheet.absoluteFill}>
          <Rect width={LADO} height={LADO} rx={RADIO} fill={colores.cuadrado} />
        </Svg>
        {/* Gira el dibujo; el cuadrado queda quieto */}
        <Animated.View style={[StyleSheet.absoluteFill, estiloGiro]}>
          <Svg width={alto} height={alto} viewBox={`0 0 ${LADO} ${LADO}`} style={StyleSheet.absoluteFill}>
            <Path d={C_PATH} fill="none" stroke={colores.c} strokeWidth={TRAZO} strokeLinecap="round" strokeLinejoin="round" />
          </Svg>
          <Animated.View style={[StyleSheet.absoluteFill, estiloBarra]}>
            <Svg width={alto} height={alto} viewBox={`0 0 ${LADO} ${LADO}`}>
              <Path d={BARRA} fill="none" stroke={colores.c} strokeWidth={BARRA_TRAZO} strokeLinecap="round" />
            </Svg>
          </Animated.View>
          <Animated.View style={[StyleSheet.absoluteFill, estiloPunto]}>
            <Svg width={alto} height={alto} viewBox={`0 0 ${LADO} ${LADO}`}>
              <Circle cx={PUNTO.cx} cy={PUNTO.cy} r={PUNTO.r} fill={colores.punto} />
            </Svg>
          </Animated.View>
        </Animated.View>
      </View>
      <View style={{ width: (APP_X0 - LADO) * escala }} />
      <Svg width={anchoApp} height={alto} viewBox={`${APP_X0} 0 ${CLUB_X0 - APP_X0} ${LADO}`}>
        <Path d={APP_PATH} fill={colores.app} />
      </Svg>
      <Animated.View style={[styles.recorte, { height: alto }, estiloClubRecorte]}>
        <Animated.View style={estiloClub}>
          <Svg width={anchoClub} height={alto} viewBox={`${CLUB_X0} 0 ${ANCHO - CLUB_X0} ${LADO}`}>
            <Path d={CLUB_PATH} fill={colores.club} />
          </Svg>
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  fila: { flexDirection: 'row', alignItems: 'center' },
  recorte: { overflow: 'hidden' },
});
