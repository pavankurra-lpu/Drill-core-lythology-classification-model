import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import datasetsApi from '../api/datasets';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';
import { Database, UploadCloud, Trash2, Calendar, FileArchive, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const DatasetsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.listDatasets()
  });

  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; name: string; description: string }) =>
      datasetsApi.uploadDataset(data.file, data.name, data.description),
    onSuccess: () => {
      toast.success('Dataset successfully ingested!');
      setZipFile(null);
      setDatasetName('');
      setDatasetDesc('');
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
    onError: () => {
      toast.error('Failed to upload dataset.');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => datasetsApi.deleteDataset(id),
    onSuccess: () => {
      toast.success('Dataset deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
    onError: () => {
      toast.error('Failed to delete dataset.');
    }
  });

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipFile || !datasetName) {
      toast.error('Name and zip file are required.');
      return;
    }
    setUploading(true);
    try {
      await uploadMutation.mutateAsync({ file: zipFile, name: datasetName, description: datasetDesc });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this dataset? This action is permanent.')) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Dataset Manager</h1>
        <p className="text-slate-400 text-sm mt-1">Upload and manage petrographic training sets for model retraining.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Form Panel */}
        <div className="space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-md font-bold text-white mb-4">Ingest Custom Dataset</h3>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Dataset Name
                </label>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="glass-input w-full px-4 py-2.5 rounded-xl text-xs"
                  placeholder="E.g. Granite Core Sequence"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Description
                </label>
                <textarea
                  value={datasetDesc}
                  onChange={(e) => setDatasetDesc(e.target.value)}
                  className="glass-input w-full px-4 py-2.5 rounded-xl text-xs"
                  placeholder="Specify location, formations, or labeling structure"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Data File (.zip archive)
                </label>
                <div className="border border-dashed border-slate-700 hover:border-indigo-500/40 rounded-xl p-6 text-center cursor-pointer transition-colors relative">
                  <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    required
                  />
                  <FileArchive className="h-8 w-8 text-slate-500 mx-auto mb-2" />
                  <span className="text-xs text-slate-400 font-medium block truncate">
                    {zipFile ? zipFile.name : 'Drag and drop .zip dataset here'}
                  </span>
                </div>
              </div>

              <button
                type="submit"
                disabled={uploading || !zipFile}
                className="w-full py-3.5 rounded-xl font-semibold text-xs text-white bg-gradient-primary hover:opacity-95 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Uploading archive...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="h-4 w-4" />
                    <span>Upload Dataset</span>
                  </>
                )}
              </button>
            </form>
          </GlassCard>
        </div>

        {/* Datasets Listing */}
        <div className="lg:col-span-2">
          {isLoading ? (
            <div className="text-center text-slate-400 py-12">Loading datasets...</div>
          ) : !datasets || datasets.length === 0 ? (
            <GlassCard className="h-full flex flex-col items-center justify-center p-8 border-dashed border-2 border-slate-800 text-center min-h-[300px]">
              <Database className="h-10 w-10 text-slate-600 mb-4 animate-bounce" />
              <h4 className="text-white font-bold text-md">No Datasets Found</h4>
              <p className="text-xs text-slate-400 mt-2 max-w-sm leading-relaxed">
                Start by uploading a .zip folder of core images structure. Files must contain folder subdivisions mapped directly as class labels.
              </p>
            </GlassCard>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {datasets.map((dataset: any) => (
                <GlassCard key={dataset.id} className="p-6 flex flex-col justify-between hover:border-indigo-500/20 transition-all duration-300">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
                        <Database className="h-5 w-5" />
                      </div>
                      <Badge content={dataset.status} variant={dataset.status === 'completed' ? 'success' : dataset.status === 'training' ? 'warning' : 'indigo'} />
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-bold text-white leading-snug">{dataset.name}</h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{dataset.description}</p>
                    </div>

                    {/* Stats List */}
                    <div className="grid grid-cols-2 gap-4 text-xs pt-2 border-t border-slate-800">
                      <div>
                        <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Samples</span>
                        <span className="text-white font-semibold">{dataset.num_samples ?? 'Processing...'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Classes</span>
                        <span className="text-white font-semibold">{dataset.num_classes ?? 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-800">
                    <span className="text-[10px] text-slate-500 flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </span>
                    
                    <button
                      onClick={() => handleDelete(dataset.id)}
                      className="p-2 rounded-xl bg-slate-800 hover:bg-red-950/40 text-red-400 transition-colors cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </GlassCard>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default DatasetsPage;
