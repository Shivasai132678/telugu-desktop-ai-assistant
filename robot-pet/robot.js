/**
 * Robot Pet — 3D Avatar Drop-in Renderer
 * Replace the old robot.js with this file.
 *
 * Keeps the original renderer contract:
 * - Uses #robot, #robot-body, #speech-bubble, #speech-text when present.
 * - Supports click, Space/Enter, resize, and window.electronAPI commands.
 * - Supports modes: sleeping, walking, awake, dancing.
 *
 * The avatar/runtime are loaded from public URLs so you can try it by replacing
 * one JS file first. For an offline build, download the same URLs and override
 * window.ROBOT_AVATAR_CONFIG before this script runs.
 */

(function () {
    'use strict';

    // ===== DOM Refs =====
    const robotContainer = document.getElementById('robot');
    const robotBody = document.getElementById('robot-body');
    const speechBubble = document.getElementById('speech-bubble');
    const speechText = document.getElementById('speech-text');

    if (!robotContainer) {
        console.error('[Robot Avatar] Missing #robot container.');
        return;
    }

    // ===== Config =====
    const USER_CONFIG = window.ROBOT_AVATAR_CONFIG || {};
    const CONFIG = {
        width: USER_CONFIG.width || 180,
        height: USER_CONFIG.height || 250,
        walkSpeed: USER_CONFIG.walkSpeed || 1.5,
        edgePadding: USER_CONFIG.edgePadding || 30,
        idleChance: USER_CONFIG.idleChance || 0.001,
        idleDuration: USER_CONFIG.idleDuration || [1200, 2200],
        sleepDelay: USER_CONFIG.sleepDelay || 120000,
        speechDuration: USER_CONFIG.speechDuration || 3200,
        awakeDuration: USER_CONFIG.awakeDuration || 15000,
        danceDuration: USER_CONFIG.danceDuration || 8500,
        avatarScale: USER_CONFIG.avatarScale || 2.25,
        startupMode: USER_CONFIG.startupMode || 'walking',
        modelUrl: USER_CONFIG.modelUrl || 'https://threejs.org/examples/models/gltf/RobotExpressive/RobotExpressive.glb',
        threeUrl: USER_CONFIG.threeUrl || 'https://esm.sh/three@0.165.0',
        loaderUrl: USER_CONFIG.loaderUrl || 'https://esm.sh/three@0.165.0/examples/jsm/loaders/GLTFLoader.js',
    };

    // ===== State =====
    const state = {
        mode: 'sleeping',
        x: 0,
        direction: 1,
        screenWidth: window.innerWidth,
        leftBound: CONFIG.edgePadding,
        rightBound: Math.max(CONFIG.edgePadding, window.innerWidth - CONFIG.edgePadding - CONFIG.width),
        speechTimer: null,
        modeTimer: null,
        animFrame: null,
        renderFrame: null,
        lastIdleTime: Date.now(),
        lastInteractionTime: Date.now(),
        avatarReady: false,
        avatarFailed: false,
        activeClip: null,
        processBubble: null,
        processTimer: null,
        llmBubble: null,
        llmTimer: null,
        // Chat overlay
        chatVisible: false,
        chatMessages: [], // {role: 'user'|'bot', text: string}
        chatOverlay: null,
        chatMessagesEl: null,
        chatThinkingEl: null,
        chatAutoCloseTimer: null,
    };

    const SPEECH = {
        wakeUp: [
            "I'm awake.",
            "Ready.",
            "Hello there.",
            "Avatar online.",
        ],
        sleep: [
            "Rest mode.",
            "Standing by.",
            "Power save.",
        ],
        dance: [
            "Dance routine engaged.",
            "Beat detected.",
            "Servo groove.",
        ],
        idle: [
            "Idle mode.",
            "Click me.",
            "Standing by.",
        ],
        load: [
            "Loading avatar...",
            "Booting 3D shell...",
        ],
    };

    const avatar = {
        THREE: null,
        scene: null,
        camera: null,
        renderer: null,
        loader: null,
        clock: null,
        mixer: null,
        robot: null,
        actions: new Map(),
        faceLight: null,
        stage: null,
        spinner: null,
        yaw: -0.2,
    };

    function random(min, max) {
        return Math.random() * (max - min) + min;
    }

    function pick(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    // ===== DOM Setup =====
    function setupContainer() {
        robotContainer.style.width = CONFIG.width + 'px';
        robotContainer.style.height = CONFIG.height + 'px';
        robotContainer.style.pointerEvents = 'auto';
        robotContainer.style.overflow = 'visible';
        robotContainer.style.transformOrigin = '50% 100%';

        // Permanently hide old blue speech bubble — all text goes to orange chat overlay
        if (speechBubble) speechBubble.style.display = 'none';

        // Don't hide CSS robot yet — show it as a fallback until 3D loads successfully
        if (robotBody) {
            robotBody.style.display = '';
        }

        avatar.stage = document.createElement('div');
        avatar.stage.className = 'robot-avatar-stage';
        avatar.stage.setAttribute('aria-label', 'Animated robot avatar');
        avatar.stage.style.position = 'absolute';
        avatar.stage.style.left = '50%';
        avatar.stage.style.bottom = '0';
        avatar.stage.style.width = CONFIG.width + 'px';
        avatar.stage.style.height = CONFIG.height + 'px';
        avatar.stage.style.transform = 'translateX(-50%)';
        avatar.stage.style.pointerEvents = 'auto';
        avatar.stage.style.cursor = 'pointer';
        avatar.stage.style.zIndex = '2';
        avatar.stage.style.filter = 'drop-shadow(0 20px 24px rgba(0, 0, 0, 0.38))';
        robotContainer.appendChild(avatar.stage);

        avatar.spinner = document.createElement('div');
        avatar.spinner.textContent = '3D';
        avatar.spinner.style.position = 'absolute';
        avatar.spinner.style.left = '50%';
        avatar.spinner.style.top = '50%';
        avatar.spinner.style.width = '46px';
        avatar.spinner.style.height = '46px';
        avatar.spinner.style.display = 'grid';
        avatar.spinner.style.placeItems = 'center';
        avatar.spinner.style.transform = 'translate(-50%, -50%)';
        avatar.spinner.style.border = '1px solid rgba(90, 225, 255, 0.5)';
        avatar.spinner.style.borderRadius = '50%';
        avatar.spinner.style.background = 'rgba(8, 14, 22, 0.72)';
        avatar.spinner.style.color = '#8cecff';
        avatar.spinner.style.font = '700 12px/1 system-ui, sans-serif';
        avatar.spinner.style.boxShadow = '0 0 30px rgba(83, 218, 255, 0.28)';
        avatar.stage.appendChild(avatar.spinner);

        const style = document.createElement('style');
        style.textContent = `
            #robot .robot-avatar-stage canvas {
                display: block;
                width: 100% !important;
                height: 100% !important;
                pointer-events: auto;
            }

            #robot.facing-left .robot-avatar-stage {
                transform: translateX(-50%);
            }

            #robot.dancing .robot-avatar-stage {
                animation: robot-avatar-bop 520ms ease-in-out infinite alternate;
            }

            #robot.awake .robot-avatar-stage {
                animation: robot-avatar-wake 900ms ease-out 1;
            }

            @keyframes robot-avatar-bop {
                from { translate: 0 0; }
                to { translate: 0 -8px; }
            }

            @keyframes robot-avatar-wake {
                0% { scale: 0.96; }
                55% { scale: 1.04; }
                100% { scale: 1; }
            }
        `;
        document.head.appendChild(style);
        setupProcessBubble();
        setupLLMBubble();
    }

    function setupLLMBubble() {
        state.llmBubble = document.createElement('div');
        state.llmBubble.className = 'robot-llm-speech';
        state.llmBubble.setAttribute('role', 'status');
        state.llmBubble.setAttribute('aria-live', 'polite');

        // Tail triangle (CSS-drawn)
        const tail = document.createElement('div');
        tail.className = 'robot-llm-tail';
        state.llmBubble.appendChild(tail);

        // Text container
        const textNode = document.createElement('span');
        textNode.className = 'robot-llm-text';
        state.llmBubble.appendChild(textNode);

        // Inject styles once
        const llmStyle = document.createElement('style');
        llmStyle.textContent = `
            .robot-llm-speech {
                position: absolute;
                left: 50%;
                bottom: calc(100% + 14px);
                transform: translateX(-50%) translateY(8px);
                width: max-content;
                min-width: 170px;
                max-width: 290px;
                padding: 12px 15px 12px 15px;
                background: linear-gradient(135deg,
                    rgba(8, 16, 28, 0.97) 0%,
                    rgba(5, 18, 26, 0.97) 100%);
                border: 1.5px solid rgba(83, 218, 255, 0.6);
                border-radius: 14px;
                color: #dff6ff;
                font: 500 13.5px/1.5 system-ui, sans-serif;
                text-align: left;
                box-shadow:
                    0 0 0 1px rgba(83, 218, 255, 0.08),
                    0 10px 32px rgba(0, 0, 0, 0.5),
                    0 0 36px rgba(83, 218, 255, 0.22);
                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
                z-index: 6;
                pointer-events: none;
                opacity: 0;
                transition: opacity 220ms ease, transform 220ms ease;
                word-break: break-word;
            }
            .robot-llm-speech.visible {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
            .robot-llm-tail {
                position: absolute;
                bottom: -9px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 9px solid transparent;
                border-right: 9px solid transparent;
                border-top: 9px solid rgba(83, 218, 255, 0.6);
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
            }
            .robot-llm-tail::after {
                content: '';
                position: absolute;
                bottom: 2px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 7.5px solid transparent;
                border-right: 7.5px solid transparent;
                border-top: 7.5px solid rgba(5, 18, 26, 0.97);
            }
            .robot-llm-typing {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 2px 0;
            }
            .robot-llm-typing span {
                display: inline-block;
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: rgba(83, 218, 255, 0.75);
                animation: llm-blink 1.2s ease-in-out infinite;
            }
            .robot-llm-typing span:nth-child(2) { animation-delay: 0.2s; }
            .robot-llm-typing span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes llm-blink {
                0%, 80%, 100% { opacity: 0.2; transform: scaleY(0.7); }
                40% { opacity: 1; transform: scaleY(1.2); }
            }
        `;
        document.head.appendChild(llmStyle);
        robotContainer.appendChild(state.llmBubble);
    }

    // ===== Chat Overlay =====
    function setupChatOverlay() {
        // Create overlay container
        const overlay = document.createElement('div');
        overlay.className = 'chat-overlay';
        overlay.id = 'chat-overlay';

        // Header
        const header = document.createElement('div');
        header.className = 'chat-header';
        header.textContent = '💬 Conversation';
        overlay.appendChild(header);

        // Messages container
        const messages = document.createElement('div');
        messages.className = 'chat-messages';
        messages.id = 'chat-messages';
        overlay.appendChild(messages);

        // Thinking indicator
        const thinking = document.createElement('div');
        thinking.className = 'chat-thinking';
        thinking.id = 'chat-thinking';
        thinking.style.display = 'none';
        thinking.innerHTML = '<span></span><span></span><span></span>';
        overlay.appendChild(thinking);

        // Close hint
        const hint = document.createElement('div');
        hint.className = 'chat-hint';
        hint.textContent = 'Click robot to toggle';
        overlay.appendChild(hint);

        document.body.appendChild(overlay);
        state.chatOverlay = overlay;
        state.chatMessagesEl = messages;
        state.chatThinkingEl = thinking;

        // Position overlay to track robot
        positionChatOverlay();
    }

    function positionChatOverlay() {
        if (!state.chatOverlay || !robotContainer) return;
        const rect = robotContainer.getBoundingClientRect();
        // 3D model's head is ~120px down from container top (model is 1.2 units tall
        // centered in 250px canvas with camera looking at waist).
        // CSS fallback head is at container top (0px offset).
        // This puts the chat bottom right above the visible head.
        const headOffset = state.avatarReady ? 112 : 0;
        state.chatOverlay.style.left = (rect.left + rect.width / 2) + 'px';
        state.chatOverlay.style.bottom = (window.innerHeight - rect.top - headOffset + 4) + 'px';
    }

    function toggleChat() {
        if (state.chatVisible) {
            hideChat();
        } else {
            showChat();
        }
    }

    function showChat() {
        state.chatVisible = true;
        if (state.chatOverlay) {
            positionChatOverlay();
            state.chatOverlay.classList.add('visible');
        }
        renderChatMessages();
        resetChatAutoClose();
    }

    function hideChat() {
        state.chatVisible = false;
        if (state.chatOverlay) state.chatOverlay.classList.remove('visible');
        clearTimeout(state.chatAutoCloseTimer);
    }

    function addChatMessage(role, text) {
        // Don't add empty messages
        if (!text || !text.trim()) return;

        state.chatMessages.push({ role, text: text.trim() });
        // Keep last 30 messages
        if (state.chatMessages.length > 30) {
            state.chatMessages = state.chatMessages.slice(-30);
        }

        // Show chat automatically when new bot message arrives
        if (role === 'bot' && !state.chatVisible) {
            showChat();
        } else if (state.chatVisible) {
            renderChatMessages();
            resetChatAutoClose();
        }
    }

    function renderChatMessages() {
        if (!state.chatMessagesEl) return;
        state.chatMessagesEl.innerHTML = state.chatMessages.map(msg => {
            const label = msg.role === 'user' ? 'You' : 'Bot';
            // Escape HTML to prevent XSS
            const safeText = String(msg.text)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            return `<div class="chat-msg chat-msg--${msg.role}"><strong>${label}:</strong> ${safeText}</div>`;
        }).join('');
        state.chatMessagesEl.scrollTop = state.chatMessagesEl.scrollHeight;
    }

    function setChatThinking(show) {
        if (!state.chatThinkingEl) return;
        state.chatThinkingEl.style.display = show ? 'flex' : 'none';
        if (show && state.chatVisible) {
            resetChatAutoClose();
        }
    }

    function resetChatAutoClose() {
        clearTimeout(state.chatAutoCloseTimer);
        // Auto-close after 12 seconds of no new messages
        state.chatAutoCloseTimer = setTimeout(() => {
            hideChat();
        }, 12000);
    }

    function showChatThinking() {
        setChatThinking(true);
    }

    function hideChatThinking() {
        setChatThinking(false);
    }

    function showLLMSpeech(text, duration) {
        if (!state.llmBubble) return;
        clearTimeout(state.llmTimer);

        // Remove any typing indicator
        const typing = state.llmBubble.querySelector('.robot-llm-typing');
        if (typing) typing.remove();

        const textNode = state.llmBubble.querySelector('.robot-llm-text');
        if (textNode) textNode.textContent = text;

        state.llmBubble.classList.add('visible');

        if (duration && duration > 0) {
            state.llmTimer = setTimeout(() => hideLLMSpeech(), duration);
        }
    }

    function showLLMThinking() {
        if (!state.llmBubble) return;
        clearTimeout(state.llmTimer);

        const textNode = state.llmBubble.querySelector('.robot-llm-text');
        if (textNode) textNode.textContent = '';

        if (!state.llmBubble.querySelector('.robot-llm-typing')) {
            const typing = document.createElement('span');
            typing.className = 'robot-llm-typing';
            typing.innerHTML = '<span></span><span></span><span></span>';
            state.llmBubble.appendChild(typing);
        }

        state.llmBubble.classList.add('visible');
    }

    function hideLLMSpeech() {
        clearTimeout(state.llmTimer);
        if (!state.llmBubble) return;
        state.llmBubble.classList.remove('visible');
    }

    function setupProcessBubble() {
        state.processBubble = document.createElement('div');
        state.processBubble.className = 'robot-process-popup';
        state.processBubble.setAttribute('role', 'status');
        state.processBubble.style.position = 'absolute';
        state.processBubble.style.left = '50%';
        state.processBubble.style.bottom = (CONFIG.height - 8) + 'px';
        state.processBubble.style.width = 'max-content';
        state.processBubble.style.minWidth = '150px';
        state.processBubble.style.maxWidth = '260px';
        state.processBubble.style.padding = '10px 12px';
        state.processBubble.style.border = '1px solid rgba(90, 225, 255, 0.42)';
        state.processBubble.style.borderRadius = '10px';
        state.processBubble.style.background = 'rgba(8, 14, 22, 0.9)';
        state.processBubble.style.color = '#eefaff';
        state.processBubble.style.font = '650 13px/1.35 system-ui, sans-serif';
        state.processBubble.style.textAlign = 'center';
        state.processBubble.style.boxShadow = '0 18px 50px rgba(0, 0, 0, 0.34), 0 0 24px rgba(83, 218, 255, 0.14)';
        state.processBubble.style.backdropFilter = 'blur(14px)';
        state.processBubble.style.zIndex = '5';
        state.processBubble.style.opacity = '0';
        state.processBubble.style.transform = 'translate(-50%, 8px)';
        state.processBubble.style.transition = 'opacity 180ms ease, transform 180ms ease';
        state.processBubble.style.pointerEvents = 'none';
        robotContainer.appendChild(state.processBubble);
    }

    function showProcess(text, options = {}) {
        if (!state.processBubble) return;

        clearTimeout(state.processTimer);
        state.processBubble.textContent = text;
        state.processBubble.style.opacity = '1';
        state.processBubble.style.transform = 'translate(-50%, 0)';

        if (options.duration !== 0) {
            state.processTimer = setTimeout(() => {
                hideProcess();
            }, options.duration || CONFIG.speechDuration);
        }
    }

    function hideProcess() {
        clearTimeout(state.processTimer);
        if (!state.processBubble) return;
        state.processBubble.style.opacity = '0';
        state.processBubble.style.transform = 'translate(-50%, 8px)';
    }

    function exposePublicApi() {
        window.robotPet = {
            say(text, duration = CONFIG.speechDuration) {
                state.lastInteractionTime = Date.now();
                // Route all speech to orange chat overlay only
                addChatMessage('bot', String(text));
            },
            setStatus(text, options = {}) {
                state.lastInteractionTime = Date.now();
                addChatMessage('bot', String(text));
            },
            setThinking(text = 'Thinking...') {
                state.lastInteractionTime = Date.now();
                // Show thinking dots in chat overlay
                showChatThinking();
                if (state.mode === 'sleeping') setMode('awake');
            },
            clearStatus: hideChatThinking,
            setMode,
            wake() {
                setMode('awake');
            },
            sleep() {
                setMode('sleeping');
            },
            // LLM speech — routed to chat overlay only
            llmSay(text, duration = 0) {
                state.lastInteractionTime = Date.now();
                if (state.mode === 'sleeping') setMode('awake');
                addChatMessage('bot', String(text));
            },
            llmThinking() {
                state.lastInteractionTime = Date.now();
                if (state.mode === 'sleeping') setMode('awake');
                showChatThinking();
            },
            llmDone() {
                hideChatThinking();
            },
            llmHide: hideChatThinking,
        };
        window.robotAvatar = window.robotPet;
    }

    // ===== Position Robot =====
    function positionRobot() {
        robotContainer.style.left = state.x + 'px';
        robotContainer.style.transform = 'none';

        if (state.direction === -1) {
            robotContainer.classList.add('facing-left');
        } else {
            robotContainer.classList.remove('facing-left');
        }

        if (state.chatVisible) {
            positionChatOverlay();
        }
    }

    // ===== Speech Bubble =====
    function showSpeech(text, duration = CONFIG.speechDuration) {
        clearTimeout(state.speechTimer);
        showProcess(text, { duration });

        if (speechText && speechBubble) {
            speechText.textContent = text;
            speechBubble.classList.add('visible');
            state.speechTimer = setTimeout(() => {
                speechBubble.classList.remove('visible');
            }, duration);
            return;
        }

        // Fallback bubble if the host page omitted the old speech DOM.
        let bubble = robotContainer.querySelector('.robot-avatar-speech');
        if (!bubble) {
            bubble = document.createElement('div');
            bubble.className = 'robot-avatar-speech';
            bubble.style.position = 'absolute';
            bubble.style.left = '50%';
            bubble.style.bottom = (CONFIG.height - 22) + 'px';
            bubble.style.transform = 'translateX(-50%)';
            bubble.style.minWidth = '130px';
            bubble.style.maxWidth = '230px';
            bubble.style.padding = '10px 12px';
            bubble.style.border = '1px solid rgba(90, 225, 255, 0.34)';
            bubble.style.borderRadius = '10px';
            bubble.style.background = 'rgba(8, 14, 22, 0.82)';
            bubble.style.color = '#eefaff';
            bubble.style.font = '650 13px/1.3 system-ui, sans-serif';
            bubble.style.textAlign = 'center';
            bubble.style.boxShadow = '0 18px 45px rgba(0, 0, 0, 0.28)';
            bubble.style.zIndex = '4';
            robotContainer.appendChild(bubble);
        }

        bubble.textContent = text;
        bubble.style.opacity = '1';
        state.speechTimer = setTimeout(() => {
            bubble.style.opacity = '0';
        }, duration);
    }

    function hideSpeech() {
        clearTimeout(state.speechTimer);
        if (speechBubble) speechBubble.classList.remove('visible');
        const bubble = robotContainer.querySelector('.robot-avatar-speech');
        if (bubble) bubble.style.opacity = '0';
    }

    // ===== Three.js Avatar =====
    async function loadAvatar() {

        try {
            const [THREE, loaderModule] = await Promise.all([
                import(CONFIG.threeUrl),
                import(CONFIG.loaderUrl),
            ]);

            avatar.THREE = THREE;
            avatar.loader = new loaderModule.GLTFLoader();
            avatar.clock = new THREE.Clock();

            avatar.scene = new THREE.Scene();
            avatar.scene.fog = new THREE.Fog(0x000000, 4.5, 9);

            avatar.camera = new THREE.PerspectiveCamera(36, CONFIG.width / CONFIG.height, 0.1, 40);
            avatar.camera.position.set(0, 1.08, 5.6);
            avatar.camera.lookAt(0, 0.58, 0);

            avatar.renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance',
            });
            avatar.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            avatar.renderer.setSize(CONFIG.width, CONFIG.height, false);
            avatar.renderer.outputColorSpace = THREE.SRGBColorSpace;
            avatar.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            avatar.renderer.toneMappingExposure = 1.15;
            avatar.renderer.shadowMap.enabled = true;
            avatar.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            avatar.stage.appendChild(avatar.renderer.domElement);

            addLights();
            addFloor();
            await loadModel();

            if (avatar.spinner) avatar.spinner.remove();
            state.avatarReady = true;
            // 3D loaded — hide CSS fallback robot body
            if (robotBody) robotBody.style.display = 'none';
            setMode(CONFIG.startupMode);
            renderAvatar();
        } catch (err) {
            state.avatarFailed = true;
            // 3D failed — show CSS fallback robot body
            if (robotBody) robotBody.style.display = '';
            if (avatar.spinner) avatar.spinner.textContent = '!';
            console.error('[Robot Avatar] Failed to load avatar runtime/model:', err);
        }
    }

    function addLights() {
        const THREE = avatar.THREE;

        const hemi = new THREE.HemisphereLight(0xdff7ff, 0x11141c, 1.55);
        avatar.scene.add(hemi);

        const key = new THREE.DirectionalLight(0xffffff, 2.6);
        key.position.set(3.2, 4.8, 4.2);
        key.castShadow = true;
        key.shadow.mapSize.set(1024, 1024);
        avatar.scene.add(key);

        const rim = new THREE.PointLight(0x52ddff, 4.8, 6);
        rim.position.set(-2.4, 2.3, 2.1);
        avatar.scene.add(rim);

        const warm = new THREE.PointLight(0xffc45c, 2.3, 6);
        warm.position.set(2.6, 1.1, 2.3);
        avatar.scene.add(warm);

        avatar.faceLight = new THREE.PointLight(0x7eeaff, 2.4, 2.6);
        avatar.faceLight.position.set(0, 1.35, 1.2);
        avatar.scene.add(avatar.faceLight);
    }

    function addFloor() {
        const THREE = avatar.THREE;

        const floor = new THREE.Mesh(
            new THREE.CircleGeometry(1.45, 64),
            new THREE.MeshStandardMaterial({
                color: 0x0d151f,
                roughness: 0.75,
                metalness: 0.08,
                transparent: true,
                opacity: 0.56,
            })
        );
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -1.02;
        floor.receiveShadow = true;
        avatar.scene.add(floor);

        const halo = new THREE.Mesh(
            new THREE.RingGeometry(0.78, 0.84, 64),
            new THREE.MeshBasicMaterial({
                color: 0x5be2ff,
                transparent: true,
                opacity: 0.34,
                side: THREE.DoubleSide,
            })
        );
        halo.rotation.x = -Math.PI / 2;
        halo.position.y = -1.01;
        avatar.scene.add(halo);
    }

    function loadModel() {
        return new Promise((resolve, reject) => {
            avatar.loader.load(
                CONFIG.modelUrl,
                (gltf) => {
                    fitRobot(gltf);
                    resolve();
                },
                undefined,
                reject
            );
        });
    }

    function fitRobot(gltf) {
        const THREE = avatar.THREE;
        avatar.robot = gltf.scene;

        const box = new THREE.Box3().setFromObject(avatar.robot);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const scale = CONFIG.avatarScale / Math.max(size.x, size.y, size.z);

        avatar.robot.scale.setScalar(scale);
        avatar.robot.position.set(
            -center.x * scale,
            -1.02 - box.min.y * scale,
            -center.z * scale
        );
        avatar.yaw = -0.2;
        avatar.robot.rotation.y = avatar.yaw;

        avatar.robot.traverse((object) => {
            if (!object.isMesh) return;
            object.castShadow = true;
            object.receiveShadow = true;
            if (object.material) {
                object.material.envMapIntensity = 1.1;
                object.material.needsUpdate = true;
            }
        });

        avatar.scene.add(avatar.robot);
        avatar.mixer = new THREE.AnimationMixer(avatar.robot);
        gltf.animations.forEach((clip) => {
            avatar.actions.set(clip.name, avatar.mixer.clipAction(clip));
        });
    }

    function playClip(name, fade = 0.24) {
        if (!state.avatarReady || !avatar.actions.has(name)) return;

        const THREE = avatar.THREE;
        const next = avatar.actions.get(name);
        const current = state.activeClip ? avatar.actions.get(state.activeClip) : null;

        next.enabled = true;
        next.reset();
        next.setEffectiveTimeScale(1);
        next.setEffectiveWeight(1);

        if (current && current !== next) {
            next.crossFadeFrom(current, fade, false);
        }

        next.loop = THREE.LoopRepeat;
        next.clampWhenFinished = false;
        next.play();
        state.activeClip = name;
    }

    function playOneShot(name) {
        if (!state.avatarReady || !avatar.actions.has(name)) return;

        const THREE = avatar.THREE;
        const action = avatar.actions.get(name);
        action.loop = THREE.LoopOnce;
        action.clampWhenFinished = true;
        playClip(name, 0.16);

        const onFinish = (event) => {
            if (event.action !== action) return;
            avatar.mixer.removeEventListener('finished', onFinish);
            action.loop = THREE.LoopRepeat;
            if (state.mode === 'awake') playClip('Idle');
            if (state.mode === 'walking') playClip('Walking');
            if (state.mode === 'dancing') playClip('Dance');
            if (state.mode === 'sleeping') playClip('Sitting');
        };

        avatar.mixer.addEventListener('finished', onFinish);
    }

    function renderAvatar() {
        const THREE = avatar.THREE;
        const delta = avatar.clock.getDelta();
        const elapsed = avatar.clock.elapsedTime;

        if (avatar.mixer) avatar.mixer.update(delta);
        if (avatar.robot) {
            const frontYaw = -0.2;
            const walkingYaw = state.direction === 1 ? Math.PI / 2 : -Math.PI / 2;
            const targetYaw = state.mode === 'walking' ? walkingYaw : frontYaw;
            const turnSpeed = state.mode === 'walking' ? 0.34 : 0.07;
            const idleSway = state.mode === 'walking' ? 0 : Math.sin(elapsed * 0.65) * 0.045;
            const danceTurn = state.mode === 'dancing' ? Math.sin(elapsed * 2.2) * 0.12 : 0;

            avatar.yaw += (targetYaw - avatar.yaw) * turnSpeed;
            avatar.robot.rotation.y = avatar.yaw + idleSway + danceTurn;
        }
        if (avatar.faceLight) {
            avatar.faceLight.intensity = 2.25 + Math.sin(elapsed * 2.6) * 0.35;
        }

        avatar.renderer.render(avatar.scene, avatar.camera);
        state.renderFrame = requestAnimationFrame(renderAvatar);
    }

    function updateAvatarCamera() {
        if (!avatar.camera || !avatar.renderer) return;
        avatar.camera.aspect = CONFIG.width / CONFIG.height;
        avatar.camera.updateProjectionMatrix();
        avatar.renderer.setSize(CONFIG.width, CONFIG.height, false);
    }

    // ===== Mode Transitions =====
    function setMode(newMode) {
        clearTimeout(state.modeTimer);
        state.mode = newMode;

        robotContainer.classList.remove('walking', 'sleeping', 'awake', 'dancing', 'idle');
        robotContainer.classList.add(newMode === 'idle' ? 'walking' : newMode);

        switch (newMode) {
            case 'walking':
                state.lastIdleTime = Date.now();
                playClip('Walking');
                hideSpeech();
                // Auto-close chat when robot starts walking
                if (state.chatVisible) hideChat();
                break;

            case 'idle': {
                playClip('Idle');
                const idleDur = random(CONFIG.idleDuration[0], CONFIG.idleDuration[1]);
                state.modeTimer = setTimeout(() => {
                    if (state.mode === 'idle') setMode('walking');
                }, idleDur);
                break;
            }

            case 'sleeping':
                playClip(avatar.actions.has('Sitting') ? 'Sitting' : 'Idle');
                break;

            case 'awake':
                playClip('Idle');
                if (avatar.actions.has('Wave')) {
                    setTimeout(() => {
                        if (state.mode === 'awake') playOneShot('Wave');
                    }, 160);
                }
                state.modeTimer = setTimeout(() => {
                    if (state.mode === 'awake') setMode('walking');
                }, CONFIG.awakeDuration);
                break;

            case 'dancing':
                playClip('Dance');
                state.modeTimer = setTimeout(() => {
                    if (state.mode === 'dancing') setMode('walking');
                }, CONFIG.danceDuration);
                break;
        }
    }

    // ===== Main Animation Loop =====
    function update() {
        if (state.mode === 'walking') {
            state.x += CONFIG.walkSpeed * state.direction;

            if (state.x >= state.rightBound) {
                state.x = state.rightBound;
                state.direction = -1;
            } else if (state.x <= state.leftBound) {
                state.x = state.leftBound;
                state.direction = 1;
            }

            positionRobot();

            // Only go idle if robot has been walking for at least 20 seconds
            // Prevents rapid flickering between Walking and Idle animations
            if (Math.random() < CONFIG.idleChance && Date.now() - state.lastIdleTime > 20000) {
                setMode('idle');
            }

            if (Date.now() - state.lastInteractionTime > CONFIG.sleepDelay) {
                setMode('sleeping');
            }
        } else {
            positionRobot();
        }

        state.animFrame = requestAnimationFrame(update);
    }

    // ===== Event Handlers =====
    function handleRobotClick() {
        state.lastInteractionTime = Date.now();

        if (state.mode === 'walking') {
            // Walking → stop and show chat
            setMode('awake');
            showChat();
        } else if (state.chatVisible) {
            // Chat visible → close it and start walking
            hideChat();
            setMode('walking');
        } else if (state.mode === 'sleeping') {
            // Sleeping → wake up
            setMode('awake');
        } else {
            // Awake/idle with no chat → start walking
            setMode('walking');
        }
    }

    function handleKeyDown(e) {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            state.lastInteractionTime = Date.now();
            if (state.mode === 'sleeping') {
                setMode('awake');
            } else if (state.mode === 'awake') {
                setMode('dancing');
            } else if (state.mode === 'dancing') {
                setMode('walking');
            } else {
                setMode('awake');
            }
        }
    }

    function handleResize() {
        state.screenWidth = window.innerWidth;
        state.rightBound = Math.max(CONFIG.edgePadding, state.screenWidth - CONFIG.edgePadding - CONFIG.width);
        state.x = Math.max(state.leftBound, Math.min(state.x, state.rightBound));
        updateAvatarCamera();
        positionRobot();
    }

    // ===== Mouse pass-through for transparent Electron windows =====
    function setupMousePassthrough() {
        if (window.electronAPI) {
            document.addEventListener('mousemove', (e) => {
                const el = document.elementFromPoint(e.clientX, e.clientY);
                const isOnRobot = robotContainer.contains(el);
                const isOnBubble = speechBubble && speechBubble.contains(el);
                const isOnLLMBubble = state.llmBubble && state.llmBubble.contains(el);
                const isOnChat = state.chatOverlay && state.chatOverlay.contains(el);
                window.electronAPI.setIgnoreMouse(!isOnRobot && !isOnBubble && !isOnLLMBubble && !isOnChat);
            });
        }
    }

    // ===== Listen for Electron IPC commands =====
    function setupElectronBridge() {
        if (window.electronAPI) {
            window.electronAPI.onCommand((cmd) => {
                state.lastInteractionTime = Date.now();
                setMode(cmd);
            });

            // LLM speech → show in chat overlay only (no persistent head bubble)
            window.electronAPI.onSpeech((text) => {
                state.lastInteractionTime = Date.now();
                if (state.mode === 'sleeping') {
                    setMode('awake');
                }
                hideChatThinking();
                addChatMessage('bot', text);
            });

            // User speech → chat overlay
            if (typeof window.electronAPI.onUserSpeech === 'function') {
                window.electronAPI.onUserSpeech((text) => {
                    addChatMessage('user', text);
                });
            }

            // Optional: show typing dots while LLM is thinking / streaming
            if (typeof window.electronAPI.onLLMStart === 'function') {
                window.electronAPI.onLLMStart(() => {
                    state.lastInteractionTime = Date.now();
                    if (state.mode === 'sleeping') setMode('awake');
                    showChatThinking();
                });
            }

            // Dismiss thinking when LLM done
            if (typeof window.electronAPI.onLLMEnd === 'function') {
                window.electronAPI.onLLMEnd(() => {
                    hideChatThinking();
                });
            }

            // Thinking-start/end via dedicated IPC channels (HTTP /thinking-start and /thinking-end)
            if (typeof window.electronAPI.onThinkingStart === 'function') {
                window.electronAPI.onThinkingStart(() => {
                    state.lastInteractionTime = Date.now();
                    if (state.mode === 'sleeping') setMode('awake');
                    showChatThinking();
                });
            }

            if (typeof window.electronAPI.onThinkingEnd === 'function') {
                window.electronAPI.onThinkingEnd(() => {
                    hideChatThinking();
                });
            }

            window.electronAPI.onScreenInfo((info) => {
                state.screenWidth = info.width;
                state.rightBound = Math.max(CONFIG.edgePadding, info.width - CONFIG.edgePadding - CONFIG.width);
                state.x = Math.max(state.leftBound, Math.min(state.x, state.rightBound));
                positionRobot();
            });
        }
    }

    // ===== Init =====
    function init() {
        setupContainer();
        setupChatOverlay();
        exposePublicApi();
        state.rightBound = Math.max(CONFIG.edgePadding, window.innerWidth - CONFIG.edgePadding - CONFIG.width);
        state.x = (state.leftBound + state.rightBound) / 2;
        state.direction = 1;
        positionRobot();

        robotContainer.addEventListener('click', handleRobotClick);
        document.addEventListener('keydown', handleKeyDown);
        window.addEventListener('resize', handleResize);

        setupElectronBridge();
        setupMousePassthrough();
        loadAvatar();
        update();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
