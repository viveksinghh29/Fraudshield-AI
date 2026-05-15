import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import { Copy, Eye, EyeOff, RefreshCw, Key } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export function Settings() {
  const [showApiKey, setShowApiKey] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);
  const [activeModel, setActiveModel] = useState<"rf" | "future">("rf");
  const [autoBlock, setAutoBlock] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(true);

  const apiKey = "sk_live_51HqJ2KLjK8fH3kL9mN5pQrSt7Uv9Wx2Yz4Ab6Cd8Ef0";

  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    toast.success("API key copied to clipboard");
  };

  const handleRegenerateApiKey = () => {
    toast.success("API key regenerated successfully");
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Manage your FraudShield AI configuration and preferences
        </p>
      </div>

      {/* API Configuration */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <CardTitle>API Configuration</CardTitle>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Manage your API keys and access tokens
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label>API Key</Label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  readOnly
                  className="font-mono text-sm pr-10"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              </div>
              <Button variant="outline" onClick={handleCopyApiKey}>
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
              <Button variant="outline" onClick={handleRegenerateApiKey}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate
              </Button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Keep this key secret. It provides full access to your FraudShield
              AI account.
            </p>
          </div>

          <div className="space-y-3">
            <Label>Webhook URL (Optional)</Label>
            <Input
              type="url"
              placeholder="https://your-domain.com/webhooks/fraud-alerts"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Receive real-time fraud alerts via webhook
            </p>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  API Rate Limit
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Current plan: Professional
                </p>
              </div>
              <Badge className="bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300">
                10,000 req/hour
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model Settings */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardHeader>
          <CardTitle>Model Settings</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Configure fraud detection behavior
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">Inference mode</p>
              <p className="text-xs text-muted-foreground mt-1">
                {offlineMode
                  ? "Offline: scoring runs on-device; GenAI explanations use cached templates only."
                  : "Online: scoring and LLM explanations use FraudShield cloud APIs."}
              </p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="text-xs text-muted-foreground">
                {offlineMode ? "Offline" : "Online"}
              </span>
              <Switch checked={offlineMode} onCheckedChange={setOfflineMode} />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-800">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Auto-Block High Risk
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Automatically block transactions with risk score &gt; 80%
              </p>
            </div>
            <Switch checked={autoBlock} onCheckedChange={setAutoBlock} />
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
            <Label className="mb-3 block">Risk Threshold</Label>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Low Risk
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    0-39
                  </span>
                </div>
                <div className="h-2 bg-green-200 dark:bg-green-900 rounded-full">
                  <div className="h-full w-[39%] bg-green-500 rounded-full" />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Medium Risk
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    40-69
                  </span>
                </div>
                <div className="h-2 bg-yellow-200 dark:bg-yellow-900 rounded-full">
                  <div className="h-full w-[30%] bg-yellow-500 rounded-full" />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    High Risk
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    70-100
                  </span>
                </div>
                <div className="h-2 bg-red-200 dark:bg-red-900 rounded-full">
                  <div className="h-full w-[31%] bg-red-500 rounded-full" />
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
            <Label className="mb-3 block">Model selection</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setActiveModel("rf")}
                className={`text-left p-4 rounded-xl border-2 transition-all ${
                  activeModel === "rf"
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border hover:border-primary/40"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold text-foreground">Random Forest</p>
                  {activeModel === "rf" && (
                    <Badge className="bg-primary text-primary-foreground">Active</Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">v2.4.1 · 98.7% accuracy · default</p>
              </button>
              <button
                type="button"
                disabled
                className="text-left p-4 rounded-xl border border-border opacity-60 cursor-not-allowed"
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold text-foreground">Future models</p>
                  <Badge variant="outline">Coming soon</Badge>
                </div>
                <p className="text-xs text-muted-foreground">Gradient boosting, temporal GNN</p>
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="border-gray-200 dark:border-gray-800">
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Configure how you receive fraud alerts
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Email Notifications
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Receive email alerts for high-risk transactions
              </p>
            </div>
            <Switch
              checked={emailNotifications}
              onCheckedChange={setEmailNotifications}
            />
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
            <Label className="mb-3 block">Email Address</Label>
            <Input
              type="email"
              placeholder="admin@company.com"
              defaultValue="admin@company.com"
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        <Button variant="outline">Reset to Defaults</Button>
        <Button onClick={() => toast.success("Settings saved successfully")}>
          Save Changes
        </Button>
      </div>
    </div>
  );
}
