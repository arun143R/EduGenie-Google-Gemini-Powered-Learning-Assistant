/**
 * EduGenie - Premium AI Workspace Dynamic Scripting Engine
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Theme Switcher Engine
    initThemeEngine();

    // 2. Initialize Mobile Navigation Drawer
    initMobileNav();

    // 3. Initialize Dashboard Tab Management
    initTabManager();

    // 4. Initialize Auto-Expanding Textareas & Keyboard Shortcuts
    initFormInteractions();

    // 5. Initialize API Form Workspaces
    initWorkspaceForms();

    // 5b. Initialize Authentication Forms
    initAuthForms();

    // 6. Load Activity Logs Sidebar
    loadSidebarHistory();
});

/**
 * Handcrafted Theme Switcher Engine (Light / Dark / System Auto)
 */
function initThemeEngine() {
    const themeButtons = document.querySelectorAll(".theme-btn");

    function getSystemTheme() {
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function applyTheme(themeVal) {
        let targetTheme = themeVal;
        if (themeVal === "auto") {
            targetTheme = getSystemTheme();
        }
        document.documentElement.setAttribute("data-theme", targetTheme);

        // Highlight active button
        themeButtons.forEach(btn => {
            if (btn.getAttribute("data-theme-val") === themeVal) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
    }

    // Set default on load
    const savedTheme = localStorage.getItem("theme") || "light";
    applyTheme(savedTheme);

    // Bind event listeners
    themeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const val = btn.getAttribute("data-theme-val");
            localStorage.setItem("theme", val);
            applyTheme(val);
        });
    });

    // Listen to system changes if auto is active
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (localStorage.getItem("theme") === "auto") {
            applyTheme("auto");
        }
    });
}

/**
 * Collapsible mobile nav drawer
 */
function initMobileNav() {
    const toggleBtn = document.getElementById("mobileNavToggle");
    const sidebar = document.getElementById("sidebar");

    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebar.classList.toggle("mobile-open");
    });

    document.addEventListener("click", (e) => {
        if (sidebar.classList.contains("mobile-open") && !sidebar.contains(e.target) && e.target !== toggleBtn) {
            sidebar.classList.remove("mobile-open");
        }
    });
}

/**
 * Handle tabs selection and page navigations
 */
function initTabManager() {
    const tabs = document.querySelectorAll(".sidebar-menu-item");
    const panes = document.querySelectorAll(".feature-pane");

    if (tabs.length === 0) return;

    function selectTab(paneId) {
        tabs.forEach(t => {
            if (t.getAttribute("data-tab") === paneId) {
                t.classList.add("active");
            } else {
                t.classList.remove("active");
            }
        });

        panes.forEach(p => {
            if (p.id === paneId) {
                p.classList.add("active");
            } else {
                p.classList.remove("active");
            }
        });
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const paneId = tab.getAttribute("data-tab");
            selectTab(paneId);

            // On mobile, close sidebar drawer automatically upon tab select
            const sidebar = document.getElementById("sidebar");
            if (sidebar) sidebar.classList.remove("mobile-open");
        });
    });

    // Handle cross-page redirection focus
    const focusTab = localStorage.getItem("activeTabFocus");
    if (focusTab) {
        selectTab(focusTab);
        localStorage.removeItem("activeTabFocus");
    }
}

/**
 * Auto-expanding Textareas and Keyboard shortcuts (Ctrl + Enter)
 */
function initFormInteractions() {
    const textareas = document.querySelectorAll("textarea.form-textarea");

    textareas.forEach(textarea => {
        // Auto-expand on input
        textarea.addEventListener("input", () => {
            textarea.style.height = "auto";
            textarea.style.height = (textarea.scrollHeight) + "px";
        });

        // Submit form on Ctrl + Enter keypress
        textarea.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                const form = textarea.closest("form");
                if (form) {
                    // Dispatch form submit event
                    form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
                }
            }
        });
    });
}

