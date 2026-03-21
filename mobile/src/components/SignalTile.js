/**
 * TradeClaw — Signal Tile Component
 * Premium glassmorphism card with dynamic glow, deep linking and haptic tiers.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Alert, Animated, Easing
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, fonts, spacing, borderRadius, confidenceColors, shadows } from '../theme';
import CountdownTimer from './CountdownTimer';
import { formatPrice, formatEntryRange, formatSymbol } from '../utils/formatting';
import { openBinance } from '../utils/deeplink';
import { scheduleExitReminder } from '../services/notifications';

export default function SignalTile({ signal, onExpire, index = 0 }) {
  const [reminderSet, setReminderSet] = useState(false);
  const tier = confidenceColors[signal.confidence] || confidenceColors.MODERATE;
  
  // Entry animation
  const slideAnim = useRef(new Animated.Value(50)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 100, // Staggered entry
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        delay: index * 100,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      })
    ]).start();
  }, []);

  const handleExitAlert = () => {
    // Custom haptic per tier when opening options
    if (signal.confidence === 'SNIPER') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    } else {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    Alert.alert(
      'Set Action Timer',
      `Check ${formatSymbol(signal.symbol)} chart in:`,
      [
        { text: '5 min', onPress: () => setReminder(5) },
        { text: '10 min', onPress: () => setReminder(10) },
        { text: '15 min', onPress: () => setReminder(15) },
        { text: '20 min', onPress: () => setReminder(20) }, // Added 4th option to be closer to "custom"
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const setReminder = async (minutes) => {
    await scheduleExitReminder(formatSymbol(signal.symbol), minutes);
    setReminderSet(true);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  const handleBinance = () => {
    openBinance(signal.symbol);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
  };

  // Select the appropriate shadow based on confidence
  const glowStyle = 
    signal.confidence === 'SNIPER' ? shadows.glowSniper :
    signal.confidence === 'HIGH' ? shadows.glowHigh : 
    shadows.glowModerate;

  return (
    <Animated.View style={[
      styles.cardWrapper,
      glowStyle,
      { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
    ]}>
      <LinearGradient
        colors={[colors.bgCardElevated, colors.bgCard]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[
          styles.cardInner,
          { borderColor: tier.border }
        ]}
      >
        {/* Glow Top Accent */}
        <View style={[styles.glowBar, { backgroundColor: tier.text }]} />

        {/* Header Row */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={[styles.badge, { backgroundColor: tier.bg, borderColor: tier.border }]}>
              <Text style={[styles.badgeText, { color: tier.text }]}>
                {tier.emoji} {signal.confidence}
              </Text>
            </View>
            <Text style={styles.symbol}>{formatSymbol(signal.symbol)}</Text>
          </View>
          <View style={styles.timerWrap}>
            <Text style={styles.timerLabel}>EXPIRES IN</Text>
            <CountdownTimer expiryAt={signal.expiry_at} onExpire={() => onExpire && onExpire(signal.id)} />
          </View>
        </View>

        {/* Target/Stop Data Grid - High contrast vs the rest */}
        <View style={styles.targetGrid}>
           <View style={styles.targetCol}>
             <Text style={styles.targetColLabel}>ENTRY ZONE</Text>
             <Text style={styles.entryValue}>{formatEntryRange(signal.entry_low, signal.entry_high)}</Text>
           </View>
           <View style={styles.targetColRight}>
             <View style={styles.pctRow}>
               <Text style={[styles.pctLabel, {color: colors.success}]}>TP</Text>
               <Text style={[styles.pctValue, {color: colors.success}]}>+{signal.target_pct}%</Text>
             </View>
             <View style={styles.pctRow}>
               <Text style={[styles.pctLabel, {color: colors.danger}]}>SL</Text>
               <Text style={[styles.pctValue, {color: colors.danger}]}>-{signal.stop_loss_pct}%</Text>
             </View>
           </View>
        </View>

        {/* Metrics Row (Small text) */}
        <View style={styles.metricsRow}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>SCORE</Text>
            <Text style={[styles.metricValue, {color: tier.text}]}>{signal.score}</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>RSI</Text>
            <Text style={styles.metricValue}>{signal.rsi?.toFixed(0) || '—'}</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>VOL</Text>
            <Text style={styles.metricValue}>{signal.volume_spike?.toFixed(1) || '—'}x</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>BTC</Text>
            <Text style={[styles.metricValue, 
               signal.btc_regime === 'UP' ? {color: colors.success} : 
               signal.btc_regime === 'DOWN' ? {color: colors.danger} : null
            ]}>{signal.btc_regime || '—'}</Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.btn, reminderSet ? styles.btnAlertSet : styles.btnAlert]}
            onPress={handleExitAlert}
            activeOpacity={0.8}
          >
            <Text style={[styles.btnText, reminderSet ? styles.btnTextSet : styles.btnTextAlert]}>
              {reminderSet ? '✓ TIMER SET' : 'T SET TIMER'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.btnBinance]}
            onPress={handleBinance}
            activeOpacity={0.8}
          >
            <Text style={[styles.btnText, styles.btnTextBinance]}>TRADE</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  cardWrapper: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.lg,
  },
  cardInner: {
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    padding: spacing.xl,
    paddingTop: spacing.xl + 4,
    overflow: 'hidden',
  },
  glowBar: {
    position: 'absolute',
    top: 0,
    left: 20,
    right: 20,
    height: 2,
    borderBottomLeftRadius: 4,
    borderBottomRightRadius: 4,
    opacity: 0.8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.xl,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  badge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: fonts.sizes.xs,
    fontWeight: fonts.weights.heavy,
    letterSpacing: 0.8,
  },
  symbol: {
    fontSize: fonts.sizes.xl,
    fontWeight: fonts.weights.black,
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  timerWrap: {
    alignItems: 'flex-end',
  },
  timerLabel: {
    fontSize: 9,
    color: colors.textMuted,
    fontWeight: fonts.weights.bold,
    letterSpacing: 1,
    marginBottom: 2,
  },
  targetGrid: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0,0,0,0.2)',
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.03)',
  },
  targetCol: {
    flex: 3,
    justifyContent: 'center',
  },
  targetColRight: {
    flex: 2,
    alignItems: 'flex-end',
    borderLeftWidth: 1,
    borderLeftColor: colors.border,
    paddingLeft: spacing.md,
  },
  targetColLabel: {
    fontSize: 10,
    color: colors.textSecondary,
    fontWeight: fonts.weights.bold,
    letterSpacing: 1,
    marginBottom: 4,
  },
  entryValue: {
    fontSize: fonts.sizes.lg,
    fontWeight: fonts.weights.semibold,
    color: colors.textPrimary,
    letterSpacing: 0.5,
  },
  pctRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: spacing.sm,
    marginBottom: 2,
  },
  pctLabel: {
    fontSize: fonts.sizes.xs,
    fontWeight: fonts.weights.bold,
    opacity: 0.7,
  },
  pctValue: {
    fontSize: fonts.sizes.md,
    fontWeight: fonts.weights.heavy,
    width: 50,
    textAlign: 'right',
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.sm,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 9,
    color: colors.textMuted,
    fontWeight: fonts.weights.bold,
    letterSpacing: 1,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: fonts.sizes.sm,
    fontWeight: fonts.weights.bold,
    color: colors.textSecondary,
  },
  metricDivider: {
    width: 1,
    height: 12,
    backgroundColor: colors.border,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  btn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  btnAlert: {
    backgroundColor: 'transparent',
    borderColor: colors.border,
  },
  btnAlertSet: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  btnText: {
    fontSize: fonts.sizes.sm,
    fontWeight: fonts.weights.heavy,
    letterSpacing: 1,
  },
  btnTextAlert: {
    color: colors.textSecondary,
  },
  btnTextSet: {
    color: colors.success,
  },
  btnBinance: {
    backgroundColor: '#FCD535', // Binance yellow
    borderColor: '#FCD535',
  },
  btnTextBinance: {
    color: '#000000', // Black text for high contrast on yellow
  },
});
