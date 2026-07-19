import { create } from "zustand";

// Lightweight global UI state (thesis selection, filters). Server data lives in
// React Query, not here.
interface AppState {
  activeThesisId: number | null;
  setActiveThesis: (id: number | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeThesisId: null,
  setActiveThesis: (id) => set({ activeThesisId: id }),
}));
