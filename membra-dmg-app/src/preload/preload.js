const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("membraAPI", {
  llm: {
    chat: (messages, options) => ipcRenderer.invoke("llm:chat", messages, options),
    generateCode: (prompt, language, context) => ipcRenderer.invoke("llm:generate-code", prompt, language, context),
    reviewCode: (code, language) => ipcRenderer.invoke("llm:review-code", code, language),
    explainCode: (code, language) => ipcRenderer.invoke("llm:explain-code", code, language),
    refactorCode: (code, language, instructions) => ipcRenderer.invoke("llm:refactor-code", code, language, instructions),
    debugCode: (code, error, language) => ipcRenderer.invoke("llm:debug-code", code, error, language),
    getConfig: () => ipcRenderer.invoke("llm:get-config"),
    setConfig: (config) => ipcRenderer.invoke("llm:set-config", config),
  },

  project: {
    open: (dirPath) => ipcRenderer.invoke("project:open", dirPath),
    readFile: (filePath) => ipcRenderer.invoke("project:read-file", filePath),
    writeFile: (filePath, content) => ipcRenderer.invoke("project:write-file", filePath, content),
    listFiles: (dirPath) => ipcRenderer.invoke("project:list-files", dirPath),
    getTree: () => ipcRenderer.invoke("project:get-tree"),
  },

  agents: {
    runPipeline: (task, agentList) => ipcRenderer.invoke("agents:run-pipeline", task, agentList),
    getStatus: () => ipcRenderer.invoke("agents:get-status"),
    list: () => ipcRenderer.invoke("agents:list"),
  },

  on: (channel, callback) => {
    const validChannels = ["navigate", "action", "project-opened"];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => callback(...args));
    }
  },
});
