/**
 * TradeClaw — Stats Screen
 * Premium analytics panel for system performance overview.
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, fonts, spacing, borderRadius } from '../theme';
import { fetchHealth, fetchSignals } from '../services/api';

function StatCard({ label, value, color = colors.textPrimary, isLarge = false }) {
  return (
    <LinearGradient
      colors={[colors.bgCardElevated, colors.bgCard]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.card, isLarge && styles.cardLarge]}
    >
      <View style={[styles.glowLine, { backgroundColor: color, shadowColor: color }]} />
      <Text style={styles.cardLabel}>{label}</Text>
      <Text style={[styles.cardValue, isLarge && styles.cardValueLarge, { color }]}>{value}</Text>
    </LinearGradient>
  );
}

export default function StatsScreen() {
  const insets = useSafeAreaInsets();
  const [stats, setStats] = useState({
    signalsToday: 0,
    sniperCount: 0,
    avgScore: 0,
    lastScan: null,
    backendStatus: 'CONNECTING...',
  });

  const loadStats = async () => {
    const healthResult = await fetchHealth();
    const signalsResult = await fetchSignals();

    let backendStatus = 'OFFLINE';
    let signalsToday = 0;
    let lastScan = null;
    let sniperCount = 0;
    let avgScore = 0;

    if (!healthResult.error && healthResult.data) {
      signalsToday = healthResult.data.signals_today || 0;
      lastScan = healthResult.data.last_scan;
      backendStatus = 'ONLINE';
    }

    if (!signalsResult.error && signalsResult.data) {
      const activeSignals = signalsResult.data;
      sniperCount = activeSignals.filter(s => s.confidence === 'SNIPER').length;
      if (activeSignals.length > 0) {
        avgScore = Math.round(
          activeSignals.reduce((sum, s) => sum + s.score, 0) / activeSignals.length
        );
      }
    }

    setStats({
      signalsToday,
      sniperCount,
      avgScore,
      lastScan,
      backendStatus,
    });
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatLastScan = () => {
    if (!stats.lastScan) return 'NEVER';
    const date = new Date(stats.lastScan * 1000);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 80 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>NETWORK OPS</Text>
          <Text style={styles.subtitle}>System Telemetry & Performance</Text>
        </View>

        <View style={styles.statusBanner}>
          <View style={[
            styles.statusDot, 
            { backgroundColor: stats.backendStatus === 'ONLINE' ? colors.success : colors.danger,
              shadowColor: stats.backendStatus === 'ONLINE' ? colors.success : colors.danger }
          ]} />
          <Text style={styles.statusBannerText}>ENGINE {stats.backendStatus}</Text>
        </View>

        <View style={styles.grid}>
          <View style={styles.row}>
            <StatCard label="SIGNALS TODAY" value={stats.signalsToday} isLarge={true} color={colors.primaryLight} />
          </View>
          <View style={styles.row}>
            <View style={styles.flexHalf}>
              <StatCard label="🎯 SNIPERS" value={stats.sniperCount} color={colors.sniper} />
            </View>
            <View style={styles.flexHalf}>
              <StatCard label="AVG SCORE" value={stats.avgScore || '—'} />
            </View>
          </View>
          <View style={styles.row}>
            <StatCard label="LAST MARKET SCAN" value={formatLastScan()} />
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    padding: spacing.xl,
  },
  header: {
    marginBottom: spacing.xl,
  },
  title: {
    fontSize: fonts.sizes.xl,
    fontWeight: fonts.weights.black,
    color: colors.textPrimary,
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: fonts.sizes.sm,
    color: colors.textSecondary,
    letterSpacing: 0.5,
    marginTop: 4,
  },
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bgCardElevated,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.xxl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.md,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 5,
  },
  statusBannerText: {
    fontSize: fonts.sizes.sm,
    fontWeight: fonts.weights.bold,
    color: colors.textPrimary,
    letterSpacing: 1,
  },
  grid: {
    gap: spacing.lg,
  },
  row: {
    flexDirection: 'row',
    gap: spacing.lg,
  },
  flexHalf: {
    flex: 1,
  },
  card: {
    flex: 1,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  cardLarge: {
    paddingVertical: spacing.xxl,
  },
  glowLine: {
    position: 'absolute',
    top: 0, left: 0, bottom: 0,
    width: 3,
    shadowOffset: { width: 4, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
  },
  cardLabel: {
    fontSize: 10,
    fontWeight: fonts.weights.heavy,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    letterSpacing: 1,
  },
  cardValue: {
    fontSize: fonts.sizes.xl,
    fontWeight: fonts.weights.black,
  },
  cardValueLarge: {
    fontSize: fonts.sizes.xxxl,
    letterSpacing: -1,
  },
});