/**
 * Helper to render Markdown documents, highlighting code blocks, and adding Copy button wrappers.
 */
function renderMarkdown(element, text, animate = false) {
    if (!element) return;
    if (animate) {
        streamMarkdown(element, text);
        return;
    }
    try {
        const rawHTML = marked.parse(text || "");
        const cleanHTML = DOMPurify.sanitize(rawHTML);
        element.innerHTML = cleanHTML;

        // Add Copy button wrappers to pre blocks
        element.querySelectorAll('pre').forEach((preBlock) => {
            const codeBlock = preBlock.querySelector('code');
            if (!codeBlock) return;

            if (preBlock.parentNode.classList.contains('code-block-wrapper')) return;

            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            preBlock.parentNode.insertBefore(wrapper, preBlock);
            wrapper.appendChild(preBlock);

            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.textContent = 'Copy';
            wrapper.appendChild(copyBtn);

            copyBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(codeBlock.textContent);
                    copyBtn.textContent = 'Copied!';
                    setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
                } catch (e) {
                    console.error("Copy failed:", e);
                }
            });
        });

        if (typeof hljs !== "undefined") {
            element.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    } catch (err) {
        console.error("Markdown render error:", err);
        element.textContent = text || "";
    }
}

/**
 * Stream Markdown response with typewriter effect and display action options bar upon completion
 */
function streamMarkdown(element, text) {
    if (!element) return;
    element.innerHTML = "";
    element.classList.add("typing-cursor");

    let index = 0;
    const speed = 5;
    const charsPerStep = 6;
    const parentBox = element.closest(".output-box");

    function type() {
        if (index < text.length) {
            index += charsPerStep;
            const substring = text.substring(0, index);
            const rawHTML = marked.parse(substring);
            element.innerHTML = DOMPurify.sanitize(rawHTML);

            if (typeof hljs !== "undefined") {
                element.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }

            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'auto'
            });

            setTimeout(type, speed);
        } else {
            element.classList.remove("typing-cursor");
            renderMarkdown(element, text, false);

            // Reveal Actions panel
            if (parentBox) {
                const actionsBar = parentBox.querySelector(".document-action-bar");
                if (actionsBar) {
                    actionsBar.style.display = "flex";
                    bindDocumentActions(actionsBar, text);
                }
            }

            // Refresh activity history sidebar seamlessly
            loadSidebarHistory();
        }
    }
    type();
}

/**
 * Configure Copy / Download / Follow-up buttons on document responses
 */
