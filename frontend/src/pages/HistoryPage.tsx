import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import predictionsApi from '../api/predictions';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';
import { Search, Trash2, RefreshCw, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import Modal from '../components/ui/Modal';
import PredictionResult from '../components/prediction/PredictionResult';

const HistoryPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRockType, setFilterRockType] = useState('');
  const [selectedPrediction, setSelectedPrediction] = useState<any | null>(null);

  // Fetch prediction list
  const { data: response, isLoading } = useQuery({
    queryKey: ['predictions', searchTerm, filterRockType],
    queryFn: () => predictionsApi.listPredictions(1, 100) // retrieve up to 100 history items
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => predictionsApi.deletePrediction(id),
    onSuccess: () => {
      toast.success('Prediction deleted.');
      queryClient.invalidateQueries({ queryKey: ['predictions'] });
    },
    onError: () => {
      toast.error('Failed to delete prediction.');
    }
  });

  const handleDelete = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this prediction history item?')) {
      deleteMutation.mutate(id);
    }
  };

  const predictions = response?.items || [];
  
  // Apply local filtering for responsiveness
  const filteredPredictions = predictions.filter((item: any) => {
    const matchesSearch = item.lithology_class?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          item.original_filename?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRockType = filterRockType ? item.rock_type === filterRockType : true;
    return matchesSearch && matchesRockType;
  });

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Diagnostics History</h1>
        <p className="text-slate-400 text-sm mt-1">Review, filter, and export historical core logs and mineral predictions.</p>
      </div>

      {/* Filters Bar */}
      <GlassCard className="p-4 flex flex-col md:flex-row items-center gap-4 bg-slate-900/40">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="glass-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
            placeholder="Search by class name, file name..."
          />
          <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
        </div>
        
        <select
          value={filterRockType}
          onChange={(e) => setFilterRockType(e.target.value)}
          className="glass-input px-4 py-2.5 rounded-xl text-xs w-full md:w-48 cursor-pointer"
        >
          <option value="">All Rock Types</option>
          <option value="Igneous">Igneous</option>
          <option value="Sedimentary">Sedimentary</option>
          <option value="Metamorphic">Metamorphic</option>
        </select>
      </GlassCard>

      {/* Table Card */}
      <GlassCard className="overflow-hidden border border-slate-800">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400">Loading history logs...</div>
        ) : filteredPredictions.length === 0 ? (
          <div className="p-12 text-center text-slate-500">No core sample diagnostics found matching filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider bg-slate-900/30">
                  <th className="px-6 py-4">Sample ID</th>
                  <th className="px-6 py-4">Core scan filename</th>
                  <th className="px-6 py-4">Lithology output</th>
                  <th className="px-6 py-4">Rock type</th>
                  <th className="px-6 py-4">Confidence</th>
                  <th className="px-6 py-4">Processed Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-xs text-slate-300">
                {filteredPredictions.map((item: any) => (
                  <tr 
                    key={item.id} 
                    onClick={() => setSelectedPrediction(item)}
                    className="hover:bg-slate-800/20 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 font-bold text-indigo-400">#{item.id}</td>
                    <td className="px-6 py-4 truncate max-w-[180px]">{item.original_filename}</td>
                    <td className="px-6 py-4 font-semibold text-white">{item.lithology_class || 'Processing...'}</td>
                    <td className="px-6 py-4">
                      {item.rock_type && <Badge content={item.rock_type} variant="indigo" />}
                    </td>
                    <td className="px-6 py-4">
                      {item.confidence_score !== undefined && (
                        <span className={`font-semibold ${
                          item.confidence_score >= 80 ? 'text-emerald-400' : item.confidence_score >= 50 ? 'text-amber-400' : 'text-rose-400'
                        }`}>
                          {item.confidence_score.toFixed(1)}%
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <button 
                          onClick={() => setSelectedPrediction(item)}
                          title="View Details"
                          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-indigo-400 cursor-pointer"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={(e) => handleDelete(item.id, e)}
                          title="Delete Record"
                          className="p-1.5 rounded bg-slate-800 hover:bg-red-950/40 text-red-400 cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Details Modal */}
      {selectedPrediction && (
        <Modal 
          isOpen={!!selectedPrediction} 
          onClose={() => setSelectedPrediction(null)}
          title={`Detailed Diagnostic Output — Sample #${selectedPrediction.id}`}
          size="lg"
        >
          <PredictionResult data={selectedPrediction} />
        </Modal>
      )}
    </div>
  );
};

export default HistoryPage;
