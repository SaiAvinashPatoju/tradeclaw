/**
 * TradeClaw — Formatting Utilities
 * Price, countdown, and confidence formatting helpers.
 */

export function formatCountdown(expiryTimestamp) {
  const now = Math.floor(Date.now() / 1000);
  const remaining = expiryTimestamp - now;

  if (remaining <= 0) return 'EXPIRED';

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function formatPrice(price) {
  if (price === undefined || price === null) return '—';
  if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return price.toFixed(4);
  return price.toFixed(8);
}

export function formatEntryRange(low, high) {
  return `${formatPrice(low)}–${formatPrice(high)}`;
}

export function confidenceEmoji(tier) {
  const emojis = { SNIPER: '🎯', HIGH: '🔥', MODERATE: '⚡' };
  return emojis[tier] || '📊';
}

export function formatSymbol(symbol) {
  // "ETHUSDT" → "ETH/USDT"
  if (!symbol) return '';
  return symbol.replace('USDT', '/USDT');
}
