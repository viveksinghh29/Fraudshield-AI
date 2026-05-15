import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { MetricCard } from "../components/MetricCard";
import { FraudAlert } from "../components/FraudAlert";
import { Badge } from "../components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "../components/ui/tooltip";
import {
  Receipt,
  ShieldAlert,
  TrendingUp,
  DollarSign,
  Clock,
  HelpCircle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  dashboardStats,
  fraudTrendData,
  transactionTrendData,
  riskDistributionData,
  transactions,
} from "../data/mockData";
import { useNavigate } from "react-router";

export function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Alert Banner */}
      <FraudAlert
        count={3}
        message="Review flagged transactions immediately to prevent potential losses."
      />

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total transactions"
          value={dashboardStats.totalTransactions.toLocaleString()}
          icon={Receipt}
          trend={{ value: 12.5, isPositive: true }}
          hint="All scored transactions in the selected window, including batch and API traffic."
        />
        <MetricCard
          title="Fraud detected"
          value={`${dashboardStats.fraudDetected}%`}
          icon={ShieldAlert}
          trend={{ value: -8.3, isPositive: true }}
          hint="Share of scored transactions classified as fraud over the trailing 7 days."
        />
        <MetricCard
          title="Risk score overview"
          value={dashboardStats.averageRiskScore}
          icon={TrendingUp}
          subtitle="Portfolio mean (0–100)"
          hint="Population-level average of calibrated risk scores across all scored transactions."
        />
        <MetricCard
          title="Blocked amount"
          value={`$${(dashboardStats.blockedAmount / 1000).toFixed(0)}K`}
          icon={DollarSign}
          trend={{ value: 24.1, isPositive: true }}
          hint="Aggregate USD value of transactions auto-blocked by policy in the same window."
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fraud vs Legit Chart */}
        <Card className="hover:shadow-[var(--fs-card-shadow-hover)] transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CardTitle>Fraud vs legitimate</CardTitle>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="text-muted-foreground hover:text-foreground rounded-md p-0.5"
                    aria-label="Chart info"
                  >
                    <HelpCircle className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Daily counts of fraud vs non-fraud labels from production scoring.</TooltipContent>
              </Tooltip>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={fraudTrendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <ChartTooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Bar dataKey="legit" fill="#10b981" name="Legitimate" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fraud" fill="#ef4444" name="Fraud" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Transaction Trend */}
        <Card className="hover:shadow-[var(--fs-card-shadow-hover)] transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CardTitle>Transaction trend (24h)</CardTitle>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" className="text-muted-foreground hover:text-foreground rounded-md p-0.5" aria-label="Chart info">
                    <HelpCircle className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Hourly volume of scored transactions (all channels).</TooltipContent>
              </Tooltip>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={transactionTrendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
                <XAxis dataKey="time" className="text-xs" />
                <YAxis className="text-xs" />
                <ChartTooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="volume"
                  stroke="#6366f1"
                  strokeWidth={3}
                  dot={{ fill: "#6366f1", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Risk Distribution and Live Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution */}
        <Card className="hover:shadow-[var(--fs-card-shadow-hover)] transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CardTitle>Risk distribution</CardTitle>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" className="text-muted-foreground hover:text-foreground rounded-md p-0.5" aria-label="Chart info">
                    <HelpCircle className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Share of transactions by calibrated risk bucket.</TooltipContent>
              </Tooltip>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <ChartTooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Live Activity Feed */}
        <Card className="lg:col-span-2 hover:shadow-[var(--fs-card-shadow-hover)] transition-shadow">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Live activity feed</CardTitle>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Live
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-[280px] overflow-y-auto">
              {transactions.slice(0, 6).map((txn) => (
                <div
                  key={txn.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-muted/40 hover:bg-muted/70 border border-transparent hover:border-border/80 transition-all cursor-pointer"
                  onClick={() => navigate(`/transactions/${txn.id}`)}
                >
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {txn.merchant}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {txn.location} • {txn.time.split(" ")[1]}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      ${txn.amount.toFixed(2)}
                    </p>
                    <Badge
                      variant={
                        txn.status === "fraud"
                          ? "destructive"
                          : txn.status === "warning"
                          ? "secondary"
                          : "default"
                      }
                      className={
                        txn.status === "legit"
                          ? "bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300"
                          : txn.status === "warning"
                          ? "bg-yellow-100 dark:bg-yellow-950 text-yellow-700 dark:text-yellow-300"
                          : ""
                      }
                    >
                      {txn.status === "legit" ? "Legit" : txn.status === "warning" ? "Warning" : "Fraud"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
