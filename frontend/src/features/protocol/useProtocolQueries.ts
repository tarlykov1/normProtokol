import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { protocolsApi } from '../../shared/api/protocolsApi'
import { tasksApi } from '../../shared/api/tasksApi'

export function useProtocolsList() {
  return useQuery({ queryKey: ['protocols'], queryFn: protocolsApi.list })
}

export function useProtocol(protocolId?: number) {
  return useQuery({ queryKey: ['protocol', protocolId], queryFn: () => protocolsApi.getById(protocolId!), enabled: !!protocolId })
}

export function useUploadProtocol() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: protocolsApi.upload, onSuccess: (data) => { qc.setQueryData(['protocol', data.id], data); qc.invalidateQueries({ queryKey: ['protocols'] }) } })
}

export function usePatchTask(protocolId?: number) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ id, patch }: { id: number; patch: Record<string, unknown> }) => tasksApi.patch(id, patch), onSuccess: () => qc.invalidateQueries({ queryKey: ['protocol', protocolId] }) })
}

export function useMoveTask(protocolId?: number) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ taskId, topicId }: { taskId: number; topicId: number | null }) => tasksApi.moveToTopic([taskId], topicId), onSuccess: () => qc.invalidateQueries({ queryKey: ['protocol', protocolId] }) })
}

export function useBootstrapDemo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: protocolsApi.demoBootstrap,
    onSuccess: (data) => {
      qc.setQueryData(['protocol', data.id], data)
      qc.invalidateQueries({ queryKey: ['protocols'] })
    }
  })
}
