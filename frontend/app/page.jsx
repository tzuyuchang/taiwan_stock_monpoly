# frontend/app/page.jsx
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import Navigation from '../components/Navigation'; 

// Import UI components
import PlayerStatsDisplay from '../components/PlayerStatsDisplay'; 
import CurrentJobDisplay from '../components/CurrentJobDisplay';
import ActionButtons from '../components/ActionButtons';

// Mock API endpoint (replace with your actual backend URL)
const API_BASE_URL = 'http://localhost:8000/api/v1'; 

export default function HomePage() {
  const [playerProfile, setPlayerProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock data for player profile if not loaded yet or for initial UI structure
  const mockProfile = {
    id: 1, displayName: "Adventurer", cash: 0, experience: 0, intelligence: 10, work_ethic: 10, luck: 10,
    current_game_day: 1, current_game_hour: 9, current_career: "Worker", 
    loan_amount: 0, loan_interest_rate: 0, level: 1
  };
  // Use mock profile as initial state, overwrite when real data loads
  const [displayProfile, setDisplayProfile] = useState(mockProfile);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch player profile
        const response = await axios.get(`${API_BASE_URL}/profile`/*, { headers: { 'Authorization': `Bearer YOUR_TOKEN_HERE` } }*/);
        setPlayerProfile(response.data);
        setDisplayProfile(response.data); // Update display state with fetched data
      } catch (err) {
        console.error("Error fetching player profile:", err);
        let errMsg = "Failed to load player data.";
        if (err.response?.data?.detail) {
            errMsg = err.response.data.detail;
        }
        setError(errMsg);
        // If not authenticated, redirect to login
        if (err.response?.status === 401 || err.response?.status === 404) {
           // In a real app, use router.push('/login');
           // setError("Please log in to continue.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleWorkAction = async () => {
    if (!playerProfile || loading) return; // Prevent actions if loading or no profile
    setLoading(true); 
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/work`, {}, {
        // headers: { 'Authorization': `Bearer YOUR_TOKEN_HERE` }
      });
      setPlayerProfile(response.data); // Update original profile state
      setDisplayProfile(response.data); // Update display state
      alert("You worked hard and earned some money!");
    } catch (err) {
      console.error("Error performing work action:", err);
      let errMsg = "Failed to perform work action.";
      if (err.response?.data?.detail) {
        errMsg = err.response.data.detail;
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 font-sans">
      <Navigation /> 
      
      <main className="container mx-auto p-4">
        <h1 className="text-4xl font-bold text-center my-6">Welcome, {displayProfile.displayName}!</h1>

        {error && <div className="bg-red-500 text-white p-3 rounded mb-4">{error}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Player Stats and Current Status */}
          <div>
            <PlayerStatsDisplay 
              stats={displayProfile} // Pass the full profile object
              isLoading={loading} 
            />
            
            <CurrentJobDisplay 
              // Pass the relevant parts of the profile for job display
              jobDetails={playerProfile?.current_player_job || null} // Assuming profile includes current job assignment
              isLoading={loading} 
            /> 
            {/* This needs backend data to correctly show current job */}
          </div>

          {/* Actions and Navigation Links */}
          <div>
            <ActionButtons 
              onWorkClick={handleWorkAction} 
              isLoading={loading} 
              // canWork should depend on playerProfile and job assignment
              canWork={displayProfile.current_career === "Worker" && !loading && playerProfile?.current_player_job} 
            />

            <div className="mt-6 p-4 bg-gray-800 rounded-lg shadow-lg">
              <h3 className="text-2xl font-semibold mb-3">Quick Links</h3>
              <ul>
                <li className="mb-2">
                  <Link href="/jobs" className="text-blue-400 hover:underline">View Available Jobs</Link>
                </li>
                <li className="mb-2">
                  <Link href="/stocks" className="text-blue-400 hover:underline">Stock Market</Link>
                </li>
                <li className="mb-2">
                  <Link href="/gambling" className="text-blue-400 hover:underline">Gambling Den</Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
