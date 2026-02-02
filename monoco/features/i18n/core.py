import fnmatch
from pathlib import Path
from typing import List, Optional
import re

DEFAULT_EXCLUDES = [
    ".git",
    ".reference",
    "dist",
    "build",
    "node_modules",
    "__pycache__",
    ".agent",
    ".mono",
    ".venv",
    "venv",
    "ENV",
    # Agent Integration Directories
    ".claude",
    ".gemini",
    ".qwen",
    ".openai",
    ".cursor",
    ".vscode",
    ".idea",
    ".fleet",
    ".vscode-test",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    # System Prompts & Agent Configs
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "QWEN.md",
    "SKILL.md",
]


def load_gitignore_patterns(root: Path) -> List[str]:
    """Load patterns from .gitignore file."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return []

    patterns = []
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Basic normalization for fnmatch
                    if line.startswith("/"):
                        line = line[1:]
                    patterns.append(line)
    except Exception:
        pass
    return patterns


def is_excluded(
    path: Path, root: Path, patterns: List[str], excludes_set: Optional[set] = None
) -> bool:
    """Check if a path should be excluded based on patterns and defaults."""
    rel_path = str(path.relative_to(root))

    # 1. Check default excludes (exact match for any path component, case-insensitive)
    if excludes_set:
        for part in path.parts:
            if part.lower() in excludes_set:
                return True

    # 2. Check gitignore patterns
    for pattern in patterns:
        # Check against relative path
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Check against filename
        if fnmatch.fnmatch(path.name, pattern):
            return True
        # Check if the pattern matches a parent directory
        # e.g. pattern "dist/" should match "dist/info.md"
        if pattern.endswith("/"):
            clean_pattern = pattern[:-1]
            if rel_path.startswith(clean_pattern + "/") or rel_path == clean_pattern:
                return True
        elif "/" in pattern:
            # If pattern has a slash, it might be a subpath match
            if rel_path.startswith(pattern + "/"):
                return True

    return False


def discover_markdown_files(root: Path, include_issues: bool = False) -> List[Path]:
    """Recursively find markdown files while respecting exclusion rules."""
    patterns = load_gitignore_patterns(root)
    all_md_files = []

    excludes = list(DEFAULT_EXCLUDES)
    if not include_issues:
        excludes.append("Issues")

    # Pre-calculate lowercase set for performance
    excludes_set = {e.lower() for e in excludes}

    # Use walk to skip excluded directories early
    for current_root, dirs, files in root.walk():
        # Filter directories in-place to skip excluded ones
        dirs[:] = [
            d
            for d in dirs
            if not is_excluded(
                current_root / d, root, patterns, excludes_set=excludes_set
            )
        ]

        for file in files:
            if file.endswith(".md"):
                p = current_root / file
                if not is_excluded(p, root, patterns, excludes_set=excludes_set):
                    all_md_files.append(p)

    return sorted(all_md_files)


def is_translation_file(path: Path, target_langs: List[str]) -> bool:
    """Check if the given path is a translation file (target)."""
    normalized_langs = [lang.lower() for lang in target_langs]

    # Suffix check (case-insensitive)
    stem_upper = path.stem.upper()
    for lang in normalized_langs:
        if stem_upper.endswith(f"_{lang.upper()}"):
            return True

    # Generic Suffix Check: Detect any _XX suffix where XX is 2-3 letters
    # This prevents files like README_ZH.md from being treated as source files
    # even if 'zh' is not in target_langs (e.g. when scanning for 'en' gaps).
    if re.search(r"_[A-Z]{2,3}$", stem_upper):
        return True

    # Subdir check (case-insensitive)
    path_parts_lower = [p.lower() for p in path.parts]
    for lang in normalized_langs:
        if lang in path_parts_lower:
            return True

    return False


def get_target_translation_path(
    path: Path, root: Path, lang: str, source_lang: str = "en"
) -> Path:
    """Calculate the expected translation path for a specific language."""
    lang = lang.lower()

    # Parallel Directory Mode: docs/en/... -> docs/zh/...
    path_parts = list(path.parts)
    # Search for source_lang component to replace
    for i, part in enumerate(path_parts):
        if part.lower() == source_lang.lower():
            path_parts[i] = lang
            return Path(*path_parts)

    # Suffix Mode:
    # If stem ends with _{SOURCE_LANG}, strip it.
    stem = path.stem
    source_suffix = f"_{source_lang.upper()}"
    if stem.upper().endswith(source_suffix):
        stem = stem[: -len(source_suffix)]

    if path.parent == root:
        return path.with_name(f"{stem}_{lang.upper()}{path.suffix}")

    # Subdir Mode: for documentation directories (fallback)
    return path.parent / lang / path.name


def check_translation_exists(
    path: Path, root: Path, target_langs: List[str], source_lang: str = "en"
) -> List[str]:
    """
    Verify which target languages have translations.
    Returns a list of missing language codes.
    """
    if is_translation_file(path, target_langs):
        return []  # Already a translation, skip

    # Special handling for standard files: always treat as EN source
    effective_source_lang = source_lang
    if path.name.upper() in [
        "README.MD",
        "CHANGELOG.MD",
        "CODE_OF_CONDUCT.MD",
        "CONTRIBUTING.MD",
        "LICENSE.MD",
        "SECURITY.MD",
    ]:
        effective_source_lang = "en"

    missing = []
    for lang in target_langs:
        # Skip if target language matches the effective source language
        if lang.lower() == effective_source_lang.lower():
            continue

        target = get_target_translation_path(path, root, lang, effective_source_lang)
        if not target.exists():
            missing.append(lang)
    return missing


# Common technical terms that should not count as "English words"
# when detecting language in Chinese documents
TECHNICAL_TERMS_ALLOWLIST = {
    # CLI/Shell
    "cli", "api", "ui", "ux", "gui", "cli", "shell", "bash", "zsh", "sh",
    "cmd", "powershell", "terminal", "console", "prompt",
    # Cloud/Container
    "kubernetes", "k8s", "docker", "container", "pod", "cluster", "node",
    "namespace", "ingress", "service", "deployment", "helm", "kubectl",
    "aws", "gcp", "azure", "cloud", "serverless", "lambda", "ec2", "s3",
    # DevOps/CI/CD
    "ci", "cd", "cicd", "pipeline", "jenkins", "gitlab", "github", "git",
    "svn", "mercurial", "hg", "commit", "branch", "merge", "rebase", "tag",
    "hook", "action", "workflow", "artifact", "build", "deploy", "release",
    # Programming Languages
    "python", "javascript", "js", "typescript", "ts", "java", "kotlin",
    "scala", "groovy", "ruby", "go", "golang", "rust", "c", "cpp", "c++",
    "csharp", "c#", "php", "perl", "lua", "swift", "objc", "objective-c",
    "r", "matlab", "julia", "dart", "flutter", "elixir", "erlang", "haskell",
    "clojure", "lisp", "scheme", "racket", "fsharp", "f#", "vb", "vba",
    # Web/Frameworks
    "html", "css", "scss", "sass", "less", "xml", "json", "yaml", "yml",
    "toml", "ini", "csv", "tsv", "markdown", "md", "rst", "asciidoc",
    "react", "vue", "angular", "svelte", "nextjs", "nuxt", "django",
    "flask", "fastapi", "tornado", "express", "koa", "nestjs", "spring",
    "rails", "laravel", "symfony", "dotnet", "aspnet", "mvc", "mvvm",
    # Databases
    "sql", "nosql", "mysql", "postgresql", "postgres", "sqlite", "oracle",
    "mssql", "sqlserver", "mongodb", "mongo", "redis", "cassandra",
    "dynamodb", "firebase", "elasticsearch", "solr", "neo4j", "graphql",
    # Testing
    "test", "testing", "unittest", "pytest", "jest", "mocha", "jasmine",
    "cypress", "selenium", "cucumber", "bdd", "tdd", "mock", "stub",
    "fixture", "assertion", "coverage", "benchmark", "profiling",
    # Architecture/Patterns
    "microservice", "microservices", "monolith", "server", "client",
    "frontend", "backend", "fullstack", "api-gateway", "load-balancer",
    "proxy", "cache", "cdn", "dns", "http", "https", "tcp", "udp",
    "websocket", "grpc", "rest", "soap", "graphql", "oauth", "jwt",
    "sso", "ldap", "auth", "authentication", "authorization",
    # OS/Platform
    "linux", "ubuntu", "debian", "centos", "rhel", "fedora", "arch",
    "alpine", "windows", "macos", "darwin", "ios", "android",
    "unix", "posix", "kernel", "systemd", "init", "daemon",
    # Tools/IDE
    "vscode", "idea", "pycharm", "webstorm", "vim", "neovim", "nvim",
    "emacs", "sublime", "atom", "eclipse", "netbeans", "xcode",
    "docker-compose", "dockerfile", "makefile", "cmake", "gradle",
    "maven", "npm", "yarn", "pnpm", "pip", "conda", "venv", "virtualenv",
    # AI/ML
    "ai", "ml", "dl", "llm", "nlp", "cv", "neural", "network",
    "tensorflow", "pytorch", "keras", "scikit", "sklearn", "pandas",
    "numpy", "scipy", "matplotlib", "seaborn", "jupyter", "notebook",
    "training", "inference", "model", "dataset", "vector", "embedding",
    # Security
    "security", "vulnerability", "exploit", "cve", "xss", "csrf",
    "injection", "encryption", "decryption", "hash", "signature",
    "certificate", "ssl", "tls", "https", "firewall", "vpn",
    # Monitoring/Observability
    "log", "logging", "metrics", "tracing", "observability", "monitoring",
    "alert", "dashboard", "grafana", "prometheus", "elk", "splunk",
    "datadog", "newrelic", "sentry", "bugsnag", "rollbar",
    # Agile/Project Management
    "agile", "scrum", "kanban", "sprint", "backlog", "epic", "story",
    "task", "issue", "ticket", "bug", "feature", "milestone", "roadmap",
    "retro", "standup", "review", "demo", "po", "sm", "pm",
    # Misc Tech Terms
    "id", "uuid", "guid", "url", "uri", "ip", "ipv4", "ipv6",
    "mac", "hostname", "domain", "subdomain", "path", "query",
    "header", "body", "payload", "request", "response", "status",
    "error", "exception", "warning", "info", "debug", "trace",
    "config", "configuration", "setting", "option", "flag", "env",
    "variable", "constant", "literal", "expression", "statement",
    "function", "method", "class", "object", "instance", "interface",
    "abstract", "virtual", "override", "inherit", "extend", "implement",
    "import", "export", "module", "package", "library", "framework",
    "sdk", "toolkit", "runtime", "compiler", "interpreter", "vm",
    "version", "release", "changelog", "license", "copyright",
    "repo", "repository", "fork", "clone", "pull", "push", "fetch",
    "upstream", "origin", "remote", "local", "stash", "stage",
    "index", "working", "tree", "head", "detached", "orphan",
    "squash", "amend", "cherry-pick", "revert", "reset", "clean",
    "linter", "formatter", "parser", "lexer", "ast", "ir",
    "bytecode", "opcode", "assembly", "binary", "executable",
    "static", "dynamic", "linking", "compilation", "transpilation",
    "minification", "bundling", "tree-shaking", "code-splitting",
    "hot-reload", "hot-restart", "live-reload", "watch", "watchman",
    "polyfill", "shim", "ponyfill", "fallback", "graceful",
    "async", "sync", "parallel", "concurrent", "sequential",
    "blocking", "non-blocking", "io", "nio", "epoll", "kqueue",
    "thread", "process", "coroutine", "fiber", "goroutine",
    "mutex", "lock", "semaphore", "channel", "queue", "stack",
    "heap", "gc", "garbage", "collection", "memory", "leak",
    "buffer", "stream", "pipe", "redirect", "tee", "cat",
    "grep", "awk", "sed", "cut", "sort", "uniq", "wc", "head", "tail",
    "find", "locate", "which", "whereis", "type", "alias",
    "export", "source", "env", "printenv", "set", "unset",
    "chmod", "chown", "chgrp", "umask", "sudo", "su",
    "ssh", "scp", "sftp", "rsync", "ftp", "telnet", "nc",
    "ping", "traceroute", "netstat", "ss", "lsof", "fuser",
    "ps", "top", "htop", "kill", "pkill", "killall", "nice",
    "cron", "at", "batch", "systemctl", "service", "init",
    "mount", "umount", "df", "du", "fsck", "mkfs", "fdisk",
    "parted", "lsblk", "blkid", "uuidgen", "tune2fs",
    "tar", "gzip", "gunzip", "zip", "unzip", "bz2", "xz",
    "7z", "rar", "archive", "compress", "decompress", "extract",
    "curl", "wget", "httpie", "postman", "insomnia",
    "nginx", "apache", "httpd", "tomcat", "jetty", "undertow",
    "haproxy", "traefik", "envoy", "istio", "linkerd",
    "rabbitmq", "kafka", "mqtt", "amqp", "stomp", "zeromq",
    "memcached", "etcd", "consul", "vault", "zookeeper",
    "prometheus", "grafana", "jaeger", "zipkin", "opentelemetry",
    "ansible", "puppet", "chef", "saltstack", "terraform",
    "pulumi", "vagrant", "packer", "nomad", "consul-template",
    "github-actions", "gitlab-ci", "travis", "circleci", "jenkins",
    "teamcity", "bamboo", "drone", "argo", "tekton", "spinnaker",
    "sonarqube", "nexus", "artifactory", "harbor", "chartmuseum",
    "loki", "fluentd", "fluent-bit", "vector", "filebeat",
    "telegraf", "influxdb", "timescaledb", "promscale",
    "minio", "ceph", "glusterfs", "nfs", "smb", "cifs",
    "vpn", "wireguard", "openvpn", "ipsec", "ssl-vpn",
    "waf", "ids", "ips", "siem", "soar", "xdr", "edr",
    "ldap", "ad", "sso", "saml", "oauth2", "openid", "oidc",
    "mfa", "2fa", "totp", "hotp", "u2f", "webauthn", "fido",
    "aes", "rsa", "ecc", "dsa", "ecdsa", "ed25519", "curve25519",
    "sha", "md5", "bcrypt", "scrypt", "argon2", "pbkdf2",
    "hmac", "cmac", "gcm", "cbc", "ecb", "ctr", "ofb", "cfb",
    "tls", "ssl", "x509", "csr", "crt", "pem", "der", "p12", "pfx",
    "acme", "letsencrypt", "certbot", "traefik", "caddy",
    "wasm", "webassembly", "wasmer", "wasmtime", "wasi",
    "pwa", "spa", "mpa", "ssr", "csr", "ssg", "isr",
    "amp", "instant", "turbo", "stimulus", "alpine", "htmx",
    "webcomponents", "shadow", "dom", "custom", "elements",
    "service-worker", "pwa", "manifest", "offline", "cache",
    "webrtc", "websocket", "sse", "eventsource", "polling",
    "graphql", "subscription", "mutation", "query", "schema",
    "resolver", "directive", "fragment", "interface", "union",
    "prisma", "sequelize", "typeorm", "sqlalchemy", "orm",
    "migration", "seed", "factory", "fixture", "mock", "stub",
    "faker", "factory-boy", "hypothesis", "property-based",
    "snapshot", "visual", "regression", "e2e", "integration",
    "unit", "functional", "acceptance", "performance", "load",
    "stress", "chaos", "contract", "pact", "consumer", "provider",
    "tdd", "bdd", "atdd", "sbe", "example", "specification",
    "given", "when", "then", "scenario", "feature", "background",
    "cucumber", "behave", "specflow", "gauge", "relish",
    "allure", "reportportal", "xunit", "nunit", "mstest",
    "sonar", "coveralls", "codecov", "codeclimate", "codacy",
    "deepsource", "snyk", "whitesource", "blackduck", "fossa",
    "dependabot", "renovate", "snyk", "greenkeeper",
    "pre-commit", "husky", "lint-staged", "commitlint",
    "semantic-release", "standard-version", "conventional",
    "changelog", "commitizen", "cz", "commitlint",
    "monoco", "kimi", "claude", "gemini", "qwen", "gpt",
}


def detect_language(content: str) -> str:
    """
    Detect the language of the content using improved heuristics.
    
    This function is designed to handle technical documents with mixed
    Chinese and English content, especially for IT/Software development topics.
    
    Returns: 'zh', 'en', or 'unknown'
    """
    if not content:
        return "unknown"

    # Strip YAML Frontmatter if present
    frontmatter_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
    content = frontmatter_pattern.sub("", content)

    if not content.strip():
        return "unknown"

    # Remove code blocks (```...```) as they often contain English keywords
    code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
    content_no_code = code_block_pattern.sub("", content)
    
    # Remove inline code (`...`)
    inline_code_pattern = re.compile(r"`[^`]+`")
    content_no_code = inline_code_pattern.sub("", content_no_code)
    
    # Remove URLs
    url_pattern = re.compile(r"https?://\S+|www\.\S+|")  
    content_clean = url_pattern.sub("", content_no_code)
    
    # Remove issue IDs (EPIC-0001, FEAT-1234, etc.)
    issue_id_pattern = re.compile(r"\b(EPIC|FEAT|CHORE|FIX)-\d{4}\b")
    content_clean = issue_id_pattern.sub("", content_clean)

    if not content_clean.strip():
        # If after cleaning there's nothing left, it was likely all code/IDs
        return "unknown"

    total_chars = len(content_clean)
    
    # Count CJK characters (Chinese/Japanese/Korean)
    cjk_count = sum(1 for c in content_clean if "\u4e00" <= c <= "\u9fff")
    
    # Count non-ASCII characters (excluding CJK)
    non_ascii_non_cjk = sum(
        1 for c in content_clean 
        if ord(c) > 127 and not ("\u4e00" <= c <= "\u9fff")
    )
    
    # Extract words for analysis (alphanumeric sequences)
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]*\b", content_clean)
    total_words = len(words)
    
    # Count technical terms in allowlist (case-insensitive)
    technical_term_count = sum(
        1 for word in words 
        if word.lower() in TECHNICAL_TERMS_ALLOWLIST
    )
    
    # Calculate non-technical English words
    non_technical_words = total_words - technical_term_count
    
    # Heuristic 1: If > 3% chars are CJK, likely Chinese document
    # Lowered threshold from 5% to 3% for better Chinese detection
    cjk_ratio = cjk_count / total_chars if total_chars > 0 else 0
    if cjk_ratio > 0.03:
        return "zh"
    
    # Heuristic 2: If significant CJK (>1%) and some English technical terms,
    # treat as Chinese (technical Chinese document)
    if cjk_ratio > 0.01 and technical_term_count > 0:
        return "zh"
    
    # Heuristic 3: For English detection
    # Only count non-technical English words towards English detection
    # Require at least 10 non-technical words to be considered English
    non_ascii_ratio = non_ascii_non_cjk / total_chars if total_chars > 0 else 0
    
    # Relaxed threshold: < 15% non-ASCII (excluding CJK) AND 
    # has meaningful non-technical English content
    if non_ascii_ratio < 0.15 and non_technical_words >= 10:
        return "en"
    
    # Heuristic 4: High English word density with low CJK
    if cjk_ratio < 0.01 and total_words > 20:
        return "en"

    return "unknown"


from enum import Enum
from dataclasses import dataclass
from typing import Iterator


class BlockType(Enum):
    """Types of content blocks in Markdown."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    LIST_ITEM = "list_item"
    QUOTE = "quote"
    TABLE = "table"
    EMPTY = "empty"


