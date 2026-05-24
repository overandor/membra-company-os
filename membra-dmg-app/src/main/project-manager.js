const fs = require("fs");
const path = require("path");

const IGNORE_DIRS = new Set([
  "node_modules", ".git", "__pycache__", ".venv", "venv",
  "dist", "build", ".next", ".cache", "target", ".tox",
  "coverage", ".nyc_output", ".pytest_cache", "egg-info",
]);

const IGNORE_EXTENSIONS = new Set([
  ".pyc", ".pyo", ".class", ".o", ".so", ".dylib",
  ".exe", ".dll", ".bin", ".dat", ".db", ".sqlite",
  ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
  ".mp3", ".mp4", ".avi", ".mov", ".wav",
  ".zip", ".tar", ".gz", ".rar", ".7z",
  ".woff", ".woff2", ".ttf", ".eot",
]);

class ProjectManager {
  constructor() {
    this.projectRoot = null;
    this.fileCache = new Map();
  }

  async openProject(dirPath) {
    if (!fs.existsSync(dirPath)) {
      return { error: `Directory not found: ${dirPath}` };
    }
    this.projectRoot = dirPath;
    this.fileCache.clear();
    const tree = await this.getTree();
    const info = this._detectProjectInfo(dirPath);
    return { root: dirPath, tree, info };
  }

  async readFile(filePath) {
    const resolved = this._resolve(filePath);
    if (!resolved) return { error: "No project open or invalid path" };
    try {
      const content = fs.readFileSync(resolved, "utf-8");
      const language = this._detectLanguage(resolved);
      return { path: resolved, content, language };
    } catch (err) {
      return { error: err.message };
    }
  }

  async writeFile(filePath, content) {
    const resolved = this._resolve(filePath);
    if (!resolved) return { error: "No project open or invalid path" };
    try {
      const dir = path.dirname(resolved);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(resolved, content, "utf-8");
      return { path: resolved, written: true };
    } catch (err) {
      return { error: err.message };
    }
  }

  async listFiles(dirPath) {
    const resolved = dirPath ? this._resolve(dirPath) : this.projectRoot;
    if (!resolved) return { error: "No project open" };
    try {
      const entries = fs.readdirSync(resolved, { withFileTypes: true });
      return entries
        .filter((e) => !e.name.startsWith(".") || e.name === ".env.example")
        .map((e) => ({
          name: e.name,
          type: e.isDirectory() ? "directory" : "file",
          path: path.join(resolved, e.name),
        }));
    } catch (err) {
      return { error: err.message };
    }
  }

  async getTree(maxDepth = 4) {
    if (!this.projectRoot) return null;
    return this._buildTree(this.projectRoot, 0, maxDepth);
  }

  _buildTree(dir, depth, maxDepth) {
    if (depth >= maxDepth) return null;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      const children = [];

      for (const entry of entries) {
        if (entry.name.startsWith(".") && entry.name !== ".env.example") continue;
        if (entry.isDirectory()) {
          if (IGNORE_DIRS.has(entry.name)) continue;
          const subtree = this._buildTree(path.join(dir, entry.name), depth + 1, maxDepth);
          children.push({
            name: entry.name,
            type: "directory",
            path: path.join(dir, entry.name),
            children: subtree,
          });
        } else {
          const ext = path.extname(entry.name).toLowerCase();
          if (IGNORE_EXTENSIONS.has(ext)) continue;
          children.push({
            name: entry.name,
            type: "file",
            path: path.join(dir, entry.name),
            language: this._detectLanguage(entry.name),
          });
        }
      }

      return children.sort((a, b) => {
        if (a.type !== b.type) return a.type === "directory" ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
    } catch {
      return null;
    }
  }

  _resolve(filePath) {
    if (!this.projectRoot) return null;
    if (path.isAbsolute(filePath)) return filePath;
    return path.join(this.projectRoot, filePath);
  }

  _detectLanguage(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const map = {
      ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
      ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript",
      ".py": "python", ".pyw": "python",
      ".rs": "rust", ".go": "go", ".rb": "ruby",
      ".java": "java", ".kt": "kotlin", ".scala": "scala",
      ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp",
      ".cs": "csharp", ".swift": "swift", ".m": "objectivec",
      ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss",
      ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
      ".xml": "xml", ".svg": "xml",
      ".md": "markdown", ".txt": "plaintext",
      ".sh": "bash", ".bash": "bash", ".zsh": "bash",
      ".sql": "sql", ".graphql": "graphql",
      ".dockerfile": "dockerfile", ".proto": "protobuf",
      ".sol": "solidity", ".move": "move",
    };
    return map[ext] || "plaintext";
  }

  _detectProjectInfo(dirPath) {
    const info = { type: "unknown", languages: [], frameworks: [] };
    const files = fs.readdirSync(dirPath);

    if (files.includes("package.json")) {
      info.type = "node";
      info.languages.push("javascript");
      try {
        const pkg = JSON.parse(fs.readFileSync(path.join(dirPath, "package.json"), "utf-8"));
        const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
        if (allDeps.react) info.frameworks.push("react");
        if (allDeps.next) info.frameworks.push("next.js");
        if (allDeps.vue) info.frameworks.push("vue");
        if (allDeps.express) info.frameworks.push("express");
        if (allDeps.electron) info.frameworks.push("electron");
        if (allDeps.typescript || files.includes("tsconfig.json")) info.languages.push("typescript");
      } catch { /* ignore */ }
    }
    if (files.includes("requirements.txt") || files.includes("pyproject.toml") || files.includes("setup.py")) {
      info.type = info.type === "unknown" ? "python" : info.type;
      info.languages.push("python");
    }
    if (files.includes("Cargo.toml")) {
      info.type = "rust";
      info.languages.push("rust");
    }
    if (files.includes("go.mod")) {
      info.type = "go";
      info.languages.push("go");
    }

    return info;
  }
}

module.exports = { ProjectManager };