function bindDocumentActions(actionBarElement, rawMarkdownText) {
    const copyBtn = actionBarElement.querySelector(".copy-doc-btn");
    const downloadBtn = actionBarElement.querySelector(".download-doc-btn");
    const continueBtn = actionBarElement.querySelector(".continue-doc-btn");
    const activePane = actionBarElement.closest(".feature-pane");

    if (copyBtn) {
        // Clear previous listeners by replacing node
        const newCopy = copyBtn.cloneNode(true);
        copyBtn.parentNode.replaceChild(newCopy, copyBtn);
        newCopy.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(rawMarkdownText);
                newCopy.textContent = "Copied!";
                setTimeout(() => { newCopy.textContent = "Copy"; }, 2000);
            } catch (err) {
                console.error("Markdown copy failed:", err);
            }
        });
    }

    if (downloadBtn) {
        const newDownload = downloadBtn.cloneNode(true);
        downloadBtn.parentNode.replaceChild(newDownload, downloadBtn);
        newDownload.addEventListener("click", () => {
            const blob = new Blob([rawMarkdownText], { type: "text/markdown" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "edugenie-document.md";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    if (continueBtn && activePane) {
        const newContinue = continueBtn.cloneNode(true);
        continueBtn.parentNode.replaceChild(newContinue, continueBtn);
        newContinue.addEventListener("click", () => {
            const input = activePane.querySelector("textarea, input[type='text']");
            if (input) {
                input.focus();
                input.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        });
    }
}

/**
 * Dynamic load sidebar activity logs from history list API
 */
async function loadSidebarHistory() {
    const historyList = document.getElementById("sidebarHistoryList");
    if (!historyList) return;

    try {
        const response = await fetch("/api/history/list");
        if (!response.ok) return;
        const items = await response.json();

        if (items.length === 0) {
            historyList.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); padding: 0.5rem 0.75rem;">No recent history</div>`;
            return;
        }

        historyList.innerHTML = "";
        // Take first 10 items to display in workspace list
        items.slice(0, 10).forEach(item => {
            const link = document.createElement("a");
            link.className = "history-item-link";
            link.textContent = `${item.activity_type.toUpperCase()}: ${item.input_text}`;
            link.title = item.input_text;

            // Bind click to load this item into active canvas view dynamically (SPA feel!)
            link.addEventListener("click", () => {
                loadHistoryItemToCanvas(item);
            });

            historyList.appendChild(link);
        });
    } catch (e) {
        console.error("Failed to fetch sidebar logs:", e);
    }
}

/**
 * Dynamic loading of a log item directly into the active dashboard workspace
 */
function loadHistoryItemToCanvas(item) {
    const typeToPane = {
        "qna": "qna-pane",
        "explain": "explain-pane",
        "summarize": "summarize-pane",
        "quiz": "quiz-pane",
        "roadmap": "roadmap-pane"
    };

    const targetPaneId = typeToPane[item.activity_type];
    if (!targetPaneId) return;

    // Switch to appropriate active tab
    const tabs = document.querySelectorAll(".sidebar-menu-item");
    const panes = document.querySelectorAll(".feature-pane");

    tabs.forEach(t => {
        if (t.getAttribute("data-tab") === targetPaneId) {
            t.classList.add("active");
        } else {
            t.classList.remove("active");
        }
    });

    panes.forEach(p => {
        if (p.id === targetPaneId) {
            p.classList.add("active");
        } else {
            p.classList.remove("active");
        }
    });

    // Populate active tab inputs and response outputs instantly
    const pane = document.getElementById(targetPaneId);
    if (!pane) return;

    // 1. Populate input
    const input = pane.querySelector("textarea, input[type='text']");
    if (input) {
        input.value = item.input_text;
        input.style.height = "auto";
        if (input.tagName === "TEXTAREA") {
            input.style.height = (input.scrollHeight) + "px";
        }
    }

    // 2. Populate output (No skeleton loading or stream typewriter animation needed for clicking logs!)
    const outputBoxId = targetPaneId.replace("-pane", "Output");
    const outputBox = document.getElementById(outputBoxId);
    if (outputBox) {
        outputBox.style.display = "block";
        const content = outputBox.querySelector(".output-content");
        const loader = outputBox.querySelector(".skeleton-loader");
        const actions = outputBox.querySelector(".document-action-bar");

        if (loader) loader.style.display = "none";
        if (content) {
            content.style.display = "block";

            // Render outputs cleanly
            if (item.activity_type === "explain") {
                content.innerHTML = `
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                        Complexity Level: <span class="complexity-badge intermediate">INTERMEDIATE</span>
                    </div>
                    <div class="explanation-text"></div>
                `;
                renderMarkdown(content.querySelector(".explanation-text"), item.output_text, false);
            } else if (item.activity_type === "summarize") {
                content.innerHTML = `
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                        Saved Study Document
                    </div>
                    <div class="summary-text"></div>
                `;
                renderMarkdown(content.querySelector(".summary-text"), item.output_text, false);
            } else if (item.activity_type === "quiz") {
                const quizText = item.output_text || "";
                if (quizText.startsWith("Score:")) {
                    content.innerHTML = `
                        <h3 style="font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">Saved Grader Review</h3>
                        <div class="feedback-text"></div>
                    `;
                    renderMarkdown(content.querySelector(".feedback-text"), quizText, false);
                } else {
                    content.innerHTML = `
                        <h3 style="font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">Saved Quiz Questions</h3>
                        <div class="quiz-text"></div>
                    `;
                    renderMarkdown(content.querySelector(".quiz-text"), quizText, false);
                }
            } else if (item.activity_type === "roadmap") {
                // For roadmaps, the output is JSON stored as text. We can parse it if it is JSON, or render as plain markdown.
                try {
                    const parsed = JSON.parse(item.output_text);
                    renderRoadmapTimeline(parsed, content);
                } catch (e) {
                    renderMarkdown(content, item.output_text, false);
                }
            } else {
                renderMarkdown(content, item.output_text, false);
            }
        }

        if (actions) {
            actions.style.display = "flex";
            bindDocumentActions(actions, item.output_text);
        }

        // Scroll to document view smoothly
        outputBox.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

/**
 * Handle Login, Logout, Registration AJAX requests
 */
function initAuthForms() {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const logoutBtn = document.getElementById("logoutBtn");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const errorBox = document.getElementById("authError");
            errorBox.style.display = "none";

            try {
                const response = await fetch("/api/auth/login", {
                    method: "POST",
                    body: formData
                });
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Authentication credentials mismatch.");
                }
                window.location.href = "/dashboard";
            } catch (err) {
                errorBox.textContent = err.message;
                errorBox.style.display = "block";
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("regUsername").value;
            const email = document.getElementById("regEmail").value;
            const password = document.getElementById("regPassword").value;
            const errorBox = document.getElementById("authError");
            const successBox = document.getElementById("authSuccess");

            errorBox.style.display = "none";
            successBox.style.display = "none";

            try {
                const response = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Error building user workspace.");
                }

                successBox.textContent = "Desk created! Loading sign in page...";
                successBox.style.display = "block";

                setTimeout(() => {
                    window.location.href = "/login";
                }, 1200);
            } catch (err) {
                errorBox.textContent = err.message;
                errorBox.style.display = "block";
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch("/api/auth/logout", { method: "POST" });
                window.location.href = "/";
            } catch (err) {
                console.error("Logout connection failed:", err);
            }
        });
    }
}

/**
 * Handle core study workspace forms
 */
function initWorkspaceForms() {
    // 1. Ask Tutor (QnA)
    const qnaForm = document.getElementById("qnaForm");
    if (qnaForm) {
        qnaForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const question = document.getElementById("qnaInput").value;
            const resultBox = document.getElementById("qnaOutput");
            const loader = resultBox.querySelector(".skeleton-loader");
            const content = resultBox.querySelector(".output-content");
            const actions = resultBox.querySelector(".document-action-bar");

            resultBox.style.display = "block";
            loader.style.display = "block";
            content.style.display = "none";
            content.innerHTML = "";
            if (actions) actions.style.display = "none";

            try {
                const response = await fetch("/api/qna/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question })
                });
                const data = await response.json();

                loader.style.display = "none";
                content.style.display = "block";

                if (!response.ok) throw new Error(data.detail || "Failed to fetch response.");
                renderMarkdown(content, data.answer, true);
            } catch (err) {
                loader.style.display = "none";
                content.style.display = "block";
                content.innerHTML = `<span style="color: #DC2626;">Error: ${err.message}</span>`;
            }
        });
    }

    // 2. Concept Explainer
    const explainForm = document.getElementById("explainForm");
    if (explainForm) {
        explainForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const concept = document.getElementById("explainInput").value;
            const level = document.getElementById("explainLevel").value;
            const resultBox = document.getElementById("explainOutput");
            const loader = resultBox.querySelector(".skeleton-loader");
            const content = resultBox.querySelector(".output-content");
            const actions = resultBox.querySelector(".document-action-bar");

            resultBox.style.display = "block";
            loader.style.display = "block";
            content.style.display = "none";
            content.innerHTML = "";
            if (actions) actions.style.display = "none";

            try {
                const response = await fetch("/api/explanation/explain", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ concept, level })
                });
                const data = await response.json();

                loader.style.display = "none";
                content.style.display = "block";

                if (!response.ok) throw new Error(data.detail || "Failed to fetch response.");
                content.innerHTML = `
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                        Complexity Level: <span class="complexity-badge ${data.level}">${data.level.toUpperCase()}</span>
                    </div>
                    <div class="explanation-text"></div>
                `;
                renderMarkdown(content.querySelector(".explanation-text"), data.explanation, true);
            } catch (err) {
                loader.style.display = "none";
                content.style.display = "block";
                content.innerHTML = `<span style="color: #DC2626;">Error: ${err.message}</span>`;
            }
        });
    }

    // 3. Note Summarizer
    const summarizeForm = document.getElementById("summarizeForm");
    if (summarizeForm) {
        summarizeForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = document.getElementById("summarizeInput").value;
            const length = document.getElementById("summarizeLength").value;
            const resultBox = document.getElementById("summarizeOutput");
            const loader = resultBox.querySelector(".skeleton-loader");
            const content = resultBox.querySelector(".output-content");
            const actions = resultBox.querySelector(".document-action-bar");

            resultBox.style.display = "block";
            loader.style.display = "block";
            content.style.display = "none";
            content.innerHTML = "";
            if (actions) actions.style.display = "none";

            try {
                const response = await fetch("/api/summary/summarize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text, length })
                });
                const data = await response.json();

                loader.style.display = "none";
                content.style.display = "block";

                if (!response.ok) throw new Error(data.detail || "Failed to fetch response.");
                content.innerHTML = `
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                        Original length: <strong>${data.original_length}</strong> chars | Summary: <strong>${data.summary_length}</strong> chars
                    </div>
                    <div class="summary-text"></div>
                `;
                renderMarkdown(content.querySelector(".summary-text"), data.summary, true);
            } catch (err) {
                loader.style.display = "none";
                content.style.display = "block";
                content.innerHTML = `<span style="color: #DC2626;">Error: ${err.message}</span>`;
            }
        });
    }

    // 3b. Note Summarizer Document Upload Handler
    const summarizeFile = document.getElementById("summarizeFile");
    const fileStatus = document.getElementById("fileUploadStatus");
    if (summarizeFile && fileStatus) {
        summarizeFile.addEventListener("change", async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            fileStatus.style.display = "block";
            fileStatus.style.color = "var(--color-primary)";
            fileStatus.textContent = `Extracting text from "${file.name}"...`;

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch("/api/summary/extract-text", {
                    method: "POST",
                    body: formData
                });
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Failed to extract text from file.");
                }

                const textarea = document.getElementById("summarizeInput");
                textarea.value = data.text;
                textarea.dispatchEvent(new Event("input")); // trigger auto-expand
                
                fileStatus.style.color = "#10B981"; // green
                fileStatus.textContent = `Successfully extracted ${data.text.length} characters from "${file.name}"!`;
            } catch (err) {
                fileStatus.style.color = "#EF4444"; // red
                fileStatus.textContent = `Error: ${err.message}`;
            }
        });
    }

    // 4. MCQ Practice Quiz
    const quizForm = document.getElementById("quizForm");
    const quizWorkspace = document.getElementById("quizWorkspace");
    const quizOutput = document.getElementById("quizOutput");

    if (quizForm) {
        quizForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const topic = document.getElementById("quizTopicInput").value;
            const count = parseInt(document.getElementById("quizCountInput").value) || 5;

            quizOutput.style.display = "none";
            quizWorkspace.style.display = "none";
            quizForm.querySelector("button").disabled = true;

            const loaderBox = document.createElement("div");
            loaderBox.className = "skeleton-loader";
            loaderBox.innerHTML = `
                <div class="skeleton-line" style="width: 50%;"></div>
                <div class="skeleton-line" style="width: 85%;"></div>
            `;
            quizForm.parentNode.insertBefore(loaderBox, quizWorkspace);

            try {
                const response = await fetch("/api/quiz/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic, num_questions: count })
                });
                const data = await response.json();
                loaderBox.remove();
                quizForm.querySelector("button").disabled = false;

                if (!response.ok) throw new Error(data.detail || "Quiz setup error.");
                renderQuizWorkspace(data);
            } catch (err) {
                loaderBox.remove();
                quizForm.querySelector("button").disabled = false;
                quizOutput.style.display = "block";
                quizOutput.querySelector(".output-content").innerHTML = `<span style="color: #DC2626;">Error: ${err.message}</span>`;
            }
        });
    }

    // 5. Study Roadmaps
    const roadmapForm = document.getElementById("roadmapForm");
    if (roadmapForm) {
        roadmapForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const topic = document.getElementById("roadmapTopicInput").value;
            const resultBox = document.getElementById("roadmapOutput");
            const loader = resultBox.querySelector(".skeleton-loader");
            const content = resultBox.querySelector(".output-content");
            const actions = resultBox.querySelector(".document-action-bar");

            resultBox.style.display = "block";
            loader.style.display = "block";
            content.style.display = "none";
            content.innerHTML = "";
            if (actions) actions.style.display = "none";

            try {
                const response = await fetch("/api/roadmap/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic })
                });
                const data = await response.json();

                loader.style.display = "none";
                content.style.display = "block";

                if (!response.ok) throw new Error(data.detail || "Roadmap generation error.");
                renderRoadmapTimeline(data, content);

                // Expose download action with markdown compilation of roadmap
                if (actions) {
                    actions.style.display = "flex";
                    const mdText = `# Learning Roadmap for ${data.topic}\n\n` +
                        data.steps.map(s => `## Step ${s.step_number}: ${s.title}\n${s.description}\nReferences: ${s.resources.join(', ')}`).join('\n\n');
                    bindDocumentActions(actions, mdText);
                }

                // Refresh activity history list
                loadSidebarHistory();
            } catch (err) {
                loader.style.display = "none";
                content.style.display = "block";
                content.innerHTML = `<span style="color: #DC2626;">Error: ${err.message}</span>`;
            }
        });
    }
}

