import { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity, Alert } from 'react-native';
import { router } from 'expo-router';
import { useTheme } from '@/hooks/useTheme';
import { ScreenHeader } from '@/components/ScreenHeader';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { useAppStore } from '@/stores/appStore';
import type { AssetType, Asset } from '@/types';

const ASSET_TYPES: { type: AssetType; label: string }[] = [
  { type: 'vehicle', label: 'Vehicle' },
  { type: 'window', label: 'Window' },
  { type: 'wearable', label: 'Wearable' },
  { type: 'bag', label: 'Bag' },
  { type: 'sign', label: 'Sign' },
  { type: 'surface', label: 'Surface' },
];

export default function AssetsScreen() {
  const { colors } = useTheme();
  const { assets, addAsset } = useAppStore();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedType, setSelectedType] = useState<AssetType>('vehicle');

  const handleRegister = () => {
    if (!name.trim()) {
      Alert.alert('Required', 'Please enter an asset name');
      return;
    }

    const newAsset: Asset = {
      id: `asset_${Date.now()}`,
      owner_id: 'demo_owner',
      type: selectedType,
      name: name.trim(),
      description: description.trim(),
      photos: [],
      status: 'pending',
      created_at: new Date().toISOString(),
    };

    addAsset(newAsset);
    setName('');
    setDescription('');
    setShowForm(false);
    Alert.alert('Success', 'Asset registered and pending review.');
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScreenHeader title="My Assets" subtitle="Register and manage your advertising surfaces" />

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {!showForm ? (
          <>
            <Button title="+ Register New Asset" onPress={() => setShowForm(true)} />

            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              {assets.length} Registered Asset{assets.length !== 1 ? 's' : ''}
            </Text>

            {assets.map((asset) => (
              <Card
                key={asset.id}
                title={asset.name}
                description={asset.description || `${asset.type} asset`}
                status={asset.status}
                statusColor={
                  asset.status === 'active'
                    ? colors.accent
                    : asset.status === 'pending'
                    ? colors.warning
                    : colors.danger
                }
              />
            ))}

            {assets.length === 0 && (
              <View style={styles.emptyState}>
                <Text style={[styles.emptyText, { color: colors.textMuted }]}>
                  No assets registered yet. Register your first vehicle, window, or wearable to start earning.
                </Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.form}>
            <Text style={[styles.formTitle, { color: colors.text }]}>Register Asset</Text>

            <Text style={[styles.label, { color: colors.textSecondary }]}>Asset Type</Text>
            <View style={styles.typeGrid}>
              {ASSET_TYPES.map((t) => (
                <TouchableOpacity
                  key={t.type}
                  style={[
                    styles.typeButton,
                    {
                      backgroundColor:
                        selectedType === t.type ? colors.primary : colors.surface,
                      borderColor: colors.border,
                    },
                  ]}
                  onPress={() => setSelectedType(t.type)}
                >
                  <Text
                    style={[
                      styles.typeButtonText,
                      {
                        color:
                          selectedType === t.type ? '#fff' : colors.text,
                      },
                    ]}
                  >
                    {t.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={[styles.label, { color: colors.textSecondary }]}>Name</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                  color: colors.text,
                },
              ]}
              placeholder="e.g. Honda Civic - Rear Window"
              placeholderTextColor={colors.textMuted}
              value={name}
              onChangeText={setName}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>Description (optional)</Text>
            <TextInput
              style={[
                styles.input,
                styles.textArea,
                {
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                  color: colors.text,
                },
              ]}
              placeholder="Describe your asset location, size, visibility..."
              placeholderTextColor={colors.textMuted}
              multiline
              numberOfLines={3}
              value={description}
              onChangeText={setDescription}
            />

            <View style={styles.formActions}>
              <Button title="Cancel" variant="outline" onPress={() => setShowForm(false)} />
              <Button title="Register Asset" onPress={handleRegister} />
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
    gap: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 4,
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 14,
    lineHeight: 20,
  },
  form: {
    gap: 12,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeButton: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  typeButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  input: {
    height: 48,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 14,
    fontSize: 15,
  },
  textArea: {
    height: 80,
    paddingTop: 12,
    textAlignVertical: 'top',
  },
  formActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
  },
});
