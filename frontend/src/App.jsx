import { useState } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import axios from 'axios';
import { HelpCircle, Settings, ArrowRight, Loader2 } from 'lucide-react';

import FieldSelector from './components/FieldSelector';
import UploadZone from './components/UploadZone';
import ResultPanel from './components/ResultPanel';

export default function App() {
  const [selectedSchema, setSelectedSchema] = useState('invoice');
  const [customFields, setCustomFields] = useState([]);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSchemaChange = (schemaName, fieldsArray) => {
    setSelectedSchema(schemaName);
    setCustomFields(fieldsArray);
  };

  const handleExtractSubmit = async () => {
    if (!file) {
      toast.error('Please upload or select a document first.');
      return;
    }

    setIsLoading(true);
    setResult(null);
    setError(null);
    toast.loading('Processing document extraction...', { id: 'extract-process' });

    try {
      const formData = new FormData();
      formData.append('file', file);

      if (selectedSchema !== 'custom') {
        formData.append('schema_name', selectedSchema);
      } else {
        if (customFields && customFields.length > 0) {
          formData.append('fields', JSON.stringify(customFields));
        } else {
          throw new Error('Please add at least one custom field tag before calling extraction.');
        }
      }

      const url = `${import.meta.env.VITE_API_URL}/v1/extract`;
      const key = import.meta.env.VITE_API_KEY;

      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'x-api-key': key,
        },
      });

      if (response.data && response.data.status === 'success') {
        setResult(response.data);
        toast.success('Successfully finished document extraction!', { id: 'extract-process' });
      } else {
        throw new Error('Server responded with an invalid response format.');
      }
    } catch (err) {
      console.error(err);
      let errorMsg = 'Failed to extract document metadata.';
      if (err.response && err.response.data && err.response.data.error) {
        errorMsg = err.response.data.error.message || errorMsg;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error(`Extraction failed: ${errorMsg}`, { id: 'extract-process' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-[#1e293b] flex flex-col font-sans antialiased selection:bg-indigo-100/80">

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#ffffff',
            color: '#1e293b',
            border: '1px solid #e2e8f0',
            fontWeight: '600',
            fontSize: '13px',
          },
        }}
      />

      {/* Top Header bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0 shadow-sm relative z-10">
        <div className="flex items-center gap-3">
          {/* Custom blue grid logo */}
          <div className="bg-[#5850ec] text-white p-2 rounded-lg shadow-sm">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold tracking-wide text-gray-800">
              Doc Intelligence
            </span>
            <span className="border border-slate-250 text-slate-500 font-bold text-[9px] px-1.5 py-0.5 rounded tracking-wide uppercase bg-slate-50">
              BETA
            </span>
          </div>
        </div>

        {/* Right header tools */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534] text-[11px] font-bold px-3 py-1.5 rounded-full shadow-sm">
            {/* Green glowing status dot */}
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>API Connected</span>
          </div>

          <button
            type="button"
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md cursor-pointer active:scale-90"
            title="Help Support"
          >
            <HelpCircle size={20} />
          </button>

          <button
            type="button"
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md cursor-pointer active:scale-90"
            title="Settings"
          >
            <Settings size={20} />
          </button>

          <div
            className="w-8 h-8 rounded-full bg-slate-205 border border-slate-300 flex items-center justify-center text-gray-600 font-bold text-xs uppercase shadow-sm cursor-pointer hover:bg-slate-100 transition-colors"
            title="User Profile"
          >
            U
          </div>
        </div>
      </header>

      {/* Main Side-by-side divided container */}
      <main className="flex-1 flex flex-col lg:flex-row h-[calc(100vh-68px)] overflow-hidden">

        {/* Left configuration panel */}
        <div className="w-full lg:w-[350px] xl:w-[380px] bg-white border-b lg:border-b-0 lg:border-r border-gray-250 p-6 flex flex-col justify-between shrink-0 shadow-sm overflow-y-auto">

          <div className="space-y-6">
            <FieldSelector onSchemaChange={handleSchemaChange} />
            <UploadZone
              file={file}
              onFileSelect={(f) => setFile(f)}
              onFileRemove={() => setFile(null)}
              isLoading={isLoading}
            />
          </div>

          {/* Extract button container at the bottom */}
          <div className="pt-6 mt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleExtractSubmit}
              disabled={isLoading || !file}
              className={`w-full bg-[#5850ec] hover:bg-[#4d45d8] text-white rounded-md font-bold py-3.5 px-4 shadow flex items-center justify-center gap-2 cursor-pointer transition-all active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Extracting...</span>
                </>
              ) : (
                <>
                  <span>Extract Fields</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>

        </div>

        {/* Right output panel */}
        <div className="flex-1 p-6 bg-[#f8fafc] flex flex-col overflow-hidden relative">
          <ResultPanel
            result={result}
            isLoading={isLoading}
            error={error}
          />
        </div>

      </main>
    </div>
  );
}