/**
 * Quiz workspace dynamic setup
 */
function renderQuizWorkspace(quizData) {
    const quizWorkspace = document.getElementById("quizWorkspace");
    const container = document.getElementById("quizQuestionsContainer");

    container.innerHTML = "";
    quizWorkspace.style.display = "block";
    quizWorkspace.setAttribute("data-quiz-id", quizData.quiz_id);

    quizData.questions.forEach((q, index) => {
        const questionDiv = document.createElement("div");
        questionDiv.className = "quiz-question-container";

        questionDiv.innerHTML = `
            <h4>Q${index + 1}. ${q.question_text}</h4>
            <div class="options-list">
                ${q.options.map(opt => `
                    <label class="option-item">
                        <input type="radio" name="question_${q.id}" value="${opt.label}">
                        <span><strong>${opt.label}.</strong> ${opt.text}</span>
                    </label>
                `).join('')}
            </div>
        `;
        container.appendChild(questionDiv);
    });

    const submitBtn = document.getElementById("submitAnswersBtn");
    const newSubmitBtn = submitBtn.cloneNode(true);
    submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);

    newSubmitBtn.addEventListener("click", async () => {
        const quizId = quizWorkspace.getAttribute("data-quiz-id");
        const answers = {};

        quizData.questions.forEach(q => {
            const selected = document.querySelector(`input[name="question_${q.id}"]:checked`);
            if (selected) {
                answers[q.id] = selected.value;
            }
        });

        const quizOutput = document.getElementById("quizOutput");
        const loader = quizOutput.querySelector(".skeleton-loader");
        const content = quizOutput.querySelector(".output-content");
        const actions = quizOutput.querySelector(".document-action-bar");

        quizOutput.style.display = "block";
        loader.style.display = "block";
        content.style.display = "none";
        content.innerHTML = "";
        if (actions) actions.style.display = "none";

        try {
            const response = await fetch(`/api/quiz/${quizId}/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ answers })
            });
            const result = await response.json();

            loader.style.display = "none";
            content.style.display = "block";
            if (!response.ok) throw new Error(result.detail || "Error during grading.");

            content.innerHTML = `
                <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Quiz Results</h3>
                <p style="font-size: 1.15rem; margin-bottom: 1.5rem; color: var(--text-primary);">Score: <strong style="color: var(--color-primary);">${result.score} / ${result.total_questions}</strong> (${result.percentage.toFixed(1)}%)</p>
                <div class="feedback-text"></div>
            `;
            renderMarkdown(content.querySelector(".feedback-text"), result.feedback, true);
            quizOutput.scrollIntoView({ behavior: "smooth" });
        } catch (err) {
            loader.style.display = "none";
            content.style.display = "block";
            content.innerHTML = `<span style="color: #DC2626;">Error submitting quiz: ${err.message}</span>`;
        }
    });
}

/**
 * Roadmap timeline rendering
 */
function renderRoadmapTimeline(roadmapData, element) {
    element.innerHTML = `
        <h3 style="margin-bottom: 2rem; font-size: 1.4rem; font-weight: 600; font-family:var(--font-heading);">Study Map: <span style="color:var(--color-primary);">${roadmapData.topic}</span></h3>
        <div class="roadmap-timeline">
            ${roadmapData.steps.map(step => `
                <div class="roadmap-step" data-step="${step.step_number}">
                    <h4>Step ${step.step_number}: ${step.title}</h4>
                    <div class="roadmap-description markdown-body" style="color:var(--text-secondary); margin: 0.5rem 0; font-size: 0.95rem;"></div>
                    ${step.resources.length > 0 ? `
                        <div style="font-size: 0.8rem; display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                            <strong style="color: var(--text-primary);">Target Resources:</strong>
                            ${step.resources.map(res => `<span class="complexity-badge" style="padding:0.15rem 0.4rem; font-size:0.72rem;">${res}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;

    roadmapData.steps.forEach(step => {
        const stepEl = element.querySelector(`.roadmap-step[data-step="${step.step_number}"] .roadmap-description`);
        if (stepEl) {
            renderMarkdown(stepEl, step.description, false);
        }
    });
}

/**
 * Delete past activity log row (triggered from standalone logs /history view)
 */
async function deleteHistoryItem(elementId, historyId) {
    if (!confirm("Are you sure you want to delete this log entry?")) return;

    try {
        const response = await fetch(`/api/history/delete/${historyId}`, {
            method: "DELETE"
        });
        const result = await response.json();

        if (response.ok) {
            const itemElement = document.getElementById(elementId);
            if (itemElement) {
                itemElement.style.opacity = "0";
                setTimeout(() => { itemElement.remove(); }, 300);
            }
            // Seamlessly refresh sidebar list if present on screen
            loadSidebarHistory();
        } else {
            alert("Error: " + (result.detail || "Unable to delete entry"));
        }
    } catch (e) {
        alert("Failed to connect to delete endpoint: " + e.message);
    }
}

// Global click delegation for delete buttons
document.addEventListener("click", (e) => {
    const deleteBtn = e.target.closest(".delete-history-btn");
    if (deleteBtn) {
        const historyId = deleteBtn.getAttribute("data-history-id");
        if (historyId) {
            deleteHistoryItem('history_row_' + historyId, historyId);
        }
    }
});
