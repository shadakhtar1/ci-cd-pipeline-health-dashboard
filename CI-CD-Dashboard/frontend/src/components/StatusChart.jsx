import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function StatusChart({ data }) {
  const chartData = {
    labels: ['Success', 'Failed', 'Pending'],
    datasets: [
      {
        data: [
          data?.success || 0,
          data?.failed || 0,
          data?.pending || 0,
        ],
        backgroundColor: ['#28a745', '#dc3545', '#ffc107'],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="card shadow-sm h-100">
      <div className="card-body">
        <h5 className="card-title">Build Status Distribution</h5>
        <div style={{ maxWidth: 320, margin: '0 auto' }}>
          <Doughnut data={chartData} />
        </div>
      </div>
    </div>
  );
}
