import { Settings as SettingsIcon } from "lucide-react";
import { ComingSoonPage } from "@/components/layout/ComingSoonPage";

export default function Settings() {
  return (
    <ComingSoonPage
      title="Settings"
      description="Manage your profile, notification preferences, and (for admins) user and model management."
      phase="a later phase"
      icon={SettingsIcon}
    />
  );
}
