# frontend/components/Navigation.jsx
import Link from 'next/link';

export default function Navigation() {
  return (
    <nav className="bg-gray-800 p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-white hover:text-gray-300">
          StockMonopoly
        </Link>
        <div className="space-x-4">
          {/* Add navigation links here */}
          <Link href="/profile" className="text-gray-300 hover:text-white">Profile</Link>
          <Link href="/jobs" className="text-gray-300 hover:text-white">Jobs</Link>
          <Link href="/stocks" className="text-gray-300 hover:text-white">Stocks</Link>
          <Link href="/gambling" className="text-gray-300 hover:text-white">Gambling</Link>
          {/* Add Login/Logout button if applicable */}
          <button className="text-gray-300 hover:text-white">Logout</button>
        </div>
      </div>
    </nav>
  );
}
