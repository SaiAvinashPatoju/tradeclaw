/**
 * TradeClaw — API Service
 * REST client for backend communication.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const DEFAULT_BACKEND_URL = 'http://192.168.1.10:8001';
const STORAGE_KEY = 'tradeclaw_backend_url';

async function getBackendUrl() {
  try {
    const url = await AsyncStorage.getItem(STORAGE_KEY);
    return url || DEFAULT_BACKEND_URL;
  } catch {
    return DEFAULT_BACKEND_URL;
  }
}

async function getBackendCandidates() {
  const configured = await getBackendUrl();
  if (configured === DEFAULT_BACKEND_URL) return [DEFAULT_BACKEND_URL];
  return [configured, DEFAULT_BACKEND_URL];
}

async function fetchWithBaseCandidates(path, timeout = 5000) {
  const candidates = await getBackendCandidates();
  let lastError = null;

  for (const baseUrl of candidates) {
    try {
      const response = await fetchWithTimeout(`${baseUrl}${path}`, timeout);
      if (response.ok && baseUrl !== candidates[0]) {
        // Self-heal stale saved backend URLs by persisting the working default.
        await AsyncStorage.setItem(STORAGE_KEY, baseUrl);
      }
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('All backend endpoints failed');
}

async function fetchWithTimeout(url, timeout = 5000, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    return response;
  } catch (error) {
    clearTimeout(timer);
    throw error;
  }
}

async function requestWithBaseCandidates(path, options = {}, timeout = 5000) {
  const candidates = await getBackendCandidates();
  let lastError = null;

  for (const baseUrl of candidates) {
    try {
      const response = await fetchWithTimeout(`${baseUrl}${path}`, timeout, options);
      if (response.ok && baseUrl !== candidates[0]) {
        await AsyncStorage.setItem(STORAGE_KEY, baseUrl);
      }
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('All backend endpoints failed');
}

export async function fetchSignals() {
  try {
    const response = await fetchWithBaseCandidates('/signals');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.signals || [], error: false };
  } catch (error) {
    return { data: [], error: true, message: error.message };
  }
}

export async function fetchHealth() {
  try {
    const response = await fetchWithBaseCandidates('/health');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data, error: false };
  } catch (error) {
    return { data: null, error: true, message: error.message };
  }
}

export async function fetchArchive(limit = 50) {
  try {
    const response = await fetchWithBaseCandidates(`/signals/archive?limit=${limit}`);
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

export async function fetchEngineConfig() {
  try {
    const response = await fetchWithBaseCandidates('/control/engine');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data, error: false };
  } catch (error) {
    return { data: null, error: true, message: error.message };
  }
}

export async function updateEngineConfig(payload) {
  try {
    const response = await requestWithBaseCandidates(
      '/control/engine',
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
      7000
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data, error: false };
  } catch (error) {
    return { data: null, error: true, message: error.message };
  }
}
