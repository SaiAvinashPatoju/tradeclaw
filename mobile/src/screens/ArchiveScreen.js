/**
 * TradeClaw — Archive Screen
 * Shows evaluated signals with WIN / LOSS / INCOMPLETE outcomes.
 * Tap any card to see entry, TP, SL, actual PnL, max/min price.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl,
  TouchableOpacity, Modal, ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, fonts, spacing, borderRadius } from '../theme';
import { fetchArchive } from '../services/api';
import { formatSymbol, formatPrice } from '../utils/formatting';

const OUTCOME_META = {
  WIN:        { emoji: '✅', label: 'WIN',        color: colors.success },
  LOSS:       { emoji: '❌', label: 'LOSS',       color: colors.danger  },
  INCOMPLETE: { emoji: '➖', label: 'INCOMPLETE', color: colors.warning  },
  EXPIRED:    { emoji: '⏳', label: 'AWAITING',   color: colors.textMuted },
};

function fmt(epoch) {
  if (!epoch) return '—';
  return new Date(epoch * 1000).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

function ArchiveCard({ signal, onPress }) {
  const meta = OUTCOME_META[signal.status] || OUTCOME_META.EXPIRED;
  const pnl  = signal.evaluated_profit_pct;
  const pnlColor = pnl == null ? colors.textMuted : pnl >= 0 ? colors.success : colors.danger;

  return (
    <TouchableOpacity onPress={() => onPress(signal)} activeOpacity={0.85}>
      <View style={[styles.card, { borderLeftColor: meta.color }]}>
        <View style={styles.cardTop}>
          <Text style={styles.symbol}>{formatSymbol(signal.symbol)}</Text>
          <View style={[styles.outcomeBadge, { borderColor: meta.color }]}>
            <Text style={[styles.outcomeText, { color: meta.color }]}>
              {meta.emoji} {meta.label}
            </Text>
          </View>
        </View>

        <View style={styles.cardMid}>
          <View style={styles.metricPair}>
            <Text style={styles.metricLabel}>SCORE</Text>
            <Text style={[styles.metricVal, { color: colors.primaryLight }]}>
              {signal.score?.toFixed(1)}
            </Text>
          </View>
          <View style={styles.metricPair}>
            <Text style={styles.metricLabel}>PnL</Text>
            <Text style={[styles.metricVal, { color: pnlColor }]}>
              {pnl != null ? `${pnl > 0 ? '+' : ''}${pnl.toFixed(2)}%` : '—'}
            </Text>
          </View>
          <View style={styles.metricPair}>
            <Text style={styles.metricLabel}>CONF</Text>
            <Text style={styles.metricVal}>{signal.confidence}</Text>
          </View>
          <View style={styles.metricPair}>
            <Text style={styles.metricLabel}>EVAL</Text>
            <Text style={styles.metricVal}>{fmt(signal.outcome_at)}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

function DetailModal({ signal, onClose }) {
  if (!signal) return null;
  const meta = OUTCOME_META[signal.status] || OUTCOME_META.EXPIRED;
  const pnl  = signal.evaluated_profit_pct;
  const pnlColor = pnl == null ? colors.textMuted : pnl >= 0 ? colors.success : colors.danger;

  const Row = ({ label, val, color }) => (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={[styles.detailVal, color ? { color } : null]}>{val ?? '—'}</Text>
    </View>
  );

  return (
    <Modal visible transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalSheet}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalSymbol}>{formatSymbol(signal.symbol)}</Text>
            <Text style={[styles.modalOutcome, { color: meta.color }]}>
              {meta.emoji} {meta.label}
            </Text>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={styles.sectionHead}>Signal Quality</Text>
            <Row label="Score"      val={signal.score?.toFixed(2)} />
            <Row label="Confidence" val={signal.confidence} />
            <Row label="Reason"     val={signal.reason} />

            <Text style={styles.sectionHead}>Trade Parameters</Text>
            <Row label="Entry Low"       val={formatPrice(signal.entry_low)} />
            <Row label="Entry High"      val={formatPrice(signal.entry_high)} />
            <Row label="Entry (assumed)" val={formatPrice(signal.entry_price_assumed)} />
            <Row label="Target Price"    val={formatPrice(signal.target_price)} color={colors.success} />
            <Row label="Stop Price"      val={formatPrice(signal.stop_price)}   color={colors.danger}  />
            <Row label="Target %"        val={`+${signal.target_pct?.toFixed(2)}%`}    color={colors.success} />
            <Row label="Stop %"          val={`-${signal.stop_loss_pct?.toFixed(2)}%`} color={colors.danger}  />

            <Text style={styles.sectionHead}>Lifecycle</Text>
            <Row label="Generated"  val={fmt(signal.generated_at)} />
            <Row label="Entry Closes" val={fmt(signal.expiry_at)} />
            <Row label="Hold Period" val={`${(signal.hold_period_secs / 3600).toFixed(1)}h`} />
            <Row label="Evaluation"  val={fmt(signal.evaluation_at)} />
            <Row label="Outcome At"  val={fmt(signal.outcome_at)} />

            <Text style={styles.sectionHead}>Outcome</Text>
            <Row label="Max Price Hit" val={formatPrice(signal.max_price_reached)} color={colors.success} />
            <Row label="Min Price Hit" val={formatPrice(signal.min_price_reached)} color={colors.danger}  />
            <Row label="Actual PnL"    val={pnl != null ? `${pnl > 0 ? '+' : ''}${pnl.toFixed(3)}%` : '—'} color={pnlColor} />
          </ScrollView>

          <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
            <Text style={styles.closeBtnText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

export default function ArchiveScreen() {
  const [signals,    setSignals]    = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selected,   setSelected]   = useState(null);
  const insets = useSafeAreaInsets();

  // Summary stats
  const wins       = signals.filter(s => s.status === 'WIN').length;
  const losses     = signals.filter(s => s.status === 'LOSS').length;
  const incomplete = signals.filter(s => s.status === 'INCOMPLETE').length;
  const awaiting   = signals.filter(s => s.status === 'EXPIRED').length;
  const total      = wins + losses + incomplete;
  const winRate    = total > 0 ? ((wins / total) * 100).toFixed(1) : '—';
  const avgPnl     = total > 0
    ? (signals.filter(s => s.evaluated_profit_pct != null)
        .reduce((a, b) => a + b.evaluated_profit_pct, 0) / total).toFixed(2)
    : '—';

  const load = useCallback(async () => {
    const res = await fetchArchive(100);
    if (!res.error) setSignals(res.data);
  }, []);

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  useEffect(() => { load(); }, []);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <LinearGradient colors={[colors.bg, '#0E0B16']} style={StyleSheet.absoluteFill} pointerEvents="none" />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>ARCHIVE 📁</Text>
      </View>

      {/* Stats Bar */}
      <View style={styles.statsBar}>
        <StatChip label="Win Rate" val={winRate !== '—' ? `${winRate}%` : '—'} color={colors.success} />
        <StatChip label="Avg PnL"  val={avgPnl !== '—' ? `${avgPnl > 0 ? '+' : ''}${avgPnl}%` : '—'} color={avgPnl >= 0 ? colors.success : colors.danger} />
        <StatChip label="Wins"     val={String(wins)}     color={colors.success} />
        <StatChip label="Losses"   val={String(losses)}   color={colors.danger}  />
        <StatChip label="Waiting"  val={String(awaiting)} color={colors.textMuted} />
      </View>

      <FlatList
        data={signals}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <ArchiveCard signal={item} onPress={setSelected} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No archived signals yet.</Text>
            <Text style={styles.emptySubText}>Signals appear here after their hold period is complete.</Text>
          </View>
        }
        contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primaryLight} />}
        showsVerticalScrollIndicator={false}
      />

      <DetailModal signal={selected} onClose={() => setSelected(null)} />
    </View>
  );
}

