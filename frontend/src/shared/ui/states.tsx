import { ReactNode } from 'react'

export const PageContainer = ({ children }: { children: ReactNode }) => <div className="mx-auto max-w-[1400px] p-4">{children}</div>
export const LoadingState = ({ label = 'Загрузка...' }: { label?: string }) => <div className="rounded border bg-white p-6 text-sm">{label}</div>
export const ErrorState = ({ message }: { message: string }) => <div className="rounded border border-red-300 bg-red-50 p-4 text-red-700">{message}</div>
export const EmptyState = ({ label }: { label: string }) => <div className="rounded border border-dashed bg-white p-6 text-gray-500">{label}</div>
