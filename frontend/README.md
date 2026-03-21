# Frontend MVP — Protocol Normalizer

Внутренний frontend-инструмент для нормализации протоколов и публикации задач в Bitrix24.

## Архитектура
- **React + TypeScript + Vite**
- **React Router**: роуты по экранам Upload / Normalize / Topics / Confirm / Result
- **TanStack Query**: server state и API lifecycle
- **Zustand**: UI state (selection, filters, autosave indicator)
- **Tailwind CSS**: быстрый утилитарный UI
- **dnd-kit**: перенос задач между темами в board view

## Структура проекта
```text
src/
  app/               # router, queryClient
  pages/             # Upload/Normalize/Topics/Confirm/Result
  features/
    upload/          # dropzone, recent list
    protocol/        # queries + ui store
    tasks/           # table rows + bulk actions
    topics/          # board + DnD
  entities/          # доменные сущности (точка расширения)
  shared/
    api/             # typed API layer
    ui/              # layout + state components + badges
    hooks/           # autosave hook
    lib/             # утилиты + mock API
    config/          # глобальные стили
  types/             # TS доменные модели
```

## Команды
```bash
npm install
npm run dev
npm run build
npm run preview
```

## Переменные окружения
Скопируйте `.env.example` в `.env`.

- `VITE_API_BASE_URL` — backend base URL (по умолчанию `http://localhost:8000/api`)
- `VITE_USE_MOCK_API` — `true/false`, моковый backend адаптер

## Интеграция с backend
API-клиент в `src/shared/api`:
- `protocolsApi`
- `tasksApi`
- `topicsApi`
- `assigneesApi`
- `publishApi`

DOCX download реализован через `axios` blob + `downloadBlob` util.

## Mock backend
Для запуска без backend:
```bash
VITE_USE_MOCK_API=true npm run dev
```
Используются fake responses из `src/shared/lib/mockApi.ts`.

## Экраны
1. **Upload** — загрузка `.docx`, статус, последние протоколы.
2. **Normalize** — inline edits, фильтрация, bulk операции, autosave.
3. **Topics** — kanban-представление, DnD перенос между темами.
4. **Confirm** — validate/generate/download/publish.
5. **Result** — итог публикации в Bitrix24.


## Демо режим
- На Upload странице доступна кнопка **"Открыть демо"**.
- При `VITE_USE_MOCK_API=false` frontend вызывает `POST /api/demo/bootstrap` и получает готовый протокол с темами/задачами для тестирования.
- При `VITE_USE_MOCK_API=true` данные берутся из `mockApi` без backend.