function StatChip({ label, val, color }) {
  return (
    <View style={styles.statChip}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statVal, { color }]}>{val}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.bg },
  header:       { paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  headerTitle:  { fontSize: 20, fontWeight: fonts.weights.black, color: colors.textPrimary, letterSpacing: 2 },

  statsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(255,255,255,0.04)',
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    borderRadius: borderRadius.lg,
    paddingVertical: spacing.md,
  },
  statChip:  { alignItems: 'center' },
  statLabel: { fontSize: 9, color: colors.textMuted, letterSpacing: 1, marginBottom: 2, fontWeight: fonts.weights.bold },
  statVal:   { fontSize: fonts.sizes.md, fontWeight: fonts.weights.heavy },

  card: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    borderLeftWidth: 3,
    padding: spacing.lg,
  },
  cardTop:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  symbol:       { fontSize: fonts.sizes.lg, fontWeight: fonts.weights.black, color: colors.textPrimary },
  outcomeBadge: { paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: borderRadius.sm, borderWidth: 1 },
  outcomeText:  { fontSize: fonts.sizes.xs, fontWeight: fonts.weights.heavy, letterSpacing: 0.5 },
  cardMid:      { flexDirection: 'row', justifyContent: 'space-between' },
  metricPair:   { alignItems: 'center' },
  metricLabel:  { fontSize: 9, color: colors.textMuted, letterSpacing: 1, marginBottom: 2, fontWeight: fonts.weights.bold },
  metricVal:    { fontSize: fonts.sizes.sm, fontWeight: fonts.weights.bold, color: colors.textSecondary },

  empty:        { alignItems: 'center', marginTop: 80 },
  emptyText:    { fontSize: fonts.sizes.md, color: colors.textSecondary, marginBottom: spacing.sm },
  emptySubText: { fontSize: fonts.sizes.sm, color: colors.textMuted, textAlign: 'center', paddingHorizontal: spacing.xxl },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
  modalSheet: {
    backgroundColor: colors.bgCard,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.xl,
    maxHeight: '85%',
  },
  modalHeader:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  modalSymbol:  { fontSize: fonts.sizes.xl, fontWeight: fonts.weights.black, color: colors.textPrimary },
  modalOutcome: { fontSize: fonts.sizes.md, fontWeight: fonts.weights.heavy },
  sectionHead:  { fontSize: 10, color: colors.textMuted, letterSpacing: 2, fontWeight: fonts.weights.bold, marginTop: spacing.lg, marginBottom: spacing.sm },
  detailRow:    { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5 },
  detailLabel:  { fontSize: fonts.sizes.sm, color: colors.textSecondary },
  detailVal:    { fontSize: fonts.sizes.sm, fontWeight: fonts.weights.bold, color: colors.textPrimary },
  closeBtn:     { marginTop: spacing.xl, backgroundColor: colors.primary, borderRadius: borderRadius.md, paddingVertical: spacing.md, alignItems: 'center' },
  closeBtnText: { fontSize: fonts.sizes.md, fontWeight: fonts.weights.heavy, color: '#fff' },
});
