import { Shield, Zap, AlertTriangle, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import { CollapsibleSection } from './CollapsibleSection';
import { StatusBadge } from './StatusBadge';
import { PasswordInput } from './PasswordInput';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Switch } from '../ui/switch';
import { Separator } from '../ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import type { ProjectEnvConfig } from '../../../shared/types';

interface AuthProviderSectionProps {
  isExpanded: boolean;
  onToggle: () => void;
  envConfig: ProjectEnvConfig;
  onUpdateConfig: (updates: Partial<ProjectEnvConfig>) => void;
}

type AuthProviderType = 'oauth' | 'antigravity';

const PHASES = ['spec', 'planning', 'coding', 'qa'] as const;
type Phase = (typeof PHASES)[number];

const DEFAULT_PHASE_PROVIDERS: Record<Phase, AuthProviderType> = {
  spec: 'oauth',
  planning: 'oauth',
  coding: 'antigravity',
  qa: 'oauth',
};

// Available Antigravity models
const ANTIGRAVITY_MODELS = [
  { value: 'claude-opus-4-5-thinking', label: 'Claude Opus 4.5 (Thinking)' },
  { value: 'claude-sonnet-4-5-thinking', label: 'Claude Sonnet 4.5 (Thinking)' },
  { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
  { value: 'gemini-2.5-flash-thinking', label: 'Gemini 2.5 Flash (Thinking)' },
  { value: 'gemini-3-flash', label: 'Gemini 3.0 Flash' },
  { value: 'gemini-3-pro-high', label: 'Gemini 3.0 Pro (High)' },
  { value: 'gemini-3-pro-low', label: 'Gemini 3.0 Pro (Low)' },
  { value: 'gemini-3-pro-image', label: 'Gemini 3.0 Pro (Image)' },
] as const;

// Default Antigravity models per phase
const DEFAULT_PHASE_ANTIGRAVITY_MODELS: Record<Phase, string> = {
  spec: 'claude-opus-4-5-thinking',
  planning: 'gemini-3-pro-high',
  coding: 'gemini-3-flash',
  qa: 'claude-sonnet-4-5-thinking',
};

export function AuthProviderSection({
  isExpanded,
  onToggle,
  envConfig,
  onUpdateConfig,
}: AuthProviderSectionProps) {
  const { t } = useTranslation(['settings']);
  const [proxyStatus, setProxyStatus] = useState<'checking' | 'running' | 'stopped' | 'starting'>('checking');
  const [proxyError, setProxyError] = useState<string | null>(null);

  // Check proxy status when antigravity is enabled
  useEffect(() => {
    if (envConfig.antigravityEnabled) {
      checkProxyStatus();
    }
  }, [envConfig.antigravityEnabled]);

  const checkProxyStatus = async () => {
    setProxyStatus('checking');
    setProxyError(null);

    try {
      const result = await window.electronAPI.checkAntigravityProxy();

      if (result.success && result.data) {
        setProxyStatus(result.data.isRunning ? 'running' : 'stopped');
      } else {
        setProxyStatus('stopped');
        setProxyError(result.error || 'Failed to check proxy status');
      }
    } catch (error) {
      setProxyStatus('stopped');
      setProxyError(error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const startProxy = async () => {
    setProxyStatus('starting');
    setProxyError(null);

    try {
      const result = await window.electronAPI.startAntigravityProxy();

      if (result.success && result.data?.started) {
        setProxyStatus('running');
      } else {
        setProxyStatus('stopped');
        setProxyError(result.error || 'Failed to start proxy');
      }
    } catch (error) {
      setProxyStatus('stopped');
      setProxyError(error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleAntigravityToggle = async (checked: boolean) => {
    onUpdateConfig({ antigravityEnabled: checked });

    if (checked) {
      // Check proxy status when enabling
      setProxyStatus('checking');
      const result = await window.electronAPI.checkAntigravityProxy();

      if (result.success && result.data) {
        if (!result.data.isRunning) {
          // Proxy not running, start it automatically
          await startProxy();
        } else {
          setProxyStatus('running');
        }
      }
    }
  };

  const badge = envConfig.antigravityEnabled ? (
    <StatusBadge status="warning" label="Antigravity" />
  ) : (
    <StatusBadge status="info" label="OAuth Only" />
  );

  const getPhaseProvider = (phase: Phase): AuthProviderType => {
    switch (phase) {
      case 'spec':
        return envConfig.authProviderSpec || DEFAULT_PHASE_PROVIDERS.spec;
      case 'planning':
        return envConfig.authProviderPlanning || DEFAULT_PHASE_PROVIDERS.planning;
      case 'coding':
        return envConfig.authProviderCoding || DEFAULT_PHASE_PROVIDERS.coding;
      case 'qa':
        return envConfig.authProviderQa || DEFAULT_PHASE_PROVIDERS.qa;
    }
  };

  const updatePhaseProvider = (phase: Phase, provider: AuthProviderType) => {
    switch (phase) {
      case 'spec':
        onUpdateConfig({ authProviderSpec: provider });
        break;
      case 'planning':
        onUpdateConfig({ authProviderPlanning: provider });
        break;
      case 'coding':
        onUpdateConfig({ authProviderCoding: provider });
        break;
      case 'qa':
        onUpdateConfig({ authProviderQa: provider });
        break;
    }
  };

  const getPhaseAntigravityModel = (phase: Phase): string => {
    switch (phase) {
      case 'spec':
        return envConfig.antigravityModelSpec || DEFAULT_PHASE_ANTIGRAVITY_MODELS.spec;
      case 'planning':
        return envConfig.antigravityModelPlanning || DEFAULT_PHASE_ANTIGRAVITY_MODELS.planning;
      case 'coding':
        return envConfig.antigravityModelCoding || DEFAULT_PHASE_ANTIGRAVITY_MODELS.coding;
      case 'qa':
        return envConfig.antigravityModelQa || DEFAULT_PHASE_ANTIGRAVITY_MODELS.qa;
    }
  };

  const updatePhaseAntigravityModel = (phase: Phase, model: string) => {
    switch (phase) {
      case 'spec':
        onUpdateConfig({ antigravityModelSpec: model });
        break;
      case 'planning':
        onUpdateConfig({ antigravityModelPlanning: model });
        break;
      case 'coding':
        onUpdateConfig({ antigravityModelCoding: model });
        break;
      case 'qa':
        onUpdateConfig({ antigravityModelQa: model });
        break;
    }
  };

  return (
    <CollapsibleSection
      title={t('authProvider.title')}
      icon={<Shield className="h-4 w-4" />}
      isExpanded={isExpanded}
      onToggle={onToggle}
      badge={badge}
    >
      <p className="text-xs text-muted-foreground mb-4">
        {t('authProvider.description')}
      </p>

      {/* Enable Antigravity Toggle */}
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-warning" />
            <Label className="font-normal text-foreground">
              {t('authProvider.antigravityEnabled')}
            </Label>
          </div>
          <p className="text-xs text-muted-foreground pl-6">
            {t('authProvider.antigravityEnabledDescription')}
          </p>
        </div>
        <Switch
          checked={envConfig.antigravityEnabled || false}
          onCheckedChange={handleAntigravityToggle}
        />
      </div>

      {/* Proxy Status Indicator */}
      {envConfig.antigravityEnabled && (
        <div className="flex items-center gap-2 text-xs">
          {proxyStatus === 'checking' && (
            <>
              <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
              <span className="text-muted-foreground">Checking proxy status...</span>
            </>
          )}
          {proxyStatus === 'starting' && (
            <>
              <Loader2 className="h-3 w-3 animate-spin text-warning" />
              <span className="text-warning">Starting proxy...</span>
            </>
          )}
          {proxyStatus === 'running' && (
            <>
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-green-600 dark:text-green-400">Proxy running</span>
            </>
          )}
          {proxyStatus === 'stopped' && (
            <>
              <div className="h-2 w-2 rounded-full bg-red-500" />
              <span className="text-red-600 dark:text-red-400">Proxy stopped</span>
              <button
                onClick={startProxy}
                className="ml-2 text-xs underline hover:no-underline"
              >
                Start manually
              </button>
            </>
          )}
          {proxyError && (
            <span className="text-red-600 dark:text-red-400 ml-2">({proxyError})</span>
          )}
        </div>
      )}

      {envConfig.antigravityEnabled && (
        <>
          {/* Warning Banner */}
          <div className="rounded-lg border border-warning/30 bg-warning/5 p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-warning mt-0.5 shrink-0" />
              <div className="text-xs text-warning">
                <p className="font-medium">{t('authProvider.warning')}</p>
                <p className="mt-1 text-muted-foreground">
                  {t('authProvider.setupInstructions')}
                </p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Proxy Configuration */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">
                {t('authProvider.antigravityBaseUrl')}
              </Label>
              <p className="text-xs text-muted-foreground">
                {t('authProvider.antigravityBaseUrlDescription')}
              </p>
              <Input
                placeholder={t('authProvider.antigravityBaseUrlPlaceholder')}
                value={envConfig.antigravityBaseUrl || ''}
                onChange={(e) => onUpdateConfig({ antigravityBaseUrl: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">
                {t('authProvider.antigravityAuthToken')}
              </Label>
              <p className="text-xs text-muted-foreground">
                {t('authProvider.antigravityAuthTokenDescription')}
              </p>
              <PasswordInput
                value={envConfig.antigravityAuthToken || ''}
                onChange={(value) => onUpdateConfig({ antigravityAuthToken: value })}
                placeholder={t('authProvider.antigravityAuthTokenPlaceholder')}
              />
            </div>
          </div>

          <Separator />

          {/* Phase Configuration */}
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-foreground">
                {t('authProvider.phaseConfig')}
              </Label>
              <p className="text-xs text-muted-foreground mt-1">
                {t('authProvider.phaseConfigDescription')}
              </p>
            </div>

            <div className="space-y-3">
              {PHASES.map((phase) => {
                const phaseProvider = getPhaseProvider(phase);
                const isAntigravity = phaseProvider === 'antigravity';

                return (
                  <div
                    key={phase}
                    className="space-y-3 rounded-lg border border-border p-3"
                  >
                    {/* Auth Provider Selection */}
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="font-normal text-foreground">
                          {t(`authProvider.phases.${phase}`)}
                        </Label>
                      </div>
                      <Select
                        value={phaseProvider}
                        onValueChange={(value: AuthProviderType) =>
                          updatePhaseProvider(phase, value)
                        }
                      >
                        <SelectTrigger className="w-[160px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="oauth">
                            {t('authProvider.oauth')}
                          </SelectItem>
                          <SelectItem value="antigravity">
                            {t('authProvider.antigravity')}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Antigravity Model Selection (only when using antigravity) */}
                    {isAntigravity && (
                      <div className="flex items-center justify-between pl-4 border-l-2 border-warning/30">
                        <div className="space-y-0.5">
                          <Label className="text-xs font-normal text-muted-foreground">
                            {t('authProvider.antigravityModel')}
                          </Label>
                        </div>
                        <Select
                          value={getPhaseAntigravityModel(phase)}
                          onValueChange={(value: string) =>
                            updatePhaseAntigravityModel(phase, value)
                          }
                        >
                          <SelectTrigger className="w-[220px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {ANTIGRAVITY_MODELS.map((model) => (
                              <SelectItem key={model.value} value={model.value}>
                                {model.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </CollapsibleSection>
  );
}
