# frontend/app/profile/page.jsx
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Navigation from '../../components/Navigation';
import ProfileDisplay from '../../components/ProfileDisplay'; // Use the new component

const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`${API_BASE_URL}/profile`/*, { headers: { ... } }*/);
        setProfile(response.data);
      } catch (err) {
        console.error("Error fetching profile:", err);
        setError("Failed to load profile data.");
        if (err.response?.status === 401) {
           setError("Please log in to view your profile.");
           // Redirect to login
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 font-sans">
      <Navigation />
      <main className="container mx-auto p-4">
        {error && <div className="bg-red-500 text-white p-3 rounded mb-4">{error}</div>}
        <ProfileDisplay profile={profile} isLoading={loading} />
      </main>
    </div>
  );
}
