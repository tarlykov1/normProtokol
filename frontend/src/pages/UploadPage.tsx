import { useNavigate } from 'react-router-dom'
import { useProtocolsList, useUploadProtocol } from '../features/protocol/useProtocolQueries'
import { RecentProtocolsList } from '../features/upload/RecentProtocolsList'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { ErrorState, LoadingState } from '../shared/ui/states'

export function UploadPage() {
  const navigate = useNavigate()
  const upload = useUploadProtocol()
  const protocols = useProtocolsList()

  const onUpload = async (file: File) => {
    const protocol = await upload.mutateAsync(file)
    localStorage.setItem('lastProtocolId', String(protocol.id))
    navigate(`/normalize?protocolId=${protocol.id}`)
  }

  return (
    <div className="space-y-4">
      <UploadDropzone onUpload={onUpload} />
      {upload.isPending && <LoadingState label="Загружаем и запускаем предварительный разбор..." />}
      {upload.error && <ErrorState message={upload.error.message} />}
      {protocols.data && <RecentProtocolsList protocols={protocols.data} />}
    </div>
  )
}
