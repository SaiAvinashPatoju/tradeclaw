/**
 * TradeClaw — Premium Theme & Design System
 * Dark aesthetic, glassmorphism, dynamic gradients, and modern typography.
 */

export const colors = {
  // Backgrounds
  bg: '#09090B', // Pitch black with slight tint
  bgCard: '#121217', // Very dark elevated
  bgCardElevated: '#18181F', // Slightly higher
  bgInput: '#18181F',
  
  // Brand / Accents
  primary: '#8B5CF6',
  primaryLight: '#A78BFA',
  primaryDark: '#5B21B6',
  
  // Text
  textPrimary: '#FAFAFA',
  textSecondary: '#A1A1AA',
  textMuted: '#52525B',
  
  // Confidence tiers (Vibrant and modern)
  sniper: '#FBBF24',      // Amber
  sniperBg: 'rgba(251, 191, 36, 0.15)',
  sniperBorder: 'rgba(251, 191, 36, 0.4)',
  
  high: '#F97316',        // Orange
  highBg: 'rgba(249, 115, 22, 0.15)',
  highBorder: 'rgba(249, 115, 22, 0.4)',
  
  moderate: '#3B82F6',    // Blue
  moderateBg: 'rgba(59, 130, 246, 0.15)',
  moderateBorder: 'rgba(59, 130, 246, 0.4)',
  
  // Status
  success: '#10B981',
  danger: '#EF4444',
  warning: '#F59E0B',
  
  // UI
  border: '#27272A',
  divider: '#18181B',
  statusLive: '#10B981',
  statusOffline: '#EF4444',
};

export const confidenceColors = {
  SNIPER: { text: colors.sniper, bg: colors.sniperBg, border: colors.sniperBorder, emoji: '🎯' },
  HIGH:   { text: colors.high, bg: colors.highBg, border: colors.highBorder, emoji: '🔥' },
  MODERATE: { text: colors.moderate, bg: colors.moderateBg, border: colors.moderateBorder, emoji: '⚡' },
};

export const fonts = {
  regular: 'System',
  bold: 'System',
  sizes: {
    xs: 11,
    sm: 13,
    md: 15,
    lg: 18,
    xl: 24,
    xxl: 32,
    xxxl: 42,
  },
  weights: {
    light: '300',
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    heavy: '800',
    black: '900',
  }
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
};

export const borderRadius = {
  sm: 6,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 9999,
};

// Premium shadows for iOS/Android
export const shadows = {
  glowSniper: {
    shadowColor: colors.sniper,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
  glowHigh: {
    shadowColor: colors.high,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
  glowModerate: {
    shadowColor: colors.moderate,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
};
