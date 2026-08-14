import { UserCircle } from "lucide-react";
import { useCurrentUser } from "@/api/hooks";
import { getApiErrorMessage } from "@/api/client";
import { Card } from "@/components/layout/Card";

export default function Profile() {
  const { data: user, isLoading, error } = useCurrentUser();

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-xl font-semibold">User Profile</h1>
        <p className="mt-1 text-sm text-gray-500">Your account details</p>
      </header>

      {isLoading && <p className="text-sm text-gray-500">Loading profile...</p>}
      {error && (
        <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical">
          {getApiErrorMessage(error)}
        </p>
      )}

      {user && (
        <Card className="max-w-lg">
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent/15">
              <UserCircle className="h-8 w-8 text-accent-soft" />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">{user.full_name}</p>
              <p className="text-sm text-gray-500">{user.email}</p>
            </div>
          </div>

          <div className="space-y-3 border-t border-border-subtle pt-4 text-sm">
            <Row label="Role" value={<span className="capitalize">{user.role}</span>} />
            <Row
              label="Account Status"
              value={
                <span className={user.is_active ? "text-risk-low" : "text-risk-critical"}>
                  {user.is_active ? "Active" : "Deactivated"}
                </span>
              }
            />
            <Row label="User ID" value={<span className="font-mono text-xs text-gray-500">{user.id}</span>} />
          </div>
        </Card>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200">{value}</span>
    </div>
  );
}
