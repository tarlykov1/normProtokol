import { useRef, useState } from 'react'
import { ProtocolType } from '../../types/domain'

const protocolTypeOptions: Array<{ value: ProtocolType; label: string }> = [
  { value: 'auto', label: 'Автоопределение (рекомендуется)' },
  { value: 'memo_meeting', label: 'Мемо рабочей встречи' },
  { value: 'memo_preparation', label: 'Мемо подготовки к совещанию' },
  { value: 'memo_mixed_sections', label: 'Мемо со смешанными секциями' },
  { value: 'memo_hierarchical', label: 'Иерархическое мемо' },
  { value: 'simple', label: 'Простой документ' }
]

export function UploadDropzone({
  onUpload,
  onDemo,
  protocolType,
  onProtocolTypeChange
}: {
  onUpload: (file: File) => void
  onDemo: () => void
  protocolType: ProtocolType
  onProtocolTypeChange: (value: ProtocolType) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  return (
    <div
      className={`rounded-lg border-2 border-dashed p-10 text-center ${dragging ? 'border-slate-900 bg-slate-50' : 'border-slate-300 bg-white'}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); const file = e.dataTransfer.files[0]; if (file) onUpload(file) }}
    >
      <p className="mb-2 text-sm">Перетащите .docx файл или выберите вручную.</p>
      <div className="mx-auto mb-4 max-w-sm text-left">
        <label className="mb-1 block text-xs text-slate-600">Тип документа</label>
        <select
          className="w-full rounded border px-2 py-1 text-sm"
          value={protocolType}
          onChange={(e) => onProtocolTypeChange(e.target.value as ProtocolType)}
        >
          {protocolTypeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </div>
      <div className="flex justify-center gap-2">
        <button onClick={() => inputRef.current?.click()} className="rounded bg-slate-900 px-4 py-2 text-white">Выбрать файл</button>
        <button onClick={onDemo} className="rounded border border-slate-300 px-4 py-2 text-slate-900">Открыть демо</button>
      </div>
      <input ref={inputRef} type="file" accept=".docx" className="hidden" onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])} />
    </div>
  )
}
