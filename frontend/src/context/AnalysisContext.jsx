import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const AnalysisContext = createContext(null)

export function AnalysisProvider({ children }) {
  const [file, setFile] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [imageSize, setImageSize] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => () => imageUrl && URL.revokeObjectURL(imageUrl), [imageUrl])

  const selectFile = (nextFile) => {
    if (!nextFile) return
    if (imageUrl) URL.revokeObjectURL(imageUrl)
    const nextUrl = URL.createObjectURL(nextFile)
    const image = new Image()
    image.onload = () => setImageSize({ width: image.naturalWidth, height: image.naturalHeight })
    image.src = nextUrl
    setFile(nextFile)
    setImageUrl(nextUrl)
    setImageSize(null)
    setResult(null)
  }

  const value = useMemo(() => ({ file, imageUrl, imageSize, result, setResult, selectFile }), [file, imageUrl, imageSize, result])
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}

export const useAnalysis = () => useContext(AnalysisContext)
