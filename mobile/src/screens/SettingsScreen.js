/**
 * TradeClaw — Settings Screen
 * Premium configuration panel for backend and system preferences.
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, Switch, StyleSheet, ScrollView,
  TouchableOpacity, Alert
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { colors, fonts, spacing, borderRadius } from '../theme';
import { getBackendUrl, setBackendUrl, getSettings, saveSettings } from '../services/storage';

const CONFIDENCE_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'SNIPER'];

export default function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const [url, setUrl] = useState('');
  const [settings, setSettings] = useState({
    notificationSound: true,
    vibration: true,
    minConfidence: 'LOW',
    autoRemoveExpired: true,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const savedUrl = await getBackendUrl();
    const savedSettings = await getSettings();
    setUrl(savedUrl);
    setSettings(savedSettings);
  };

  const autoDetectUrl = () => {
    // Basic auto-fill for emulator users
    Haptics.selectionAsync();
    setUrl('http://10.0.2.2:8000');
  };

  const handleSave = async () => {
    if (!url.trim()) {
      Alert.alert('Error', 'Backend URL cannot be empty');
      return;
    }
    await setBackendUrl(url.trim());
    await saveSettings(settings);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const updateSetting = (key, value) => {
    Haptics.selectionAsync();
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>PREFERENCES</Text>
          <Text style={styles.subtitle}>System Core Parameters</Text>
        </View>

        {/* Backend Configuration */}
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>SERVER LINK</Text>
          <View style={styles.card}>
            <View style={styles.urlHeader}>
              <Text style={styles.label}>REST API Endpoint</Text>
              <TouchableOpacity onPress={autoDetectUrl}>
                <Text style={styles.autoDetectText}>Auto-Fill</Text>
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.input}
              value={url}
              onChangeText={setUrl}
              placeholder="http://192.168.1.xxx:8000"
              placeholderTextColor={colors.textMuted}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
          </View>
        </View>

        {/* Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>SYSTEM ALERTS</Text>
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.label}>Push Sounds</Text>
              <Switch
                value={settings.notificationSound}
                onValueChange={(v) => updateSetting('notificationSound', v)}
                trackColor={{ false: colors.border, true: colors.primary }}
                thumbColor={colors.textPrimary}
              />
            </View>
            <View style={[styles.row, { borderBottomWidth: 0 }]}>
              <Text style={styles.label}>Haptic Feedback</Text>
              <Switch
                value={settings.vibration}
                onValueChange={(v) => updateSetting('vibration', v)}
                trackColor={{ false: colors.border, true: colors.primary }}
                thumbColor={colors.textPrimary}
              />
            </View>
          </View>
        </View>

        {/* Filters */}
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>SIGNAL ENGINE</Text>
          <View style={styles.card}>
            <Text style={[styles.label, { marginBottom: spacing.md }]}>Minimum Confidence Tier</Text>
            
            <View style={styles.segmentControl}>
              {CONFIDENCE_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt}
                  style={[
                    styles.segmentBtn,
                    settings.minConfidence === opt && styles.segmentBtnActive,
                  ]}
                  onPress={() => updateSetting('minConfidence', opt)}
                >
                  <Text style={[
                    styles.segmentText,
                    settings.minConfidence === opt && styles.segmentTextActive,
                  ]}>
                    {opt}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={[styles.row, { borderBottomWidth: 0, marginTop: spacing.md }]}>
              <Text style={styles.label}>Auto-Purge Expired</Text>
              <Switch
                value={settings.autoRemoveExpired}
                onValueChange={(v) => updateSetting('autoRemoveExpired', v)}
                trackColor={{ false: colors.border, true: colors.primary }}
                thumbColor={colors.textPrimary}
              />
            </View>
          </View>
        </View>

        {/* Save/Execute */}
        <TouchableOpacity
          style={[styles.saveBtn, saved && styles.saveBtnSuccess]}
          onPress={handleSave}
          activeOpacity={0.8}
        >
          <Text style={styles.saveBtnText}>
            {saved ? 'PARAMETERS SECURED' : 'UPDATE SYSTEM'}
          </Text>
        </TouchableOpacity>
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
    marginBottom: spacing.xxl,
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
  section: {
    marginBottom: spacing.xxl,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: fonts.weights.heavy,
    color: colors.primaryLight,
    letterSpacing: 1.5,
    marginBottom: spacing.md,
  },
  card: {
    backgroundColor: colors.bgCardElevated,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  urlHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.sm,
  },
  autoDetectText: {
    fontSize: 10,
    fontWeight: fonts.weights.bold,
    color: colors.primaryLight,
    textDecorationLine: 'underline',
  },
  label: {
    fontSize: fonts.sizes.sm,
    fontWeight: fonts.weights.bold,
    color: colors.textPrimary,
  },
  input: {
    backgroundColor: colors.bgInput,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    color: colors.textPrimary,
    fontSize: fonts.sizes.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  segmentControl: {
    flexDirection: 'row',
    backgroundColor: colors.bgInput,
    borderRadius: borderRadius.md,
    padding: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: borderRadius.sm,
  },
  segmentBtnActive: {
    backgroundColor: '#3F3F46', // Distinct highlight
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: {
    fontSize: 11,
    fontWeight: fonts.weights.bold,
    color: colors.textMuted,
    letterSpacing: 0.5,
  },
  segmentTextActive: {
    color: colors.textPrimary,
  },
  saveBtn: {
    backgroundColor: colors.primaryDark,
    borderRadius: borderRadius.lg,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    marginTop: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  saveBtnSuccess: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  saveBtnText: {
    fontSize: 12,
    fontWeight: fonts.weights.heavy,
    color: '#FFF',
    letterSpacing: 1.5,
  },
});
