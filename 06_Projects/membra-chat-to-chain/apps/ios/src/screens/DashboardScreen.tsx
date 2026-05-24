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
import KPICard from '../components/KPICard';
import { membraApi } from '../api/membra_kpi_client';
import { DashboardCounts } from '../types/membra_kpi';

export default function DashboardScreen() {
  const [counts, setCounts] = useState<DashboardCounts | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const data = await membraApi.dashboard();
      setCounts(data.counts);
    } catch (e: any) {
      setError(e.message || 'Failed to load KPIs');
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
        <Text style={styles.loadingText}>Loading Membra KPIs...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <Text style={styles.errorTitle}>Connection Error</Text>
        <Text style={styles.errorText}>{error}</Text>
        <Text style={styles.hint}>Make sure the Membra KPI backend is running on http://localhost:8000</Text>
      </SafeAreaView>
    );
  }

  if (!counts) return null;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#007AFF" />
        }
      >
        <Text style={styles.header}>Membra KPIs</Text>
        <Text style={styles.subheader}>Assetification marketplace dashboard</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Inventory</Text>
          <View style={styles.row}>
            <View style={styles.half}>
              <KPICard title="Photos" value={counts.photos} color="#5856D6" />
            </View>
            <View style={styles.half}>
              <KPICard title="Inventory" value={counts.inventory} color="#34C759" />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Listings</Text>
          <View style={styles.row}>
            <View style={styles.half}>
              <KPICard title="Drafts" value={counts.drafts} color="#FF9500" />
            </View>
            <View style={styles.half}>
              <KPICard title="Public" value={counts.public_listings} color="#FF2D55" />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Proof & Events</Text>
          <KPICard title="KPI Cards" value={counts.kpis} color="#007AFF" />
          <KPICard title="Proofbook Entries" value={counts.proofs} color="#AF52DE" />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Event Outbox</Text>
          <View style={styles.row}>
            <View style={styles.half}>
              <KPICard title="Pending" value={counts.event_outbox_pending} color="#FF9500" />
            </View>
            <View style={styles.half}>
              <KPICard title="Delivered" value={counts.event_outbox_delivered} color="#34C759" />
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.half}>
              <KPICard title="Failed" value={counts.event_outbox_failed} color="#FF3B30" />
            </View>
            <View style={styles.half}>
              <KPICard title="Dead Letter" value={counts.event_outbox_dead_letter} color="#8E8E93" />
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f2f2f7',
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    fontSize: 32,
    fontWeight: '800',
    color: '#1c1c1e',
    marginBottom: 4,
  },
  subheader: {
    fontSize: 15,
    color: '#8e8e93',
    marginBottom: 20,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1c1c1e',
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  half: {
    flex: 1,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: '#8e8e93',
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FF3B30',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#8e8e93',
    textAlign: 'center',
    marginBottom: 8,
  },
  hint: {
    fontSize: 12,
    color: '#c7c7cc',
    textAlign: 'center',
  },
});
