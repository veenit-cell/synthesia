import { create } from 'zustand';
import { SimulationState } from './types';

interface SimStore {
  connected: boolean;
  state: SimulationState | null;
  selectedAgent: string | null;
  setConnected: (c: boolean) => void;
  setState: (s: SimulationState) => void;
  setSelectedAgent: (id: string | null) => void;
}

export const useSimStore = create<SimStore>((set) => ({
  connected: false,
  state: null,
  selectedAgent: null,
  setConnected: (c) => set({ connected: c }),
  setState: (s) => set({ state: s }),
  setSelectedAgent: (id) => set({ selectedAgent: id }),
}));
