import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Upload, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
import { motion } from "motion/react";

const PREVIEW_ROWS = [
  { id: "…18421", amount: "$120.00", ts: "2026-05-12 09:14", merchant: "City Cafe", loc: "Austin, US" },
  { id: "…18422", amount: "$4,250.00", ts: "2026-05-12 09:15", merchant: "Electronics Hub", loc: "Lagos, NG" },
  { id: "…18423", amount: "$39.99", ts: "2026-05-12 09:16", merchant: "Streaming Co", loc: "Toronto, CA" },
  { id: "…18424", amount: "$890.00", ts: "2026-05-12 09:17", merchant: "Travel Agency", loc: "Berlin, DE" },
];

export function UploadCSV() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith(".csv")) {
      setFile(droppedFile);
      setIsComplete(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setIsComplete(false);
    }
  };

  const handleRunDetection = () => {
    setIsProcessing(true);
    setProgress(0);

    // Simulate processing
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          setIsComplete(true);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Upload CSV for Batch Analysis
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Upload a CSV file containing transaction data for fraud detection
        </p>
      </div>

      {/* Upload Area */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragging
                ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/20"
                : "border-gray-300 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-600"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Drop your CSV file here
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              or click to browse from your computer
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button asChild>
                <span>Choose File</span>
              </Button>
            </label>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
              Supported format: CSV (Max 50MB)
            </p>
          </div>

          {/* File Preview */}
          {file && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 space-y-4"
            >
              <div className="flex items-center justify-between p-4 rounded-xl bg-muted/50 border border-border">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="w-10 h-10 text-primary" />
                  <div>
                    <p className="text-sm font-semibold text-foreground">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                {isComplete && <CheckCircle2 className="w-6 h-6 text-emerald-500" />}
              </div>

              <div>
                <p className="text-sm font-medium text-foreground mb-2">File preview (first rows)</p>
                <div className="rounded-xl border border-border overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-muted/50 border-b border-border">
                          <th className="text-left py-2 px-3 font-medium text-muted-foreground">ID</th>
                          <th className="text-left py-2 px-3 font-medium text-muted-foreground">Amount</th>
                          <th className="text-left py-2 px-3 font-medium text-muted-foreground">Timestamp</th>
                          <th className="text-left py-2 px-3 font-medium text-muted-foreground">Merchant</th>
                          <th className="text-left py-2 px-3 font-medium text-muted-foreground">Location</th>
                        </tr>
                      </thead>
                      <tbody>
                        {isProcessing
                          ? Array.from({ length: 4 }).map((_, i) => (
                              <tr key={i} className="border-b border-border last:border-0">
                                <td className="py-2 px-3" colSpan={5}>
                                  <Skeleton className="h-8 w-full rounded-md" />
                                </td>
                              </tr>
                            ))
                          : PREVIEW_ROWS.map((row) => (
                              <tr
                                key={row.id}
                                className="border-b border-border last:border-0 hover:bg-muted/30"
                              >
                                <td className="py-2 px-3 font-mono text-xs text-primary">{row.id}</td>
                                <td className="py-2 px-3 font-medium">{row.amount}</td>
                                <td className="py-2 px-3 text-muted-foreground">{row.ts}</td>
                                <td className="py-2 px-3">{row.merchant}</td>
                                <td className="py-2 px-3 text-muted-foreground">{row.loc}</td>
                              </tr>
                            ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* CSV Format Requirements */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardHeader>
          <CardTitle>CSV Format Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Your CSV file should contain the following columns:
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                transaction_id
              </code>
            </div>
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                amount
              </code>
            </div>
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                timestamp
              </code>
            </div>
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                merchant
              </code>
            </div>
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                location
              </code>
            </div>
            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <code className="text-sm text-indigo-600 dark:text-indigo-400">
                category
              </code>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing */}
      {isProcessing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-gray-200 dark:border-gray-800">
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Processing transactions...
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {progress}%
                  </span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Results */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-gray-200 dark:border-gray-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-green-500" />
                Analysis Complete
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/20">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Legitimate
                  </p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
                    1,247
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Needs Review
                  </p>
                  <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
                    38
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/20">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Fraud Detected
                  </p>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                    15
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button className="flex-1">Download Report</Button>
                <Button variant="outline" className="flex-1">
                  View Flagged Transactions
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Action Button */}
      {file && !isProcessing && !isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Button onClick={handleRunDetection} className="w-full h-12 text-base" size="lg">
            Run detection
          </Button>
        </motion.div>
      )}
    </div>
  );
}
