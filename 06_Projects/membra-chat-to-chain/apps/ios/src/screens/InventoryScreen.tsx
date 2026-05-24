import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  SafeAreaView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { membraApi } from '../api/membra_kpi_client';
import { InventoryItem, ListingDraft, PublicListing } from '../types/membra_kpi';
import KPICard from '../components/KPICard';

export default function InventoryScreen() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [drafts, setDrafts] = useState<ListingDraft[]>([]);
  const [publicListings, setPublicListings] = useState<PublicListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [invData, draftData, pubData] = await Promise.all([
        membraApi.inventory(),
        membraApi.listingDrafts(),
        membraApi.publicListings(),
      ]);
      setInventory(invData.inventory || []);
      setDrafts(draftData.drafts || []);
      setPublicListings(pubData.public_listings || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load inventory');
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

  async function handleRequestVisibility(listingId: string) {
    try {
      const res = await membraApi.requestVisibility(listingId);
      Alert.alert('Success', `Visibility requested for ${res.listing?.title || listingId}`);
      load();
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  }

  async function handleConfirmVisibility(listingId: string) {
    try {
      const res = await membraApi.confirmVisibility(listingId);
      Alert.alert('Success', `Visibility confirmed. Public listing: ${res.public_listing?.public_listing_id}`);
      load();
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading inventory...</Text>
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
        <Text style={styles.header}>Inventory</Text>
        <Text style={styles.subheader}>Assets, drafts & marketplace</Text>

        <View style={styles.row}>
          <View style={styles.half}>
            <KPICard title="Inventory" value={inventory.length} color="#5856D6" />
          </View>
          <View style={styles.half}>
            <KPICard title="Drafts" value={drafts.length} color="#FF9500" />
          </View>
        </View>
        <KPICard title="Public Listings" value={publicListings.length} color="#34C759" />

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Inventory Items</Text>
          {inventory.length === 0 ? (
            <Text style={styles.empty}>No inventory items yet. Upload a photo to get started.</Text>
          ) : (
            inventory.map((item: InventoryItem) => (
              <View key={item.inventory_item_id} style={styles.listItem}>
                <Text style={styles.listTitle}>{item.detected_name || item.sku}</Text>
                <Text style={styles.listSub}>{item.description}</Text>
                <Text style={styles.listMeta}>
                  SKU: {item.sku} | Type: {item.asset_type} | Score: {item.kpi_score}
                </Text>
                <Text style={styles.listMeta}>
                  ${item.suggested_price_low} - ${item.suggested_price_high} {item.pricing_unit}
                </Text>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Drafts</Text>
          {drafts.length === 0 ? (
            <Text style={styles.empty}>No drafts yet.</Text>
          ) : (
            drafts.map((d: ListingDraft) => (
              <View key={d.listing_id} style={styles.listItem}>
                <Text style={styles.listTitle}>{d.title}</Text>
                <Text style={styles.listSub}>{d.description}</Text>
                <Text style={styles.listMeta}>Status: {d.status}</Text>
                <View style={styles.actions}>
                  {d.status === 'draft' && (
                    <TouchableOpacity style={styles.button} onPress={() => handleRequestVisibility(d.listing_id)}>
                      <Text style={styles.buttonText}>Request Visibility</Text>
                    </TouchableOpacity>
                  )}
                  {d.status === 'visibility_requested' && (
                    <TouchableOpacity style={[styles.button, styles.confirmBtn]} onPress={() => handleConfirmVisibility(d.listing_id)}>
                      <Text style={styles.buttonText}>Confirm Visibility</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Public Listings</Text>
          {publicListings.length === 0 ? (
            <Text style={styles.empty}>No public listings yet.</Text>
          ) : (
            publicListings.map((p: PublicListing) => (
              <View key={p.public_listing_id} style={styles.listItem}>
                <Text style={styles.listTitle}>{p.title}</Text>
                <Text style={styles.listSub}>{p.description}</Text>
                <Text style={styles.listMeta}>
                  ${p.price_low} - ${p.price_high} | Status: {p.visibility_status}
                </Text>
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
  listTitle: { fontSize: 15, fontWeight: '600', color: '#1c1c1e', marginBottom: 2 },
  listSub: { fontSize: 13, color: '#3a3a3c', marginTop: 2 },
  listMeta: { fontSize: 12, color: '#8e8e93', marginTop: 4 },
  empty: { fontSize: 14, color: '#8e8e93', fontStyle: 'italic', paddingVertical: 8 },
  actions: { flexDirection: 'row', gap: 8, marginTop: 8 },
  button: { backgroundColor: '#007AFF', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 14 },
  confirmBtn: { backgroundColor: '#34C759' },
  buttonText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  loadingText: { marginTop: 12, fontSize: 15, color: '#8e8e93' },
  errorTitle: { fontSize: 20, fontWeight: '700', color: '#FF3B30', marginBottom: 8 },
  errorText: { fontSize: 14, color: '#8e8e93', textAlign: 'center', marginBottom: 8 },
  hint: { fontSize: 12, color: '#c7c7cc', textAlign: 'center' },
});
