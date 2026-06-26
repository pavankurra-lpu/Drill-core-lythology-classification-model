import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import reportsApi from '../api/reports';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';
import { FileText, Download, Trash2, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

const ReportsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsApi.listReports()
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => reportsApi.deleteReport(id),
    onSuccess: () => {
      toast.success('Report deleted.');
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: () => {
      toast.error('Failed to delete report.');
    }
  });

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this geological report?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleDownload = (report: any) => {
    if (report.pdf_path) {
      window.open(`http://localhost:8000${report.pdf_path}`, '_blank');
    } else {
      toast.error('PDF file is not compiled yet.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Geological Reports</h1>
        <p className="text-slate-400 text-sm mt-1">Access, download, and review generated PDF reports for drill samples.</p>
      </div>

      {isLoading ? (
        <div className="text-center text-slate-400 py-12">Loading reports...</div>
      ) : !reports || reports.length === 0 ? (
        <GlassCard className="p-12 text-center text-slate-500 max-w-lg mx-auto">
          <FileText className="h-10 w-10 text-slate-600 mx-auto mb-4" />
          <h4 className="text-white font-bold text-md">No Reports Found</h4>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            Geological reports are compiled from the Core Classifier lab outputs. Perform classification diagnostics, then click "Compile PDF Report".
          </p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map((report: any) => (
            <GlassCard key={report.id} className="p-6 flex flex-col justify-between hover:border-indigo-500/20 transition-all duration-300">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
                    <FileText className="h-5 w-5" />
                  </div>
                  <Badge content={`Sample #${report.prediction_id}`} variant="indigo" />
                </div>
                
                <div>
                  <h4 className="text-sm font-bold text-white leading-snug">{report.title}</h4>
                  <p className="text-[10px] text-slate-500 mt-1">Generated: {new Date(report.created_at).toLocaleDateString()}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 mt-6 pt-4 border-t border-slate-800">
                <button
                  onClick={() => handleDownload(report)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors cursor-pointer"
                >
                  <Download className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Download PDF</span>
                </button>
                
                <button
                  onClick={() => handleDelete(report.id)}
                  title="Delete Report"
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
  );
};

export default ReportsPage;