@dataclass
class ContentBlock:
    """Represents a block of content with its type and language info."""
    type: BlockType
    content: str
    line_start: int
    line_end: int
    detected_lang: str = "unknown"
    should_skip: bool = False


def parse_markdown_blocks(content: str) -> List[ContentBlock]:
    """
    Parse markdown content into blocks for language detection.
    
    This function respects block boundaries like:
    - Code blocks (```...```)
    - Headings (# ...)
    - Paragraphs
    - List items
    
    Returns a list of ContentBlock objects.
    """
    # Strip YAML Frontmatter if present
    frontmatter_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
    content_without_fm = frontmatter_pattern.sub("", content)
    
    lines = content_without_fm.splitlines()
    blocks = []
    current_block_lines = []
    current_block_type = BlockType.PARAGRAPH
    current_start_line = 0
    in_code_block = False
    code_block_lang = ""
    
    def flush_block():
        nonlocal current_block_lines, current_start_line
        if current_block_lines:
            content = "\n".join(current_block_lines)
            block = ContentBlock(
                type=current_block_type,
                content=content,
                line_start=current_start_line,
                line_end=current_start_line + len(current_block_lines),
            )
            blocks.append(block)
            current_block_lines = []
    
    for i, line in enumerate(lines):
        # Code block handling
        if line.strip().startswith("```"):
            if not in_code_block:
                # Start of code block
                flush_block()
                in_code_block = True
                code_block_lang = line.strip()[3:].strip()
                current_block_type = BlockType.CODE_BLOCK
                current_start_line = i
                current_block_lines.append(line)
            else:
                # End of code block
                current_block_lines.append(line)
                flush_block()
                in_code_block = False
                current_block_type = BlockType.PARAGRAPH
            continue
        
        if in_code_block:
            current_block_lines.append(line)
            continue
        
        # Heading
        if re.match(r"^#{1,6}\s", line):
            flush_block()
            block = ContentBlock(
                type=BlockType.HEADING,
                content=line,
                line_start=i,
                line_end=i + 1,
            )
            blocks.append(block)
            current_start_line = i + 1
            current_block_type = BlockType.PARAGRAPH
            continue
        
        # Empty line
        if not line.strip():
            flush_block()
            blocks.append(ContentBlock(
                type=BlockType.EMPTY,
                content="",
                line_start=i,
                line_end=i + 1,
            ))
            current_start_line = i + 1
            current_block_type = BlockType.PARAGRAPH
            continue
        
        # List item
        if re.match(r"^\s*[-*+]\s", line) or re.match(r"^\s*\d+\.\s", line):
            flush_block()
            current_block_type = BlockType.LIST_ITEM
            current_start_line = i
            current_block_lines.append(line)
            continue
        
        # Quote
        if line.strip().startswith(">"):
            flush_block()
            current_block_type = BlockType.QUOTE
            current_start_line = i
            current_block_lines.append(line)
            continue
        
        # Table row
        if "|" in line and not line.strip().startswith("#"):
            if current_block_type != BlockType.TABLE:
                flush_block()
                current_block_type = BlockType.TABLE
                current_start_line = i
            current_block_lines.append(line)
            continue
        
        # Default: accumulate into paragraph
        if not current_block_lines:
            current_start_line = i
        current_block_lines.append(line)
    
    # Flush remaining
    flush_block()
    
    return blocks


