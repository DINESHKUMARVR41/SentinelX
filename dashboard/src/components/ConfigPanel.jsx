import { useState, useEffect } from 'react'
import { fetchConfig, updateConfig, testGeminiConnection } from '../api/client'
import { TestTube, CheckCircle, XCircle, AlertTriangle, RotateCcw, Database, Zap, Brain, Shield, Sparkles, Info } from 'lucide-react'

function ConfigPanel() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testingGemini, setTestingGemini] = useState(false)
  const [geminiTestResult, setGeminiTestResult] = useState(null)
  const [resetConfirm, setResetConfirm] = useState(false)

  // Default configuration
  const defaultConfig = {
    auto_investigate: true,
    max_concurrent_investigations: 3,
    max_storage_mb: 1024,
    cleanup_threshold_mb: 900,
    cleanup_amount_mb: 100
  }

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const configData = await fetchConfig()
      setConfig(configData)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load config:', error)
      setLoading(false)
    }
  }

  const handleUpdate = async (updates) => {
    setSaving(true)
    try {
      await updateConfig(updates)
      await loadData()
    } catch (error) {
      console.error('Failed to update config:', error)
    }
    setSaving(false)
  }

  const handleResetToDefaults = async () => {
    if (!resetConfirm) {
      setResetConfirm(true)
      setTimeout(() => setResetConfirm(false), 5000)
      return
    }
    
    setSaving(true)
    try {
      await updateConfig(defaultConfig)
      await loadData()
      setResetConfirm(false)
    } catch (error) {
      console.error('Failed to reset config:', error)
    }
    setSaving(false)
  }

  const handleTestGemini = async () => {
    setTestingGemini(true)
    setGeminiTestResult(null)
    try {
      const result = await testGeminiConnection()
      setGeminiTestResult(result)
    } catch (error) {
      setGeminiTestResult({
        success: false,
        error: error.message,
        message: 'Connection test failed'
      })
    }
    setTestingGemini(false)
  }

  if (loading || !config) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '400px',
        color: '#9ca3af' 
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '14px', marginBottom: '8px' }}>
            {loading ? 'Loading configuration...' : 'Failed to load configuration'}
          </div>
          {!loading && !config && (
            <div style={{ fontSize: '12px', color: '#ef4444', marginTop: '8px' }}>
              Please check the API server is running
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto',
      padding: '0 20px'
    }}>
      {/* Header with Reset Button */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '1px solid #2a2a2a'
      }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '4px' }}>
            Settings
          </h1>
          <p style={{ fontSize: '13px', color: '#9ca3af' }}>
            Configure SentinelX's behavior and monitoring parameters
          </p>
        </div>
        <button
          onClick={handleResetToDefaults}
          disabled={saving}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            background: resetConfirm ? '#7c2d12' : '#1a1a1a',
            border: resetConfirm ? '1px solid #dc2626' : '1px solid #3a3a3a',
            borderRadius: '6px',
            color: resetConfirm ? '#fca5a5' : '#e0e0e0',
            fontSize: '13px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <RotateCcw size={16} />
          {resetConfirm ? 'Click again to confirm' : 'Reset to defaults'}
        </button>
      </div>

      {/* Gemini Connection */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '8px', 
            background: '#1a1a1a',
            border: '1px solid #3a3a3a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={20} color="#a78bfa" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px' }}>
              Gemini 2.5 Flash Connection
            </h2>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              Test connectivity to Google's AI model
            </p>
          </div>
        </div>
        
        <button
          onClick={handleTestGemini}
          disabled={testingGemini}
          className="button button-primary"
          style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <TestTube size={16} />
          {testingGemini ? 'Testing connection...' : 'Test connection'}
        </button>

        {geminiTestResult && (
          <div style={{
            background: geminiTestResult.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${geminiTestResult.success ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '8px',
            padding: '12px'
          }}>
            <div style={{
              fontSize: '13px',
              color: geminiTestResult.success ? '#4ade80' : '#ef4444',
              fontWeight: '500',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              {geminiTestResult.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
              {geminiTestResult.success ? 'Connected successfully' : 'Connection failed'}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>
              {geminiTestResult.message}
            </div>
            {geminiTestResult.model && (
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '8px', fontFamily: 'monospace' }}>
                Model: {geminiTestResult.model}
              </div>
            )}
            {geminiTestResult.error && (
              <div style={{ fontSize: '11px', color: '#ef4444', marginTop: '8px', fontFamily: 'monospace' }}>
                Error: {geminiTestResult.error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Investigation Behavior */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '8px', 
            background: '#1a1a1a',
            border: '1px solid #3a3a3a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Zap size={20} color="#3b82f6" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px' }}>
              Investigation behavior
            </h2>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              Control how SentinelX responds to suspicious processes
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gap: '24px' }}>
          {/* Auto Investigate Toggle */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            padding: '16px',
            background: '#0a0a0a',
            borderRadius: '8px',
            border: '1px solid #2a2a2a'
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
                Auto-investigate triggered processes
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                Automatically start full investigations when suspicious processes are detected
              </div>
            </div>
            <label style={{ 
              position: 'relative', 
              display: 'inline-block', 
              width: '48px', 
              height: '26px',
              marginLeft: '16px'
            }}>
              <input
                type="checkbox"
                checked={config.auto_investigate}
                onChange={(e) => handleUpdate({ auto_investigate: e.target.checked })}
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                cursor: 'pointer',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: config.auto_investigate ? '#3b82f6' : '#3a3a3a',
                transition: '0.3s',
                borderRadius: '26px'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '',
                  height: '20px',
                  width: '20px',
                  left: config.auto_investigate ? '25px' : '3px',
                  bottom: '3px',
                  background: 'white',
                  transition: '0.3s',
                  borderRadius: '50%'
                }} />
              </span>
            </label>
          </div>

          {/* Max Concurrent Investigations */}
          <div style={{ 
            padding: '16px',
            background: '#0a0a0a',
            borderRadius: '8px',
            border: '1px solid #2a2a2a'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
                Maximum concurrent investigations
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                Limit simultaneous investigations to prevent resource exhaustion
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={config.max_concurrent_investigations}
                onChange={(e) => handleUpdate({ max_concurrent_investigations: parseInt(e.target.value) })}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  background: '#2a2a2a',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
              <div style={{ 
                minWidth: '40px',
                padding: '6px 12px',
                background: '#1a1a1a',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#3b82f6',
                textAlign: 'center'
              }}>
                {config.max_concurrent_investigations}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Storage Management */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '8px', 
            background: '#1a1a1a',
            border: '1px solid #3a3a3a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Database size={20} color="#10b981" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px' }}>
              Storage management
            </h2>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              Configure automatic cleanup of raw process events
            </p>
          </div>
        </div>

        <div style={{ 
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '20px',
          display: 'flex',
          gap: '8px'
        }}>
          <Info size={16} color="#10b981" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#10b981', marginBottom: '4px', fontWeight: '500' }}>
              Active investigation data is always protected
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>
              Cleanup only removes old events from completed or inactive investigations
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gap: '20px' }}>
          {/* Max Storage */}
          <div style={{ 
            padding: '16px',
            background: '#0a0a0a',
            borderRadius: '8px',
            border: '1px solid #2a2a2a'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
                Maximum database size
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                Database will not grow beyond this size
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <input
                type="range"
                min="512"
                max="4096"
                step="256"
                value={config.max_storage_mb || 1024}
                onChange={(e) => handleUpdate({ max_storage_mb: parseInt(e.target.value) })}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  background: '#2a2a2a',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
              <div style={{ 
                minWidth: '80px',
                padding: '6px 12px',
                background: '#1a1a1a',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#3b82f6',
                textAlign: 'center'
              }}>
                {config.max_storage_mb || 1024} MB
              </div>
            </div>
          </div>

          {/* Cleanup Threshold */}
          <div style={{ 
            padding: '16px',
            background: '#0a0a0a',
            borderRadius: '8px',
            border: '1px solid #2a2a2a'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
                Cleanup threshold
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                Start cleanup when database reaches this size
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <input
                type="range"
                min="256"
                max={config.max_storage_mb || 1024}
                step="50"
                value={config.cleanup_threshold_mb || 900}
                onChange={(e) => handleUpdate({ cleanup_threshold_mb: parseInt(e.target.value) })}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  background: '#2a2a2a',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
              <div style={{ 
                minWidth: '80px',
                padding: '6px 12px',
                background: '#1a1a1a',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#f59e0b',
                textAlign: 'center'
              }}>
                {config.cleanup_threshold_mb || 900} MB
              </div>
            </div>
          </div>

          {/* Cleanup Amount */}
          <div style={{ 
            padding: '16px',
            background: '#0a0a0a',
            borderRadius: '8px',
            border: '1px solid #2a2a2a'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
                Cleanup amount
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                How much data to remove during each cleanup cycle
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <input
                type="range"
                min="50"
                max="500"
                step="50"
                value={config.cleanup_amount_mb || 100}
                onChange={(e) => handleUpdate({ cleanup_amount_mb: parseInt(e.target.value) })}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  background: '#2a2a2a',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
              <div style={{ 
                minWidth: '80px',
                padding: '6px 12px',
                background: '#1a1a1a',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#ef4444',
                textAlign: 'center'
              }}>
                {config.cleanup_amount_mb || 100} MB
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gemini Analysis Info */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '8px', 
            background: '#1a1a1a',
            border: '1px solid #3a3a3a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Brain size={20} color="#8b5cf6" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px' }}>
              Gemini 2.5 Flash analysis
            </h2>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              AI thinking levels are automatically optimized
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gap: '12px' }}>
          {[
            { title: 'Interval analysis', desc: '1-minute summaries', level: 'low', color: '#60a5fa' },
            { title: 'Triggered triage', desc: 'Rapid initial assessment', level: 'low', color: '#60a5fa' },
            { title: 'Deep forensics', desc: 'Comprehensive investigation', level: 'high', color: '#a78bfa' },
            { title: 'Report generation', desc: 'Detailed markdown reports', level: 'high', color: '#a78bfa' }
          ].map((item, idx) => (
            <div key={idx} style={{ 
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#0a0a0a',
              borderRadius: '8px',
              border: '1px solid #2a2a2a'
            }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: '500', color: '#e0e0e0', marginBottom: '2px' }}>
                  {item.title}
                </div>
                <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                  {item.desc}
                </div>
              </div>
              <div style={{ 
                padding: '4px 12px',
                background: `${item.color}20`,
                border: `1px solid ${item.color}40`,
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '600',
                color: item.color,
                fontFamily: 'monospace'
              }}>
                thinking_level: {item.level}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Beta Prevention */}
      <div className="card" style={{ border: '1px solid #4a1a1a', background: '#0f0a0a' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '8px', 
            background: '#1a1a1a',
            border: '1px solid #4a2a2a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Shield size={20} color="#ef4444" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px', color: '#fca5a5' }}>
              Beta prevention features
            </h2>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              Experimental - Use only in sandbox environments
            </p>
          </div>
        </div>
        
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '16px',
          display: 'flex',
          gap: '8px'
        }}>
          <AlertTriangle size={16} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#fca5a5', marginBottom: '4px', fontWeight: '500' }}>
              Warning
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>
              Allows autonomous action against suspicious processes. Only enable in isolated test environments.
            </div>
          </div>
        </div>

        <label style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px',
          background: '#0a0a0a',
          borderRadius: '8px',
          border: '1px solid #4a2a2a',
          cursor: 'pointer'
        }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '500', color: '#e0e0e0', marginBottom: '4px' }}>
              Enable beta prevention
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>
              Allow automatic process termination and isolation
            </div>
          </div>
          <div style={{ 
            position: 'relative', 
            display: 'inline-block', 
            width: '48px', 
            height: '26px',
            marginLeft: '16px'
          }}>
            <input
              type="checkbox"
              checked={config.enable_beta_prevention}
              onChange={(e) => {
                if (e.target.checked) {
                  if (confirm('Enable Beta Prevention?\n\nThis allows the agent to take automatic action. Only use in test environments.')) {
                    handleUpdate({ enable_beta_prevention: true })
                  }
                } else {
                  handleUpdate({ enable_beta_prevention: false })
                }
              }}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: 'absolute',
              cursor: 'pointer',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: config.enable_beta_prevention ? '#ef4444' : '#3a3a3a',
              transition: '0.3s',
              borderRadius: '26px'
            }}>
              <span style={{
                position: 'absolute',
                content: '',
                height: '20px',
                width: '20px',
                left: config.enable_beta_prevention ? '25px' : '3px',
                bottom: '3px',
                background: 'white',
                transition: '0.3s',
                borderRadius: '50%'
              }} />
            </span>
          </div>
        </label>
      </div>

      {/* Saving Indicator */}
      {saving && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '12px 20px',
          background: '#1a1a1a',
          border: '1px solid #3a3a3a',
          borderRadius: '8px',
          fontSize: '13px',
          color: '#e0e0e0',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          zIndex: 1000
        }}>
          Saving changes...
        </div>
      )}
    </div>
  )
}

export default ConfigPanel
