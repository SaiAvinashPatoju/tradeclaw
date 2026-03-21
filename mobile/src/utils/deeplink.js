/**
 * TradeClaw — Deep Link Utility
 * Opens Binance app or fallback web URL.
 */
import * as Linking from 'expo-linking';

export async function openBinance(symbol) {
  // Clean symbol: "ETHUSDT" → "ETH_USDT"
  const pair = symbol.replace('USDT', '_USDT').replace('/USDT', '_USDT');
  const appUrl = `binance://trade/${pair}`;
  const webUrl = `https://www.binance.com/en/trade/${pair}`;

  try {
    const supported = await Linking.canOpenURL(appUrl);
    if (supported) {
      await Linking.openURL(appUrl);
    } else {
      await Linking.openURL(webUrl);
    }
  } catch {
    // Fallback to web
    try {
      await Linking.openURL(webUrl);
    } catch (error) {
      console.error('Failed to open Binance:', error);
    }
  }
}
