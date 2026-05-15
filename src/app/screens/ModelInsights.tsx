import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { TrendingUp, Target, Activity, Award } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { modelMetrics, confusionMatrix, featureImportance } from "../data/mockData";

export function ModelInsights() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Model Performance Insights
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Detailed metrics and analysis of the fraud detection model
        </p>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="border-gray-200 dark:border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-950/50 flex items-center justify-center">
                <Target className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Accuracy</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {modelMetrics.accuracy}%
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200 dark:border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-950/50 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Precision</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {modelMetrics.precision}%
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200 dark:border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-950/50 flex items-center justify-center">
                <Activity className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Recall</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {modelMetrics.recall}%
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200 dark:border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-950/50 flex items-center justify-center">
                <Award className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">F1-Score</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {modelMetrics.f1Score}%
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200 dark:border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-yellow-100 dark:bg-yellow-950/50 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">ROC-AUC</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {modelMetrics.rocAuc}%
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix */}
        <Card className="border-gray-200 dark:border-gray-800">
          <CardHeader>
            <CardTitle>Confusion Matrix</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Model prediction accuracy breakdown
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Visual Matrix */}
              <div className="grid grid-cols-2 gap-4">
                {/* True Negative */}
                <div className="p-6 rounded-lg bg-green-50 dark:bg-green-950/20 border-2 border-green-200 dark:border-green-900">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    True Negative
                  </p>
                  <p className="text-4xl font-bold text-green-600 dark:text-green-400">
                    {confusionMatrix[0][0].toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Correctly identified as legit
                  </p>
                </div>

                {/* False Positive */}
                <div className="p-6 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border-2 border-yellow-200 dark:border-yellow-900">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    False Positive
                  </p>
                  <p className="text-4xl font-bold text-yellow-600 dark:text-yellow-400">
                    {confusionMatrix[0][1].toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Legit flagged as fraud
                  </p>
                </div>

                {/* False Negative */}
                <div className="p-6 rounded-lg bg-red-50 dark:bg-red-950/20 border-2 border-red-200 dark:border-red-900">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    False Negative
                  </p>
                  <p className="text-4xl font-bold text-red-600 dark:text-red-400">
                    {confusionMatrix[1][0].toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Fraud missed
                  </p>
                </div>

                {/* True Positive */}
                <div className="p-6 rounded-lg bg-blue-50 dark:bg-blue-950/20 border-2 border-blue-200 dark:border-blue-900">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    True Positive
                  </p>
                  <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
                    {confusionMatrix[1][1].toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Correctly identified fraud
                  </p>
                </div>
              </div>

              {/* Matrix Labels */}
              <div className="flex items-center justify-center gap-12 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-green-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    Legit (Predicted)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-red-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    Fraud (Predicted)
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Feature Importance */}
        <Card className="border-gray-200 dark:border-gray-800">
          <CardHeader>
            <CardTitle>Feature Importance</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Most influential factors in fraud detection
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={featureImportance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
                <XAxis type="number" className="text-xs" />
                <YAxis dataKey="feature" type="category" width={150} className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {featureImportance.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={`hsl(${250 - index * 20}, 70%, 60%)`}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Model Information */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardHeader>
          <CardTitle>Model Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Algorithm
              </p>
              <Badge className="bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                Random Forest Classifier
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Training Dataset
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                284,807 transactions
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Last Updated
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                March 20, 2026
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Model Version
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                v2.4.1
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Inference Time
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                ~32ms avg
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Cross-Validation
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                5-Fold CV
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
