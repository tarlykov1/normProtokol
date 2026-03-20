import { create } from 'zustand'

type SaveState = 'saved' | 'saving' | 'error' | 'idle'

type Filters = {
  noTopic: boolean
  noAssignee: boolean
  noDeadline: boolean
  onlyErrors: boolean
  onlyUnconfirmed: boolean
  search: string
}

interface ProtocolUiState {
  selectedTaskIds: number[]
  currentView: 'table' | 'board'
  filters: Filters
  autosaveState: SaveState
  setAutosaveState: (s: SaveState) => void
  toggleTask: (id: number) => void
  clearSelection: () => void
  setView: (view: 'table' | 'board') => void
  setFilters: (patch: Partial<Filters>) => void
}

export const useProtocolStore = create<ProtocolUiState>((set: (fn: any) => void) => ({
  selectedTaskIds: [],
  currentView: 'table',
  filters: { noTopic: false, noAssignee: false, noDeadline: false, onlyErrors: false, onlyUnconfirmed: false, search: '' },
  autosaveState: 'idle',
  setAutosaveState: (autosaveState) => set({ autosaveState }),
  toggleTask: (id) => set((s) => ({ selectedTaskIds: s.selectedTaskIds.includes(id) ? s.selectedTaskIds.filter((x) => x !== id) : [...s.selectedTaskIds, id] })),
  clearSelection: () => set({ selectedTaskIds: [] }),
  setView: (currentView) => set({ currentView }),
  setFilters: (patch) => set((s) => ({ filters: { ...s.filters, ...patch } }))
}))
