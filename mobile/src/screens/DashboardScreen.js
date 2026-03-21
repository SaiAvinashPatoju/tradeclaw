/**
 * TradeClaw — Dashboard Screen
 * High-performance list of signal tiles with pull-to-refresh and glassmorphism.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { View, FlatList, StyleSheet, RefreshControl, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, fonts, spacing } from '../theme';
import StatusIndicator from '../components/StatusBar';
import SignalTile from '../components/SignalTile';
import EmptyState from '../components/EmptyState';
import { fetchSignals } from '../services/api';
import { getSettings } from '../services/storage';

const POLL_INTERVAL = 15000;

export default function DashboardScreen() {
  const [signals, setSignals] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [settings, setSettings] = useState(null);
  const intervalRef = useRef(null);
  const insets = useSafeAreaInsets();
  
  // For staggering animations, we keep track of old keys
  const knownIdsRef = useRef(new Set());

  const loadSignals = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    const result = await fetchSignals();
    if (!result.error && result.data) {
      const currentSettings = settings || await getSettings();
      let filtered = result.data;

      if (currentSettings?.minConfidence) {
        const tiers = { SNIPER: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
        const minTier = tiers[currentSettings.minConfidence] || 0;
        filtered = filtered.filter(s => (tiers[s.confidence] || 0) >= minTier);
      }

      // Filter Expired
      const now = Math.floor(Date.now() / 1000);
      if (currentSettings?.autoRemoveExpired !== false) {
        filtered = filtered.filter(s => s.expiry_at > now);
      }

      // Check for strictly new signals for Haptics vs existing ones
      const hasNew = filtered.some(s => !knownIdsRef.current.has(s.id));
      if (hasNew && signals.length > 0) {
        // Haptic on new signals arriving via polling
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }

      // Update known IDs
      filtered.forEach(s => knownIdsRef.current.add(s.id));

      setSignals(filtered);
    }
  }, [signals, settings]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadSignals(true);
    setRefreshing(false);
  }, [loadSignals]);

  const handleExpire = useCallback((signalId) => {
    setSignals(prev => prev.filter(s => s.id !== signalId));
    knownIdsRef.current.delete(signalId);
  }, []);

  useEffect(() => {
    getSettings().then(setSettings);
    loadSignals();

    intervalRef.current = setInterval(() => loadSignals(false), POLL_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, []);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Top Header */}
      <View style={styles.headerArea}>
        <Text style={styles.headerTitle}>TRADECLAW 🦀</Text>
      </View>
      
      <StatusIndicator signalCount={signals.length} />

      {/* Background Gradient */}
      <LinearGradient
        colors={[colors.bg, '#0E0B16']} // subtle purple-black background
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <FlatList
        data={signals}
        keyExtractor={(item) => item.id}
        renderItem={({ item, index }) => (
          <SignalTile signal={item} onExpire={handleExpire} index={index} />
        )}
        ListEmptyComponent={<EmptyState />}
        contentContainerStyle={[
          signals.length === 0 ? styles.emptyContainer : styles.list,
          { paddingBottom: insets.bottom + 80 } // Extra padding for tab bar
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primaryLight}
            colors={[colors.primary]}
          />
        }
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  headerArea: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    backgroundColor: 'transparent',
    zIndex: 10,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: fonts.weights.black,
    color: colors.textPrimary,
    letterSpacing: 2,
  },
  list: {
    paddingTop: spacing.xl,
  },
  emptyContainer: {
    flexGrow: 1,
  },
});
