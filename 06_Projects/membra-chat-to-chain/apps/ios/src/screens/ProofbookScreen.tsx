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
import { ProofbookEntry, OutboxEvent, DashboardCounts } from '../types/membra_kpi';
import KPICard from '../components/KPICard';

export default function ProofbookScreen() {
  const [proofs, setProofs] = useState<ProofbookEntry[]>([]);
  const [events, setEvents] = useState<OutboxEvent[]>([]);
  const [counts, setCounts] = useState<DashboardCounts | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [pb, ob, dash] = await Promise.all([
        membraApi.proofbook(),
        membraApi.outboxEvents(undefined, 50),
        membraApi.dashboard(),
      ]);
      setProofs(pb.proofbook || []);
      setEvents(ob.events || []);
      setCounts(dash.counts);
    } catch (e: any) {
      setError(e.message || 'Failed to load proofbook');
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

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading proofbook...</Text>
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
        <Text style={styles.header}>Proofbook</Text>
        <Text style={styles.subheader}>Audit ledger & event outbox</Text>

        {counts && (
          <View style={styles.row}>
            <View style={styles.half}>
              <KPICard title="Proofs" value={counts.proofs} color="#5856D6" />
            </View>
            <View style={styles.half}>
              <KPICard
                title="Outbox Pending"
                value={counts.event_outbox_pending}
                subtitle={`${counts.event_outbox_delivered} delivered`}
                color="#FF9500"
              />
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Proofbook Entries</Text>
          {proofs.length === 0 ? (
            <Text style={styles.empty}>No proofbook entries yet.</Text>
          ) : (
            proofs.slice(0, 20).map((p: ProofbookEntry) => (
              <View key={p.proof_id} style={styles.listItem}>
                <View style={styles.listRow}>
                  <Text style={styles.listTitle}>{p.event_type}</Text>
                  <Text style={styles.hash}>{p.proof_hash?.slice(0, 16)}...</Text>
                </View>
                <Text style={styles.listSub}>Subject: {p.subject_type} / {p.subject_id?.slice(0, 12)}</Text>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Outbox Events</Text>
          {events.length === 0 ? (
            <Text style={styles.empty}>No outbox events yet.</Text>
          ) : (
            events.map((e: OutboxEvent) => (
              <View key={e.event_id} style={styles.listItem}>
                <View style={styles.listRow}>
                  <Text style={styles.listTitle}>{e.event_type}</Text>
                  <Text style={[styles.badge, e.status === 'pending' ? styles.pending : e.status === 'delivered' ? styles.delivered : styles.failed]}>
                    {e.status}
                  </Text>
                </View>
                <Text style={styles.listSub}>{e.subject_type} / {e.subject_id?.slice(0, 12)}</Text>
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
  listTitle: { fontSize: 14, fontWeight: '600', color: '#1c1c1e' },
  listSub: { fontSize: 12, color: '#8e8e93', marginTop: 2 },
  hash: { fontSize: 12, color: '#8e8e93', fontFamily: 'monospace' },
  badge: { fontSize: 11, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10, overflow: 'hidden' },
  pending: { backgroundColor: '#FF9500', color: '#fff' },
  delivered: { backgroundColor: '#34C759', color: '#fff' },
  failed: { backgroundColor: '#FF3B30', color: '#fff' },
  empty: { fontSize: 14, color: '#8e8e93', fontStyle: 'italic', paddingVertical: 8 },
  loadingText: { marginTop: 12, fontSize: 15, color: '#8e8e93' },
  errorTitle: { fontSize: 20, fontWeight: '700', color: '#FF3B30', marginBottom: 8 },
  errorText: { fontSize: 14, color: '#8e8e93', textAlign: 'center', marginBottom: 8 },
  hint: { fontSize: 12, color: '#c7c7cc', textAlign: 'center' },
});
