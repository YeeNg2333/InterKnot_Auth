import http.server
import socketserver
import json
import subprocess
import os
import sys
import threading
import time
import datetime
import tempfile
from PyQt5.QtCore import QThread

from modules.State import global_state

state = global_state()

PORT = 50000
_webui_httpd = None
_webui_httpd_lock = threading.Lock()

EXTERNAL_HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>InterKnot - Share</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:,">
    <style>
        :root {
            --bg-color: #fff0f5;
            --panel-bg: rgba(255, 255, 255, 0.9);
            --border-glow: #ff69b4;
            --text-main: #664d54;
            --text-hl: #e75480;
            --accent: #ff69b4;
        }

        :root.dark-mode {
            --bg-color: #050510;
            --panel-bg: rgba(15, 20, 30, 0.8);
            --border-glow: #0ff;
            --text-main: #dfdfdf;
            --text-hl: #0ff;
            --accent: #0ff;
        }
        
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 20px;
            font-family: 'Segoe UI', Tahoma, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            width: 100vw;
            transition: all 0.3s ease;
        }
        
        body {
            background: radial-gradient(circle at 50% 10%, #fffbfc, #ffe4e1 80%);
        }
        
        :root.dark-mode body {
            background: radial-gradient(circle at 50% 10%, #1a1a2e, #050510 60%);
        }

        body::after {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 999;
            opacity: 0;
            background: radial-gradient(circle at 50% 50%, rgba(var(--accent-rgb, 255, 105, 180), 0.22), transparent 60%);
        }

        body.theme-switching::after {
            animation: themePulse 0.45s ease;
        }

        @keyframes themePulse {
            0% { opacity: 0; }
            30% { opacity: 1; }
            100% { opacity: 0; }
        }

        .theme-switching .main-panel,
        .theme-switching .content,
        .theme-switching .btn-download,
        .theme-switching .feature-box,
        .theme-switching .theme-toggle-btn,
        .theme-switching .desc,
        .theme-switching h1 {
            transition: background-color 0.45s ease, color 0.45s ease, border-color 0.45s ease, box-shadow 0.45s ease, text-shadow 0.45s ease;
        }

        .decor {
            position: fixed;
            pointer-events: none;
            z-index: 0;
            opacity: 0.15;
            filter: blur(20px);
        }
        .decor-1 { top: -50px; left: -50px; width: 300px; height: 300px; background: radial-gradient(var(--accent), transparent 60%); }
        .decor-2 { bottom: -100px; right: -50px; width: 400px; height: 400px; background: radial-gradient(var(--border-glow), transparent 60%); }
        
        .main-panel {
            position: relative;
            background: rgba(var(--panel-rgb, 255, 255, 255), 0.6);
            border-radius: 16px;
            padding: 4px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(var(--accent-rgb, 255, 182, 193), 0.3), 0 0 0 1px rgba(var(--panel-rgb, 255, 255, 255), 0.5) inset;
            max-width: 600px;
            width: 100%;
            z-index: 10;
            animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            backdrop-filter: blur(10px);
        }
        
        :root {
            --panel-rgb: 255, 255, 255;
            --accent-rgb: 255, 105, 180;
            --btn-grad-1: #fff0f5;
            --btn-grad-2: #ffe4e1;
            --btn-grad-hover-1: #ffe4e1;
            --btn-grad-hover-2: #ff69b4;
            --link-color: #d14a70;
            --link-hover-color: #e75480;
            --feature-bg: rgba(255, 240, 245, 0.5);
            --feature-bg-hover: rgba(255, 228, 225, 0.8);
            --btn-border: #ff69b4;
            --btn-border-hover: #ff1493;
            --btn-text-hover: #fff;
        }

        :root.dark-mode {
            --panel-rgb: 30, 30, 40;
            --accent-rgb: 0, 255, 255;
            --btn-grad-1: rgba(0, 255, 255, 0.1);
            --btn-grad-2: rgba(0, 255, 255, 0.2);
            --btn-grad-hover-1: rgba(0, 255, 255, 0.2);
            --btn-grad-hover-2: rgba(0, 255, 255, 0.4);
            --link-color: #0ff;
            --link-hover-color: #fff;
            --feature-bg: rgba(0, 255, 255, 0.05);
            --feature-bg-hover: rgba(0, 255, 255, 0.15);
            --btn-border: rgba(0, 255, 255, 0.5);
            --btn-border-hover: rgba(0, 255, 255, 0.8);
            --btn-text-hover: #0ff;
        }

        ::selection {
            background: rgba(var(--accent-rgb, 255, 105, 180), 0.35);
            color: var(--text-main);
        }

        ::-moz-selection {
            background: rgba(var(--accent-rgb, 255, 105, 180), 0.35);
            color: var(--text-main);
        }

        ::view-transition-old(root),
        ::view-transition-new(root) {
            animation: none;
            mix-blend-mode: normal;
        }
        ::view-transition-old(root) { z-index: 1; }
        ::view-transition-new(root) { z-index: 2; }
        .dark-mode::view-transition-old(root) { z-index: 2; }
        .dark-mode::view-transition-new(root) { z-index: 1; }





        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .main-panel::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(
                300px circle at var(--mouse-x, -500px) var(--mouse-y, -500px),
                rgba(var(--accent-rgb, 255, 105, 180), 0.8),
                transparent 60%
            );
            z-index: 1;
            transition: opacity 0.5s ease;
            opacity: 0;
        }

        .main-panel:hover::before { opacity: 1; }

        .content {
            position: relative;
            z-index: 10;
            padding: 40px;
            background: var(--panel-bg);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow: inset 0 0 20px rgba(var(--panel-rgb, 255, 255, 255), 0.5);
        }

        h1 {
            color: var(--text-hl);
            margin-top: 0;
            font-size: 2.2em;
            letter-spacing: 1px;
            text-shadow: 0 2px 4px rgba(var(--accent-rgb, 231, 84, 128), 0.2);
            border-bottom: 2px dashed rgba(var(--accent-rgb, 255, 182, 193), 0.5);
            padding-bottom: 15px;
            width: 100%;
            font-weight: 600;
        }

        .desc {
            color: var(--text-main);
            line-height: 1.7;
            margin-bottom: 30px;
            font-size: 1.05em;
        }
        
        .desc a {
            color: var(--link-color);
            text-decoration: none;
            border-bottom: 1px dashed var(--link-color);
            transition: all 0.3s;
        }
        
        .desc a:hover {
            color: var(--link-hover-color);
            border-bottom-style: solid;
        }

        .btn-download {
            display: inline-block;
            background: linear-gradient(135deg, var(--btn-grad-1) 0%, var(--btn-grad-2) 100%);
            color: var(--link-color);
            text-decoration: none;
            padding: 16px 45px;
            font-size: 1.2em;
            font-weight: bold;
            border: 2px solid var(--btn-border);
            border-radius: 30px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 4px 15px rgba(var(--accent-rgb, 255, 182, 193), 0.4);
            position: relative;
            overflow: hidden;
        }

        .btn-download:hover {
            background: linear-gradient(135deg, var(--btn-grad-hover-1) 0%, var(--btn-grad-hover-2) 100%);
            color: var(--btn-text-hover);
            box-shadow: 0 6px 20px rgba(var(--accent-rgb, 255, 105, 180), 0.4);
            transform: translateY(-2px) scale(1.02);
            border-color: var(--btn-border-hover);
        }
        
        .btn-download:active {
            transform: translateY(1px);
        }

        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            width: 100%;
            margin-top: 40px;
        }

        .feature-box {
            background: var(--feature-bg);
            border: 1px solid rgba(var(--accent-rgb, 255, 182, 193), 0.4);
            padding: 15px;
            border-radius: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(var(--accent-rgb, 255, 182, 193), 0.1);
        }

        .feature-box:hover {
            background: var(--feature-bg-hover);
            border-color: var(--btn-border-hover);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(var(--accent-rgb, 255, 182, 193), 0.3);
        }

        .feature-box span {
            color: var(--link-color);
            font-weight: bold;
            letter-spacing: 1px;
            font-size: 0.95em;
        }
        
        .theme-toggle-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(var(--panel-rgb, 255, 255, 255), 0.7);
            border: 2px solid var(--accent);
            color: var(--accent);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            z-index: 100;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(var(--accent-rgb, 255, 182, 193), 0.2);
            backdrop-filter: blur(5px);
        }
        
        .theme-toggle-btn:hover {
            background: rgba(var(--accent-rgb, 255, 182, 193), 0.2);
            box-shadow: 0 0 15px rgba(var(--accent-rgb, 255, 182, 193), 0.6);
            transform: scale(1.05);
        }
        
        @media screen and (max-width: 480px) {
            .features { grid-template-columns: 1fr; }
            .content { padding: 20px; }
        }
    </style>
