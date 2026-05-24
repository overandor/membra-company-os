import { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, TextInput, Switch } from 'react-native';
import { router } from 'expo-router';
import { useTheme } from '@/hooks/useTheme';
import { ScreenHeader } from '@/components/ScreenHeader';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/stores/authStore';
import { useAppStore } from '@/stores/appStore';
import type { Claim } from '@/types';

type ProfileTab = 'overview' | 'wallet' | 'claims';

export default function ProfileScreen() {
  const { colors } = useTheme();
  const { owner, wallet, logout } = useAuthStore();
  const { rewardStatus, claims, addClaim } = useAppStore();
  const [activeTab, setActiveTab] = useState<ProfileTab>('overview');
  const [claimType, setClaimType] = useState('support');
  const [claimDescription, setClaimDescription] = useState('');
  const [payoutMethod, setPayoutMethod] = useState<'crypto' | 'bank_transfer' | 'paypal'>('crypto');

  const handleSubmitClaim = () => {
    if (!claimDescription.trim()) {
      Alert.alert('Required', 'Please describe your issue');
      return;
    }

    const claim: Claim = {
      id: `claim_${Date.now()}`,
      owner_id: owner?.id || 'demo_owner',
      type: claimType as Claim['type'],
      description: claimDescription.trim(),
      status: 'open',
      created_at: new Date().toISOString(),
    };

    addClaim(claim);
    setClaimDescription('');
    Alert.alert('Claim Submitted', 'Your support request has been logged. We will review it shortly.');
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: () => {
          logout();
          router.replace('/login');
        },
      },
    ]);
  };

  const tabs: { key: ProfileTab; label: string }[] = [
    { key: 'overview', label: 'Profile' },
    { key: 'wallet', label: 'Wallet' },
    { key: 'claims', label: 'Support' },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScreenHeader title="Profile" subtitle="Account, wallet, and support" />

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
            <Text style={[styles.tabText, { color: activeTab === t.key ? '#fff' : colors.text }]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {activeTab === 'overview' && (
          <>
            <View style={[styles.profileCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {(owner?.display_name || owner?.email || 'O').charAt(0).toUpperCase()}
                </Text>
              </View>
              <Text style={[styles.name, { color: colors.text }]}>
                {owner?.display_name || owner?.email || 'Demo Owner'}
              </Text>
              <Text style={[styles.email, { color: colors.textSecondary }]}>
                {owner?.email || 'demo@membra.labs'}
              </Text>
            </View>

            <Text style={[styles.sectionTitle, { color: colors.text }]}>Account Status</Text>
            <Card
              title="Identity Verification"
              description="Basic email verification complete. Connect wallet for payouts."
              status="Verified"
              statusColor={colors.accent}
            />
            <Card
              title="Asset Compliance"
              description="All registered assets follow safety and content guidelines."
              status="Compliant"
              statusColor={colors.accent}
            />

            <Button title="Logout" variant="danger" onPress={handleLogout} />
          </>
        )}

        {activeTab === 'wallet' && (
          <>
            <View style={[styles.walletCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.walletLabel, { color: colors.textSecondary }]}>Total Earned</Text>
              <Text style={[styles.walletAmount, { color: colors.text }]}>
                {rewardStatus ? `${rewardStatus.total_earned} ${rewardStatus.currency}` : '0.00 USDC'}
              </Text>
              <View style={styles.walletRow}>
                <View>
                  <Text style={[styles.walletSublabel, { color: colors.textMuted }]}>Pending</Text>
                  <Text style={[styles.walletSubvalue, { color: colors.warning }]}>
                    {rewardStatus?.pending_amount || '0'} {rewardStatus?.currency || 'USDC'}
                  </Text>
                </View>
                <View>
                  <Text style={[styles.walletSublabel, { color: colors.textMuted }]}>Paid Out</Text>
                  <Text style={[styles.walletSubvalue, { color: colors.accent }]}>
                    {rewardStatus?.total_paid || '0'} {rewardStatus?.currency || 'USDC'}
                  </Text>
                </View>
              </View>
            </View>

            <Text style={[styles.sectionTitle, { color: colors.text }]}>Payout Method</Text>
            <View style={[styles.payoutOptions, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              {(['crypto', 'bank_transfer', 'paypal'] as const).map((method) => (
                <TouchableOpacity
                  key={method}
                  style={[styles.payoutOption, { borderBottomColor: colors.border }]}
                  onPress={() => setPayoutMethod(method)}
                >
                  <Text style={[styles.payoutLabel, { color: colors.text }]}>
                    {method === 'crypto' ? 'Crypto Wallet' : method === 'bank_transfer' ? 'Bank Transfer' : 'PayPal'}
                  </Text>
                  <View style={[styles.radio, { borderColor: colors.border }]}>
                    {payoutMethod === method && (
                      <View style={[styles.radioInner, { backgroundColor: colors.primary }]} />
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={[styles.disclaimer, { color: colors.textMuted }]}>
              Rewards are processed after proof approval and campaign completion. Minimum payout threshold may apply.
            </Text>
          </>
        )}

        {activeTab === 'claims' && (
          <>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>Submit a Claim</Text>
            <View style={[styles.claimForm, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>Issue Type</Text>
              <View style={styles.typeRow}>
                {(['payment_missing', 'proof_rejected', 'campaign_issue', 'support'] as const).map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeChip,
                      {
                        backgroundColor: claimType === type ? colors.primary : colors.surfaceHighlight,
                        borderColor: colors.border,
                      },
                    ]}
                    onPress={() => setClaimType(type)}
                  >
                    <Text
                      style={[
                        styles.typeChipText,
                        { color: claimType === type ? '#fff' : colors.text },
                      ]}
                    >
                      {type.replace('_', ' ')}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={[styles.label, { color: colors.textSecondary }]}>Description</Text>
              <TextInput
                style={[
                  styles.textArea,
                  { backgroundColor: colors.background, borderColor: colors.border, color: colors.text },
                ]}
                placeholder="Describe your issue..."
                placeholderTextColor={colors.textMuted}
                multiline
                numberOfLines={4}
                value={claimDescription}
                onChangeText={setClaimDescription}
              />

              <Button title="Submit Claim" onPress={handleSubmitClaim} />
            </View>

            <Text style={[styles.sectionTitle, { color: colors.text }]}>Your Claims</Text>
            {claims.map((claim) => (
              <Card
                key={claim.id}
                title={claim.type.replace('_', ' ').toUpperCase()}
                description={claim.description}
                status={claim.status}
                statusColor={
                  claim.status === 'resolved'
                    ? colors.accent
                    : claim.status === 'under_review'
                    ? colors.warning
                    : colors.primary
                }
              >
                <Text style={[styles.meta, { color: colors.textMuted }]}>
                  Opened: {new Date(claim.created_at).toLocaleDateString()}
                </Text>
              </Card>
            ))}
            {claims.length === 0 && (
              <Text style={[styles.emptyText, { color: colors.textMuted }]}>
                No claims submitted. Use the form above if you need support.
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
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  tabText: {
    fontSize: 13,
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
  profileCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 24,
    alignItems: 'center',
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '700',
  },
  name: {
    fontSize: 20,
    fontWeight: '700',
  },
  email: {
    fontSize: 14,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 4,
  },
  walletCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 20,
  },
  walletLabel: {
    fontSize: 13,
    fontWeight: '600',
  },
  walletAmount: {
    fontSize: 32,
    fontWeight: '800',
    marginTop: 4,
    marginBottom: 16,
  },
  walletRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  walletSublabel: {
    fontSize: 12,
  },
  walletSubvalue: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 2,
  },
  payoutOptions: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  payoutOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  payoutLabel: {
    fontSize: 15,
    fontWeight: '600',
  },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  disclaimer: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  claimForm: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    gap: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
  },
  typeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  typeChipText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  textArea: {
    height: 100,
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 15,
    textAlignVertical: 'top',
  },
  meta: {
    fontSize: 12,
    marginTop: 6,
  },
  emptyText: {
    textAlign: 'center',
    paddingVertical: 32,
    fontSize: 14,
  },
});
