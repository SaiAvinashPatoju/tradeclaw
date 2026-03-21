/**
 * TradeClaw — Notifications Service
 * Push notification registration and local exit reminder scheduling.
 */
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

// Configure notification handler for foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function registerForPushNotifications() {
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device');
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Notification permission not granted');
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('signals', {
      name: 'Trade Signals',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FFD700',
      sound: 'default',
    });
  }

  try {
    // In Expo Go, projectId may not be available — gracefully skip
    const token = (await Notifications.getExpoPushTokenAsync({
      projectId: undefined,
    })).data;
    console.log('Push token:', token);
    return token;
  } catch (error) {
    // Expected in Expo Go — FCM push works via EAS/dev build
    console.log('Push token skipped (Expo Go):', error.message);
    return null;
  }
}

export async function scheduleExitReminder(coinName, delayMinutes) {
  try {
    const id = await Notifications.scheduleNotificationAsync({
      content: {
        title: `⏰ Check your ${coinName} trade!`,
        body: `Set ${delayMinutes} min ago — review and exit if needed`,
        sound: 'default',
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
        seconds: delayMinutes * 60,
      },
    });
    console.log(`Exit reminder scheduled for ${coinName} in ${delayMinutes}m (id: ${id})`);
    return id;
  } catch (error) {
    console.error('Failed to schedule reminder:', error);
    return null;
  }
}

export async function cancelAllReminders() {
  await Notifications.cancelAllScheduledNotificationsAsync();
}
