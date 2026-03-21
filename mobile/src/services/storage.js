/**
 * TradeClaw — Storage Service
 * AsyncStorage wrapper for settings and app state.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  BACKEND_URL: 'tradeclaw_backend_url',
  SETTINGS: 'tradeclaw_settings',
};

const DEFAULT_SETTINGS = {
  notificationSound: true,
  vibration: true,
  minConfidence: 'MODERATE',
  autoRemoveExpired: true,
};

export async function getBackendUrl() {
  try {
    const url = await AsyncStorage.getItem(KEYS.BACKEND_URL);
    return url || 'http://192.168.1.100:8000';
  } catch {
    return 'http://192.168.1.100:8000';
  }
}

export async function setBackendUrl(url) {
  try {
    await AsyncStorage.setItem(KEYS.BACKEND_URL, url);
    return true;
  } catch {
    return false;
  }
}

export async function getSettings() {
  try {
    const raw = await AsyncStorage.getItem(KEYS.SETTINGS);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export async function saveSettings(settings) {
  try {
    await AsyncStorage.setItem(KEYS.SETTINGS, JSON.stringify(settings));
    return true;
  } catch {
    return false;
  }
}
