export function parseFrontmatter(content: string): any {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) {
    return {};
  }

  const yamlStr = match[1];
  const result: any = {};
  const lines = yamlStr.split(/\r?\n/);

  for (const line of lines) {
    const parts = line.split(":");
    if (parts.length >= 2) {
      const key = parts[0].trim();
      let value = parts.slice(1).join(":").trim();

      // Basic unquoting
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.substring(1, value.length - 1);
      }

      result[key] = value;
    }
  }

  return result;
}
