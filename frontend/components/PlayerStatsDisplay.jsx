# frontend/components/PlayerStatsDisplay.jsx
import React from 'react';

export default function PlayerStatsDisplay({ stats, isLoading }) {
  if (isLoading || !stats) { // Added !stats check
    return (
      <div className="p-4 bg-gray-800 rounded-lg shadow-lg animate-pulse">
        <h3 className="text-2xl font-semibold mb-3 text-center">Player Stats</h3>
        <p className="text-center text-gray-400">Loading...</p>
      </div>
    );
  }

  const formatCurrency = (amount) => {
    // Handle potential null or undefined amounts gracefully
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg mb-6">
      <h3 className="text-2xl font-semibold mb-3 text-center">Player Stats</h3>
      <div className="grid grid-cols-2 gap-2">
        <p><strong>Name:</strong> {stats.displayName || 'Adventurer'}</p>
        <p><strong>Net Worth:</strong> {formatCurrency(stats.cash)}</p>
        <p><strong>XP:</strong> {stats.experience}</p>
        <p><strong>Level:</strong> {stats.level || 1}</p>
        
        <div className="col-span-2 mt-2 pt-2 border-t border-gray-700">
            <h4 className="text-lg font-semibold mb-1">Attributes:</h4>
            <p><strong>Intelligence:</strong> {stats.intelligence}</p>
            <p><strong>Work Ethic:</strong> {stats.work_ethic}</p>
            <p><strong>Luck:</strong> {stats.luck}</p> {/* Added Luck */}
        </div>

        <div className="col-span-2 mt-2 pt-2 border-t border-gray-700">
             <h4 className="text-lg font-semibold mb-1">Game Time:</h4>
             <p><strong>Day:</strong> {stats.current_game_day}</p>
             <p><strong>Hour:</strong> {stats.current_game_hour}:00</p>
        </div>

        {stats.loan_amount > 0 && (
            <div className="col-span-2 mt-2 pt-2 border-t border-gray-700 text-red-400">
                <h4 className="text-lg font-semibold mb-1">Debt:</h4>
                <p><strong>Loan Amount:</strong> {formatCurrency(stats.loan_amount)}</p>
                <p><strong>Daily Interest:</strong> {(stats.loan_interest_rate * 100).toFixed(2)}%</p> {/* Fixed formatting */}
            </div>
        )}
      </div>
    </div>
  );
}
