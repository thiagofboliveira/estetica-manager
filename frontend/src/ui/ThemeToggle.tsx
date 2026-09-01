import { useTheme } from "@/lib/theme/ThemeContext";
import { IconSun, IconMoon } from "@/ui/icons";

interface Props {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className, showLabel = false }: Props) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={className}
      title={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      aria-label="Alternar tema de cores"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "6px",
        background: "transparent",
        color: "var(--text-muted)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "6px 10px",
        cursor: "pointer",
        minHeight: "auto",
        boxShadow: "none",
        transition: "all 0.15s ease",
      }}
    >
      {isDark ? (
        <IconSun width="16" height="16" style={{ color: "#f59e0b" }} />
      ) : (
        <IconMoon width="16" height="16" style={{ color: "#64748b" }} />
      )}
      {showLabel && (
        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-h)" }}>
          {isDark ? "Modo Claro" : "Modo Escuro"}
        </span>
      )}
    </button>
  );
}
