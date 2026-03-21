import { useNavigate } from 'react-router-dom'
import { useBootstrapDemo, useProtocolsList, useUploadProtocol } from '../features/protocol/useProtocolQueries'
import { RecentProtocolsList } from '../features/upload/RecentProtocolsList'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { ErrorState, LoadingState } from '../shared/ui/states'

export function UploadPage() {
  const navigate = useNavigate()
  const upload = useUploadProtocol()
  const protocols = useProtocolsList()
  const bootstrapDemo = useBootstrapDemo()

  const onUpload = async (file: File) => {
    const protocol = await upload.mutateAsync(file)
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
      <UploadDropzone onUpload={onUpload} onDemo={onDemo} />
      {(upload.isPending || bootstrapDemo.isPending) && <LoadingState label="Подготавливаем данные для демонстрации..." />}
      {(upload.error || bootstrapDemo.error) && <ErrorState message={(upload.error || bootstrapDemo.error)?.message ?? "Ошибка"} />}
      {protocols.data && <RecentProtocolsList protocols={protocols.data} />}
    </div>
  )
}
