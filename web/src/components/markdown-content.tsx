"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy } from "lucide-react";
import { useState, useCallback, type ComponentPropsWithoutRef } from "react";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="absolute right-2 top-2 rounded-md border border-border bg-background/80 p-1.5 text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
      aria-label="Copy code"
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

type CodeProps = ComponentPropsWithoutRef<"code"> & { inline?: boolean };

export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="prose prose-sm prose-invert max-w-none break-words">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
        code({ className, children, ...props }: CodeProps) {
          const match = /language-(\w+)/.exec(className || "");
          const codeString = String(children).replace(/\n$/, "");

          if (match) {
            return (
              <div className="group relative my-3">
                <div className="flex items-center justify-between rounded-t-lg border border-b-0 border-border bg-card/50 px-4 py-1.5">
                  <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    {match[1]}
                  </span>
                </div>
                <CopyButton text={codeString} />
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    borderTopLeftRadius: 0,
                    borderTopRightRadius: 0,
                    borderBottomLeftRadius: "0.5rem",
                    borderBottomRightRadius: "0.5rem",
                    fontSize: "0.8125rem",
                    border: "1px solid var(--border)",
                    borderTop: "none",
                  }}
                >
                  {codeString}
                </SyntaxHighlighter>
              </div>
            );
          }
          return (
            <code
              className="rounded-md bg-muted px-1.5 py-0.5 text-[0.8125rem] font-mono text-foreground"
              {...props}
            >
              {children}
            </code>
          );
        },
        pre({ children }) {
          return <>{children}</>;
        },
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2 hover:text-primary/80"
            >
              {children}
            </a>
          );
        },
        table({ children }) {
          return (
            <div className="my-3 overflow-x-auto">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          );
        },
        th({ children }) {
          return (
            <th className="border border-border bg-muted/50 px-3 py-2 text-left font-semibold">
              {children}
            </th>
          );
        },
        td({ children }) {
          return (
            <td className="border border-border px-3 py-2">{children}</td>
          );
        },
        blockquote({ children }) {
          return (
            <blockquote className="my-3 border-l-4 border-primary/50 pl-4 italic text-muted-foreground">
              {children}
            </blockquote>
          );
        },
        ul({ children }) {
          return <ul className="my-2 list-disc space-y-1 pl-6">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="my-2 list-decimal space-y-1 pl-6">{children}</ol>;
        },
        h1({ children }) {
          return <h1 className="mb-3 mt-6 text-xl font-bold">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="mb-2 mt-5 text-lg font-semibold">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="mb-2 mt-4 text-base font-semibold">{children}</h3>;
        },
        p({ children }) {
          return <p className="my-2 leading-relaxed">{children}</p>;
        },
        hr() {
          return <hr className="my-4 border-border" />;
        },
      }}
    >
      {content}
    </Markdown>
    </div>
  );
}
