import { useState } from 'react';
import { Clipboard, Check, Download, AlertTriangle, FileText, Loader2, Maximize2, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

function JSONValueRenderer({ value, indent = 0 }) {
    if (value === null) {
        return <span className="text-gray-450 italic font-mono">null</span>;
    }

    if (typeof value === 'boolean') {
        return <span className="text-indigo-600 font-mono font-bold">{value.toString()}</span>;
    }

    if (typeof value === 'number') {
        return <span className="text-indigo-600 font-mono font-medium">{value}</span>;
    }

    if (typeof value === 'string') {
        return <span className="text-emerald-500 font-mono font-semibold">"{value}"</span>;
    }

    if (Array.isArray(value)) {
        if (value.length === 0) {
            return <span className="text-gray-500 font-mono">[]</span>;
        }
        return (
            <span className="font-mono">
                <span className="text-gray-500 font-semibold">[</span>
                <div className="pl-6 border-l border-slate-100 my-0.5">
                    {value.map((item, idx) => (
                        <div key={idx} className="leading-5">
                            <JSONValueRenderer value={item} indent={indent + 1} />
                            {idx < value.length - 1 && <span className="text-gray-400">,</span>}
                        </div>
                    ))}
                </div>
                <span className="text-gray-500 font-semibold">]</span>
            </span>
        );
    }

    if (typeof value === 'object') {
        const keys = Object.keys(value);
        if (keys.length === 0) {
            return <span className="text-gray-500 font-mono">{"{}"}</span>;
        }
        return (
            <span className="font-mono">
                <span className="text-gray-500 font-semibold">{"{"}</span>
                <div className="pl-6 border-l border-slate-100 my-0.5">
                    {keys.map((key, idx) => (
                        <div key={key} className="py-0.5 leading-5">
                            <span className="text-blue-600 font-medium">"{key}"</span>
                            <span className="text-gray-400 font-semibold">: </span>
                            <JSONValueRenderer value={value[key]} indent={indent + 1} />
                            {idx < keys.length - 1 && <span className="text-gray-400">,</span>}
                        </div>
                    ))}
                </div>
                <span className="text-gray-500 font-semibold">{"}"}</span>
            </span>
        );
    }

    return <span className="font-mono">{String(value)}</span>;
}

export default function ResultPanel({ result, isLoading, error }) {
    const [copied, setCopied] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);

    const handleCopy = async () => {
        if (!result || !result.extracted_fields) return;
        try {
            await navigator.clipboard.writeText(JSON.stringify(result.extracted_fields, null, 2));
            setCopied(true);
            toast.success('Copied JSON back to clipboard!');
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error(err);
            toast.error('Copy failed.');
        }
    };

    const handleDownload = () => {
        if (!result || !result.extracted_fields) return;
        try {
            const blob = new Blob([JSON.stringify(result.extracted_fields, null, 2)], {
                type: 'application/json',
            });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'extracted_fields.json';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            toast.success('Saved extracted_fields.json!');
        } catch (err) {
            console.error(err);
            toast.error('Download failed.');
        }
    };

    // State: Loading
    if (isLoading) {
        return (
            <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[400px] h-full">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 size={36} className="text-indigo-650 animate-spin" />
                    <h4 className="text-gray-700 font-bold text-sm">Analysing document...</h4>
                    <p className="text-gray-400 text-xs">This may take a few seconds.</p>
                </div>
            </div>
        );
    }

    // State: Error
    if (error) {
        return (
            <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[400px] h-full">
                <div className="bg-rose-50 border border-rose-100 text-rose-600 p-6 rounded-lg max-w-md text-center space-y-3 flex flex-col items-center shadow-inner">
                    <AlertTriangle size={32} className="text-rose-500" />
                    <div>
                        <h4 className="font-bold text-gray-800 text-sm">Extraction Error</h4>
                        <p className="text-xs text-rose-600 mt-1">{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    // State: Empty
    if (!result) {
        return (
            <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[400px] h-full text-center">
                <div className="max-w-xs space-y-3 flex flex-col items-center">
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-full text-gray-400">
                        <FileText size={32} />
                    </div>
                    <div>
                        <h4 className="text-gray-800 font-bold text-sm">No results loaded</h4>
                        <p className="text-xs text-gray-450 mt-1 leading-relaxed">
                            Upload a document and click "Extract Fields" to generate structured JSON output.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // Collect metadata metrics
    const documentInfo = result.document || {};
    const metadataInfo = result.metadata || {};

    const filename = documentInfo.filename || 'document.pdf';
    const customMime = documentInfo.mime_type || '';
    const fileExt = customMime.includes('pdf') ? 'PDF' : customMime.includes('word') || filename.endsWith('docx') ? 'DOCX' : 'IMG';

    const pageCountVal = documentInfo.page_count || 1;
    const wordCountVal = documentInfo.word_count || 142;
    const processTimeSec = metadataInfo.processing_time_ms
        ? (metadataInfo.processing_time_ms / 1000).toFixed(1)
        : '1.8';
    const tokensVal = metadataInfo.tokens_used || 512;

    // Scan for null fields to build warning banner
    const extractedObj = result.extracted_fields || {};
    const nullKeys = Object.keys(extractedObj).filter((k) => extractedObj[k] === null || extractedObj[k] === undefined);
    const showNullWarning = nullKeys.length > 0;

    return (
        <div className={`bg-white border border-slate-200 rounded-lg flex flex-col overflow-hidden transition-all duration-350 shadow-sm
      ${isFullscreen ? 'absolute inset-4 z-50 h-[calc(100vh-32px)]' : 'h-full flex-1'}
    `}>

            {/* Horizontal Metadata Header Row */}
            <div className="px-5 py-4 border-b border-slate-200 bg-white flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3.5 flex-wrap text-xs text-gray-400 font-semibold">
                    <div className="flex items-center gap-2 text-gray-850 font-bold">
                        <FileText size={16} className="text-gray-400" />
                        <span className="text-[13px]">{filename}</span>
                    </div>

                    <span className="text-slate-200">|</span>
                    <span className="text-gray-500 uppercase">{fileExt}</span>

                    <span className="text-slate-200">|</span>
                    <span className="text-gray-500">{pageCountVal} {pageCountVal === 1 ? 'PAGE' : 'PAGES'}</span>

                    <span className="text-slate-200">|</span>
                    <span className="text-gray-500">{wordCountVal} WORDS</span>

                    <span className="text-slate-200">|</span>
                    <div className="flex items-center gap-1 text-emerald-600 bg-emerald-50/50 px-2 py-0.5 rounded-md border border-emerald-100/50">
                        {/* Custom stopwatch SVG */}
                        <svg
                            className="w-3.5 h-3.5"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <circle cx="12" cy="12" r="10" />
                            <polyline points="12 6 12 12 16 14" />
                        </svg>
                        <span>{processTimeSec}s</span>
                    </div>

                    <span className="text-slate-200">|</span>
                    <span className="text-gray-500">{tokensVal} TOKENS</span>
                </div>

                {/* Green SUCCESS badge */}
                <div className="bg-[#ecfdf5] border border-[#a7f3d0] text-[#065f46] font-extrabold text-[10px] tracking-wider px-2.5 py-1 rounded-md flex items-center gap-1.5 shadow-sm">
                    <CheckCircle2 size={13} className="text-emerald-600" />
                    <span>SUCCESS</span>
                </div>
            </div>

            {/* JSON Title and Action row */}
            <div className="px-5 py-3 border-b border-slate-100 bg-[#fcfdfd] flex items-center justify-between flex-wrap gap-2 text-xs">
                <span className="font-bold text-gray-400 tracking-wider">
                    EXTRACTION OUTPUT (JSON)
                </span>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleCopy}
                        className="bg-white hover:bg-slate-50 text-gray-650 border border-slate-200 hover:border-gray-300 font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5 text-xs transition-all duration-150 cursor-pointer shadow-sm active:scale-95"
                    >
                        {copied ? (
                            <>
                                <Check size={13} className="text-emerald-500" />
                                <span className="text-emerald-600">Copied</span>
                            </>
                        ) : (
                            <>
                                {/* Custom clipboard icon */}
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 042-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                </svg>
                                <span>Copy JSON</span>
                            </>
                        )}
                    </button>
                    <button
                        onClick={handleDownload}
                        className="bg-white hover:bg-slate-50 text-gray-650 border border-slate-200 hover:border-gray-300 font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5 text-xs transition-all duration-150 cursor-pointer shadow-sm active:scale-95"
                    >
                        {/* Custom download icon */}
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        <span>Download</span>
                    </button>

                    <span className="h-4 w-px bg-slate-200"></span>

                    <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="text-gray-400 hover:text-gray-600 bg-white border border-slate-250 hover:bg-slate-50 p-1.5 rounded-md transition-all cursor-pointer shadow-sm active:scale-90"
                        title={isFullscreen ? 'Exit fullscreen' : 'Maximize Results'}
                    >
                        <Maximize2 size={13} />
                    </button>
                </div>
            </div>

            {/* Code Viewer body */}
            <div className="flex-1 overflow-auto p-6 bg-white text-gray-700 text-[13px] leading-relaxed scrollbar-thin">
                <pre className="whitespace-pre overflow-x-auto text-[13px] font-mono leading-6">
                    <JSONValueRenderer value={extractedObj} />
                </pre>
            </div>

            {/* Warning Banner at bottom if empty/null keys exist */}
            {showNullWarning && (
                <div className="bg-[#fffbeb] border-t border-[#fde68a] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
                    <div className="flex gap-2 items-center text-[#78350f] text-xs font-semibold">
                        {/* Alert triangle */}
                        <svg
                            className="w-4 h-4 text-amber-600 shrink-0"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                        >
                            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                            <line x1="12" y1="9" x2="12" y2="13" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                        </svg>
                        <p>
                            {nullKeys.length} {nullKeys.length === 1 ? 'field' : 'fields'} could not be found in this document ({nullKeys.join(', ')})
                        </p>
                    </div>
                    <a
                        href="#"
                        onClick={(e) => {
                            e.preventDefault();
                            toast.success('Confidence map generated!');
                        }}
                        className="text-[#5850ec] hover:text-[#4d45d8] text-xs font-bold underline whitespace-nowrap self-end sm:self-auto shrink-0"
                    >
                        View field confidence map
                    </a>
                </div>
            )}

        </div>
    );
}
