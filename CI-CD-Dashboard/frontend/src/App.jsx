import React, { useEffect, useState } from 'react';
import { getDashboard, getBuilds, refreshBuilds } from './services/api';
import MetricCard from './components/MetricCard';
import StatusChart from './components/StatusChart';

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [builds, setBuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [dashboardRes, buildsRes] = await Promise.all([
        getDashboard(),
        getBuilds({ limit: 8 }),
      ]);
      setDashboard(dashboardRes.data);
      setBuilds(Array.isArray(buildsRes.data) ? buildsRes.data : buildsRes.data.builds || []);
    } catch (err) {
      setError('Unable to load dashboard data from the backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = async () => {
    try {
      await refreshBuilds();
      await loadData();
    } catch (err) {
      setError('Refresh failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status" />
          <p className="mt-3">Loading dashboard…</p>
        </div>
      </div>
    );
  }

  const statusSummary = {
    success: dashboard?.successful_builds ?? 0,
    failed: dashboard?.failed_builds ?? 0,
    pending: dashboard?.running_builds ?? 0,
  };

  return (
    <div className="bg-light min-vh-100">
      <div className="container py-4">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 className="fw-bold mb-1">CI/CD Pipeline Health Dashboard</h2>
            <p className="text-muted mb-0">Monitor workflow health, failures, and recent build activity.</p>
          </div>
          <button className="btn btn-primary" onClick={handleRefresh}>
            Refresh Data
          </button>
        </div>

        {error ? <div className="alert alert-danger">{error}</div> : null}

        <div className="row g-4 mb-4">
          <MetricCard title="Overall Health" value={`${(dashboard?.success_rate ?? 0).toFixed(2)}%`} subtitle="Success rate across recent builds" />
          <MetricCard title="Successful Builds" value={dashboard?.successful_builds ?? 0} subtitle="Recent successful workflow runs" />
          <MetricCard title="Failed Builds" value={dashboard?.failed_builds ?? 0} subtitle="Recent failed workflow runs" />
          <MetricCard title="Average Duration" value={dashboard?.average_build_duration ?? '--'} subtitle="Average build duration in seconds" />
          <MetricCard title="Last Update" value={dashboard?.last_refresh_time ? new Date(dashboard.last_refresh_time).toLocaleString() : '--'} subtitle="Most recent data sync" />
          <MetricCard title="Builds Tracked" value={dashboard?.total_builds ?? 0} subtitle="Total workflow runs in the database" />
        </div>

        <div className="row g-4">
          <div className="col-lg-5">
            <StatusChart data={statusSummary} />
          </div>
          <div className="col-lg-7">
            <div className="card shadow-sm h-100">
              <div className="card-body">
                <h5 className="card-title">Recent Builds</h5>
                <div className="table-responsive">
                  <table className="table table-hover align-middle">
                    <thead>
                      <tr>
                        <th>Workflow</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Started</th>
                      </tr>
                    </thead>
                    <tbody>
                      {builds.map((build) => (
                        <tr key={build.id}>
                          <td>{build.workflow_name || build.pipeline_name || 'Unknown'}</td>
                          <td>
                            <span className={`badge ${build.status === 'success' ? 'bg-success' : build.status === 'failure' ? 'bg-danger' : 'bg-warning text-dark'}`}>
                              {build.status || 'unknown'}
                            </span>
                          </td>
                          <td>{build.duration != null ? `${build.duration}s` : '--'}</td>
                          <td>{build.started_at ? new Date(build.started_at).toLocaleString() : '--'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
