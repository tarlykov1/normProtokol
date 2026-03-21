import { useRef, useState } from 'react'

export function UploadDropzone({ onUpload, onDemo }: { onUpload: (file: File) => void; onDemo: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  return (
    <div
      className={`rounded-lg border-2 border-dashed p-10 text-center ${dragging ? 'border-slate-900 bg-slate-50' : 'border-slate-300 bg-white'}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); const file = e.dataTransfer.files[0]; if (file) onUpload(file) }}
    >
      <p className="mb-4 text-sm">Перетащите .docx файл или выберите вручную.</p>
      <div className="flex justify-center gap-2">
        <button onClick={() => inputRef.current?.click()} className="rounded bg-slate-900 px-4 py-2 text-white">Выбрать файл</button>
        <button onClick={onDemo} className="rounded border border-slate-300 px-4 py-2 text-slate-900">Открыть демо</button>
      </div>
      <input ref={inputRef} type="file" accept=".docx" className="hidden" onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])} />
    </div>
  )
}
