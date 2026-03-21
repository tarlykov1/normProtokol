import { create } from 'zustand'

type SaveState = 'saved' | 'saving' | 'error' | 'idle'

type Filters = {
  noTopic: boolean
  noAssignee: boolean
  noDeadline: boolean
  onlyErrors: boolean
  onlyUnconfirmed: boolean
  onlyReady: boolean
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

export const useProtocolStore = create<ProtocolUiState>()((set) => ({
  selectedTaskIds: [],
  currentView: 'table',
  filters: { noTopic: false, noAssignee: false, noDeadline: false, onlyErrors: false, onlyUnconfirmed: false, onlyReady: false, search: '' },
  autosaveState: 'idle',
  setAutosaveState: (autosaveState) => set({ autosaveState }),
  toggleTask: (id) => set((state) => ({ selectedTaskIds: state.selectedTaskIds.includes(id) ? state.selectedTaskIds.filter((taskId) => taskId !== id) : [...state.selectedTaskIds, id] })),
  clearSelection: () => set({ selectedTaskIds: [] }),
  setView: (currentView) => set({ currentView }),
  setFilters: (patch) => set((state) => ({ filters: { ...state.filters, ...patch } }))
}))