def is_review_comments_section(block: ContentBlock, all_blocks: List[ContentBlock], block_index: int) -> bool:
    """
    Check if a block is within a Review Comments section.
    
    This handles cases where English text appears in Review Comments sections
    of Chinese documents (which is valid and expected).
    """
    # Look backwards for the most recent heading
    for i in range(block_index - 1, -1, -1):
        prev_block = all_blocks[i]
        if prev_block.type == BlockType.HEADING:
            heading_content = prev_block.content.lower()
            # Check for Review Comments section indicators
            if any(keyword in heading_content for keyword in [
                "review comments", "review", "评审", "确认事项", 
                "评审记录", "复盘记录", "确认"
            ]):
                return True
            # If we hit another major section heading, stop looking
            if prev_block.type == BlockType.HEADING:
                break
    return False


def should_skip_block_for_language_check(
    block: ContentBlock, 
    all_blocks: List[ContentBlock], 
    block_index: int,
    source_lang: str = "zh"
) -> bool:
    """
    Determine if a block should be skipped during language consistency checks.
    
    Reasons to skip:
    1. Code blocks (always contain English keywords)
    2. Review Comments sections in non-English documents (may contain English feedback)
    3. Empty blocks
    4. Blocks with only technical terms/IDs
    """
    # Always skip code blocks
    if block.type == BlockType.CODE_BLOCK:
        return True
    
    # Skip empty blocks
    if block.type == BlockType.EMPTY:
        return True
    
    # Skip Review Comments sections in Chinese documents
    # (English review comments in Chinese issues are expected)
    if source_lang == "zh" and is_review_comments_section(block, all_blocks, block_index):
        return True
    
    # Check if block contains only technical content
    content = block.content.strip()
    if not content:
        return True
    
    # Remove common non-language elements
    cleaned = content
    # Remove inline code
    cleaned = re.sub(r"`[^`]+`", "", cleaned)
    # Remove URLs
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)
    # Remove issue IDs
    cleaned = re.sub(r"\b(EPIC|FEAT|CHORE|FIX)-\d{4}\b", "", cleaned)
    
    if not cleaned.strip():
        return True
    
    return False


