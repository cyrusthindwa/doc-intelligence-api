import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';

const MAX_SIZE = 25 * 1024 * 1024; // 25MB

function formatBytes(bytes, decimals = 2) {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export default function UploadZone({ file, onFileSelect, onFileRemove, isLoading }) {
    const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
        if (rejectedFiles && rejectedFiles.length > 0) {
            const reject = rejectedFiles[0];
            if (reject.file.size > MAX_SIZE) {
                toast.error('File size exceeds the 25MB limit.');
            } else {
                toast.error('Unsupported file type. Please upload PDF, PNG, or JPG.');
            }
            return;
        }

        if (acceptedFiles && acceptedFiles.length > 0) {
            onFileSelect(acceptedFiles[0]);
        }
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        maxSize: MAX_SIZE,
        multiple: false,
        disabled: isLoading,
        accept: {
            'application/pdf': ['.pdf'],
            'image/png': ['.png'],
            'image/jpeg': ['.jpeg', '.jpg'],
        },
    });

    return (
        <div className="space-y-3">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                Document
            </h3>

            <div
                {...getRootProps()}
                className={`bg-white border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer min-h-[170px] text-center
          ${isDragActive
                        ? 'border-[#5850ec] bg-indigo-50/30'
                        : 'border-slate-200 hover:border-gray-350 hover:bg-slate-50/40'
                    }
          ${isLoading ? 'opacity-55 cursor-not-allowed pointer-events-none' : ''}
        `}
            >
                <input {...getInputProps()} />

                {file ? (
                    <div className="space-y-3 w-full flex flex-col items-center">
                        {/* Custom file outline with upward arrow icon */}
                        <svg
                            className="w-10 h-10 text-indigo-500 animate-bounce"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="12" y1="18" x2="12" y2="12" />
                            <polyline points="9 15 12 12 15 15" />
                        </svg>
                        <div className="max-w-xs text-center space-y-0.5">
                            <p className="text-xs font-bold text-gray-800 truncate px-4" title={file.name}>
                                {file.name}
                            </p>
                            <p className="text-[10px] text-gray-400">
                                {formatBytes(file.size)}
                            </p>
                        </div>
                        {!isLoading && (
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onFileRemove();
                                }}
                                className="mt-1 flex items-center justify-center gap-1.5 bg-red-50 text-red-500 border border-red-100 hover:bg-red-100/60 rounded-md text-[10px] font-bold px-2.5 py-1 transition-all duration-150 cursor-pointer active:scale-95 shadow-sm"
                            >
                                <X size={12} />
                                Remove
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="space-y-2 flex flex-col items-center">
                        {/* Custom file outline with upward arrow icon */}
                        <svg
                            className="w-10 h-10 text-gray-300"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="12" y1="18" x2="12" y2="12" />
                            <polyline points="9 15 12 12 15 15" />
                        </svg>
                        <div>
                            <p className="text-xs font-bold text-gray-700">
                                Drop your document here
                            </p>
                            <p className="text-xs text-gray-400 mt-0.5">
                                or <span className="text-[#5850ec] underline font-semibold">browse files</span>
                            </p>
                        </div>
                        <p className="text-[9px] text-gray-400 font-medium tracking-wide">
                            PDF, PNG, JPG (MAX 25MB)
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
