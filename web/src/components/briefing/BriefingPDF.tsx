import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from '@react-pdf/renderer';

/* ------------------------------------------------------------------ */
/*  Shared types — mirrors the BriefingData shape from the page       */
/* ------------------------------------------------------------------ */

export interface BriefingSummary {
  totalFacilities: number;
  avgStarRating: number;
  qualityFlags: number;
  careGapCount: number;
  highSVICounties: number;
}

export interface WorstFacility {
  facility_id: string;
  name: string;
  count: number;
}

export interface CareGap {
  facility_id: string;
  facility_name: string;
  measure_name: string;
  excess_readmission_ratio: string;
}

export interface EquityConcern {
  county_fips: string;
  svi_score: string;
  poverty_rate: string;
  uninsured_rate: string;
  minority_pct: string;
}

export interface BriefingData {
  state: string;
  summary: BriefingSummary;
  starDistribution: Record<string, string | number>;
  worstFacilities: WorstFacility[];
  topCareGaps: CareGap[];
  equityConcerns: EquityConcern[];
}

/* ------------------------------------------------------------------ */
/*  Styles                                                            */
/* ------------------------------------------------------------------ */

const colors = {
  headerBg: '#0F1B2D',
  headerText: '#FFFFFF',
  accent: '#3B82F6',
  sectionBorder: '#E2E8F0',
  bodyText: '#1E293B',
  mutedText: '#64748B',
  white: '#FFFFFF',
  lightGray: '#F8FAFC',
  red: '#DC2626',
  yellow: '#D97706',
  green: '#16A34A',
  orange: '#EA580C',
};

const s = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 10,
    paddingTop: 30,
    paddingBottom: 40,
    paddingHorizontal: 40,
    color: colors.bodyText,
  },
  /* Header */
  header: {
    backgroundColor: colors.headerBg,
    marginHorizontal: -40,
    marginTop: -30,
    paddingHorizontal: 40,
    paddingVertical: 24,
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 20,
    fontFamily: 'Helvetica-Bold',
    color: colors.headerText,
    marginBottom: 4,
  },
  headerSub: {
    fontSize: 10,
    color: '#94A3B8',
  },
  headerMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  headerMetaItem: {
    fontSize: 9,
    color: '#94A3B8',
  },
  /* Sections */
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontFamily: 'Helvetica-Bold',
    color: colors.headerBg,
    marginBottom: 8,
    paddingBottom: 4,
    borderBottomWidth: 2,
    borderBottomColor: colors.accent,
  },
  /* Summary stats */
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: colors.lightGray,
    borderRadius: 4,
    padding: 10,
    marginHorizontal: 3,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontFamily: 'Helvetica-Bold',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 8,
    color: colors.mutedText,
    textTransform: 'uppercase',
  },
  /* Tables */
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: colors.lightGray,
    borderBottomWidth: 1,
    borderBottomColor: colors.sectionBorder,
    paddingVertical: 6,
    paddingHorizontal: 6,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    paddingVertical: 5,
    paddingHorizontal: 6,
  },
  tableCell: {
    fontSize: 9,
    color: colors.bodyText,
  },
  tableCellHeader: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    color: colors.mutedText,
    textTransform: 'uppercase',
  },
  /* Footer */
  footer: {
    position: 'absolute',
    bottom: 20,
    left: 40,
    right: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: colors.sectionBorder,
    paddingTop: 8,
  },
  footerText: {
    fontSize: 7,
    color: colors.mutedText,
  },
  /* Badges */
  badge: {
    fontSize: 7,
    fontFamily: 'Helvetica-Bold',
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 3,
  },
  badgeCritical: { backgroundColor: '#FEE2E2', color: colors.red },
  badgeWarning: { backgroundColor: '#FEF3C7', color: colors.yellow },
  badgeGood: { backgroundColor: '#DCFCE7', color: colors.green },
  /* Misc */
  emptyText: {
    fontSize: 9,
    color: colors.mutedText,
    fontStyle: 'italic',
  },
});

/* ------------------------------------------------------------------ */
/*  Helper components                                                 */
/* ------------------------------------------------------------------ */

function Badge({ level }: { level: 'critical' | 'warning' | 'good' }) {
  const badgeStyle =
    level === 'critical'
      ? s.badgeCritical
      : level === 'warning'
      ? s.badgeWarning
      : s.badgeGood;
  const label = level.toUpperCase();
  return <Text style={[s.badge, badgeStyle]}>{label}</Text>;
}

