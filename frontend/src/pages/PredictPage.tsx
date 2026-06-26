import React, { useState } from 'react';
import DropZone from '../components/prediction/DropZone';
import PredictionResult from '../components/prediction/PredictionResult';
import GlassCard from '../components/ui/GlassCard';
import { Cpu, Loader2, Sparkles } from 'lucide-react';
import predictionsApi from '../api/predictions';
import toast from 'react-hot-toast';

const PredictPage: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState<'EfficientNet-B3' | 'ResNet50'>('EfficientNet-B3');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setResult(null); // Clear previous results
  };

  const handlePredict = async () => {
    if (!file) {
      toast.error('Please upload a drill core image first.');
      return;
    }
    
    setLoading(true);
    const toastId = toast.loading('Uploading and preprocessing image...');
    
    try {
      const response = await predictionsApi.uploadImage(file, selectedModel);
      toast.loading('Running ML lithology classification...', { id: toastId });
      
      // Since it's a celery task or immediate response, if task is async, poll it.
      // In this setup, we poll the prediction details endpoint
      let predData = response;
      if (predData.status === 'pending' || predData.status === 'processing') {
        const checkStatus = async () => {
          for (let i = 0; i < 20; i++) {
            await new Promise(r => setTimeout(r, 1000));
            const check = await predictionsApi.getPrediction(predData.id);
            if (check.status === 'completed') {
              return check;
            }
            if (check.status === 'failed') {
              throw new Error('Prediction job failed on celery worker.');
            }
          }
          throw new Error('Prediction job timed out.');
        };
        predData = await checkStatus();
      }
      
      setResult(predData);
      toast.success('Classification completed successfully!', { id: toastId });
    } catch (err: any) {
      toast.error(err.message || 'Failed to complete classification.', { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Core Classifier Lab</h1>
        <p className="text-slate-400 text-sm mt-1">Upload drill core scans to perform petrographic classification.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload & Model Configurations */}
        <div className="space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-md font-bold text-white mb-4">1. Select Target Model</h3>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setSelectedModel('EfficientNet-B3')}
                className={`p-4 rounded-xl flex flex-col items-center gap-2 border text-center transition-all cursor-pointer ${
                  selectedModel === 'EfficientNet-B3'
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <Cpu className="h-5 w-5" />
                <span className="text-xs font-semibold">EfficientNet-B3</span>
                <span className="text-[9px] text-slate-500">92.4% Accuracy</span>
              </button>
              
              <button
                type="button"
                onClick={() => setSelectedModel('ResNet50')}
                className={`p-4 rounded-xl flex flex-col items-center gap-2 border text-center transition-all cursor-pointer ${
                  selectedModel === 'ResNet50'
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <Cpu className="h-5 w-5" />
                <span className="text-xs font-semibold">ResNet50</span>
                <span className="text-[9px] text-slate-500">88.7% Accuracy</span>
              </button>
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <h3 className="text-md font-bold text-white mb-4">2. Core Scan Upload</h3>
            <DropZone onFileSelect={handleFileSelect} />
            
            <button
              onClick={handlePredict}
              disabled={loading || !file}
              className="w-full mt-6 py-3.5 rounded-xl font-semibold text-sm text-white bg-gradient-primary hover:opacity-95 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4.5 w-4.5 animate-spin" />
                  <span>Analyzing core sample...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4.5 w-4.5" />
                  <span>Execute Diagnostic</span>
                </>
              )}
            </button>
          </GlassCard>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          {result ? (
            <PredictionResult data={result} />
          ) : (
            <GlassCard className="h-full flex flex-col items-center justify-center p-8 border-dashed border-2 border-slate-800 text-center min-h-[350px]">
              <div className="p-4 rounded-full bg-slate-800/40 border border-slate-700/60 mb-4">
                <Cpu className="h-8 w-8 text-slate-500" />
              </div>
              <h4 className="text-md font-bold text-white">Diagnostics Panel</h4>
              <p className="text-xs text-slate-400 max-w-sm mt-2 leading-relaxed">
                Configure your model weights, upload a core slice scan, and execute diagnostics to view lithology classification and mineral abundances.
              </p>
            </GlassCard>
          )}
        </div>

      </div>
    </div>
  );
};

export default PredictPage;
