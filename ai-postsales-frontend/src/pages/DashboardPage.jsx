import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

// This is the function React Query will call
const fetchDashboardSummary = async () => {
  // Note: we use /api/dashboard/summary, which the proxy sends to the backend
  const { data } = await axios.get('/api/dashboard/summary')
  return data
}

export default function DashboardPage() {
  // Use the useQuery hook
  const { data, error, isLoading } = useQuery({
    queryKey: ['dashboardSummary'], // A unique key for this query
    queryFn: fetchDashboardSummary // The function to fetch data
  })

  if (isLoading) {
    return <div className="p-4">Loading dashboard...</div>
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error.message}</div>
  }

  // Data is loaded!
  return (
    <div className="p-8" style={{ backgroundColor: '#E6F0FA' }}>
      <h1 className="text-4xl font-black" style={{ color: '#004AAD' }}>
        Dashboard
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
        <KpiCard title="Total Active Contracts" value={data.total_contracts} />
        <KpiCard title="Total Contract Value" value={`$${data.total_contract_value.toLocaleString()}`} />
        <KpiCard title="Expiring in 30 Days" value={data.contracts_expiring_30_days} />
      </div>

      {/* TODO: Add Charts Here */}
      {/* <pre className="mt-8 bg-white p-4 rounded">
        {JSON.stringify(data, null, 2)}
      </pre> */}
    </div>
  )
}

// A simple, reusable component
function KpiCard({ title, value }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="text-5xl font-extrabold" style={{ color: '#006EE6' }}>
        {value}
      </div>
      <p className="mt-2 font-semibold text-lg" style={{ color: '#004AAD' }}>
        {title}
      </p>
    </div>
  )
}