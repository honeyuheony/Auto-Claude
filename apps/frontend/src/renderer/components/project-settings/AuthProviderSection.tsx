import { Shield, Zap, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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

export function AuthProviderSection({
  isExpanded,
  onToggle,
  envConfig,
  onUpdateConfig,
}: AuthProviderSectionProps) {
  const { t } = useTranslation(['settings']);

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
          onCheckedChange={(checked) => onUpdateConfig({ antigravityEnabled: checked })}
        />
      </div>

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
              {PHASES.map((phase) => (
                <div
                  key={phase}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div className="space-y-0.5">
                    <Label className="font-normal text-foreground">
                      {t(`authProvider.phases.${phase}`)}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {t(`authProvider.defaults.${phase}`)}
                    </p>
                  </div>
                  <Select
                    value={getPhaseProvider(phase)}
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
              ))}
            </div>
          </div>
        </>
      )}
    </CollapsibleSection>
  );
}
