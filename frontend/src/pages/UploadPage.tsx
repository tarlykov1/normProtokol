import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBootstrapDemo, useProtocolsList, useUploadProtocol } from '../features/protocol/useProtocolQueries'
import { RecentProtocolsList } from '../features/upload/RecentProtocolsList'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { ProtocolType } from '../types/domain'
import { ErrorState, LoadingState } from '../shared/ui/states'

export function UploadPage() {
  const navigate = useNavigate()
  const upload = useUploadProtocol()
  const protocols = useProtocolsList()
  const bootstrapDemo = useBootstrapDemo()
  const [protocolType, setProtocolType] = useState<ProtocolType>('standard')

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

  return (
    <div className="space-y-4">
      <UploadDropzone onUpload={onUpload} onDemo={onDemo} protocolType={protocolType} onProtocolTypeChange={setProtocolType} />
      {(upload.isPending || bootstrapDemo.isPending) && <LoadingState label="Подготавливаем данные для демонстрации..." />}
      {(upload.error || bootstrapDemo.error) && <ErrorState message={(upload.error || bootstrapDemo.error)?.message ?? "Ошибка"} />}
      {protocols.data && <RecentProtocolsList protocols={protocols.data} />}
    </div>
  )
}
