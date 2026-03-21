/**
 * TradeClaw — Root Application
 * Bottom tab navigator with dark theme, notification listeners, and haptic feedback.
 */
import React, { useEffect, useRef, useState } from 'react';
import { StatusBar, Platform, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import DashboardScreen from './src/screens/DashboardScreen';
import StatsScreen from './src/screens/StatsScreen';
import ArchiveScreen from './src/screens/ArchiveScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { registerForPushNotifications } from './src/services/notifications';
import { colors, fonts, borderRadius } from './src/theme';

const Tab = createBottomTabNavigator();

const darkTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    primary: colors.primary,
    background: colors.bg,
    card: colors.bgCard,
    text: colors.textPrimary,
    border: colors.divider,
    notification: colors.sniper,
  },
};

// Simple text-based icon component to replace emojis without heavy libraries
const TabIcon = ({ name, color, size, focused }) => {
  const icons = {
    Dashboard: '₪', // Signal-like icon
    Stats: '⑊',     // Bar-chart-like icon
    Archive: '📁',  // Archive
    Settings: '⚙',   // Gear
  };

  return (
    <View style={[styles.iconContainer, focused && styles.iconContainerFocused]}>
      <Text style={[styles.iconText, { color, fontSize: size, fontWeight: focused ? '800' : '400' }]}>
        {icons[name] || '•'}
      </Text>
    </View>
  );
};

export default function App() {
  const notificationListener = useRef();
  const responseListener = useRef();

  useEffect(() => {
    registerForPushNotifications();

    notificationListener.current = Notifications.addNotificationReceivedListener(
      (notification) => {
        if (Platform.OS !== 'web') {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        }
      }
    );

    responseListener.current = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        console.log('Notification tapped:', response);
      }
    );

    return () => {
      if (notificationListener.current) Notifications.removeNotificationSubscription(notificationListener.current);
      if (responseListener.current) Notifications.removeNotificationSubscription(responseListener.current);
    };
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />
      <NavigationContainer theme={darkTheme}>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerShown: false,
            tabBarIcon: ({ color, size, focused }) => (
              <TabIcon name={route.name} color={color} size={size} focused={focused} />
            ),
            tabBarStyle: {
              backgroundColor: 'rgba(18, 18, 23, 0.95)',
              borderTopColor: colors.border,
              borderTopWidth: 1,
              height: Platform.OS === 'ios' ? 88 : 65,
              paddingBottom: Platform.OS === 'ios' ? 28 : 10,
              paddingTop: 10,
              position: 'absolute', // Creates a floating effect over bottom content
              elevation: 0,
            },
            tabBarActiveTintColor: colors.primaryLight,
            tabBarInactiveTintColor: colors.textMuted,
            tabBarLabelStyle: {
              fontSize: fonts.sizes.xs,
              fontWeight: fonts.weights.bold,
              marginTop: 4,
            },
          })}
        >
          <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ tabBarLabel: 'SIGNALS' }} />
          <Tab.Screen name="Stats" component={StatsScreen} options={{ tabBarLabel: 'STATS' }} />
          <Tab.Screen name="Archive" component={ArchiveScreen} options={{ tabBarLabel: 'ARCHIVE' }} />
          <Tab.Screen name="Settings" component={SettingsScreen} options={{ tabBarLabel: 'SETTINGS' }} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 32,
    width: 48,
    borderRadius: borderRadius.pill,
  },
  iconContainerFocused: {
    backgroundColor: 'rgba(139, 92, 246, 0.15)', // Light primary bg
  },
  iconText: {
    textAlign: 'center',
  }
});
