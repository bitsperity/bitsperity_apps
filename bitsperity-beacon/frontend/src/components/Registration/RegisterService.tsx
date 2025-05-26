import { useState } from 'react'
import { useServiceStore } from '../../stores/serviceStore'
import { ServiceCreate } from '../../types/service'

export default function RegisterService() {
  const { registerService, loading } = useServiceStore()
  const [formData, setFormData] = useState<ServiceCreate>({
    name: '',
    type: 'iot',
    host: '',
    port: 8080,
    protocol: 'http',
    tags: [],
    metadata: {},
    ttl: 300
  })
  const [tagInput, setTagInput] = useState('')
  const [metadataKey, setMetadataKey] = useState('')
  const [metadataValue, setMetadataValue] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await registerService(formData)
      // Reset form
      setFormData({
        name: '',
        type: 'iot',
        host: '',
        port: 8080,
        protocol: 'http',
        tags: [],
        metadata: {},
        ttl: 300
      })
      setTagInput('')
      setMetadataKey('')
      setMetadataValue('')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 5000)
    } catch (error) {
      console.error('Registration failed:', error)
    }
  }

  const addTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()]
      }))
      setTagInput('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags?.filter(tag => tag !== tagToRemove) || []
    }))
  }

  const addMetadata = () => {
    if (metadataKey.trim() && metadataValue.trim()) {
      setFormData(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          [metadataKey.trim()]: metadataValue.trim()
        }
      }))
      setMetadataKey('')
      setMetadataValue('')
    }
  }

  const removeMetadata = (keyToRemove: string) => {
    setFormData(prev => {
      const newMetadata = { ...prev.metadata }
      delete newMetadata[keyToRemove]
      return {
        ...prev,
        metadata: newMetadata
      }
    })
  }

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'iot',
      host: '',
      port: 8080,
      protocol: 'http',
      tags: [],
      metadata: {},
      ttl: 300
    })
    setTagInput('')
    setMetadataKey('')
    setMetadataValue('')
  }

  return (
    <div className="space-y-6 lg:space-y-8">
      {/* Header */}
      <div className="text-center lg:text-left">
        <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Service registrieren
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto lg:mx-0">
          Registriere einen neuen Service im Bitsperity Beacon Discovery System
        </p>
      </div>

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-4 lg:p-6 animate-slide-up">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-semibold text-green-800">Service erfolgreich registriert!</h3>
              <p className="mt-1 text-sm text-green-700">Der Service ist jetzt im Discovery System verfügbar.</p>
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="px-6 py-8 lg:px-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Basic Information */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                Grundinformationen
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="form-label">
                    Service Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="form-input"
                    placeholder="z.B. homegrow-client"
                  />
                  <p className="mt-1 text-xs text-gray-500">Ein eindeutiger Name für deinen Service</p>
                </div>
                
                <div>
                  <label className="form-label">
                    Service Type *
                  </label>
                  <select
                    required
                    value={formData.type}
                    onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                    className="form-select"
                  >
                    <option value="iot">IoT Device</option>
                    <option value="mqtt">MQTT Broker</option>
                    <option value="http">HTTP Service</option>
                    <option value="api">REST API</option>
                    <option value="database">Database</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Wähle den passenden Service-Typ</p>
                </div>
              </div>
            </div>

            {/* Network Configuration */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </div>
                Netzwerk-Konfiguration
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="form-label">
                    Host/IP Address *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.host}
                    onChange={(e) => setFormData(prev => ({ ...prev, host: e.target.value }))}
                    className="form-input"
                    placeholder="192.168.1.100 oder example.com"
                  />
                  <p className="mt-1 text-xs text-gray-500">IP-Adresse oder Hostname des Services</p>
                </div>
                
                <div>
                  <label className="form-label">
                    Port *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="65535"
                    value={formData.port}
                    onChange={(e) => setFormData(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                    className="form-input"
                    placeholder="8080"
                  />
                  <p className="mt-1 text-xs text-gray-500">Port-Nummer (1-65535)</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                <div>
                  <label className="form-label">
                    Protocol
                  </label>
                  <select
                    value={formData.protocol}
                    onChange={(e) => setFormData(prev => ({ ...prev, protocol: e.target.value }))}
                    className="form-select"
                  >
                    <option value="http">HTTP</option>
                    <option value="https">HTTPS</option>
                    <option value="mqtt">MQTT</option>
                    <option value="tcp">TCP</option>
                    <option value="udp">UDP</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Kommunikationsprotokoll</p>
                </div>
                
                <div>
                  <label className="form-label">
                    TTL (Sekunden)
                  </label>
                  <input
                    type="number"
                    min="60"
                    max="3600"
                    value={formData.ttl}
                    onChange={(e) => setFormData(prev => ({ ...prev, ttl: parseInt(e.target.value) }))}
                    className="form-input"
                    placeholder="300"
                  />
                  <p className="mt-1 text-xs text-gray-500">Zeit bis zur automatischen Löschung (60-3600s)</p>
                </div>
              </div>
            </div>

            {/* Tags */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
                Tags
              </h2>
              
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    className="form-input flex-1"
                    placeholder="Tag hinzufügen (z.B. production, iot, sensor)"
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    className="btn-secondary px-6"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Hinzufügen
                  </button>
                </div>
                
                {formData.tags && formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-lg border border-blue-200 group"
                      >
                        <span>{tag}</span>
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-2 text-blue-500 hover:text-blue-700 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-500">Tags helfen bei der Kategorisierung und Suche</p>
              </div>
            </div>

            {/* Metadata */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                Metadata
              </h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <input
                    type="text"
                    value={metadataKey}
                    onChange={(e) => setMetadataKey(e.target.value)}
                    className="form-input"
                    placeholder="Key (z.B. version)"
                  />
                  <input
                    type="text"
                    value={metadataValue}
                    onChange={(e) => setMetadataValue(e.target.value)}
                    className="form-input"
                    placeholder="Value (z.B. 1.0.0)"
                  />
                  <button
                    type="button"
                    onClick={addMetadata}
                    className="btn-secondary"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Hinzufügen
                  </button>
                </div>
                
                {formData.metadata && Object.keys(formData.metadata).length > 0 && (
                  <div className="space-y-2">
                    {Object.entries(formData.metadata).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between bg-gray-50 px-4 py-3 rounded-xl border border-gray-200">
                        <span className="text-sm font-medium">
                          <span className="text-gray-600">{key}:</span> <span className="text-gray-900">{value}</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => removeMetadata(key)}
                          className="text-red-500 hover:text-red-700 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-500">Zusätzliche Informationen über den Service</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={resetForm}
                className="btn-secondary flex-1 sm:flex-none"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Zurücksetzen
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 sm:flex-none px-8"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Registriere...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Service registrieren
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}