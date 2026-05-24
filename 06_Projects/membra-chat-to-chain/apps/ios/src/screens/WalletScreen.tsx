import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { membraApi } from '../api/membra_kpi_client';
import { WalletEvent, PayoutEligibility } from '../types/membra_kpi';
import KPICard from '../components/KPICard';

export default function WalletScreen() {
  const [events, setEvents] = useState<WalletEvent[]>([]);
  const [payouts, setPayouts] = useState<PayoutEligibility[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [eventsData, payoutsData] = await Promise.all([
        membraApi.walletEvents(),
        membraApi.payoutEligibility(),
      ]);
      setEvents(eventsData.wallet_events || []);
      setPayouts(payoutsData.payout_eligibility || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load wallet data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const totalLedger = events.reduce((sum: number, e: WalletEvent) => sum + (e.amount_usd || 0), 0);
  const totalEligible = payouts.reduce((sum: number, p: PayoutEligibility) => sum + (p.eligible_amount_usd || 0), 0);
  const pendingPayouts = payouts.filter((p: PayoutEligibility) => p.status === 'eligible_pending_external_settlement').length;

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading wallet...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <Text style={styles.errorTitle}>Connection Error</Text>
        <Text style={styles.errorText}>{error}</Text>
        <Text style={styles.hint}>Make sure Membra KPI backend is running on port 8000</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#007AFF" />
        }
      >
        <Text style={styles.header}>Membra Wallet</Text>
        <Text style={styles.subheader}>Ledger events & payout eligibility</Text>

        <View style={styles.row}>
          <View style={styles.half}>
            <KPICard title="Total Ledger" value={`$${totalLedger.toFixed(2)}`} color="#5856D6" />
          </View>
          <View style={styles.half}>
            <KPICard title="Eligible" value={`$${totalEligible.toFixed(2)}`} color="#34C759" />
          </View>
        </View>
        <KPICard title="Pending Payouts" value={pendingPayouts} subtitle={`${payouts.length} total records`} color="#FF9500" />

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Wallet Events</Text>
          {events.length === 0 ? (
            <Text style={styles.empty}>No wallet events yet.</Text>
          ) : (
            events.map((e: WalletEvent) => (
              <View key={e.ledger_event_id} style={styles.listItem}>
                <View style={styles.listRow}>
                  <Text style={styles.listTitle}>{e.event_type}</Text>
                  <Text style={[styles.listValue, e.amount_usd >= 0 ? styles.positive : styles.negative]}>
                    ${e.amount_usd.toFixed(2)}
                  </Text>
                </View>
                <Text style={styles.listSub}>Status: {e.status}</Text>
                <Text style={styles.listSub}>Subject: {e.subject_type} / {e.subject_id?.slice(0, 12)}</Text>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payout Eligibility</Text>
          {payouts.length === 0 ? (
            <Text style={styles.empty}>No payout records yet.</Text>
          ) : (
            payouts.map((p: PayoutEligibility) => (
              <View key={p.payout_event_id} style={styles.listItem}>
                <View style={styles.listRow}>
                  <Text style={styles.listTitle}>{p.eligibility_reason}</Text>
                  <Text style={styles.listValue}>${p.eligible_amount_usd.toFixed(2)}</Text>
                </View>
                <Text style={styles.listSub}>Status: {p.status}</Text>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  center: { justifyContent: 'center', alignItems: 'center', padding: 24 },
  scrollContent: { padding: 16, paddingBottom: 32 },
  header: { fontSize: 32, fontWeight: '800', color: '#1c1c1e', marginBottom: 4 },
  subheader: { fontSize: 15, color: '#8e8e93', marginBottom: 20 },
  row: { flexDirection: 'row', gap: 12 },
  half: { flex: 1 },
  section: { marginBottom: 20 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1c1c1e', marginBottom: 10 },
  listItem: { backgroundColor: '#fff', borderRadius: 12, padding: 14, marginBottom: 8 },
  listRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  listTitle: { fontSize: 15, fontWeight: '600', color: '#1c1c1e' },
  listValue: { fontSize: 15, fontWeight: '700', color: '#007AFF' },
  positive: { color: '#34C759' },
  negative: { color: '#FF3B30' },
  listSub: { fontSize: 12, color: '#8e8e93', marginTop: 2 },
  empty: { fontSize: 14, color: '#8e8e93', fontStyle: 'italic', paddingVertical: 8 },
  loadingText: { marginTop: 12, fontSize: 15, color: '#8e8e93' },
  errorTitle: { fontSize: 20, fontWeight: '700', color: '#FF3B30', marginBottom: 8 },
  errorText: { fontSize: 14, color: '#8e8e93', textAlign: 'center', marginBottom: 8 },
  hint: { fontSize: 12, color: '#c7c7cc', textAlign: 'center' },
});
