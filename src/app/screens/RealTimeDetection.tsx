import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { RiskGauge } from "../components/RiskGauge";
import { Zap, Bot } from "lucide-react";
import { useState } from "react";
import { motion } from "motion/react";

export function RealTimeDetection() {
  const [formData, setFormData] = useState({
    amount: "",
    merchant: "",
    location: "",
    time: "",
  });
  const [result, setResult] = useState<{
    riskScore: number;
    fraudProbability: number;
    status: "fraud" | "legit" | "warning";
    explanation: string;
  } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsAnalyzing(true);

    // Simulate API call
    setTimeout(() => {
      const amount = parseFloat(formData.amount);
      let riskScore = Math.floor(Math.random() * 100);
      
      // Make higher amounts more risky for demo
      if (amount > 5000) {
        riskScore = Math.max(riskScore, 70);
      } else if (amount > 2000) {
        riskScore = Math.min(Math.max(riskScore, 40), 70);
      } else {
        riskScore = Math.min(riskScore, 40);
      }

      const status: "fraud" | "legit" | "warning" =
        riskScore >= 70 ? "fraud" : riskScore >= 40 ? "warning" : "legit";

      const explanations = {
        fraud: `High-risk transaction detected. The amount of $${amount} combined with the location (${formData.location}) shows unusual patterns. Multiple risk factors including transaction velocity and merchant category suggest potential fraud.`,
        warning: `Moderate risk detected. Transaction amount and location require verification. Consider requesting additional authentication before approving.`,
        legit: `Low-risk transaction. All parameters fall within normal ranges. Amount, location, and merchant information are consistent with legitimate transaction patterns.`,
      };

      setResult({
        riskScore,
        status,
        explanation: explanations[status],
      });
      setIsAnalyzing(false);
    }, 1500);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "fraud":
        return "text-red-600 dark:text-red-400";
      case "warning":
        return "text-yellow-600 dark:text-yellow-400";
      default:
        return "text-green-600 dark:text-green-400";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "fraud":
        return "FRAUD DETECTED";
      case "warning":
        return "NEEDS REVIEW";
      default:
        return "LEGITIMATE";
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Real-Time Fraud Detection
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Analyze individual transactions instantly with AI-powered detection
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card className="border-gray-200 dark:border-gray-800">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <CardTitle>Transaction Details</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Transaction Amount ($)</Label>
                <Input
                  id="amount"
                  name="amount"
                  type="number"
                  step="0.01"
                  placeholder="Enter amount..."
                  value={formData.amount}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="merchant">Merchant Name</Label>
                <Input
                  id="merchant"
                  name="merchant"
                  placeholder="e.g., Amazon, Walmart..."
                  value={formData.merchant}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  name="location"
                  placeholder="e.g., New York, USA"
                  value={formData.location}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="time">Transaction Time</Label>
                <Input
                  id="time"
                  name="time"
                  type="datetime-local"
                  value={formData.time}
                  onChange={handleChange}
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full h-11"
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Predict
                  </>
                )}
              </Button>
            </form>

            {/* Example Button */}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                Quick Test:
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setFormData({
                      amount: "8500",
                      merchant: "Wire Transfer Service",
                      location: "Lagos, Nigeria",
                      time: new Date().toISOString().slice(0, 16),
                    });
                    setResult(null);
                  }}
                >
                  High Risk
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setFormData({
                      amount: "45.99",
                      merchant: "Starbucks",
                      location: "San Francisco, USA",
                      time: new Date().toISOString().slice(0, 16),
                    });
                    setResult(null);
                  }}
                >
                  Low Risk
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="space-y-6">
          {result ? (
            <>
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <Card className="border-gray-200 dark:border-gray-800">
                  <CardHeader>
                    <CardTitle>Detection Result</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col items-center text-center space-y-4">
                      <RiskGauge score={result.riskScore} size="lg" />
                      <div>
                        <p
                          className={`text-2xl font-bold ${getStatusColor(
                            result.status
                          )}`}
                        >
                          {getStatusLabel(result.status)}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Fraud probability:{" "}
                          <span className="font-semibold text-foreground tabular-nums">
                            {result.fraudProbability}%
                          </span>
                          {" · "}
                          Risk score:{" "}
                          <span className="font-semibold text-foreground tabular-nums">
                            {result.riskScore}
                          </span>
                        </p>
                      </div>

                      <div className="w-full grid grid-cols-2 gap-3 mt-4">
                        <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Model
                          </p>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">
                            Random Forest
                          </p>
                        </div>
                        <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Time
                          </p>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">
                            28ms
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="border-gray-200 dark:border-gray-800">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <CardTitle>AI Explanation</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/20 dark:to-indigo-950/20 border border-purple-200 dark:border-purple-900">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {result.explanation}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </>
          ) : (
            <Card className="border-gray-200 dark:border-gray-800">
              <CardContent className="p-12 text-center">
                <div className="w-20 h-20 mx-auto rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                  <Zap className="w-10 h-10 text-gray-400 dark:text-gray-600" />
                </div>
                <p className="text-muted-foreground">
                  Enter transaction details and click <span className="font-medium text-foreground">Predict</span>{" "}
                  to see risk score, fraud probability, and an explanation.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
