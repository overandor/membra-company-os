import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, StyleSheet } from 'react-native';
import DashboardScreen from './src/screens/DashboardScreen';
import WalletScreen from './src/screens/WalletScreen';
import InventoryScreen from './src/screens/InventoryScreen';
import UploadScreen from './src/screens/UploadScreen';
import ProofbookScreen from './src/screens/ProofbookScreen';

const Tab = createBottomTabNavigator();

function TabLabel({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text style={[styles.tabLabel, focused && styles.tabLabelFocused]}>
      {label}
    </Text>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: styles.tabBar,
          tabBarActiveTintColor: '#007AFF',
          tabBarInactiveTintColor: '#8E8E93',
        }}
      >
        <Tab.Screen
          name="Dashboard"
          component={DashboardScreen}
          options={{ tabBarLabel: ({ focused }) => <TabLabel label="Dashboard" focused={focused} /> }}
        />
        <Tab.Screen
          name="Inventory"
          component={InventoryScreen}
          options={{ tabBarLabel: ({ focused }) => <TabLabel label="Inventory" focused={focused} /> }}
        />
        <Tab.Screen
          name="Wallet"
          component={WalletScreen}
          options={{ tabBarLabel: ({ focused }) => <TabLabel label="Wallet" focused={focused} /> }}
        />
        <Tab.Screen
          name="Upload"
          component={UploadScreen}
          options={{ tabBarLabel: ({ focused }) => <TabLabel label="Upload" focused={focused} /> }}
        />
        <Tab.Screen
          name="Proofbook"
          component={ProofbookScreen}
          options={{ tabBarLabel: ({ focused }) => <TabLabel label="Proofbook" focused={focused} /> }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e5ea',
    paddingTop: 4,
    paddingBottom: 4,
    height: 64,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: '#8E8E93',
  },
  tabLabelFocused: {
    color: '#007AFF',
    fontWeight: '700',
  },
});
