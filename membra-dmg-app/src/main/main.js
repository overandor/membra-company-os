const { app, BrowserWindow, ipcMain, Menu, dialog } = require("electron");
const path = require("path");
const { LLMBridge } = require("./llm-bridge");
const { ProjectManager } = require("./project-manager");
const { AgentOrchestrator } = require("./agent-orchestrator");

let mainWindow;
let llmBridge;
let projectManager;
let agentOrchestrator;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: "#0d0d0d",
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "..", "renderer", "index.html"));

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function buildMenu() {
  const template = [
    {
      label: "MEMBRA",
      submenu: [
        { label: "About MEMBRA LLM Developer", role: "about" },
        { type: "separator" },
        { label: "Settings...", accelerator: "CmdOrCtrl+,", click: () => mainWindow.webContents.send("navigate", "settings") },
        { type: "separator" },
        { label: "Quit", accelerator: "CmdOrCtrl+Q", role: "quit" },
      ],
    },
    {
      label: "File",
      submenu: [
        { label: "New Project", accelerator: "CmdOrCtrl+N", click: () => mainWindow.webContents.send("action", "new-project") },
        { label: "Open Project...", accelerator: "CmdOrCtrl+O", click: handleOpenProject },
        { type: "separator" },
        { label: "Save", accelerator: "CmdOrCtrl+S", click: () => mainWindow.webContents.send("action", "save") },
      ],
    },
    {
      label: "LLM",
      submenu: [
        { label: "New Chat", accelerator: "CmdOrCtrl+T", click: () => mainWindow.webContents.send("action", "new-chat") },
        { label: "Generate Code", accelerator: "CmdOrCtrl+G", click: () => mainWindow.webContents.send("action", "generate-code") },
        { label: "Review Code", accelerator: "CmdOrCtrl+R", click: () => mainWindow.webContents.send("action", "review-code") },
        { type: "separator" },
        { label: "Run Agent Pipeline", accelerator: "CmdOrCtrl+Shift+A", click: () => mainWindow.webContents.send("action", "run-agents") },
      ],
    },
    {
      label: "View",
      submenu: [
        { label: "Toggle Sidebar", accelerator: "CmdOrCtrl+B", click: () => mainWindow.webContents.send("action", "toggle-sidebar") },
        { type: "separator" },
        { role: "toggleDevTools" },
        { role: "togglefullscreen" },
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function handleOpenProject() {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openDirectory"],
    title: "Open Project Directory",
  });
  if (!result.canceled && result.filePaths.length > 0) {
    mainWindow.webContents.send("project-opened", result.filePaths[0]);
  }
}

app.whenReady().then(() => {
  llmBridge = new LLMBridge();
  projectManager = new ProjectManager();
  agentOrchestrator = new AgentOrchestrator(llmBridge, projectManager);

  createWindow();
  buildMenu();

  registerIpcHandlers();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

function registerIpcHandlers() {
  ipcMain.handle("llm:chat", async (_event, messages, options) => {
    return llmBridge.chat(messages, options);
  });

  ipcMain.handle("llm:generate-code", async (_event, prompt, language, context) => {
    return llmBridge.generateCode(prompt, language, context);
  });

  ipcMain.handle("llm:review-code", async (_event, code, language) => {
    return llmBridge.reviewCode(code, language);
  });

  ipcMain.handle("llm:explain-code", async (_event, code, language) => {
    return llmBridge.explainCode(code, language);
  });

  ipcMain.handle("llm:refactor-code", async (_event, code, language, instructions) => {
    return llmBridge.refactorCode(code, language, instructions);
  });

  ipcMain.handle("llm:debug-code", async (_event, code, error, language) => {
    return llmBridge.debugCode(code, error, language);
  });

  ipcMain.handle("llm:get-config", async () => {
    return llmBridge.getConfig();
  });

  ipcMain.handle("llm:set-config", async (_event, config) => {
    llmBridge.setConfig(config);
    return { ok: true };
  });

  ipcMain.handle("project:open", async (_event, dirPath) => {
    return projectManager.openProject(dirPath);
  });

  ipcMain.handle("project:read-file", async (_event, filePath) => {
    return projectManager.readFile(filePath);
  });

  ipcMain.handle("project:write-file", async (_event, filePath, content) => {
    return projectManager.writeFile(filePath, content);
  });

  ipcMain.handle("project:list-files", async (_event, dirPath) => {
    return projectManager.listFiles(dirPath);
  });

  ipcMain.handle("project:get-tree", async () => {
    return projectManager.getTree();
  });

  ipcMain.handle("agents:run-pipeline", async (_event, task, agentList) => {
    return agentOrchestrator.runPipeline(task, agentList);
  });

  ipcMain.handle("agents:get-status", async () => {
    return agentOrchestrator.getStatus();
  });

  ipcMain.handle("agents:list", async () => {
    return agentOrchestrator.listAgents();
  });
}
