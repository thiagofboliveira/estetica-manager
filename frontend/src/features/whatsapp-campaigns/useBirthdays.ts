import { useQuery } from "@tanstack/react-query";
import { getBirthdays } from "./campaignsApi";

export const BIRTHDAYS_KEY = ["patient_birthdays"] as const;

export function useBirthdays(month?: number) {
  return useQuery({
    queryKey: [...BIRTHDAYS_KEY, month],
    queryFn: () => getBirthdays(month),
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