function ratingColor(avg: number): string {
  return avg >= 4 ? colors.green : avg >= 3 ? colors.yellow : colors.red;
}

/* ------------------------------------------------------------------ */
/*  Document                                                          */
/* ------------------------------------------------------------------ */

interface BriefingPDFProps {
  data: BriefingData;
  generatedAt?: string;
}

export default function BriefingPDF({ data, generatedAt }: BriefingPDFProps) {
  const dateStr =
    generatedAt ??
    new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

  const { summary } = data;

  return (
    <Document>
      <Page size="A4" style={s.page}>
        {/* ---- Header ---- */}
        <View style={s.header}>
          <Text style={s.headerTitle}>
            HealthPulse AI — Executive Briefing
          </Text>
          <Text style={s.headerSub}>
            AI-powered state-level healthcare intelligence from CMS data
          </Text>
          <View style={s.headerMeta}>
            <Text style={s.headerMetaItem}>State: {data.state}</Text>
            <Text style={s.headerMetaItem}>{dateStr}</Text>
          </View>
        </View>

        {/* ---- Summary Stats ---- */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Performance Overview</Text>
          <View style={s.statsRow}>
            <View style={s.statBox}>
              <Text style={s.statValue}>
                {summary.totalFacilities.toLocaleString()}
              </Text>
              <Text style={s.statLabel}>Total Facilities</Text>
            </View>
            <View style={s.statBox}>
              <Text
                style={[
                  s.statValue,
                  { color: ratingColor(summary.avgStarRating) },
                ]}
              >
                {summary.avgStarRating.toFixed(2)}
              </Text>
              <Text style={s.statLabel}>Avg Star Rating</Text>
            </View>
            <View style={s.statBox}>
              <Text style={[s.statValue, { color: colors.red }]}>
                {summary.qualityFlags.toLocaleString()}
              </Text>
              <Text style={s.statLabel}>Quality Flags</Text>
            </View>
            <View style={s.statBox}>
              <Text style={[s.statValue, { color: colors.yellow }]}>
                {summary.careGapCount.toLocaleString()}
              </Text>
              <Text style={s.statLabel}>Care Gaps</Text>
            </View>
            <View style={s.statBox}>
              <Text style={[s.statValue, { color: colors.orange }]}>
                {summary.highSVICounties.toLocaleString()}
              </Text>
              <Text style={s.statLabel}>High-Risk Counties</Text>
            </View>
          </View>
        </View>

        {/* ---- Star Distribution ---- */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Star Rating Distribution</Text>
          <View style={s.statsRow}>
            {[1, 2, 3, 4, 5].map((star) => {
              const count = parseInt(
                String(data.starDistribution[String(star)] ?? 0),
                10
              );
              const barColor =
                star >= 4
                  ? colors.green
                  : star >= 3
                  ? colors.yellow
                  : colors.red;
              return (
                <View key={star} style={s.statBox}>
                  <Text style={[s.statValue, { color: barColor }]}>
                    {count}
                  </Text>
                  <Text style={s.statLabel}>{star} Star</Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* ---- Worst Facilities ---- */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>
            Quality Concerns — Worst Performing Facilities
          </Text>
          {data.worstFacilities.length === 0 ? (
            <Text style={s.emptyText}>
              No significant quality concerns identified.
            </Text>
          ) : (
            <View>
              <View style={s.tableHeader}>
                <Text style={[s.tableCellHeader, { flex: 0.5 }]}>#</Text>
                <Text style={[s.tableCellHeader, { flex: 4 }]}>
                  Facility Name
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Flags
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Severity
                </Text>
              </View>
              {data.worstFacilities.map((f, i) => (
                <View key={f.facility_id} style={s.tableRow}>
                  <Text style={[s.tableCell, { flex: 0.5 }]}>{i + 1}</Text>
                  <Text style={[s.tableCell, { flex: 4 }]}>{f.name}</Text>
                  <Text
                    style={[
                      s.tableCell,
                      { flex: 1, textAlign: 'right', color: colors.red },
                    ]}
                  >
                    {f.count}
                  </Text>
                  <View
                    style={{
                      flex: 1,
                      alignItems: 'flex-end',
                      justifyContent: 'center',
                    }}
                  >
                    <Badge level={f.count >= 5 ? 'critical' : 'warning'} />
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* ---- Readmission / Care Gaps ---- */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>
            Readmission Analysis — Excess Ratio {'>'} 1.05
          </Text>
          {data.topCareGaps.length === 0 ? (
            <Text style={s.emptyText}>
              No excess readmission concerns detected.
            </Text>
          ) : (
            <View>
              <View style={s.tableHeader}>
                <Text style={[s.tableCellHeader, { flex: 3 }]}>Facility</Text>
                <Text style={[s.tableCellHeader, { flex: 3 }]}>Measure</Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Ratio
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Severity
                </Text>
              </View>
              {data.topCareGaps.map((gap, i) => {
                const ratio = parseFloat(gap.excess_readmission_ratio || '0');
                const level: 'critical' | 'warning' =
                  ratio >= 1.15 ? 'critical' : 'warning';
                return (
                  <View key={`${gap.facility_id}-${i}`} style={s.tableRow}>
                    <Text style={[s.tableCell, { flex: 3 }]}>
                      {gap.facility_name}
                    </Text>
                    <Text
                      style={[s.tableCell, { flex: 3, color: colors.mutedText }]}
                    >
                      {gap.measure_name}
                    </Text>
                    <Text
                      style={[
                        s.tableCell,
                        { flex: 1, textAlign: 'right', color: colors.yellow },
                      ]}
                    >
                      {ratio.toFixed(3)}
                    </Text>
                    <View
                      style={{
                        flex: 1,
                        alignItems: 'flex-end',
                        justifyContent: 'center',
                      }}
                    >
                      <Badge level={level} />
                    </View>
                  </View>
                );
              })}
            </View>
          )}
        </View>

        {/* ---- Equity Concerns ---- */}
        {data.equityConcerns.length > 0 && (
          <View style={s.section} break>
            <Text style={s.sectionTitle}>
              Health Equity — High Social Vulnerability Counties
            </Text>
            <View>
              <View style={s.tableHeader}>
                <Text style={[s.tableCellHeader, { flex: 1.5 }]}>
                  County FIPS
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  SVI Score
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Poverty
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Uninsured
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Minority %
                </Text>
                <Text
                  style={[s.tableCellHeader, { flex: 1, textAlign: 'right' }]}
                >
                  Severity
                </Text>
              </View>
              {data.equityConcerns.map((c, i) => {
                const svi = parseFloat(c.svi_score || '0');
                const poverty = parseFloat(c.poverty_rate || '0');
                const uninsured = parseFloat(c.uninsured_rate || '0');
                const minority = parseFloat(c.minority_pct || '0');
                return (
                  <View key={`${c.county_fips}-${i}`} style={s.tableRow}>
                    <Text style={[s.tableCell, { flex: 1.5 }]}>
                      {c.county_fips}
                    </Text>
                    <Text
                      style={[
                        s.tableCell,
                        { flex: 1, textAlign: 'right', color: colors.orange },
                      ]}
                    >
                      {svi.toFixed(3)}
                    </Text>
                    <Text style={[s.tableCell, { flex: 1, textAlign: 'right' }]}>
                      {isNaN(poverty) ? 'N/A' : `${(poverty * 100).toFixed(1)}%`}
                    </Text>
                    <Text style={[s.tableCell, { flex: 1, textAlign: 'right' }]}>
                      {isNaN(uninsured)
                        ? 'N/A'
                        : `${(uninsured * 100).toFixed(1)}%`}
                    </Text>
                    <Text style={[s.tableCell, { flex: 1, textAlign: 'right' }]}>
                      {c.minority_pct
                        ? `${(minority * 100).toFixed(1)}%`
                        : 'N/A'}
                    </Text>
                    <View
                      style={{
                        flex: 1,
                        alignItems: 'flex-end',
                        justifyContent: 'center',
                      }}
                    >
                      <Badge level={svi >= 0.9 ? 'critical' : 'warning'} />
                    </View>
                  </View>
                );
              })}
            </View>
          </View>
        )}

        {/* ---- Footer ---- */}
        <View style={s.footer} fixed>
          <Text style={s.footerText}>
            HealthPulse AI — Confidential Executive Briefing
          </Text>
          <Text
            style={s.footerText}
            render={({ pageNumber, totalPages }) =>
              `Page ${pageNumber} of ${totalPages}`
            }
          />
        </View>
      </Page>
    </Document>
  );
}
