/**
 * TradeClaw — Empty State Component
 * Animated scanner visualization for empty states.
 */
import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing } from 'react-native';
import { colors, fonts, spacing } from '../theme';

export default function EmptyState() {
  const pulseAnim = useRef(new Animated.Value(0.3)).current;
  const lineAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Pulse animation for the background circle
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0.3,
          duration: 1500,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Scanning line animation
    Animated.loop(
      Animated.timing(lineAnim, {
        toValue: 100, // translate Y distance
        duration: 2000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  return (
    <View style={styles.container}>
      {/* Animated Radar visual */}
      <View style={styles.radarContainer}>
        <Animated.View style={[styles.radarCircle, { transform: [{ scale: pulseAnim }], opacity: pulseAnim.interpolate({ inputRange: [0.3, 1], outputRange: [0.1, 0] }) }]} />
        <Animated.View style={[styles.radarCircle, { transform: [{ scale: 0.6 }], opacity: 0.05 }]} />
        <View style={styles.radarCore} />
        <Animated.View style={[styles.scanLine, { transform: [{ translateY: lineAnim }] }]} />
      </View>
      
      <Text style={styles.title}>AWAITING SIGNALS</Text>
      <Text style={styles.subtitle}>Our engine is currently scanning 30 top Binance pairs for momentum spikes.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
    paddingHorizontal: spacing.xl,
  },
  radarContainer: {
    width: 120,
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xxl,
    overflow: 'hidden',
    borderRadius: 60,
  },
  radarCircle: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 2,
    borderColor: colors.primaryLight,
  },
  radarCore: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 5,
  },
  scanLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: colors.primaryLight,
    shadowColor: colors.primaryLight,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 1,
    shadowRadius: 5,
  },
  title: {
    fontSize: fonts.sizes.lg,
    fontWeight: fonts.weights.heavy,
    color: colors.textPrimary,
    marginBottom: spacing.md,
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: fonts.sizes.md,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: '80%',
  },
});
