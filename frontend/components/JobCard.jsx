# frontend/components/JobCard.jsx
// This component is now integrated into frontend/app/jobs/page.jsx
// If you want it as a separate reusable component, you can extract it back.
// For now, the logic is directly in the jobs page for simplicity.

// Example of how it would look if extracted:
/*
import React from 'react';

const JobCard = ({ job, onAssign, isLoading }) => {
  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg flex justify-between items-center mb-3">
      <div>
        <h4 className="text-xl font-semibold text-blue-400">{job.name}</h4>
        <p className="text-sm text-gray-400">{job.description}</p>
        <p className="text-sm text-gray-400">Career: {job.career_requirement}</p>
        <p className="text-sm text-gray-300 mt-1">Salary: ${job.base_salary.toLocaleString()}</p>
        <p className="text-sm text-gray-300">Duration: {job.work_cycle_duration_hours} hours</p>
      </div>
      <button 
        onClick={() => onAssign(job.id)}
        disabled={isLoading}
        className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold transition-colors duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Assigning...' : 'Assign'}
      </button>
    </div>
  );
};

export default JobCard;
*/
