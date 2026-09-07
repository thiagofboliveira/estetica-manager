import type { DashboardPeriod } from "@/features/dashboard/api";
import { formatLocalDate } from "@/lib/format/date";

export type ReportCategory = "financial" | "appointments" | "retention" | "procedures";

export type PeriodDateRange = {
  from: string;
  to: string;
};

export function resolvePeriodDateRange(
  period: DashboardPeriod,
  customFrom?: string,
  customTo?: string,
): PeriodDateRange {
  const now = new Date();
  const todayStr = formatLocalDate(now);

  if (period === "today") {
    return { from: todayStr, to: todayStr };
  }

  if (period === "last_7_days") {
    const d = new Date(now);
    d.setDate(d.getDate() - 6);
    return { from: formatLocalDate(d), to: todayStr };
  }

  if (period === "this_month") {
    const d = new Date(now.getFullYear(), now.getMonth(), 1);
    return { from: formatLocalDate(d), to: todayStr };
  }

  if (period === "last_month") {
    const firstOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastOfLastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
    return {
      from: formatLocalDate(firstOfLastMonth),
      to: formatLocalDate(lastOfLastMonth),
    };
  }

  if (period === "custom") {
    return {
      from: customFrom || todayStr,
      to: customTo || todayStr,
    };
  }

  return { from: todayStr, to: todayStr };
}
