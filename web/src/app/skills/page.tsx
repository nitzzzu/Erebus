"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Zap, Plus, Loader2, Code2, X, Trash2, FileText, GitBranch, ChevronDown, ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import {
  listSkills,
  installSkillFromGitHub,
  deleteSkill,
  listSkillFiles,
  readSkillFile,
} from "@/lib/api-client";

interface SkillFile {
  path: string;
  size: number;
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Install from GitHub
  const [showInstall, setShowInstall] = useState(false);
  const [installUrl, setInstallUrl] = useState("");
  const [installing, setInstalling] = useState(false);
  const [installError, setInstallError] = useState<string | null>(null);

  // Delete
  const [deletingSkill, setDeletingSkill] = useState<string | null>(null);

  // View files dialog
  const [viewSkill, setViewSkill] = useState<string | null>(null);
  const [skillFiles, setSkillFiles] = useState<SkillFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [openFile, setOpenFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileContentLoading, setFileContentLoading] = useState(false);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSkills();
      setSkills(data.skills);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch skills");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleInstall = async () => {
    if (!installUrl.trim()) return;
    setInstalling(true);
    setInstallError(null);
    try {
      await installSkillFromGitHub(installUrl.trim());
      setInstallUrl("");
      setShowInstall(false);
      await fetchSkills();
    } catch (err) {
      setInstallError(err instanceof Error ? err.message : "Failed to install skill");
    } finally {
      setInstalling(false);
    }
  };

  const handleDelete = async (name: string) => {
    setDeletingSkill(name);
    try {
      await deleteSkill(name);
      await fetchSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to delete skill '${name}'`);
    } finally {
      setDeletingSkill(null);
    }
  };

  const handleViewFiles = async (name: string) => {
    setViewSkill(name);
    setSkillFiles([]);
    setOpenFile(null);
    setFileContent(null);
    setFilesLoading(true);
    try {
      const data = await listSkillFiles(name);
      setSkillFiles(data.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to list files for skill '${name}'`);
      setSkillFiles([]);
    } finally {
      setFilesLoading(false);
    }
  };

  const handleOpenFile = async (skillName: string, filePath: string) => {
    if (openFile === filePath) {
      setOpenFile(null);
      setFileContent(null);
      return;
    }
    setOpenFile(filePath);
    setFileContent(null);
    setFileContentLoading(true);
    try {
      const data = await readSkillFile(skillName, filePath);
      setFileContent(data.content);
    } catch (err) {
      setFileContent(
        `Error: ${err instanceof Error ? err.message : "failed to load file"}`
      );
    } finally {
      setFileContentLoading(false);
    }
  };

  const isDeletable = (skill: Record<string, unknown>) =>
    skill.source === "user" ||
    skill.source === "user-skill-md" ||
    skill.source === "user-created";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="h-5 w-5" /> Skills
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage agent skills and capabilities
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => { setShowInstall(!showInstall); setInstallError(null); }}
        >
          {showInstall
            ? <X className="mr-1 h-3 w-3" />
            : <GitBranch className="mr-1 h-3 w-3" />}
          {showInstall ? "Cancel" : "Install from GitHub"}
        </Button>
      </div>

      <div className="p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {showInstall && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <GitBranch className="h-4 w-4" /> Install Skill from GitHub
              </CardTitle>
              <CardDescription>
                Paste a GitHub folder URL to sparse-checkout and install a skill.{" "}
                Example:{" "}
                <code className="text-xs bg-muted px-1 rounded">
                  https://github.com/owner/repo/tree/main/skills/my-skill
                </code>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {installError && (
                <div className="rounded-lg border border-destructive bg-destructive/10 p-2 text-xs text-destructive">
                  {installError}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  value={installUrl}
                  onChange={(e) => setInstallUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo/tree/main/path/to/skill"
                  className="flex-1 text-sm"
                  onKeyDown={(e) => { if (e.key === "Enter") handleInstall(); }}
                />
                <Button onClick={handleInstall} disabled={installing || !installUrl.trim()}>
                  {installing
                    ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    : <Plus className="mr-2 h-4 w-4" />}
                  Install
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <ScrollArea className="h-[calc(100vh-220px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : skills.length === 0 ? (
            <div className="text-center py-12">
              <Code2 className="mx-auto h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 text-sm text-muted-foreground">No skills registered yet</p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {skills.map((skill, i) => (
                <Card key={i}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-sm truncate">
                        {String(skill.name ?? "Unnamed")}
                      </CardTitle>
                      <Badge
                        variant={skill.source === "builtin" ? "secondary" : "outline"}
                        className="text-[10px] shrink-0"
                      >
                        {String(skill.source ?? "unknown")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                      {String(skill.description ?? "")}
                    </p>
                    {isDeletable(skill) && (
                      <div className="flex gap-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={() => handleViewFiles(String(skill.name))}
                        >
                          <FileText className="h-3 w-3 mr-1" />
                          Files
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 px-2 text-xs text-destructive hover:bg-destructive/10"
                          disabled={deletingSkill === String(skill.name)}
                          onClick={() => handleDelete(String(skill.name))}
                        >
                          {deletingSkill === String(skill.name) ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Trash2 className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* View Files Dialog */}
      <Dialog
        open={viewSkill !== null}
        onOpenChange={(open) => { if (!open) setViewSkill(null); }}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {viewSkill} — files
            </DialogTitle>
            <DialogDescription>
              Files inside this skill directory
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto min-h-0">
            {filesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : skillFiles.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No files found.</p>
            ) : (
              <div className="space-y-1">
                {skillFiles.map((file) => (
                  <div key={file.path} className="rounded border border-border overflow-hidden">
                    <button
                      className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-accent transition-colors text-left"
                      onClick={() => handleOpenFile(viewSkill!, file.path)}
                    >
                      <span className="flex items-center gap-2 truncate">
                        {openFile === file.path
                          ? <ChevronDown className="h-3 w-3 shrink-0" />
                          : <ChevronRight className="h-3 w-3 shrink-0" />}
                        <span className="font-mono truncate">{file.path}</span>
                      </span>
                      <span className="text-muted-foreground shrink-0 ml-2">
                        {file.size < 1024
                          ? `${file.size}B`
                          : `${(file.size / 1024).toFixed(1)}KB`}
                      </span>
                    </button>
                    {openFile === file.path && (
                      <div className="border-t bg-muted/40 p-3">
                        {fileContentLoading ? (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Loader2 className="h-3 w-3 animate-spin" /> Loading…
                          </div>
                        ) : (
                          <pre className="text-xs font-mono whitespace-pre-wrap break-all max-h-64 overflow-auto">
                            {fileContent}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
