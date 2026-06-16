# frontend/components/ActionButtons.jsx
import React from 'react';

export default function ActionButtons({ onWorkClick, isLoading, canWork }) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg mb-6">
      <h3 className="text-2xl font-semibold mb-3 text-center">Actions</h3>
      <div className="flex flex-col space-y-3">
        <button 
          onClick={onWorkClick} 
          disabled={isLoading || !canWork}
          className={`px-6 py-3 rounded-lg font-semibold transition-colors duration-200
            ${isLoading || !canWork 
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
              : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
        >
          {isLoading ? 'Working...' : 'Work'}
        </button>
        
        {/* Add buttons for other actions like Invest, Gamble, etc. */}
        {/* <button 
          onClick={() => alert('Invest action not yet implemented!')} 
          disabled={isLoading}
          className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
        >
          Invest
        </button> */}
      </div>
    </div>
  );
}
