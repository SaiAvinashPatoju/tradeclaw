/**
 * TradeClaw — Status Bar Component
 * Top indicator showing network status and signal count.
 */
import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { colors, fonts, spacing } from '../theme';
import { fetchHealth } from '../services/api';

export default function StatusIndicator({ signalCount = 0 }) {
  const [isLive, setIsLive] = useState(false);
  const intervalRef = useRef(null);
  
  // Subtle pulse for the live dot
  const dotAnim = useRef(new Animated.Value(1)).current;

  const checkHealth = async () => {
    const result = await fetchHealth();
    setIsLive(!result.error && result.data?.status === 'ok');
  };

  useEffect(() => {
    checkHealth();
    intervalRef.current = setInterval(checkHealth, 30000);

    Animated.loop(
      Animated.sequence([
        Animated.timing(dotAnim, { toValue: 0.4, duration: 1000, useNativeDriver: true }),
        Animated.timing(dotAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ])
    ).start();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.statusRow}>
        <Animated.View style={[
          styles.dot, 
          { backgroundColor: isLive ? colors.statusLive : colors.statusOffline },
          isLive && { opacity: dotAnim }
        ]} />
        <Text style={styles.statusText}>
          {isLive ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
        </Text>
      </View>
      <View style={styles.countBadge}>
        <Text style={styles.countText}>
          {signalCount} ACTIVES
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    backgroundColor: 'transparent',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: fonts.weights.heavy,
    color: colors.textSecondary,
    letterSpacing: 1.5,
  },
  countBadge: {
    backgroundColor: 'rgba(139, 92, 246, 0.1)',
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(139, 92, 246, 0.3)',
  },
  countText: {
    fontSize: 9,
    fontWeight: fonts.weights.heavy,
    color: colors.primaryLight,
    letterSpacing: 1,
  },
});
