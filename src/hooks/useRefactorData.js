import refactorData from "../data/refactorData.json";

export function useRefactorData() {
  // This centralizes data access so a real API call can replace JSON import later.
  return refactorData;
}
