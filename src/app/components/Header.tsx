import { useTheme } from "next-themes";
import { Moon, Sun, Bell } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="h-14 shrink-0 bg-card/95 backdrop-blur border-b border-border flex items-center justify-between px-4 sm:px-6">
      <div className="min-w-0 flex-1 pr-4">
        <h2 className="text-sm font-medium text-muted-foreground truncate">
          FraudShield AI
        </h2>
        <p className="text-base sm:text-lg font-semibold tracking-tight text-foreground truncate">
          GenAI-powered fraud detection
        </p>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <Button variant="ghost" size="icon" className="relative rounded-lg">
          <Bell className="w-5 h-5" />
          <Badge className="absolute -top-0.5 -right-0.5 min-w-[1.125rem] h-[1.125rem] flex items-center justify-center p-0 text-[10px] bg-red-600 hover:bg-red-600">
            3
          </Badge>
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="relative rounded-lg"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle color theme"
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        <div className="hidden sm:flex items-center gap-3 pl-3 ml-1 border-l border-border">
          <div className="text-right">
            <p className="text-sm font-medium text-foreground">Admin User</p>
            <p className="text-xs text-muted-foreground">Security Analyst</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-primary-foreground text-sm font-semibold shadow-md">
            AU
          </div>
        </div>
      </div>
    </header>
  );
}
