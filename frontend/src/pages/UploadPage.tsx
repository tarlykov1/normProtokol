import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBootstrapDemo, useDeleteProtocol, useProtocolsList, useUploadProtocol } from '../features/protocol/useProtocolQueries'
import { RecentProtocolsList } from '../features/upload/RecentProtocolsList'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { Protocol, ProtocolType } from '../types/domain'
import { ErrorState, LoadingState } from '../shared/ui/states'

export function UploadPage() {
  const navigate = useNavigate()
  const upload = useUploadProtocol()
  const protocols = useProtocolsList()
  const bootstrapDemo = useBootstrapDemo()
  const deleteProtocol = useDeleteProtocol()
  const [protocolType, setProtocolType] = useState<ProtocolType>('auto')

  const onUpload = async (file: File) => {
    const protocol = await upload.mutateAsync({ file, protocolType })
    localStorage.setItem('lastProtocolId', String(protocol.id))
    navigate(`/normalize?protocolId=${protocol.id}`)
  }

  const onDemo = async () => {
    const protocol = await bootstrapDemo.mutateAsync()
    localStorage.setItem('lastProtocolId', String(protocol.id))
    navigate(`/normalize?protocolId=${protocol.id}`)
  }

  const clearLastProtocolPointer = (deletedProtocolId: number) => {
    const savedLocalProtocolId = Number(localStorage.getItem('lastProtocolId'))
    if (savedLocalProtocolId === deletedProtocolId) localStorage.removeItem('lastProtocolId')

    const savedSessionProtocolId = Number(sessionStorage.getItem('lastProtocolId'))
    if (savedSessionProtocolId === deletedProtocolId) sessionStorage.removeItem('lastProtocolId')
  }

  const onDeleteProtocol = async (protocol: Protocol) => {
    const shouldDelete = window.confirm(`Удалить протокол #${protocol.id}?\nЭто действие нельзя отменить.`)
    if (!shouldDelete) return
    await deleteProtocol.mutateAsync(protocol.id)
    clearLastProtocolPointer(protocol.id)
  }

  return (
    <div className="space-y-4">
      <UploadDropzone onUpload={onUpload} onDemo={onDemo} protocolType={protocolType} onProtocolTypeChange={setProtocolType} />
      {(upload.isPending || bootstrapDemo.isPending) && <LoadingState label="Подготавливаем данные для демонстрации..." />}
      {(upload.error || bootstrapDemo.error || deleteProtocol.error) && <ErrorState message={(upload.error || bootstrapDemo.error || deleteProtocol.error)?.message ?? "Ошибка"} />}
      {protocols.data && <RecentProtocolsList protocols={protocols.data} deletingId={deleteProtocol.variables ?? null} onDelete={onDeleteProtocol} />}
    </div>
  )
}
