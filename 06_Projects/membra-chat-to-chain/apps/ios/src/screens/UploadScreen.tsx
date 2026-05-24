import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { membraApi } from '../api/membra_kpi_client';

export default function UploadScreen() {
  const [ownerId, setOwnerId] = useState('owner_default');
  const [roomType, setRoomType] = useState('');
  const [monetizationGoal, setMonetizationGoal] = useState('');
  const [userNotes, setUserNotes] = useState('');
  const [locationHint, setLocationHint] = useState('');
  const [loading, setLoading] = useState(false);

  async function handlePhotoAnalyze() {
    // On iPhone, this would use ImagePicker; for demo we simulate with a dummy FormData
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('owner_id', ownerId);
      formData.append('room_type', roomType);
      formData.append('monetization_goal', monetizationGoal);
      formData.append('user_notes', userNotes);
      formData.append('location_hint', locationHint);
      // In real app, append file from ImagePicker here
      // formData.append('image', { uri: ..., name: 'photo.jpg', type: 'image/jpeg' } as any);

      const res = await membraApi.analyzePhoto(formData);
      Alert.alert('Photo Analyzed', `Detected ${res.detected_inventory?.length || 0} items. Room summary: ${res.room_summary || 'N/A'}`);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleKPIUpload() {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('owner_id', ownerId);
      // In real app, append CSV/XLSX file here
      // formData.append('file', { uri: ..., name: 'data.csv', type: 'text/csv' } as any);

      const res = await membraApi.uploadKPI(formData);
      Alert.alert('KPI Uploaded', `Rows: ${res.summary?.row_count || 0}, Columns: ${res.summary?.column_count || 0}`);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>Upload</Text>
        <Text style={styles.subheader}>Analyze photos & upload KPI datasets</Text>

        <View style={styles.form}>
          <Text style={styles.label}>Owner ID</Text>
          <TextInput style={styles.input} value={ownerId} onChangeText={setOwnerId} placeholder="owner_default" />

          <Text style={styles.label}>Room Type</Text>
          <TextInput style={styles.input} value={roomType} onChangeText={setRoomType} placeholder="e.g. living_room, bedroom" />

          <Text style={styles.label}>Monetization Goal</Text>
          <TextInput style={styles.input} value={monetizationGoal} onChangeText={setMonetizationGoal} placeholder="e.g. short_term_rental" />

          <Text style={styles.label}>User Notes</Text>
          <TextInput style={styles.input} value={userNotes} onChangeText={setUserNotes} placeholder="Optional notes" />

          <Text style={styles.label}>Location Hint</Text>
          <TextInput style={styles.input} value={locationHint} onChangeText={setLocationHint} placeholder="e.g. downtown NYC" />
        </View>

        {loading ? (
          <ActivityIndicator size="large" color="#007AFF" style={{ marginVertical: 20 }} />
        ) : (
          <>
            <TouchableOpacity style={styles.button} onPress={handlePhotoAnalyze}>
              <Text style={styles.buttonText}>Analyze Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.button, styles.secondaryBtn]} onPress={handleKPIUpload}>
              <Text style={[styles.buttonText, styles.secondaryText]}>Upload KPI Dataset</Text>
            </TouchableOpacity>
          </>
        )}

        <Text style={styles.note}>
          Note: In a real iPhone build, this screen would integrate with react-native-image-picker for photo selection and document picker for CSV/XLSX files.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  scrollContent: { padding: 16, paddingBottom: 32 },
  header: { fontSize: 32, fontWeight: '800', color: '#1c1c1e', marginBottom: 4 },
  subheader: { fontSize: 15, color: '#8e8e93', marginBottom: 20 },
  form: { marginBottom: 16 },
  label: { fontSize: 13, fontWeight: '600', color: '#3a3a3c', marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    color: '#1c1c1e',
    borderWidth: 1,
    borderColor: '#e5e5ea',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  secondaryBtn: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#007AFF' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  secondaryText: { color: '#007AFF' },
  note: { fontSize: 12, color: '#8e8e93', textAlign: 'center', marginTop: 16, lineHeight: 18 },
});
