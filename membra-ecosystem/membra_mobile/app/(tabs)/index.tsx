import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { useTheme } from '@/hooks/useTheme';
import { ScreenHeader } from '@/components/ScreenHeader';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { useAppStore } from '@/stores/appStore';

export default function HomeScreen() {
  const { colors } = useTheme();
  const { assets, offers, proofs, rewardStatus } = useAppStore();

  const activeAssets = assets.filter((a) => a.status === 'active').length;
  const pendingProofs = proofs.filter((p) => p.status === 'pending').length;
  const availableOffers = offers.filter((o) => o.status === 'offered').length;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScreenHeader
        title="MEMBRA"
        subtitle="Owner Dashboard"
      />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {/* Stats Summary */}
        <View style={styles.statsRow}>
          <View style={[styles.statCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.statNumber, { color: colors.primary }]}>{activeAssets}</Text>
            <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Active Assets</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.statNumber, { color: colors.warning }]}>{pendingProofs}</Text>
            <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Pending Proofs</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.statNumber, { color: colors.accent }]}>{availableOffers}</Text>
            <Text style={[styles.statLabel, { color: colors.textSecondary }]}>New Offers</Text>
          </View>
        </View>

        {/* Quick Actions */}
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: colors.primary }]}
            onPress={() => router.push('/assets')}
          >
            <Text style={styles.actionButtonText}>+ Register Asset</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: colors.accent }]}
            onPress={() => router.push('/proof')}
          >
            <Text style={styles.actionButtonText}>📷 Submit Proof</Text>
          </TouchableOpacity>
        </View>

        {/* Reward Status */}
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Reward Status</Text>
        <Card
          title={rewardStatus ? `${rewardStatus.total_earned} ${rewardStatus.currency}` : 'Connect Wallet'}
          description={
            rewardStatus
              ? `${rewardStatus.pending_amount} pending · Next payout: ${rewardStatus.next_payout_date || 'TBD'}`
              : 'Link your wallet to view reward status and payout readiness.'
          }
          status={rewardStatus ? 'Active' : 'Setup'}
          statusColor={rewardStatus ? colors.accent : colors.warning}
          onPress={() => router.push('/profile')}
        />

        {/* Recent Activity */}
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Recent Activity</Text>
        {proofs.slice(0, 3).map((proof) => (
          <Card
            key={proof.id}
            title={`Proof: ${proof.campaign_id}`}
            description={`Status: ${proof.status}`}
            status={proof.status}
            statusColor={
              proof.status === 'approved'
                ? colors.accent
                : proof.status === 'rejected'
                ? colors.danger
                : colors.warning
            }
          />
        ))}
        {proofs.length === 0 && (
          <Text style={[styles.emptyText, { color: colors.textMuted }]}>
            No proof submissions yet. Submit your first proof to get started.
          </Text>
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
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '800',
  },
  statLabel: {
    fontSize: 11,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
    marginTop: 8,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  actionButton: {
    flex: 1,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyText: {
    textAlign: 'center',
    paddingVertical: 24,
    fontSize: 14,
  },
});
