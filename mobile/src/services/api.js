/**
 * TradeClaw — API Service
 * REST client for backend communication.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const DEFAULT_BACKEND_URL = 'http://192.168.1.7:8000';
const STORAGE_KEY = 'tradeclaw_backend_url';

async function getBackendUrl() {
  try {
    const url = await AsyncStorage.getItem(STORAGE_KEY);
    return url || DEFAULT_BACKEND_URL;
  } catch {
    return DEFAULT_BACKEND_URL;
  }
}

async function fetchWithTimeout(url, timeout = 5000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    return response;
  } catch (error) {
    clearTimeout(timer);
    throw error;
  }
}

export async function fetchSignals() {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/signals`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.signals || [], error: false };
  } catch (error) {
    return { data: [], error: true, message: error.message };
  }
}

export async function fetchHealth() {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data, error: false };
  } catch (error) {
    return { data: null, error: true, message: error.message };
  }
}

export async function fetchArchive(limit = 50) {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/signals/archive?limit=${limit}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.signals || [], error: false };
  } catch (error) {
    return { data: [], error: true, message: error.message };
  }
}

export async function postSignal(signalData) {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetch(`${baseUrl}/signals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signalData),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return { data: await response.json(), error: false };
  } catch (error) {
    return { data: null, error: true, message: error.message };
  }
}
