# frontend/components/CurrentJobDisplay.jsx
import React from 'react';

export default function CurrentJobDisplay({ jobDetails, isLoading }) {
  // If isLoading, return a placeholder skeleton
  if (isLoading) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg shadow-lg animate-pulse mb-6">
        <h3 className="text-2xl font-semibold mb-3 text-center">Current Job</h3>
        <p className="text-center text-gray-400">Loading...</p>
      </div>
    );
  }

  // Extract job name and potentially other details from jobDetails
  // jobDetails might come directly from playerProfile or a separate API call
  const jobName = jobDetails?.job?.name || "None Assigned"; // Assuming jobDetails structure includes job object
  const assignmentId = jobDetails?.id; // Assuming jobDetails is the PlayerJobAssignment object

  // Display message if no job is assigned
  if (!assignmentId) {
     return (
      <div className="p-4 bg-gray-800 rounded-lg shadow-lg mb-6">
        <h3 className="text-2xl font-semibold mb-3 text-center">Current Job</h3>
        <p className="text-center text-gray-500">You are currently not assigned to any job.</p>
      </div>
    );
  }

  // Display assigned job details
  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg mb-6">
      <h3 className="text-2xl font-semibold mb-3 text-center">Current Job</h3>
      <div>
        <p className="text-lg font-medium">Job: <span className="text-blue-400">{jobName}</span></p>
        {/* Add more details if available, e.g., time remaining, rewards */}
        <p className="text-sm text-gray-400 mt-1">Assignment ID: {assignmentId}</p> 
        {/* In a real app, you might show time until completion or other job-specific info */}
      </div>
    </div>
  );
}
