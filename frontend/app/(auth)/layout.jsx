# frontend/app/(auth)/layout.jsx
// This file will define the layout for authentication pages (login, register)
// It might include a centered form or a specific auth-related visual theme.

export default function AuthLayout({ children }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="w-full max-w-md p-8 space-y-6 bg-gray-800 rounded-lg shadow-lg">
        {children}
      </div>
    </div>
  );
}
