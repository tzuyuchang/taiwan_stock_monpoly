# frontend/app/(auth)/page.jsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import axios from 'axios';

// Mock API base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function AuthPage() {
  const [isLoginMode, setIsLoginMode] = useState(true); // State to toggle between login and register
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE_URL}/token`, {
        username: username,
        password: password,
      });
      // On successful login, store token and redirect (e.g., to dashboard)
      console.log("Login successful:", response.data);
      localStorage.setItem('authToken', response.data.access_token);
      // Redirect to dashboard - in a real app, use router.push('/')
      alert("Login successful! Redirecting to dashboard...");
      // window.location.href = '/'; // Simple redirect
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        username: username,
        password: password,
      });
      console.log("Registration successful:", response.data);
      alert("Registration successful! You can now log in.");
      setIsLoginMode(true); // Switch to login form after successful registration
    } catch (err) {
      console.error("Registration error:", err);
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = isLoginMode ? handleLogin : handleRegister;

  return (
    <div className="text-center">
      <h2 className="text-3xl font-bold mb-6 text-white">
        {isLoginMode ? 'Login' : 'Register'}
      </h2>
      {error && <p className="text-red-400 mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg font-semibold transition-colors duration-200
            bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : (isLoginMode ? 'Login' : 'Register')}
        </button>
      </form>
      <p className="mt-4 text-gray-400">
        {isLoginMode ? "Don't have an account?" : "Already have an account?"}
        <button
          onClick={() => setIsLoginMode(!isLoginMode)}
          className="ml-1 text-blue-400 hover:underline focus:outline-none"
        >
          {isLoginMode ? 'Register here' : 'Login here'}
        </button>
      </p>
    </div>
  );
}
