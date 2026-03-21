/**
 * TradeClaw — Countdown Timer Component
 * Animated countdown component with pulsing effect when nearing expiration.
 */
import React, { useState, useEffect, useRef } from 'react';
import { Text, StyleSheet, Animated } from 'react-native';
import { colors, fonts } from '../theme';
import { formatCountdown } from '../utils/formatting';

export default function CountdownTimer({ expiryAt, onExpire, style }) {
  const [display, setDisplay] = useState(formatCountdown(expiryAt));
  const intervalRef = useRef(null);
  
  // Animation value for pulsing effect (< 5 mins left)
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Track if we are currently pulsing to avoid re-triggering the loop
  const isPulsing = useRef(false);

  useEffect(() => {
    const tick = () => {
      const text = formatCountdown(expiryAt);
      setDisplay(text);
      
      const now = Math.floor(Date.now() / 1000);
      const remaining = expiryAt - now;

      if (remaining <= 0) {
        clearInterval(intervalRef.current);
        onExpire && onExpire();
        return;
      }

      // Start pulsing if < 5 minutes (300 seconds)
      if (remaining < 300 && remaining > 0) {
        if (!isPulsing.current) {
          isPulsing.current = true;
          Animated.loop(
            Animated.sequence([
              Animated.timing(pulseAnim, {
                toValue: 0.4,
                duration: 500,
                useNativeDriver: true,
              }),
              Animated.timing(pulseAnim, {
                toValue: 1,
                duration: 500,
                useNativeDriver: true,
              }),
            ])
          ).start();
        }
      } else {
        if (isPulsing.current) {
          isPulsing.current = false;
          pulseAnim.stopAnimation();
          pulseAnim.setValue(1);
        }
      }
    };

    tick(); // Initial call
    intervalRef.current = setInterval(tick, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      pulseAnim.stopAnimation();
    };
  }, [expiryAt]);

  const isExpiring = (() => {
    const now = Math.floor(Date.now() / 1000);
    return (expiryAt - now) < 300 && (expiryAt - now) > 0;
  })();

  const isExpired = display === 'EXPIRED';

  return (
    <Animated.Text style={[
      styles.timer,
      isExpiring && styles.expiring,
      isExpired && styles.expired,
      isExpiring && { opacity: pulseAnim },
      style,
    ]}>
      {display}
    </Animated.Text>
  );
}

const styles = StyleSheet.create({
  timer: {
    fontSize: fonts.sizes.sm,
    fontWeight: fonts.weights.bold,
    color: colors.textPrimary,
    fontVariant: ['tabular-nums'],
    letterSpacing: 0.5,
  },
  expiring: {
    color: colors.warning,
  },
  expired: {
    color: colors.danger,
    opacity: 0.4,
  },
});
