# frontend/app/jobs/page.jsx
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';

// Mock API endpoint
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Re-use or create specific Job component for rendering job details
const JobCard = ({ job, onAssign, isLoading }) => {
  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg flex justify-between items-center mb-3">
      <div>
        <h4 className="text-xl font-semibold text-blue-400">{job.name}</h4>
        <p className="text-sm text-gray-400">{job.description}</p>
        <p className="text-sm text-gray-400">Career: {job.career_requirement}</p>
        {/* Display other job details like salary, duration, etc. */}
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

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assigningJobId, setAssigningJobId] = useState(null);

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch jobs available for the player's current career
        // In a real app, you'd get player profile first to know their career
        // For now, let's assume we fetch all jobs or filter on backend based on assumed player
        
        // Placeholder: Assuming player ID 1 and career "Worker"
        const playerId = 1; 
        const playerProfile = await axios.get(`${API_BASE_URL}/profile` /*, { headers: { ... } } */);
        const playerCareer = playerProfile.data.current_career; // e.g., "Worker"

        const response = await axios.get(`${API_BASE_URL}/jobs/available`, {
             params: { career_type: playerCareer }, // Filter by player's career
            // headers: { 'Authorization': `Bearer YOUR_TOKEN_HERE` }
        });
        setJobs(response.data);
      } catch (err) {
        console.error("Error fetching jobs:", err);
        setError("Failed to load jobs. Please try again later.");
         if (err.response && err.response.data && err.response.data.detail) {
            setError(`Error: ${err.response.data.detail}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const handleAssignJob = async (jobId) => {
    setAssigningJobId(jobId);
    setError(null);
    try {
      // Assume player ID 1 is currently logged in
      const playerId = 1; 
      await axios.post(`${API_BASE_URL}/jobs/assign/${jobId}`, {}, {
        params: { player_profile_id: playerId }, // Send player ID (or get from auth context)
        // headers: { 'Authorization': `Bearer YOUR_TOKEN_HERE` }
      });
      alert(`Successfully assigned to job ${jobId}!`);
      // Optionally, redirect to dashboard or refresh player profile data
      // window.location.href = '/'; 
    } catch (err) {
      console.error(`Error assigning job ${jobId}:`, err);
      let detailedError = "Failed to assign job.";
      if (err.response && err.response.data && err.response.data.detail) {
        detailedError = `Error: ${err.response.data.detail}`;
      }
      setError(detailedError);
    } finally {
      setAssigningJobId(null);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold text-center my-6">Available Jobs</h1>
      {error && <div className="bg-red-500 text-white p-3 rounded mb-4">{error}</div>}
      
      {loading ? (
        <p className="text-center text-gray-400">Loading jobs...</p>
      ) : jobs.length === 0 ? (
        <p className="text-center text-gray-500">No jobs available for your current career.</p>
      ) : (
        <div>
          {jobs.map((job) => (
            <JobCard 
              key={job.id} 
              job={job} 
              onAssign={handleAssignJob} 
              isLoading={assigningJobId === job.id} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
