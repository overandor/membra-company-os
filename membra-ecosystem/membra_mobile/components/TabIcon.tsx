import { View, Text, StyleSheet } from 'react-native';

interface TabIconProps {
  name: string;
  color: string;
  focused: boolean;
}

const ICON_MAP: Record<string, string> = {
  home: '⌂',
  grid: '⊞',
  tag: '🏷',
  camera: '◉',
  user: '◎',
};

export function TabIcon({ name, color, focused }: TabIconProps) {
  return (
    <View style={[styles.container, focused && styles.focused]}>
      <Text style={[styles.icon, { color }]}>{ICON_MAP[name] || '•'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  focused: {
    transform: [{ scale: 1.1 }],
  },
  icon: {
    fontSize: 20,
    fontWeight: '600',
  },
});
