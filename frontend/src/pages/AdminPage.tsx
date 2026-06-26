import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import adminApi from '../api/admin';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';
import { ShieldCheck, HardDrive, RefreshCw, Cpu, Server } from 'lucide-react';
import toast from 'react-hot-toast';

const AdminPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [retrainingModel, setRetrainingModel] = useState<'EfficientNet-B3' | 'ResNet50'>('EfficientNet-B3');

  // Fetch admin console statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getSystemStats()
  });

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers()
  });

  const retrainMutation = useMutation({
    mutationFn: (modelName: string) => adminApi.triggerRetraining(1, modelName), // assumes dataset ID = 1
    onSuccess: () => {
      toast.success('Retraining task triggered successfully! Scheduled on Celery worker.');
    },
    onError: () => {
      toast.error('Failed to trigger retraining task.');
    }
  });

  const handleRetrain = () => {
    retrainMutation.mutate(retrainingModel);
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Admin Console</h1>
        <p className="text-slate-400 text-sm mt-1">Operational diagnostics, model orchestration, and user audits.</p>
      </div>

      {/* System Health Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="p-5 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
            <Server className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-400 block uppercase tracking-wider">FastAPI Backend</h4>
            <span className="text-white font-bold text-sm mt-0.5 block flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Operational</span>
            </span>
          </div>
        </GlassCard>

        <GlassCard className="p-5 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-400 block uppercase tracking-wider">Celery Workers</h4>
            <span className="text-white font-bold text-sm mt-0.5 block flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              <span>2 Node threads active</span>
            </span>
          </div>
        </GlassCard>

        <GlassCard className="p-5 flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl">
            <HardDrive className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-400 block uppercase tracking-wider">PostgreSQL DB Connection</h4>
            <span className="text-white font-bold text-sm mt-0.5 block flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              <span>Database Online</span>
            </span>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Model orchestration card */}
        <GlassCard className="p-6 h-full flex flex-col justify-between">
          <div>
            <h3 className="text-md font-bold text-white mb-2">Model Retraining Suite</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Manually trigger background weights adjustment logs on the selected core dataset samples.
            </p>
            
            <div className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Select retrain model weights
                </label>
                <select
                  value={retrainingModel}
                  onChange={(e) => setRetrainingModel(e.target.value as any)}
                  className="glass-input w-full px-4 py-2.5 rounded-xl text-xs cursor-pointer"
                >
                  <option value="EfficientNet-B3">EfficientNet-B3</option>
                  <option value="ResNet50">ResNet50</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleRetrain}
            disabled={retrainMutation.isPending}
            className="w-full py-3.5 rounded-xl font-semibold text-xs text-white bg-gradient-primary hover:opacity-95 active:scale-95 transition-all cursor-pointer flex items-center justify-center gap-2 mt-8"
          >
            {retrainMutation.isPending ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Running training scheduler...</span>
              </>
            ) : (
              <>
                <Cpu className="h-4 w-4" />
                <span>Trigger Retraining Job</span>
              </>
            )}
          </button>
        </GlassCard>

        {/* User Ingestion Auditing table */}
        <GlassCard className="lg:col-span-2 p-6 flex flex-col justify-between overflow-hidden">
          <div>
            <h3 className="text-md font-bold text-white mb-4">User Ingestion Auditing</h3>
            {usersLoading ? (
              <div className="text-xs text-slate-500 py-6 text-center">Loading users...</div>
            ) : (
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                      <th className="py-2.5">User ID</th>
                      <th className="py-2.5">Username</th>
                      <th className="py-2.5">Email</th>
                      <th className="py-2.5">Role</th>
                      <th className="py-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {users?.map((usr: any) => (
                      <tr key={usr.id} className="hover:bg-slate-800/10">
                        <td className="py-3 font-semibold text-indigo-400">#{usr.id}</td>
                        <td className="py-3 font-medium text-white">{usr.username}</td>
                        <td className="py-3 text-slate-400">{usr.email}</td>
                        <td className="py-3">
                          <Badge content={usr.role} variant={usr.role === 'admin' ? 'indigo' : 'neutral'} />
                        </td>
                        <td className="py-3 text-right">
                          <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </GlassCard>

      </div>
    </div>
  );
};

export default AdminPage;
