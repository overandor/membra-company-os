import { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { ScreenHeader } from '@/components/ScreenHeader';
import { Card } from '@/components/Card';
import { useAppStore } from '@/stores/appStore';
import type { CampaignOffer, Campaign } from '@/types';

const DEMO_OFFERS: CampaignOffer[] = [
  {
    campaign: {
      id: 'camp_001',
      title: 'Downtown Coffee Campaign',
      description: 'Display coffee brand vinyl on your vehicle for 30 days. High-traffic downtown routes preferred.',
      brand_name: 'RoastDaily',
      reward_amount: 150,
      reward_currency: 'USDC',
      requirements: ['Vehicle in downtown area', 'Min 500 miles/month', 'Clean surface'],
      asset_types: ['vehicle', 'window'],
      start_date: '2026-06-01',
      end_date: '2026-06-30',
      status: 'active',
    },
    status: 'offered',
  },
  {
    campaign: {
      id: 'camp_002',
      title: 'Fitness Wearable Takeover',
      description: 'Wear branded athletic gear with QR code during your daily runs. GPS tracking required.',
      brand_name: 'FitPulse',
      reward_amount: 75,
      reward_currency: 'USDC',
      requirements: ['Daily outdoor activity', 'GPS proof required', 'Social share optional'],
      asset_types: ['wearable', 'bag'],
      start_date: '2026-05-20',
      end_date: '2026-07-20',
      status: 'active',
    },
    status: 'offered',
  },
  {
    campaign: {
      id: 'camp_003',
      title: 'Tech Startup Window Display',
      description: 'Place window cling on your home/office window facing a street with 1000+ daily foot traffic.',
      brand_name: 'CloudNine',
      reward_amount: 200,
      reward_currency: 'USDC',
      requirements: ['Street-facing window', 'Photo proof weekly', 'Min 4 weeks'],
      asset_types: ['window', 'sign'],
      start_date: '2026-05-15',
      end_date: '2026-08-15',
      status: 'active',
    },
    status: 'accepted',
    accepted_at: '2026-05-10T14:00:00Z',
  },
];

export default function CampaignsScreen() {
  const { colors } = useTheme();
  const { offers, setOffers, updateOffer } = useAppStore();
  const [filter, setFilter] = useState<'all' | 'offered' | 'accepted'>('all');

  // Seed demo offers if empty
  if (offers.length === 0) {
    setOffers(DEMO_OFFERS);
  }

  const filtered = offers.filter((o) => (filter === 'all' ? true : o.status === filter));

  const handleAccept = (offer: CampaignOffer) => {
    Alert.alert(
      'Accept Campaign?',
      `Join "${offer.campaign.title}" by ${offer.campaign.brand_name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Accept',
          onPress: () => {
            updateOffer({
              ...offer,
              status: 'accepted',
              accepted_at: new Date().toISOString(),
            });
            Alert.alert('Accepted', 'Check your media kit tab for delivery status.');
          },
        },
      ]
    );
  };

  const handleDecline = (offer: CampaignOffer) => {
    Alert.alert('Decline?', `Decline "${offer.campaign.title}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Decline',
        style: 'destructive',
        onPress: () => {
          updateOffer({ ...offer, status: 'declined' });
        },
      },
    ]);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScreenHeader title="Campaigns" subtitle="Available offers and active campaigns" />

      <View style={styles.filterRow}>
        {(['all', 'offered', 'accepted'] as const).map((f) => (
          <TouchableOpacity
            key={f}
            style={[
              styles.filterButton,
              {
                backgroundColor: filter === f ? colors.primary : colors.surface,
                borderColor: colors.border,
              },
            ]}
            onPress={() => setFilter(f)}
          >
            <Text
              style={[
                styles.filterText,
                { color: filter === f ? '#fff' : colors.text },
              ]}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {filtered.map((offer) => (
          <Card
            key={offer.campaign.id}
            title={offer.campaign.title}
            description={offer.campaign.description}
            status={offer.status}
            statusColor={
              offer.status === 'accepted'
                ? colors.accent
                : offer.status === 'declined'
                ? colors.danger
                : colors.primary
            }
          >
            <View style={styles.campaignDetails}>
              <Text style={[styles.brand, { color: colors.textSecondary }]}>
                {offer.campaign.brand_name}
              </Text>
              <Text style={[styles.reward, { color: colors.accent }]}>
                {offer.campaign.reward_amount} {offer.campaign.reward_currency}
              </Text>
            </View>
            <View style={styles.requirements}>
              {offer.campaign.requirements.map((req, i) => (
                <View key={i} style={[styles.reqTag, { backgroundColor: colors.surfaceHighlight }]}>
                  <Text style={[styles.reqText, { color: colors.textSecondary }]}>{req}</Text>
                </View>
              ))}
            </View>
            {offer.status === 'offered' && (
              <View style={styles.actions}>
                <TouchableOpacity
                  style={[styles.actionBtn, { backgroundColor: colors.primary }]}
                  onPress={() => handleAccept(offer)}
                >
                  <Text style={styles.actionBtnText}>Accept</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.actionBtn, { backgroundColor: colors.surfaceHighlight }]}
                  onPress={() => handleDecline(offer)}
                >
                  <Text style={[styles.actionBtnText, { color: colors.text }]}>Decline</Text>
                </TouchableOpacity>
              </View>
            )}
          </Card>
        ))}

        {filtered.length === 0 && (
          <Text style={[styles.emptyText, { color: colors.textMuted }]}>
            No {filter !== 'all' ? filter : ''} campaigns found.
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
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 12,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  filterText: {
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
  campaignDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  brand: {
    fontSize: 13,
    fontWeight: '600',
  },
  reward: {
    fontSize: 14,
    fontWeight: '700',
  },
  requirements: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 10,
  },
  reqTag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  reqText: {
    fontSize: 11,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  actionBtn: {
    flex: 1,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyText: {
    textAlign: 'center',
    paddingVertical: 40,
    fontSize: 14,
  },
});
