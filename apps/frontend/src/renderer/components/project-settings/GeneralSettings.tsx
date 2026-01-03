import {
  RefreshCw,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Checkbox } from '../ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select';
import { Separator } from '../ui/separator';
import { AVAILABLE_MODELS } from '../../../shared/constants';
import type {
  Project,
  ProjectSettings as ProjectSettingsType,
  AutoBuildVersionInfo,
  ClaudeMdSource,
  ClaudeSettingSource
} from '../../../shared/types';

interface GeneralSettingsProps {
  project: Project;
  settings: ProjectSettingsType;
  setSettings: React.Dispatch<React.SetStateAction<ProjectSettingsType>>;
  versionInfo: AutoBuildVersionInfo | null;
  isCheckingVersion: boolean;
  isUpdating: boolean;
  handleInitialize: () => Promise<void>;
}

export function GeneralSettings({
  project,
  settings,
  setSettings,
  versionInfo,
  isCheckingVersion,
  isUpdating,
  handleInitialize
}: GeneralSettingsProps) {
  const { t } = useTranslation(['settings']);

  return (
    <>
      {/* Auto-Build Integration */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Auto-Build Integration</h3>
        {!project.autoBuildPath ? (
          <div className="rounded-lg border border-border bg-muted/50 p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-warning mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">Not Initialized</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Initialize Auto-Build to enable task creation and agent workflows.
                </p>
                <Button
                  size="sm"
                  className="mt-3"
                  onClick={handleInitialize}
                  disabled={isUpdating}
                >
                  {isUpdating ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Initializing...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Initialize Auto-Build
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-muted/50 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span className="text-sm font-medium text-foreground">Initialized</span>
              </div>
              <code className="text-xs bg-background px-2 py-1 rounded">
                {project.autoBuildPath}
              </code>
            </div>
            {isCheckingVersion ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                Checking status...
              </div>
            ) : versionInfo && (
              <div className="text-xs text-muted-foreground">
                {versionInfo.isInitialized ? 'Initialized' : 'Not initialized'}
              </div>
            )}
          </div>
        )}
      </section>

      {project.autoBuildPath && (
        <>
          <Separator />

          {/* Agent Settings */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Agent Configuration</h3>
            <div className="space-y-2">
              <Label htmlFor="model" className="text-sm font-medium text-foreground">Model</Label>
              <Select
                value={settings.model}
                onValueChange={(value) => setSettings({ ...settings, model: value })}
              >
                <SelectTrigger id="model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* CLAUDE.md Sources */}
            <div className="space-y-3 pt-2">
              <div className="space-y-0.5">
                <Label className="font-normal text-foreground">
                  {t('projectSections.general.claudeMdSources')}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {t('projectSections.general.claudeMdSourcesDescription')}
                </p>
              </div>
              <div className="flex flex-col gap-2 pl-1">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="claudeMd-user"
                    checked={settings.claudeMdSources?.includes('user') ?? false}
                    onCheckedChange={(checked) => {
                      const current = settings.claudeMdSources ?? [];
                      const newSources = checked
                        ? [...current.filter(s => s !== 'user'), 'user'] as ClaudeMdSource[]
                        : current.filter(s => s !== 'user') as ClaudeMdSource[];
                      setSettings({ ...settings, claudeMdSources: newSources.length > 0 ? newSources : undefined });
                    }}
                  />
                  <Label htmlFor="claudeMd-user" className="text-sm font-normal cursor-pointer">
                    {t('projectSections.general.claudeMdUser')}
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="claudeMd-project"
                    checked={settings.claudeMdSources?.includes('project') ?? false}
                    onCheckedChange={(checked) => {
                      const current = settings.claudeMdSources ?? [];
                      const newSources = checked
                        ? [...current.filter(s => s !== 'project'), 'project'] as ClaudeMdSource[]
                        : current.filter(s => s !== 'project') as ClaudeMdSource[];
                      setSettings({ ...settings, claudeMdSources: newSources.length > 0 ? newSources : undefined });
                    }}
                  />
                  <Label htmlFor="claudeMd-project" className="text-sm font-normal cursor-pointer">
                    {t('projectSections.general.claudeMdProject')}
                  </Label>
                </div>
              </div>
            </div>

            {/* Claude Setting Sources (Skills, Hooks, Commands) */}
            <div className="space-y-3 pt-2">
              <div className="space-y-0.5">
                <Label className="font-normal text-foreground">
                  {t('projectSections.general.claudeSettingSources')}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {t('projectSections.general.claudeSettingSourcesDescription')}
                </p>
              </div>
              <div className="flex flex-col gap-2 pl-1">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="settingSources-user"
                    checked={settings.claudeSettingSources?.includes('user') ?? false}
                    onCheckedChange={(checked) => {
                      const current = settings.claudeSettingSources ?? [];
                      const newSources = checked
                        ? [...current.filter(s => s !== 'user'), 'user'] as ClaudeSettingSource[]
                        : current.filter(s => s !== 'user') as ClaudeSettingSource[];
                      setSettings({ ...settings, claudeSettingSources: newSources.length > 0 ? newSources : undefined });
                    }}
                  />
                  <Label htmlFor="settingSources-user" className="text-sm font-normal cursor-pointer">
                    {t('projectSections.general.settingSourceUser')}
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="settingSources-project"
                    checked={settings.claudeSettingSources?.includes('project') ?? false}
                    onCheckedChange={(checked) => {
                      const current = settings.claudeSettingSources ?? [];
                      const newSources = checked
                        ? [...current.filter(s => s !== 'project'), 'project'] as ClaudeSettingSource[]
                        : current.filter(s => s !== 'project') as ClaudeSettingSource[];
                      setSettings({ ...settings, claudeSettingSources: newSources.length > 0 ? newSources : undefined });
                    }}
                  />
                  <Label htmlFor="settingSources-project" className="text-sm font-normal cursor-pointer">
                    {t('projectSections.general.settingSourceProject')}
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="settingSources-local"
                    checked={settings.claudeSettingSources?.includes('local') ?? false}
                    onCheckedChange={(checked) => {
                      const current = settings.claudeSettingSources ?? [];
                      const newSources = checked
                        ? [...current.filter(s => s !== 'local'), 'local'] as ClaudeSettingSource[]
                        : current.filter(s => s !== 'local') as ClaudeSettingSource[];
                      setSettings({ ...settings, claudeSettingSources: newSources.length > 0 ? newSources : undefined });
                    }}
                  />
                  <Label htmlFor="settingSources-local" className="text-sm font-normal cursor-pointer">
                    {t('projectSections.general.settingSourceLocal')}
                  </Label>
                </div>
              </div>
            </div>
          </section>

          <Separator />

          {/* Notifications */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="font-normal text-foreground">On Task Complete</Label>
                <Switch
                  checked={settings.notifications.onTaskComplete}
                  onCheckedChange={(checked) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        onTaskComplete: checked
                      }
                    })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="font-normal text-foreground">On Task Failed</Label>
                <Switch
                  checked={settings.notifications.onTaskFailed}
                  onCheckedChange={(checked) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        onTaskFailed: checked
                      }
                    })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="font-normal text-foreground">On Review Needed</Label>
                <Switch
                  checked={settings.notifications.onReviewNeeded}
                  onCheckedChange={(checked) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        onReviewNeeded: checked
                      }
                    })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="font-normal text-foreground">Sound</Label>
                <Switch
                  checked={settings.notifications.sound}
                  onCheckedChange={(checked) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        sound: checked
                      }
                    })
                  }
                />
              </div>
            </div>
          </section>
        </>
      )}
    </>
  );
}