def detect_language_blocks(content: str, source_lang: str = "zh") -> List[ContentBlock]:
    """
    Detect language for each block in the content.
    
    This provides block-level language detection that respects:
    - Code blocks (skipped)
    - Review Comments sections (skipped for Chinese docs)
    - Paragraph boundaries
    
    Returns a list of ContentBlock objects with detected language.
    """
    blocks = parse_markdown_blocks(content)
    
    for i, block in enumerate(blocks):
        # Determine if this block should be skipped
        block.should_skip = should_skip_block_for_language_check(
            block, blocks, i, source_lang
        )
        
        if block.should_skip:
            block.detected_lang = "unknown"
            continue
        
        # Detect language for this specific block
        block.detected_lang = detect_language(block.content)
    
    return blocks


def has_language_mismatch_blocks(content: str, source_lang: str = "zh") -> Tuple[bool, List[ContentBlock]]:
    """
    Check if content has language mismatches at block level.
    
    Returns:
        (has_mismatch, mismatched_blocks)
        - has_mismatch: True if any non-skipped block has mismatched language
        - mismatched_blocks: List of blocks that don't match source language
    """
    blocks = detect_language_blocks(content, source_lang)
    mismatched = []
    
    for block in blocks:
        if block.should_skip or block.detected_lang == "unknown":
            continue
        
        if source_lang.lower() in ["zh", "cn"]:
            if block.detected_lang == "en":
                mismatched.append(block)
        elif source_lang.lower() == "en":
            if block.detected_lang == "zh":
                mismatched.append(block)
    
    return len(mismatched) > 0, mismatched


