'use client';

import { useState } from 'react';
import type { BriefingData } from '@/components/briefing/BriefingPDF';

/**
 * Self-contained "Download PDF" button for the executive briefing page.
 *
 * Usage:
 *   <DownloadPDFButton briefingData={data} />
 *
 * All PDF dependencies are loaded dynamically on click so there is
 * zero cost on initial page load.
 */
export default function DownloadPDFButton({
  briefingData,
}: {
  briefingData: BriefingData | null;
}) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    if (!briefingData || generating) return;

    setGenerating(true);
    setError(null);

    try {
      const { downloadBriefingPDF } = await import('@/lib/pdf/download-pdf');
      await downloadBriefingPDF(briefingData);
    } catch (err) {
      console.error('PDF generation failed:', err);
      setError(err instanceof Error ? err.message : 'PDF generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="inline-flex items-center gap-2">
      <button
        onClick={handleClick}
        disabled={!briefingData || generating}
        className={
          'flex items-center gap-2 px-4 py-2 rounded text-sm font-medium transition-colors ' +
          (!briefingData
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : generating
            ? 'bg-blue-800 text-blue-300 cursor-wait'
            : 'bg-blue-600 hover:bg-blue-500 text-white')
        }
        title={!briefingData ? 'Load briefing data first' : 'Download as PDF'}
      >
        {/* Download icon (SVG) */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={generating ? 'animate-pulse' : ''}
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        {generating ? 'Generating PDF...' : 'Download PDF'}
      </button>
      {error && (
        <span className="text-xs text-red-400" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
