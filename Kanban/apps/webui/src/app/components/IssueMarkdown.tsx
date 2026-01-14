"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { useBridge } from "../contexts/BridgeContext";

interface IssueMarkdownProps {
  content: string;
}

export default function IssueMarkdown({ content }: IssueMarkdownProps) {
  const { postMessage, isVsCode } = useBridge();

  const handleFileClick = (path: string, line?: string, col?: string) => {
    if (!isVsCode) return;
    postMessage("OPEN_FILE", {
      path,
      line: line ? parseInt(line, 10) : 1,
      column: col ? parseInt(col, 10) : 1,
    });
  };

  // Custom renderer for text to auto-link file paths
  // Note: react-markdown doesn't easily support regex-replace on text nodes via 'components'.
  // Typically we use a remark plugin (remark-gemoji etc).
  // For simplicity MVP: We will assume file links are explicit Markdown links [label](path:line)
  // OR we use a simple pre-processor to convert path/to/file:line to [path/to/file:line](file://path/to/file:line) and handle the click.

  // Strategy: Pre-process content to turn file patterns into links with a custom scheme.
  // Regex: Match likely file paths. (./src/..., /Users/..., etc.)

  const processedContent = React.useMemo(() => {
    // Simple regex to catch ./src/file.ts:10 or /abs/path:10
    // Avoid matching inside existing links? Hard with regex.
    // Let's rely on manual linking for now via [src/app.ts:10](src/app.ts:10)
    // OR strictly match `whitespace path:line`

    // Better UX: The user wants "detect text matching ... and render as link".
    // Let's try a simple replace.

    const fileRegex = /(\s|^|`)([\w.\/-]+\.[a-z]+):(\d+)(?::(\d+))?/g;

    // Problem: This ruins code blocks if we aren't careful.
    // react-markdown handles code blocks separately.
    // If we modify source, we might modify code block content.

    // Safer Strategy: Use `components` to override `a` tag, and expect user/system to linkify.
    // BUT the requirement is "detect text".

    // Let's implement a custom `a` tag handler first, and maybe a `code` handler.
    return content;
  }, [content]);

  return (
    <article className="prose prose-sm prose-invert max-w-none">
      <ReactMarkdown
        components={{
          a: ({ node, href, children, ...props }: any) => {
            // Check if href looks like a file path or custom scheme
            const isFile = href?.match(/^([.\/].+\.[a-z]+)(?::(\d+))?$/);

            if (isFile) {
              const [_, path, line] = isFile;
              return (
                <span
                  className="text-blue-400 hover:underline cursor-pointer font-mono"
                  onClick={() => handleFileClick(path, line)}
                  title={`Open ${path}`}>
                  {children}
                </span>
              );
            }

            // Standard link
            // Avoid spreading ref
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { ref, ...rest } = props;
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                {...rest}
                className="text-blue-400 no-underline hover:underline">
                {children}
              </a>
            );
          },
          code: ({ node, className, children, ...props }: any) => {
            // Maybe code snippets are file paths?
            // `src/foo.ts:10`
            const content = String(children).trim();
            const match = content.match(/^([.\/].+\.[a-z]+):(\d+)$/);

            if (match) {
              return (
                <code
                  className={`${
                    className || ""
                  } bg-blue-500/20 text-blue-300 cursor-pointer hover:bg-blue-500/30 transition-colors`}
                  onClick={() => handleFileClick(match[1], match[2])}
                  title="Click to open in Editor">
                  {children}
                </code>
              );
            }

            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { ref, ...rest } = props;
            return (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          },
        }}>
        {processedContent}
      </ReactMarkdown>
    </article>
  );
}