def is_content_source_language(path: Path, source_lang: str = "en") -> bool:
    """
    Check if file content appears to be in the source language.
    """
    try:
        # Special handling for README/CHANGELOG
        if path.name.upper() in ["README.MD", "CHANGELOG.MD"]:
            source_lang = "en"

        content = path.read_text(encoding="utf-8")
        detected = detect_language(content)

        # 'unknown' is leniently accepted as valid to avoid false positives on code-heavy files
        if detected == "unknown":
            return True

        # Normalize source_lang
        expected = source_lang.lower()
        if expected == "zh" or expected == "cn":
            return detected == "zh"
        elif expected == "en":
            return detected == "en"

        # For other languages, we don't have detectors yet
        return True
    except Exception:
        return True  # Assume valid on error


# ... (Existing code) ...

SKILL_CONTENT = """---
name: i18n-scan
description: Internationalization quality control skill.
---

# i18n Maintenance Standard

i18n is a "first-class citizen" in Monoco.

## Core Standards

### 1. i18n Structure
- **Root Files**: Suffix pattern (e.g. `README_ZH.md`).
- **Docs Directories**: Subdirectory pattern (`docs/guide/zh/intro.md`).

### 2. Exclusion Rules
- `.gitignore` (respected automatically)
- `.references/`
- Build artifacts

## Automated Checklist
1. **Coverage Scan**: `monoco i18n scan` - Checks missing translations.
2. **Integrity Check**: Planned.

## Working with I18n
- Create English docs first.
- Create translations following the naming convention.
- Run `monoco i18n scan` to verify coverage.
"""


def init(root: Path):
    """Initialize I18n environment (No-op currently as it relies on config)."""
    # In future, could generate i18n config section if missing.
    pass

    return {
        "skills": {"i18n": SKILL_CONTENT},
        "prompts": {},  # Handled by adapter via resource files
    }
