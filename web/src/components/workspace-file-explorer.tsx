"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Folder,
  FolderOpen,
  File,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  X,
  Loader2,
  PanelRightOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listWorkspaceFiles, readWorkspaceFile, type WorkspaceEntry } from "@/lib/api-client";

interface TreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  children?: TreeNode[];
  expanded?: boolean;
  loaded?: boolean;
}

interface Props {
  workspaceName: string;
  /** Called to close/collapse the panel */
  onClose?: () => void;
}

export function WorkspaceFileExplorer({ workspaceName, onClose }: Props) {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openFile, setOpenFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileLoading, setFileLoading] = useState(false);

  const loadDir = useCallback(
    async (dirPath = "") => {
      try {
        const data = await listWorkspaceFiles(workspaceName, dirPath);
        return data.entries;
      } catch {
        return [] as WorkspaceEntry[];
      }
    },
    [workspaceName]
  );

  const loadRoot = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const entries = await loadDir("");
      setTree(
        entries.map((e) => ({
          name: e.name,
          path: e.path,
          type: e.type,
          size: e.size,
          expanded: false,
          loaded: e.type === "file",
          children: e.type === "directory" ? [] : undefined,
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspace");
    } finally {
      setLoading(false);
    }
  }, [loadDir]);

  useEffect(() => {
    loadRoot();
  }, [loadRoot]);

  const toggleDir = useCallback(
    async (node: TreeNode, nodes: TreeNode[], setNodes: (n: TreeNode[]) => void) => {
      if (node.type !== "directory") return;

      const updateNode = (items: TreeNode[]): TreeNode[] =>
        items.map((item) => {
          if (item.path === node.path) {
            const nowExpanded = !item.expanded;
            return { ...item, expanded: nowExpanded };
          }
          if (item.children) {
            return { ...item, children: updateNode(item.children) };
          }
          return item;
        });

      // Load children if not yet loaded
      if (!node.loaded) {
        const children = await loadDir(node.path);
        const childNodes: TreeNode[] = children.map((e) => ({
          name: e.name,
          path: e.path,
          type: e.type,
          size: e.size,
          expanded: false,
          loaded: e.type === "file",
          children: e.type === "directory" ? [] : undefined,
        }));

        const injectChildren = (items: TreeNode[]): TreeNode[] =>
          items.map((item) => {
            if (item.path === node.path) {
              return { ...item, expanded: true, loaded: true, children: childNodes };
            }
            if (item.children) {
              return { ...item, children: injectChildren(item.children) };
            }
            return item;
          });

        setNodes(injectChildren(nodes));
        return;
      }

      setNodes(updateNode(nodes));
    },
    [loadDir]
  );

  const handleToggle = (node: TreeNode) => {
    toggleDir(node, tree, setTree);
  };

  const handleFileClick = async (node: TreeNode) => {
    if (openFile === node.path) {
      setOpenFile(null);
      setFileContent(null);
      return;
    }
    setOpenFile(node.path);
    setFileContent(null);
    setFileLoading(true);
    try {
      const data = await readWorkspaceFile(workspaceName, node.path);
      setFileContent(data.content);
    } catch (err) {
      setFileContent(
        err instanceof Error ? `Error: ${err.message}` : "Failed to read file"
      );
    } finally {
      setFileLoading(false);
    }
  };

  const renderNodes = (nodes: TreeNode[], depth = 0): React.ReactNode =>
    nodes.map((node) => (
      <div key={node.path}>
        <button
          className={`
            w-full flex items-center gap-1.5 py-1 px-2 text-xs hover:bg-accent rounded
            transition-colors text-left truncate
            ${openFile === node.path ? "bg-accent" : ""}
          `}
          style={{ paddingLeft: `${8 + depth * 12}px` }}
          onClick={() => (node.type === "directory" ? handleToggle(node) : handleFileClick(node))}
        >
          {node.type === "directory" ? (
            <>
              {node.expanded ? (
                <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" />
              )}
              {node.expanded ? (
                <FolderOpen className="h-3.5 w-3.5 shrink-0 text-yellow-500" />
              ) : (
                <Folder className="h-3.5 w-3.5 shrink-0 text-yellow-500" />
              )}
            </>
          ) : (
            <>
              <span className="w-3 shrink-0" />
              <File className="h-3.5 w-3.5 shrink-0 text-blue-400" />
            </>
          )}
          <span className="truncate">{node.name}</span>
          {node.type === "file" && node.size !== null && (
            <span className="ml-auto text-[10px] text-muted-foreground shrink-0">
              {node.size < 1024
                ? `${node.size}B`
                : node.size < 1048576
                ? `${(node.size / 1024).toFixed(0)}K`
                : `${(node.size / 1048576).toFixed(1)}M`}
            </span>
          )}
        </button>
        {node.type === "directory" && node.expanded && node.children && (
          <div>{renderNodes(node.children, depth + 1)}</div>
        )}
        {openFile === node.path && node.type === "file" && (
          <div className="mx-2 mb-1 rounded border border-border bg-muted/40 overflow-hidden">
            {fileLoading ? (
              <div className="flex items-center gap-2 p-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" /> Loading…
              </div>
            ) : (
              <pre className="text-[10px] font-mono p-2 whitespace-pre-wrap break-all max-h-48 overflow-auto leading-relaxed">
                {fileContent}
              </pre>
            )}
          </div>
        )}
      </div>
    ));

  return (
    <div className="flex flex-col h-full bg-background border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
        <div className="flex items-center gap-1.5 min-w-0">
          <PanelRightOpen className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="text-xs font-medium truncate">{workspaceName}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={loadRoot}
            title="Refresh"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={onClose}
              title="Close explorer"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Tree */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="py-1">
          {error ? (
            <p className="text-xs text-destructive px-3 py-2">{error}</p>
          ) : loading ? (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" /> Loading…
            </div>
          ) : tree.length === 0 ? (
            <p className="text-xs text-muted-foreground px-3 py-2">Empty workspace</p>
          ) : (
            renderNodes(tree)
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
