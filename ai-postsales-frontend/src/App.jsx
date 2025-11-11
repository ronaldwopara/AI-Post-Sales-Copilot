import { useState, useEffect } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    // Fetch from the proxy, not http://localhost:8000
    axios.get('/')
      .then(response => {
        // Data from app/main.py's root() function
        setMessage(JSON.stringify(response.data));
      })
      .catch(error => {
        setMessage(`Error: ${error.message}`);
      });
  }, []);

  return (
    <div className="p-10 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold text-blue-700">AI Post-Sales Copilot</h1>
      <div className="mt-4 p-4 bg-white rounded shadow">
        <p className="font-mono">
          <strong>Backend Connection Test:</strong> {message}
        </p>
      </div>
    </div>
  )
}

export default App