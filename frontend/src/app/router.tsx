import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../shared/ui/layout'
import { ConfirmPage } from '../pages/ConfirmPage'
import { NormalizePage } from '../pages/NormalizePage'
import { ResultPage } from '../pages/ResultPage'
import { TopicsPage } from '../pages/TopicsPage'
import { UploadPage } from '../pages/UploadPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <UploadPage /> },
      { path: 'normalize', element: <NormalizePage /> },
      { path: 'topics', element: <TopicsPage /> },
      { path: 'confirm', element: <ConfirmPage /> },
      { path: 'result', element: <ResultPage /> }
    ]
  }
])
