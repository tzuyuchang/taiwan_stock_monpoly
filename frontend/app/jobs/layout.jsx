# frontend/app/jobs/layout.jsx
// A layout specific for the jobs section, if needed.
// For now, it can be simple and just pass children through.

export default function JobsLayout({ children }) {
  return (
    <div className="container mx-auto p-4">
      {children}
    </div>
  );
}
