/**
 * Error handling component for API errors.
 */

'use client';

interface ErrorDisplayProps {
  error: string;
  onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
  // Check if it's an API key error
  const isApiKeyError = error.includes('401') || error.includes('Unauthorized');
  
  if (isApiKeyError) {
    return (
      <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-lg font-semibold text-yellow-800 mb-2">
          API Key Required
        </h3>
        <p className="text-yellow-700 mb-3">
          The CollegeFootballData API requires an API key. Please set up your API key:
        </p>
        <ol className="list-decimal list-inside text-yellow-700 space-y-1 mb-3">
          <li>Get a free API key from <a href="https://collegefootballdata.com" target="_blank" rel="noopener noreferrer" className="underline">collegefootballdata.com</a></li>
          <li>Create a <code className="bg-yellow-100 px-1 rounded">.env</code> file in the project root</li>
          <li>Add: <code className="bg-yellow-100 px-1 rounded">CFBD_API_KEY=your_api_key_here</code></li>
          <li>Restart the FastAPI backend server</li>
        </ol>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-sm text-yellow-800 hover:text-yellow-900 underline"
          >
            Dismiss
          </button>
        )}
      </div>
    );
  }
  
  return (
    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
      <h3 className="text-lg font-semibold mb-2">Error</h3>
      <p>{error}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="mt-2 text-sm text-red-800 hover:text-red-900 underline"
        >
          Dismiss
        </button>
      )}
    </div>
  );
}
