import type { BriefingData } from '@/components/briefing/BriefingPDF';

/**
 * Dynamically imports @react-pdf/renderer + BriefingPDF, renders the
 * document to a blob, and triggers a browser download.
 *
 * All heavy dependencies are loaded lazily so the briefing page
 * stays fast on initial load.
 */
export async function downloadBriefingPDF(data: BriefingData): Promise<void> {
  const [reactMod, pdfMod, briefingMod] = await Promise.all([
    import('react'),
    import('@react-pdf/renderer'),
    import('@/components/briefing/BriefingPDF'),
  ]);

  const { createElement } = reactMod;
  const { pdf } = pdfMod;
  const BriefingPDF = briefingMod.default;

  const dateStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const element = createElement(BriefingPDF, { data, generatedAt: dateStr }) as any;
  const blob = await pdf(element).toBlob();

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `HealthPulse-Briefing-${data.state}-${new Date().toISOString().slice(0, 10)}.pdf`;
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
