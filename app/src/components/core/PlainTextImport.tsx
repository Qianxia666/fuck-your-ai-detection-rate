import { useEffect, useRef } from "react";
import { CornerDownLeft, Eraser, WandSparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

/** Mirrors the backend default; the runtime value comes from `settings.maxTextChars`. */
export const MAX_TEXT_CHARS = 300_000;

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  busy?: boolean;
  autoFocus?: boolean;
  className?: string;
  textareaId?: string;
  /** Backend limit (FYADR_MAX_TEXT_CHARS); falls back to the built-in default. */
  maxChars?: number;
}

export function PlainTextEditor({
  value,
  onChange,
  onSubmit,
  busy = false,
  autoFocus = false,
  className,
  textareaId = "plain-text-input",
  maxChars = MAX_TEXT_CHARS,
}: Props) {
  const textarea = useRef<HTMLTextAreaElement>(null);
  const characters = value.replace(/\s/g, "").length;
  const overflow = characters > maxChars;
  const blank = !value.trim();

  useEffect(() => {
    if (!autoFocus) return;
    // 只在有精确指针且足够宽的屏幕上自动聚焦，避免手机上弹出键盘挡住卡片。
    if (!globalThis.matchMedia?.("(min-width: 1024px) and (pointer: fine)").matches) return;
    textarea.current?.focus();
  }, [autoFocus]);

  return (
    <div className={cn("flex min-h-0 flex-1 flex-col gap-3", className)}>
      <Textarea
        id={textareaId}
        ref={textarea}
        value={value}
        spellCheck={false}
        data-testid="plain-text-input"
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            if (!blank && !overflow && !busy) onSubmit();
          }
        }}
        placeholder={"把要改写的正文粘贴到这里。空行分段，标题行也可以一起贴进来。"}
        aria-label="要改写的正文"
        className={cn(
          "min-h-[11rem] flex-1 resize-none bg-background text-[15px] leading-7",
          overflow && "border-destructive focus-visible:ring-destructive",
        )}
      />

      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className={cn("text-[13px] tabular-nums text-muted-foreground", overflow && "text-destructive")}>
          {characters.toLocaleString("zh-CN")} 字
          {overflow ? ` · 超出 ${(characters - maxChars).toLocaleString("zh-CN")} 字上限` : ""}
        </span>
        <span className="hidden items-center gap-1 text-[13px] text-muted-foreground md:inline-flex">
          <CornerDownLeft className="size-3.5" aria-hidden />
          Ctrl + Enter
        </span>
        <div className="ml-auto flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            disabled={blank || busy}
            onClick={() => {
              onChange("");
              textarea.current?.focus();
            }}
          >
            <Eraser data-icon="inline-start" />
            清空
          </Button>
          <Button size="sm" disabled={blank || overflow || busy} onClick={onSubmit} data-testid="plain-text-submit">
            {busy ? <Spinner data-icon="inline-start" /> : <WandSparkles data-icon="inline-start" />}
            开始改写
          </Button>
        </div>
      </div>
    </div>
  );
}
