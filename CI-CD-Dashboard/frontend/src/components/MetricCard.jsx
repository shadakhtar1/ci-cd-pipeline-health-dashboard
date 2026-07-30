import React from 'react';

export default function MetricCard({ title, value, subtitle }) {
  return (
    <div className="col-md-6 col-xl-4 mb-4">
      <div className="card shadow-sm h-100">
        <div className="card-body">
          <h6 className="text-muted text-uppercase">{title}</h6>
          <h3 className="mt-3 mb-1">{value}</h3>
          {subtitle ? <p className="text-muted mb-0">{subtitle}</p> : null}
        </div>
      </div>
    </div>
  );
}
