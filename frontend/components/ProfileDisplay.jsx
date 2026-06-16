# frontend/components/ProfileDisplay.jsx
import React from 'react';

// This component would display the full player profile details, possibly editable.
// For now, it's a placeholder. The HomePage already uses PlayerStatsDisplay for key info.
export default function ProfileDisplay({ profile, isLoading }) {
  if (isLoading || !profile) {
    return <div className="p-4 bg-gray-800 rounded-lg shadow-lg">Loading profile...</div>;
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  return (
    <div className="p-6 bg-gray-800 rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-4 text-center">Player Profile</h2>
      <p className="mb-2"><strong>Display Name:</strong> {profile.displayName}</p>
      <p className="mb-2"><strong>Username:</strong> {profile.user?.username || 'N/A'}</p> {/* Assuming user data is joined */}
      <p className="mb-2"><strong>Career:</strong> {profile.current_career}</p>
      <p className="mb-2"><strong>Level:</strong> {profile.level}</p>
      <p className="mb-2"><strong>Experience:</strong> {profile.experience}</p>
      <p className="mb-2"><strong>Cash:</strong> {formatCurrency(profile.cash)}</p>
      <p className="mb-2"><strong>Bank Balance:</strong> {formatCurrency(profile.bank_balance)}</p>
      {profile.loan_amount > 0 && (
        <p className="mb-2 text-red-400"><strong>Loan Amount:</strong> {formatCurrency(profile.loan_amount)} (Rate: {profile.loan_interest_rate * 100:.2f}%)</p>
      )}
      <h4 className="mt-4 mb-2 font-semibold">Attributes:</h4>
      <p className="ml-4"><strong>Intelligence:</strong> {profile.intelligence}</p>
      <p className="ml-4"><strong>Luck:</strong> {profile.luck}</p>
      <p className="ml-4"><strong>Work Ethic:</strong> {profile.work_ethic}</p>
      <p className="ml-4"><strong>Leadership:</strong> {profile.leadership}</p>
      <p className="ml-4"><strong>Analysis:</strong> {profile.analysis}</p>
       <h4 className="mt-4 mb-2 font-semibold">Game Time:</h4>
       <p className="ml-4"><strong>Day:</strong> {profile.current_game_day}</p>
       <p className="ml-4"><strong>Hour:</strong> {profile.current_game_hour}:00</p>
      
      {/* Add buttons for editing profile if implemented */}
    </div>
  );
}
