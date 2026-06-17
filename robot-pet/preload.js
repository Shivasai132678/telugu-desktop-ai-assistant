/**
 * Preload script — bridges Electron main process and renderer
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onCommand: (callback) => ipcRenderer.on('command', (_event, cmd) => callback(cmd)),
    onSpeech: (callback) => ipcRenderer.on('speech', (_event, text) => callback(text)),
    onUserSpeech: (callback) => ipcRenderer.on('user-speech', (_event, text) => callback(text)),
    onThinkingStart: (callback) => ipcRenderer.on('thinking-start', () => callback()),
    onThinkingEnd: (callback) => ipcRenderer.on('thinking-end', () => callback()),
    onScreenInfo: (callback) => ipcRenderer.on('screen-info', (_event, info) => callback(info)),
    setIgnoreMouse: (ignore) => ipcRenderer.send('set-ignore-mouse', ignore),
});
