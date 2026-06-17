/**
 * Robot Pet — Electron Main Process
 * Creates a transparent, frameless, always-on-top desktop pet window
 * that sits at the bottom of the screen near the macOS dock.
 * Also runs a local HTTP server on port 8766 to receive commands from python modules.
 */

const { app, BrowserWindow, Tray, Menu, screen, nativeImage, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const url = require('url');

let mainWindow = null;
let tray = null;
let server = null;

function createWindow() {
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().bounds;
    const windowHeight = 400; // Tall enough for robot (250px) + chat overlay above

    // Create a transparent frameless window spanning the bottom of the screen
    mainWindow = new BrowserWindow({
        width: screenWidth,
        height: windowHeight,
        x: 0,
        y: Math.max(0, screenHeight - windowHeight - 10), // Sits just above the dock
        transparent: true,
        frame: false,
        hasShadow: false,
        alwaysOnTop: true,
        skipTaskbar: true,
        resizable: false,
        movable: false,
        focusable: false, // Don't steal focus from other apps
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    // Make clicks pass through transparent areas
    mainWindow.setIgnoreMouseEvents(false);

    // Load the HTML
    mainWindow.loadFile('index.html');

    // macOS: Hide dock icon since this is a background widget
    if (process.platform === 'darwin') {
        app.dock.hide();
    }

    // Send screen dimensions to renderer
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.send('screen-info', {
            width: screenWidth,
            height: screenHeight,
            windowHeight: windowHeight,
        });
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function createTray() {
    // Create a simple tray icon (16x16 colored circle)
    const icon = nativeImage.createFromDataURL(
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA' +
        'mElEQVQ4T2NkoBAwUqifYdAY8B8E/v//z4AGGBkZGRkY/v9nQJJgQFcDt4EB3SUMDAwM' +
        'yC5BdgEDsjuRXYLsAgZkGxhQXIBsA4pNDMguwOYFBmwuYMDmBYZ///4xoHsBPhoZkJ2C' +
        '7AUGbF5gwOYCBmxeYMDmBQZsXmDA5gUGdC8wEBULDNhigeE/AwMDNi8wYPMCAwDHCHER' +
        'jE/IGQAAAABJRU5ErkJggg=='
    );
    
    tray = new Tray(icon.resize({ width: 16, height: 16 }));
    tray.setToolTip('Robot Pet');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: '🤖 Wake Up',
            click: () => {
                if (mainWindow) {
                    mainWindow.webContents.send('command', 'awake');
                    mainWindow.show();
                }
            },
        },
        {
            label: '💤 Sleep',
            click: () => {
                if (mainWindow) {
                    mainWindow.webContents.send('command', 'sleeping');
                }
            },
        },
        {
            label: '💃 Dance',
            click: () => {
                if (mainWindow) {
                    mainWindow.webContents.send('command', 'dancing');
                }
            },
        },
        { type: 'separator' },
        {
            label: '👋 Quit Robot Pet',
            click: () => {
                app.quit();
            },
        },
    ]);

    tray.setContextMenu(contextMenu);
    
    tray.on('click', () => {
        if (mainWindow) {
            mainWindow.webContents.send('command', 'awake');
            mainWindow.show();
        }
    });
}

// Start a local HTTP server to receive wake/sleep/speak events from Python
function startHttpServer() {
    server = http.createServer((req, res) => {
        const parsedUrl = url.parse(req.url, true);
        const pathname = parsedUrl.pathname;
        const query = parsedUrl.query;

        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', 'application/json');

        if (mainWindow) {
            if (pathname === '/state') {
                const mode = query.mode || 'awake';
                mainWindow.webContents.send('command', mode);
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'ok', mode: mode }));
                return;
            } 
            
            if (pathname === '/speech') {
                const text = query.text || '';
                mainWindow.webContents.send('speech', text);
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'ok', text: text }));
                return;
            }

            if (pathname === '/user-speech') {
                const text = query.text || '';
                mainWindow.webContents.send('user-speech', text);
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'ok', text: text }));
                return;
            }

            if (pathname === '/thinking-start') {
                mainWindow.webContents.send('thinking-start');
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'ok', thinking: true }));
                return;
            }

            if (pathname === '/thinking-end') {
                mainWindow.webContents.send('thinking-end');
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'ok', thinking: false }));
                return;
            }
        }

        res.writeHead(404);
        res.end(JSON.stringify({ error: 'Not Found' }));
    });

    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            console.warn('Port 8766 already in use — HTTP event server skipped (another instance running?)');
        } else {
            console.error('HTTP server error:', err.message);
        }
    });

    server.listen(8766, '127.0.0.1', () => {
        console.log('Electron HTTP event server listening on http://127.0.0.1:8766');
    });
}

// Handle click-through toggling from renderer
ipcMain.on('set-ignore-mouse', (_event, ignore) => {
    if (mainWindow) {
        mainWindow.setIgnoreMouseEvents(ignore, { forward: true });
    }
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    createTray();
    startHttpServer();
});

app.on('window-all-closed', () => {
    if (server) server.close();
    app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