</head>
<body>
    <button class="theme-toggle-btn" onclick="toggleTheme(event)" id="themeBtn">☀️</button>
    <div class="decor decor-1"></div>
    <div class="decor decor-2"></div>

    <div class="main-panel" id="tiltPanel">
        <div class="content">
            <h1>欢迎加入绳网</h1>
            <div class="desc">
                在无形的数据洪流之中，我们以结为契，以绳为网，将零散的节点重新编织。绳网源于对效率与自由的追求——让繁琐的认证流程化作一次优雅的连接。<br><br>
                借助 EasyTier 的组网能力，已连接的设备还可作为出口节点，在封闭的边界之中，悄然编织属于自己的通路。<br><br>
                <a href="https://github.com/Yish1/InterKnot_Auth">
                InterKnot项目地址: Yish1/InterKnot_Auth
                </a>
            </div>
            
            <a href="#" class="btn-download" id="downloadBtn" onclick="startDownload(event)">立即下载</a>
            <div id="statusMsg" style="max-height: 0; opacity: 0; margin-top: 0; overflow: hidden; transition: all 0.4s ease; color: var(--text-hl); font-size: 0.95em; font-weight: bold; width: 80%; text-shadow: 0 1px 2px rgba(var(--accent-rgb, 231, 84, 128), 0.2);"></div>

            <div class="features">
                <div class="feature-box"><span>校园网助手</span></div>
                <div class="feature-box"><span>多拨网速翻倍</span></div>
                <div class="feature-box"><span>一键共享</span></div>
                <div class="feature-box"><span>端到端加密</span></div>
            </div>
        </div>
    </div>

    <script>
        const panel = document.getElementById('tiltPanel');
        document.body.addEventListener('mousemove', e => {
            const rect = panel.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            panel.style.setProperty('--mouse-x', `${x}px`);
            panel.style.setProperty('--mouse-y', `${y}px`);
        });

        let downloadRetryInterval = null;

        function startDownload(event) {
            event.preventDefault();
            const btn = document.getElementById('downloadBtn');
            const statusMsg = document.getElementById('statusMsg');
            
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.5';
            statusMsg.style.maxHeight = '100px';
            statusMsg.style.opacity = '1';
            statusMsg.style.marginTop = '15px';
            statusMsg.textContent = '正在请求下载...';
            
            attemptDownload();
        }

        function attemptDownload() {
            const statusMsg = document.getElementById('statusMsg');
            fetch('/download/InterKnot')
                .then(async response => {
                    if (response.status === 200) {
                        // 文件准备完毕，开始下载
                        statusMsg.innerHTML = '<div style="margin-bottom: 8px;">开始下载... <span id="dl-speed" style="color:var(--text-hl); font-size:0.9em; font-weight:normal;"></span></div><div style="width: 100%; height: 8px; background: rgba(var(--accent-rgb, 255, 105, 180), 0.3); border-radius: 4px; overflow: hidden;"><div id="dl-progress" style="width: 0%; height: 100%; background: var(--text-hl); transition: width 0.3s ease;"></div></div>';
                        
                        const contentLength = response.headers.get('content-length');
                        const total = contentLength ? parseInt(contentLength, 10) : 0;
                        let loaded = 0;
                        
                        const reader = response.body.getReader();
                        const chunks = [];
                        let startTime = Date.now();
                        let lastTime = startTime;
                        let lastLoaded = 0;

                        while(true) {
                            const {done, value} = await reader.read();
                            if (done) break;
                            
                            chunks.push(value);
                            loaded += value.length;

                            if (total) {
                                const progress = (loaded / total) * 100;
                                const progEl = document.getElementById('dl-progress');
                                if(progEl) progEl.style.width = progress + '%';
                            }
                            
                            const now = Date.now();
                            if (now - lastTime > 500) {
                                const speed = (loaded - lastLoaded) / ((now - lastTime) / 1000);
                                let speedTxt = (speed / 1024 / 1024).toFixed(2) + ' MB/s';
                                if (speed < 1024 * 1024) {
                                    speedTxt = (speed / 1024).toFixed(2) + ' KB/s';
                                }
                                const speedEl = document.getElementById('dl-speed');
                                if(speedEl) speedEl.innerText = `(${speedTxt})`;
                                lastLoaded = loaded;
                                lastTime = now;
                            }
                        }

                        const blob = new Blob(chunks, { type: 'application/zip' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'InterKnot.zip';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        setTimeout(() => {
                            statusMsg.textContent = '下载完成！';
                            resetDownloadButton();
                        }, 1000);
                    } else if (response.status === 202) {
                        // 文件正在准备中
                        return response.json().then(data => {
                            let progPercent = data.progress || 0;
                            statusMsg.innerHTML = `<div style="margin-bottom: 8px;">${data.message || '文件正在准备中...'}</div><div style="width: 100%; height: 8px; background: rgba(var(--accent-rgb, 255, 105, 180), 0.3); border-radius: 4px; overflow: hidden;"><div style="width: ${progPercent}%; height: 100%; background: var(--text-hl); transition: width 0.3s ease;"></div></div>`;
                            // 1秒后重试获取状态
                            setTimeout(attemptDownload, 1000);
                        });
                    } else {
                        throw new Error('下载失败');
                    }
                })
                .catch(error => {
                    statusMsg.textContent = '下载失败: ' + error.message;
                    statusMsg.style.color = '#ff4040';
                    setTimeout(resetDownloadButton, 3000);
                });
        }

        function resetDownloadButton() {
            const btn = document.getElementById('downloadBtn');
            const statusMsg = document.getElementById('statusMsg');
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
            setTimeout(() => {
                statusMsg.style.maxHeight = '0';
                statusMsg.style.opacity = '0';
                statusMsg.style.marginTop = '0';
                setTimeout(() => { statusMsg.textContent = ''; }, 400);
            }, 2000);
        }

        function playThemeTransition() {
            const body = document.body;
            body.classList.remove('theme-switching');
            void body.offsetWidth;
            body.classList.add('theme-switching');
            setTimeout(() => body.classList.remove('theme-switching'), 500);
        }
        
        function toggleTheme(event) {
            const root = document.documentElement;
            const btn = document.getElementById('themeBtn');
            playThemeTransition();
            root.classList.toggle('dark-mode');
            
            if (root.classList.contains('dark-mode')) {
                btn.textContent = '🌙';
            } else {
                btn.textContent = '☀️';
            }
        }
        
        // 自动检测时间切换主题，大于等于18点为深色模式
        function autoSetThemeExternal() {
            const hour = new Date().getHours();
            const root = document.documentElement;
            const btn = document.getElementById('themeBtn');
            
            if (hour >= 18 || hour < 6) {
                root.classList.add('dark-mode');
                if (btn) btn.textContent = '🌙';
            } else {
                root.classList.remove('dark-mode');
                if (btn) btn.textContent = '☀️';
            }
        }
        
        // 页面加载时执行
        autoSetThemeExternal();
    </script>
</body>
</html>
"""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>InterKnot - Nodes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:,">
    <script src="/chart.js"></script>
    <style>
        :root {
            --bg-color: #fff0f5;
            --panel-bg: rgba(255, 255, 255, 0.9);
            --panel-rgb: 255, 255, 255;
            --border-glow: #ff69b4;
            --border-glow-rgb: 255, 105, 180;
            --border-glow-alt-rgb: 62, 180, 137;
            --text-main: #664d54;
            --text-hl: #e75480;
            --table-th: #888;
            --table-tr-border: rgba(255, 105, 180, 0.2);
            --table-tr-hover: rgba(255, 105, 180, 0.3);
            --status-good-bg: rgba(255, 105, 180, 0.2);
            --status-good-border: #ff69b4;
            --status-good-text: #e75480;
        }

        body.dark-mode {
            --bg-color: #050510;
            --panel-bg: rgba(15, 20, 30, 0.8);
            --panel-rgb: 15, 20, 30;
            --border-glow: #0ff;
            --border-glow-rgb: 0, 255, 255;
            --border-glow-alt-rgb: 255, 0, 255;
            --text-main: #dfdfdf;
            --text-hl: #0ff;
            --table-th: #888;
            --table-tr-border: rgba(255, 255, 255, 0.05);
            --table-tr-hover: rgba(0, 255, 255, 0.03);
            --status-good-bg: rgba(0,255,255,0.1);
            --status-good-border: #0ff;
            --status-good-text: #0ff;
        }

        ::selection {
            background: rgba(var(--border-glow-rgb, 255, 105, 180), 0.35);
            color: var(--text-main);
        }

        ::-moz-selection {
            background: rgba(var(--border-glow-rgb, 255, 105, 180), 0.35);
            color: var(--text-main);
        }

        ::view-transition-old(root),
        ::view-transition-new(root) {
            animation: none;
            mix-blend-mode: normal;
        }
        ::view-transition-old(root) { z-index: 1; }
        ::view-transition-new(root) { z-index: 2; }
        .dark-mode::view-transition-old(root) { z-index: 2; }
        .dark-mode::view-transition-new(root) { z-index: 1; }




* { box-sizing: border-box; }
        body {
            margin: 0; padding: 20px;
            font-family: 'Segoe UI', Tahoma, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 15px;
            height: 100vh;
            width: 100vw;
            transition: all 0.3s ease;
        }
        
        body.dark-mode {
            background: radial-gradient(circle at 50% 10%, #1a1a2e, #050510 60%);
        }
        
        body.light-mode, body:not(.dark-mode) {
            background: radial-gradient(circle at 50% 10%, #fffbfc, #ffe4e1 80%);
        }

        body::after {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 999;
            opacity: 0;
            background: radial-gradient(circle at 50% 50%, rgba(var(--border-glow-rgb, 255, 105, 180), 0.18), transparent 60%);
        }

        body.theme-switching::after {
            animation: themePulse 0.45s ease;
        }

        @keyframes themePulse {
            0% { opacity: 0; }
            30% { opacity: 1; }
            100% { opacity: 0; }
        }

        .theme-switching .interactive-box,
        .theme-switching .interactive-box::after,
        .theme-switching .content,
        .theme-switching .status-badge,
        .theme-switching .peer-table th,
        .theme-switching .peer-table td,
        .theme-switching .custom-legend,
        .theme-switching .theme-toggle-btn {
            transition: background-color 0.45s ease, color 0.45s ease, border-color 0.45s ease, box-shadow 0.45s ease;
        }

        .panel-container {
            max-width: 1400px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        /* Mouse tracking light border */
        .interactive-box {
            position: relative;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 2px;
            margin-bottom: 15px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(var(--border-glow-rgb, 0, 255, 255), 0.05);
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .interactive-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(
                300px circle at var(--mouse-x, -500px) var(--mouse-y, -500px),
                rgba(var(--border-glow-rgb, 0, 255, 255), 0.5),
                transparent 60%
            );
            z-index: 1;
            transition: opacity 0.5s ease;
            opacity: 0;
        }

        .interactive-box:hover::before {
            opacity: 1;
        }

        .interactive-box::after {
            content: '';
            position: absolute;
            inset: 2px;
            background: var(--bg-color);
            border-radius: 10px;
            z-index: 2;
        }

        .content {
            position: relative;
            z-index: 10;
            padding: 20px;
            background: rgba(var(--panel-rgb), 0.4);
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            flex: 1;
            backdrop-filter: blur(10px);
        }

        h2 { margin-top: 0; margin-bottom: 10px; color: var(--text-hl); border-bottom: 1px solid rgba(var(--border-glow-rgb, 0, 255, 255), 0.2); padding-bottom: 5px; flex-shrink: 0; }
        
        .chart-container {
            position: relative; 
            height: max(22vh, 200px); 
            width: 100%;
            max-width: 100%;
            overflow: hidden;
        }

        .grid-info {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }
        
        .info-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .info-card:hover {
            border-color: rgba(var(--border-glow-rgb, 0, 255, 255), 0.3);
            background: rgba(var(--border-glow-rgb, 0, 255, 255), 0.03);
            transform: translateY(-2px);
        }
        
        .info-label {
            font-size: 0.8em;
            color: #888;
            text-transform: uppercase;
        }
        .info-value {
            font-size: 1.1em;
            color: var(--text-main);
            margin-top: 5px;
            word-break: break-all;
        }

        .table-container {
            width: 100%;
            overflow-x: auto;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
            margin-top: 10px;
        }

        .peer-table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            min-width: 600px;
        }

        .peer-table th, .peer-table td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--table-tr-border);
        }

        .peer-table th {
            color: var(--table-th);
            font-size: 0.85em;
            text-transform: uppercase;
            font-weight: normal;
            white-space: nowrap;
        }

        .peer-table td {
            color: var(--text-main);
            font-size: 0.95em;
        }

        .peer-table tbody tr:hover {
            background: var(--table-tr-hover);
        }
        
        .peer-table tbody tr:last-child td {
            border-bottom: none;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            background: var(--status-good-bg);
            color: var(--status-good-text);
            border: 1px solid var(--status-good-border);
            box-shadow: 0 0 10px rgba(var(--border-glow-rgb, 0, 255, 255), 0.3);
            text-align: center;
            margin-bottom: 10px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 5px rgba(var(--border-glow-rgb, 0, 255, 255), 0.2); }
            50% { box-shadow: 0 0 15px rgba(var(--border-glow-rgb, 0, 255, 255), 0.6); }
            100% { box-shadow: 0 0 5px rgba(var(--border-glow-rgb, 0, 255, 255), 0.2); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .decor {
            position: fixed;
            pointer-events: none;
            z-index: 0;
            opacity: 0.1;
        }
        .decor-1 { top: -50px; left: -50px; width: 300px; height: 300px; background: radial-gradient(rgba(var(--border-glow-rgb, 0, 255, 255), 1), transparent 60%); }
        .decor-2 { bottom: -100px; right: -50px; width: 400px; height: 400px; background: radial-gradient(rgba(var(--border-glow-alt-rgb, 255, 0, 255), 1), transparent 60%); }
    
        /* 响应式自适应布局 */
        @media screen and (max-width: 768px) {
            body {
                padding: 10px;
                gap: 15px;
            }
            .content {
                padding: 10px;
            }
            h2 {
                font-size: 1.2em;
            }
            .chart-container {
                height: 250px !important;
            }
            .grid-info {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            .info-card {
                padding: 10px;
            }
            .status-badge {
                font-size: 0.7em;
                padding: 4px 8px;
            }
        }
        
        @media screen and (max-width: 480px) {
            .chart-container {
                height: 200px !important;
            }
            .info-value {
                font-size: 1em;
            }
        }

    
        .custom-legend {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--panel-bg);
            border: 1px solid rgba(var(--border-glow-rgb, 0, 255, 255), 0.4);
            padding: 10px 15px;
            border-radius: 8px;
            z-index: 100;
            pointer-events: none;
            box-shadow: 0 0 15px rgba(var(--border-glow-rgb, 0, 255, 255), 0.1);
            display: flex;
            flex-direction: column;
            gap: 8px;
            backdrop-filter: blur(5px);
        }
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 13px;
            font-weight: bold;
            color: var(--text-main);
        }
        .legend-color {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            display: inline-block;
        }
        .theme-toggle-btn {
            position: relative;
            background: rgba(var(--panel-rgb, 255, 255, 255), 0.7);
            border: 2px solid var(--text-hl);
            color: var(--text-hl);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            z-index: 100;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(var(--border-glow-rgb, 0, 255, 255), 0.2);
            backdrop-filter: blur(5px);
        }
        
        .theme-toggle-btn:hover {
            background: rgba(var(--border-glow-rgb, 0, 255, 255), 0.2);
            box-shadow: 0 0 15px rgba(var(--border-glow-rgb, 0, 255, 255), 0.6);
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="decor decor-1"></div>
    <div class="decor decor-2"></div>

    <div class="panel-container">

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 15px;">
            <div class="status-badge fade-in" id="conn-state">SYS CONNECTION: INITIALIZING</div>
            <button class="theme-toggle-btn" onclick="toggleTheme(event)" id="themeBtn">☀️</button>
        </div>

        <div class="interactive-box fade-in" style="animation-delay: 0.1s; opacity: 0;">
            <div class="content">
                <h2>📊 实时流量</h2>
                <div class="chart-container">
                    <div class="custom-legend" id="customLegend">
                        <div class="legend-item">
                            <span class="legend-color" style="box-shadow: 0 0 8px rgba(var(--border-glow-rgb, 0, 255, 255), 1); background: rgba(var(--border-glow-rgb, 0, 255, 255), 1);"></span> 
                            <span style="color:rgba(var(--border-glow-rgb, 0, 255, 255), 1)">出站: </span>
                            <span id="legend-tx" style="margin-left: 5px; color:var(--text-main); font-family: monospace;">0.00 KB/s</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="box-shadow: 0 0 8px rgba(var(--border-glow-alt-rgb, 255, 0, 255), 1); background: rgba(var(--border-glow-alt-rgb, 255, 0, 255), 1);"></span> 
                            <span style="color:rgba(var(--border-glow-alt-rgb, 255, 0, 255), 1)">入站: </span>
                            <span id="legend-rx" style="margin-left: 5px; color:var(--text-main); font-family: monospace;">0.00 KB/s</span>
                        </div>
                    </div>
                    <div style="width: 100%; height: 100%; overflow: hidden; position: relative;">
                        <canvas id="trafficChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="interactive-box fade-in" style="animation-delay: 0.2s; opacity: 0;">
            <div class="content">
                <h2 style="color:var(--text-hl); margin-top: 5px; border-bottom: 1px dashed rgba(var(--border-glow-rgb, 0, 255, 255), 0.2); padding-bottom:5px;">🔗 节点信息</h2>
                <div class="table-container">
                    <table class="peer-table">
                        <thead>
                            <tr>
                                <th>主机名 / IP</th>
                                <th>延迟</th>
                                <th>丢包率</th>
                                <th>协议</th>
                                <th>NAT</th>
                                <th>出站 / 入站</th>
                            </tr>
                        </thead>
                        <tbody id="peer-tbody">
                            <tr><td colspan="6" style="text-align:center; padding: 20px; color:#888;">WAITING FOR DATA...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Mouse tracking spotlight effect
        document.querySelectorAll('.interactive-box').forEach(box => {
            box.addEventListener('mousemove', e => {
                const rect = box.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                box.style.setProperty('--mouse-x', `${x}px`);
                box.style.setProperty('--mouse-y', `${y}px`);
            });
        });

        const ctx = document.getElementById('trafficChart').getContext('2d');
        const trafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '出站 (KB/s)',
                        data: [],
                        borderColor: '#0ff', // will be updated by theme
                        backgroundColor: 'rgba(0, 255, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        cubicInterpolationMode: 'monotone',
                        spanGaps: true,
                        clip: { left: 0, top: false, right: false, bottom: false }, // 仅在左侧裁剪，防止数据退出时溢出边界
                        pointRadius: 0,
                        pointHoverRadius: 6, // 鼠标悬浮时显示圆点
                        pointHitRadius: 15   // 扩大鼠标吸附范围
                    },
                    {
                        label: '入站 (KB/s)',
                        data: [],
                        borderColor: '#f0f', // will be updated by theme
                        backgroundColor: 'rgba(255, 0, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        cubicInterpolationMode: 'monotone',
                        spanGaps: true,
                        clip: { left: 0, top: false, right: false, bottom: false }, // 仅在左侧裁剪，防止数据退出时溢出边界
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHitRadius: 15
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: { right: 50, left: 0, top: 10, bottom: 5 } // 增加右侧padding防止边界溅出/闪烁
                },
                // 优化动画时间，既保留丝滑又减少因为长时间补间导致的重绘闪烁
                animation: { duration: 600, easing: 'linear' },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                        ticks: { color: '#888', maxRotation: 0, autoSkip: true, maxTicksLimit: 9 }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                        ticks: { color: '#888', maxTicksLimit: 8 },
                        beginAtZero: true,
                        min: 0,
                        suggestedMax: 10
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false, // 鼠标在一条垂直线上激活所有数据
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 20, 30, 0.95)',
                        titleColor: '#0ff',
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13, weight: 'bold' },
                        bodyColor: '#fff',
                        bodySpacing: 8,
                        padding: 12,
                        borderColor: 'rgba(0, 255, 255, 0.4)',
                        borderWidth: 1,
                        displayColors: true,
                        boxPadding: 4,
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${context.parsed.y} KB/s`;
                            }
                        }
                    }
                }
            }
        });

        // 为了响应主题切换，我们需要能够更新图表颜色
        function updateChartTheme(isDark) {
            trafficChart.data.datasets[0].borderColor = isDark ? '#0ff' : '#ff69b4';
            trafficChart.data.datasets[0].backgroundColor = isDark ? 'rgba(0, 255, 255, 0.1)' : 'rgba(255, 105, 180, 0.1)';

            trafficChart.data.datasets[1].borderColor = isDark ? '#f0f' : '#3eb489';
            trafficChart.data.datasets[1].backgroundColor = isDark ? 'rgba(255, 0, 255, 0.1)' : 'rgba(62, 180, 137, 0.1)';

            trafficChart.options.plugins.tooltip.backgroundColor = isDark ? 'rgba(15, 20, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)';
            trafficChart.options.plugins.tooltip.titleColor = isDark ? '#0ff' : '#e75480';
            trafficChart.options.plugins.tooltip.bodyColor = isDark ? '#fff' : '#664d54';
            trafficChart.options.plugins.tooltip.borderColor = isDark ? 'rgba(0, 255, 255, 0.4)' : 'rgba(255, 105, 180, 0.4)';
            trafficChart.update('none'); // Update without animation
        }

        const MAX_POINTS = 60;
        let lastTime = Date.now();
        let lastTx = -1;
        let lastRx = -1;

        function parseBytes(str) {
            if (!str || str === '-') return 0;
            const parts = str.trim().split(' ');
            if (parts.length !== 2) return parseFloat(str) || 0;
            const val = parseFloat(parts[0]);
            const unit = parts[1].toUpperCase();
            if (unit === 'B') return val;
            if (unit === 'KB') return val * 1024;
            if (unit === 'MB') return val * 1024 * 1024;
            if (unit === 'GB') return val * 1024 * 1024 * 1024;
            return val;
        }

        async function fetchInfo() {
            try {
                const res = await fetch('/api/info');
                const data = await res.json();
                
                const stateEl = document.getElementById('conn-state');
                const isDark = document.body.classList.contains('dark-mode');
                
                if (data.node && data.node.error) {
                    stateEl.textContent = 'SYS_ERR: RPC DOWN / EASYTIER OFFLINE';
                    stateEl.style.borderColor = isDark ? '#f0f' : '#ff69b4';
                    stateEl.style.color = isDark ? '#f0f' : '#ff69b4';
                    stateEl.style.background = isDark ? 'rgba(255,0,255,0.1)' : 'rgba(255,105,180,0.1)';
                    return;
                } else {
                    stateEl.textContent = 'SYS_OK: ACTIVE // SYNC: 3s';
                    stateEl.style.borderColor = isDark ? '#0ff' : '#ff69b4';
                    stateEl.style.color = isDark ? '#0ff' : '#e75480';
                    stateEl.style.background = isDark ? 'rgba(0,255,255,0.1)' : 'rgba(255,105,180,0.2)';
                }

                const node = data.node || {};
                let stunData = node.stun_info || {};
                let publicIp = (stunData.public_ip && stunData.public_ip.length > 0) ? stunData.public_ip[0] : 'N/A';
                
                
const peers = data.peer || [];
                let currentTxSum = 0;
                let currentRxSum = 0;

                let tbody = document.getElementById('peer-tbody');
                let newHtml = '';

                if (peers.length === 0) {
                    newHtml = '<tr><td colspan="6" style="text-align:center; padding: 20px; color:#888;">No peers connected</td></tr>';
                } else {
                    for (let p of peers) {
                        let rx = parseBytes(p.rx_bytes);
                        let tx = parseBytes(p.tx_bytes);
                        currentRxSum += rx;
                        currentTxSum += tx;
                    }

                    let rows = tbody.querySelectorAll('tr');
                    if (rows.length !== peers.length || rows[0].cells.length === 1) {
                        let newHtml = '';
                        for (let p of peers) {
                            newHtml += `<tr>
                                <td><span class="p-host" style="transition: color 0.3s"></span> <br> <span class="p-ip" style="color:var(--text-hl); font-size: 0.9em; transition: color 0.3s"></span></td>
                                <td style="color:var(--status-good-text)"><span class="p-lat" style="transition: color 0.3s"></span></td>
                                <td><span class="p-loss" style="transition: color 0.3s"></span></td>
                                <td><span class="p-proto" style="transition: color 0.3s"></span></td>
                                <td><span class="p-nat" style="transition: color 0.3s"></span></td>
                                <td><span class="p-tx" style="transition: color 0.3s"></span><br><span class="p-rx" style="color:var(--table-th); font-size: 0.9em; transition: color 0.3s"></span></td>
                            </tr>`;
                        }
                        tbody.innerHTML = newHtml;
                        rows = tbody.querySelectorAll('tr');
                    }

                    for (let i = 0; i < peers.length; i++) {
                        let p = peers[i];
                        let row = rows[i];
                        
                        let els = {
                            host: row.querySelector('.p-host'),
                            ip: row.querySelector('.p-ip'),
                            lat: row.querySelector('.p-lat'),
                            loss: row.querySelector('.p-loss'),
                            proto: row.querySelector('.p-proto'),
                            nat: row.querySelector('.p-nat'),
                            tx: row.querySelector('.p-tx'),
                            rx: row.querySelector('.p-rx')
                        };

                        if (els.host.innerText !== p.hostname) els.host.innerText = p.hostname;
                        if (els.ip.innerText !== p.ipv4) els.ip.innerText = p.ipv4;
                        if (els.lat.innerText !== p.lat_ms + ' ms') els.lat.innerText = p.lat_ms + ' ms';
                        if (els.loss.innerText !== p.loss_rate) els.loss.innerText = p.loss_rate;
                        if (els.proto.innerText !== p.tunnel_proto) els.proto.innerText = p.tunnel_proto;
                        if (els.nat.innerText !== p.nat_type) els.nat.innerText = p.nat_type;
                        if (els.tx.innerText !== p.tx_bytes) els.tx.innerText = p.tx_bytes;
                        if (els.rx.innerText !== p.rx_bytes) els.rx.innerText = p.rx_bytes;
                    }
                }

                let now = Date.now();
                let dt = (now - lastTime) / 1000;
                if (dt < 1) dt = 1;

                if (lastTime > 0 && lastTx !== -1 && lastRx !== -1) {
                    let txRate = Math.max(0, (currentTxSum - lastTx) / dt / 1024);
                    let rxRate = Math.max(0, (currentRxSum - lastRx) / dt / 1024);

                    let ts = new Date().toLocaleTimeString('en-US', {hour12:false});
                    trafficChart.data.labels.push(ts);
                    trafficChart.data.datasets[0].data.push(txRate.toFixed(2));
                    trafficChart.data.datasets[1].data.push(rxRate.toFixed(2));

                    let totalLen = trafficChart.data.labels.length;

                    // 为了实现真实的“向左走”滑动动画，保留数组并在 X 轴推移 min/max 视窗
                    if (totalLen > MAX_POINTS) {
                        trafficChart.options.scales.x.min = totalLen - MAX_POINTS;
                        trafficChart.options.scales.x.max = totalLen - 1;
                    }

                    // 当越出屏幕的旧历史数据累积过多时进行静默清理，防止内存泄漏（后台无感知）
                    if (totalLen > MAX_POINTS + 120) {
                        trafficChart.data.labels.splice(0, 120);
                        trafficChart.data.datasets[0].data.splice(0, 120);
                        trafficChart.data.datasets[1].data.splice(0, 120);
                        
                        let newLen = trafficChart.data.labels.length;
                        trafficChart.options.scales.x.min = newLen - MAX_POINTS;
                        trafficChart.options.scales.x.max = newLen - 1;
                        trafficChart.update('none'); // 静默吸附新坐标索引，避免此帧发生视觉跳变
                    } else {
                        // 触发正常的视窗右移平移动画
                        trafficChart.update();
                    }
                    
                    document.getElementById('legend-tx').innerText = txRate.toFixed(2) + ' KB/s';
                    document.getElementById('legend-rx').innerText = rxRate.toFixed(2) + ' KB/s';
                } else if (trafficChart.data.labels.length === 0) {
                    let ts = new Date().toLocaleTimeString('en-US', {hour12:false});
                    trafficChart.data.labels.push(ts);
                    trafficChart.data.datasets[0].data.push(0);
                    trafficChart.data.datasets[1].data.push(0);
                    trafficChart.update('none');
                    
                    document.getElementById('legend-tx').innerText = '0.00 KB/s';
                    document.getElementById('legend-rx').innerText = '0.00 KB/s';
                }

                lastTx = currentTxSum;
                lastRx = currentRxSum;
                lastTime = now;

            } catch (e) {
                console.error(e);
                const stateEl = document.getElementById('conn-state');
                const isDark = document.body.classList.contains('dark-mode');
                stateEl.textContent = 'SYS_ERR: BACKEND UNREACHABLE';
                stateEl.style.borderColor = isDark ? '#f0f' : '#ff69b4';
                stateEl.style.color = isDark ? '#f0f' : '#ff69b4';
                stateEl.style.background = isDark ? 'rgba(255,0,255,0.1)' : 'rgba(255,105,180,0.1)';
            }
        }

        function toggleTheme(event) {
            const root = document.documentElement;
            const body = document.body;
            const btn = document.getElementById('themeBtn');
            const isDark = !body.classList.contains('dark-mode');

            body.classList.remove('theme-switching');
            void body.offsetWidth;
            body.classList.add('theme-switching');
            setTimeout(() => body.classList.remove('theme-switching'), 500);
            
            if (isDark) {
                body.classList.add('dark-mode');
                body.classList.remove('light-mode');
                root.classList.add('dark-mode');
                if(btn) btn.textContent = '🌙';
            } else {
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                root.classList.remove('dark-mode');
                if(btn) btn.textContent = '☀️';
            }
            
            updateChartTheme(isDark);
        }
        
        // 自动检测时间切换主题，大于等于18点为深色模式
        function autoSetTheme() {
            const hour = new Date().getHours();
            const root = document.documentElement;
            const body = document.body;
            const btn = document.getElementById('themeBtn');
            const isDark = (hour >= 18 || hour < 6);
            
            if (isDark) {
                body.classList.add('dark-mode');
                body.classList.remove('light-mode');
                root.classList.add('dark-mode');
                if(btn) btn.textContent = '🌙';
            } else {
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                root.classList.remove('dark-mode');
                if(btn) btn.textContent = '☀️';
            }
            // 不要在这里立刻更新Chart，因为还没初始化完成
            setTimeout(() => { 
                if (typeof updateChartTheme === 'function' && typeof trafficChart !== 'undefined') {
                    updateChartTheme(isDark); 
                }
            }, 100);
        }
        
        // 页面加载时执行
        window.addEventListener('DOMContentLoaded', autoSetTheme);

        setInterval(fetchInfo, 1500);
        setTimeout(fetchInfo, 500);
    </script>
</body>
</html>
"""

class EasyTierAPIHandler(http.server.SimpleHTTPRequestHandler):
    _api_cache_lock = threading.Lock()
    _api_cache_data = None
    _api_cache_ts = 0.0

    def get_easytier_cli(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        
        return os.path.join(base_dir, "easytier", "easytier-cli.exe")

    def run_cli_cmd(self, cmd_name):
        cli_exe = self.get_easytier_cli()
        if not os.path.exists(cli_exe):
            return {"error": "找不到 easytier-cli.exe", "path": cli_exe}
            
        try:
            result = subprocess.run(
                [cli_exe, "-p", "127.0.0.1:15888", "-o", "json", cmd_name], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"result": result.stdout}
            else:
                return {"error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"error": f"{cmd_name} 请求超时"}
        except Exception as e:
            return {"error": str(e)}

    def get_api_info_cached(self):
        # 高频轮询接口使用短缓存，减少子进程压力和页面卡顿。
        now = time.time()
        with self._api_cache_lock:
            if self._api_cache_data is not None and (now - self._api_cache_ts) < 1.0:
                return self._api_cache_data

            data = {
                "node": self.run_cli_cmd("node"),
                "peer": self.run_cli_cmd("peer"),
                "route": self.run_cli_cmd("route")
            }
            self._api_cache_data = data
            self._api_cache_ts = now
            return data

    def do_GET(self):
        try:
        # 防外网访问控制（禁止非本机访问部分路由）
            client_ip = self.client_address[0]
            is_local = (client_ip == '127.0.0.1' or client_ip == 'localhost')

            if self.path == '/':
                if not is_local:
                    # 外网引导去外网专属页面
                    self.send_response(302)
                    self.send_header('Location', '/external')
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(HTML_PAGE.encode('utf-8'))
            
            elif self.path == '/external':
                # 外网专属页面
                # 检查是否启用 WebDL
                if not state.et_enable_webdl:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b"Download service is disabled.")
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(EXTERNAL_HTML_PAGE.encode('utf-8'))
            
            elif self.path == '/download/InterKnot':
                # 提供InterKnot压缩包下载
                # 检查是否启用 WebDL
                if not state.et_enable_webdl:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b"This Page is not accessible.")
                    return

                temp_dir = os.path.join(tempfile.gettempdir(), "InterKnot")
                file_path = os.path.join(temp_dir, "InterKnot.zip")
                log_path = os.path.join(temp_dir, "downloads.log")
                
                if os.path.exists(file_path):
                    # 文件存在，记录下载日志
                    try:
                        os.makedirs(temp_dir, exist_ok=True)
                        with open(log_path, 'a', encoding='utf-8') as log_file:
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            log_file.write(f"[{timestamp}] Download from {client_ip}\n")
                    except Exception as e:
                        print(f"Failed to write download log: {e}")
                    
                    # 提供文件下载
                    self.send_response(200)
                    self.send_header('Content-type', 'application/zip')
                    self.send_header('Content-Disposition', 'attachment; filename="InterKnot.zip"')
                    file_size = os.path.getsize(file_path)
                    self.send_header('Content-Length', str(file_size))
                    self.end_headers()
                    import shutil
                    with open(file_path, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                else:
                    # 文件不存在，触发生成
                    try:
                        # 调用 main_window 的 share_zip 方法生成文件
                        if hasattr(self.server, 'main_window') and hasattr(self.server.main_window, 'share_zip'):
                            self.server.main_window.share_zip()
                        
                        # 返回 202 Accepted，告诉前端正在准备
                        self.send_response(202)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.end_headers()
                        
                        # 获取准备文件的进度
                        progress = getattr(self.server.main_window, 'zip_progress', 0) if hasattr(self.server, 'main_window') else 0
                        progress_text = f"正在打包文件 ({progress:.1f}%)" if progress > 0 else "文件正在准备中，请稍候..."
                        
                        response = {"status": "preparing", "message": progress_text, "progress": progress}
                        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return
                    except Exception as e:
                        print(f"Failed to trigger share_zip: {e}")
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.end_headers()
                        response = {"status": "error", "message": "文件生成失败"}
                        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return
                
                self.send_response(404)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"File not found.")
            
            elif self.path == '/chart.js':
                try:
                    from modules.chart_js import CHART_JS_CODE
                except ImportError:
                    from chart_js import CHART_JS_CODE
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript; charset=utf-8')
                self.send_header('Cache-Control', 'max-age=31536000')
                self.end_headers()
                self.wfile.write(CHART_JS_CODE.encode('utf-8'))
            
            elif self.path == '/api/info':
                if not is_local:
                    # 拒绝外网请求API
                    self.send_response(403)
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                data = self.get_api_info_cached()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            
            else:
                self.send_response(404)
                self.end_headers()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            # 浏览器中止请求时避免抛出噪音异常
            pass
            
    # Suppress log messages to stdout
    def log_message(self, format, *args):
        pass

def start_webui_server(main_window):
    global _webui_httpd
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.ThreadingTCPServer(("", PORT), EasyTierAPIHandler)
        httpd.daemon_threads = True
        httpd.main_window = main_window  # 将 main_window 传递给 handler
        with _webui_httpd_lock:
            _webui_httpd = httpd
        print(f"\nWebUI started at http://localhost:{PORT}")
        main_window.update_list(f"WebUI started at http://localhost:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Failed to start WebUI on port {PORT}: {e}")
        main_window.update_list(f"Failed to start WebUI on port {PORT}: {e}")
    finally:
        with _webui_httpd_lock:
            _webui_httpd = None
        state.webui_thread = None

def stop_webui_server():
    global _webui_httpd
    with _webui_httpd_lock:
        httpd = _webui_httpd
        _webui_httpd = None

    if httpd is None:
        return

    try:
        httpd.shutdown()
    except Exception:
        pass

    try:
        httpd.server_close()
    except Exception:
        pass

    state.webui_thread = None

class WebUIThread(QThread):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    def run(self):
        start_webui_server(self.main_window)
        