import { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, TextInput } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { ScreenHeader } from '@/components/ScreenHeader';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { useAppStore } from '@/stores/appStore';
import type { ProofSubmission } from '@/types';

type ProofTab = 'photo' | 'qr' | 'nfc' | 'history';

export default function ProofScreen() {
  const { colors } = useTheme();
  const { proofs, addProof } = useAppStore();
  const [activeTab, setActiveTab] = useState<ProofTab>('photo');
  const [campaignId, setCampaignId] = useState('');
  const [assetId, setAssetId] = useState('');
  const [notes, setNotes] = useState('');
  const [scanResult, setScanResult] = useState('');

  const handleSubmitProof = () => {
    if (!campaignId.trim() || !assetId.trim()) {
      Alert.alert('Required', 'Campaign ID and Asset ID are required');
      return;
    }

    const proof: ProofSubmission = {
      id: `proof_${Date.now()}`,
      owner_id: 'demo_owner',
      campaign_id: campaignId.trim(),
      asset_id: assetId.trim(),
      photo_url: 'https://placeholder.membra/proof.jpg',
      submitted_at: new Date().toISOString(),
      status: 'pending',
      review_notes: notes.trim(),
    };

    addProof(proof);
    setCampaignId('');
    setAssetId('');
    setNotes('');
    Alert.alert('Proof Submitted', 'Your proof is now pending review. You will be notified once approved.');
  };

  const handleScan = (type: 'qr' | 'nfc') => {
    if (!scanResult.trim()) {
      Alert.alert('Required', `Enter ${type.toUpperCase()} scan payload`);
      return;
    }
    Alert.alert(
      `${type.toUpperCase()} Scan Recorded`,
      `Payload: ${scanResult}\n\nIn production, this will verify against membra-qr-gateway.`,
      [{ text: 'OK', onPress: () => setScanResult('') }]
    );
  };

  const tabs: { key: ProofTab; label: string }[] = [
    { key: 'photo', label: '📷 Photo' },
    { key: 'qr', label: '◼ QR' },
    { key: 'nfc', label: '◎ NFC' },
    { key: 'history', label: '⏱ History' },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScreenHeader title="Submit Proof" subtitle="Capture photos, scan QR, or tap NFC" />

      {/* Tab Switcher */}
      <View style={styles.tabRow}>
        {tabs.map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[
              styles.tab,
              {
                backgroundColor: activeTab === t.key ? colors.primary : colors.surface,
                borderColor: colors.border,
              },
            ]}
            onPress={() => setActiveTab(t.key)}
          >
            <Text
              style={[
                styles.tabText,
                { color: activeTab === t.key ? '#fff' : colors.text },
              ]}
            >
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {activeTab === 'photo' && (
          <>
            <Text style={[styles.instructions, { color: colors.textSecondary }]}>
              Submit proof that your asset is displaying the campaign media. A clear photo showing the full asset with the media visible is required.
            </Text>

            <Text style={[styles.label, { color: colors.textSecondary }]}>Campaign ID</Text>
            <TextInput
              style={[styles.input, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              placeholder="e.g. camp_001"
              placeholderTextColor={colors.textMuted}
              value={campaignId}
              onChangeText={setCampaignId}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>Asset ID</Text>
            <TextInput
              style={[styles.input, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              placeholder="e.g. asset_123"
              placeholderTextColor={colors.textMuted}
              value={assetId}
              onChangeText={setAssetId}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>Notes (optional)</Text>
            <TextInput
              style={[styles.input, styles.textArea, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              placeholder="Any additional context..."
              placeholderTextColor={colors.textMuted}
              multiline
              numberOfLines={3}
              value={notes}
              onChangeText={setNotes}
            />

            {/* Photo Placeholder */}
            <View style={[styles.photoPlaceholder, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.photoText, { color: colors.textMuted }]}>
                📷 In production, this opens the camera to capture proof.
              </Text>
            </View>

            <Button title="Submit Proof" onPress={handleSubmitProof} />
          </>
        )}

        {activeTab === 'qr' && (
          <>
            <Text style={[styles.instructions, { color: colors.textSecondary }]}>
              Scan a QR code to verify asset placement or confirm a check-in. The scan will be timestamped and geolocated.
            </Text>

            <View style={[styles.scannerPlaceholder, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.scannerText, { color: colors.textMuted }]}>
                ◼ QR Scanner placeholder{'\n'}Production: expo-barcode-scanner
              </Text>
            </View>

            <Text style={[styles.label, { color: colors.textSecondary }]}>Or enter payload manually</Text>
            <TextInput
              style={[styles.input, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              placeholder="QR payload..."
              placeholderTextColor={colors.textMuted}
              value={scanResult}
              onChangeText={setScanResult}
            />
            <Button title="Record QR Scan" onPress={() => handleScan('qr')} />
          </>
        )}

        {activeTab === 'nfc' && (
          <>
            <Text style={[styles.instructions, { color: colors.textSecondary }]}>
              Tap an NFC tag to verify proximity to an asset or confirm a location-based check-in.
            </Text>

            <View style={[styles.scannerPlaceholder, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.scannerText, { color: colors.textMuted }]}>
                ◎ NFC Reader placeholder{'\n'}Production: react-native-nfc-manager
              </Text>
            </View>

            <Text style={[styles.label, { color: colors.textSecondary }]}>Or enter tag ID manually</Text>
            <TextInput
              style={[styles.input, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              placeholder="NFC tag ID..."
              placeholderTextColor={colors.textMuted}
              value={scanResult}
              onChangeText={setScanResult}
            />
            <Button title="Record NFC Tap" onPress={() => handleScan('nfc')} />
          </>
        )}

        {activeTab === 'history' && (
          <>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              {proofs.length} Submission{proofs.length !== 1 ? 's' : ''}
            </Text>
            {proofs.map((proof) => (
              <Card
                key={proof.id}
                title={`Campaign: ${proof.campaign_id}`}
                description={proof.review_notes || 'No notes'}
                status={proof.status}
                statusColor={
                  proof.status === 'approved'
                    ? colors.accent
                    : proof.status === 'rejected'
                    ? colors.danger
                    : colors.warning
                }
              >
                <Text style={[styles.meta, { color: colors.textMuted }]}>
                  Asset: {proof.asset_id} · {new Date(proof.submitted_at).toLocaleDateString()}
                </Text>
              </Card>
            ))}
            {proofs.length === 0 && (
              <Text style={[styles.emptyText, { color: colors.textMuted }]}>
                No proof submissions yet. Use the Photo tab to submit your first proof.
              </Text>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 12,
    gap: 6,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
  },
  scroll: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
    gap: 12,
  },
  instructions: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 4,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
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
  photoPlaceholder: {
    height: 180,
    borderRadius: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 8,
  },
  photoText: {
    fontSize: 14,
    textAlign: 'center',
  },
  scannerPlaceholder: {
    height: 200,
    borderRadius: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 8,
  },
  scannerText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 4,
  },
  meta: {
    fontSize: 12,
    marginTop: 6,
  },
  emptyText: {
    textAlign: 'center',
    paddingVertical: 40,
    fontSize: 14,
  },
});
