import { useSearchParams } from 'react-router-dom'
import { TopicsBoard } from '../features/topics/TopicsBoard'
import { useMoveTask, useProtocol } from '../features/protocol/useProtocolQueries'
import { ErrorState, LoadingState } from '../shared/ui/states'

export function TopicsPage() {
  const [params] = useSearchParams()
  const protocolId = Number(params.get('protocolId') || localStorage.getItem('lastProtocolId'))
  const { data, isLoading, error } = useProtocol(protocolId)
  const move = useMoveTask(protocolId)

  if (isLoading) return <LoadingState />
  if (error || !data) return <ErrorState message={(error as Error)?.message || 'Не удалось загрузить board'} />

  return <TopicsBoard topics={data.topics} tasks={data.tasks} onDrop={(taskId, topicId) => move.mutate({ taskId, topicId })} />
}
