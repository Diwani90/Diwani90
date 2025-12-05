import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';

const SettingsScreen = () => {
  const settingsItems = [
    { icon: 'person-outline', title: 'الملف الشخصي', subtitle: 'إدارة معلوماتك الشخصية' },
    { icon: 'notifications-outline', title: 'الإشعارات', subtitle: 'إعدادات الإشعارات' },
    { icon: 'language-outline', title: 'اللغة', subtitle: 'العربية' },
    { icon: 'help-circle-outline', title: 'المساعدة', subtitle: 'الأسئلة الشائعة والدعم' },
    { icon: 'information-circle-outline', title: 'حول التطبيق', subtitle: 'الإصدار 1.0.0' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>الإعدادات</Text>
      </View>
      
      <ScrollView style={styles.content}>
        {settingsItems.map((item, index) => (
          <TouchableOpacity key={index} style={styles.settingItem}>
            <View style={styles.settingIcon}>
              <Ionicons name={item.icon} size={24} color={Colors.primary} />
            </View>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>{item.title}</Text>
              <Text style={styles.settingSubtitle}>{item.subtitle}</Text>
            </View>
            <Ionicons name="chevron-back" size={20} color={Colors.gray[400]} />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: Colors.primary,
    paddingTop: 50,
    paddingBottom: Spacing.lg,
    paddingHorizontal: Spacing.lg,
    alignItems: 'center',
  },
  headerTitle: { fontSize: FontSizes.xl, fontWeight: 'bold', color: Colors.white },
  content: { flex: 1, padding: Spacing.lg },
  settingItem: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingIcon: {
    width: 40,
    height: 40,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: Spacing.md,
  },
  settingInfo: { flex: 1 },
  settingTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  settingSubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    textAlign: 'right',
  },
});

export default SettingsScreen;

