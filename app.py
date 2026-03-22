#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple File Browser - Preview configuration files on web
Display directory structure like GitHub, click to view file content
"""

import os
from flask import Flask, render_template_string, jsonify, send_file
import markdown

app = Flask(__name__)

# 根目录展示
BASE_DIR = "/root/.openclaw/workspace"

def get_directory_structure(path):
    """Recursively get directory structure"""
    items = []
    try:
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                items.append({
                    "name": entry,
                    "type": "dir",
                    "children": get_directory_structure(full_path)
                })
            else:
                ext = os.path.splitext(entry)[1].lower()
                items.append({
                    "name": entry,
                    "type": "file",
                    "ext": ext[1:] if ext else "",
                    "path": full_path
                })
    except PermissionError:
        pass
    return items

def get_file_content(path):
    """Read file content, return text or indicate binary"""
    # 二进制后缀
    binary_exts = {'.pyc', '.git', '.DS_Store', '.zip', '.tar', '.gz', '.bin', 
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.pdf', 
                '.doc', '.docx', '.xls', '.xlsx'}
    
    ext = os.path.splitext(path)[1].lower()
    if ext in binary_exts:
        return None, "binary"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read(), "text"
    except UnicodeDecodeError:
        return None, "binary"
    except Exception as e:
        return None, f"error: {str(e)}"

HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workspace File Browser</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f6f8fa;
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 300px;
            background-color: #ffffff;
            border-right: 1px solid #e1e4e8;
            overflow-y: auto;
            padding: 10px;
        }
        .main {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .directory {
            margin-left: 10px;
        }
        .item {
            padding: 4px 8px;
            cursor: pointer;
            border-radius: 3px;
            user-select: none;
        }
        .item:hover {
            background-color: #f1f3f4;
        }
        .item.dir {
            font-weight: 600;
        }
        .item.file {
            color: #0969da;
        }
        .item.file:hover {
            background-color: #ddf4ff;
        }
        .icon {
            display: inline-block;
            width: 18px;
            text-align: center;
            color: #656d76;
        }
        .file-content {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            overflow-x: auto;
        }
        .file-header {
            background-color: #f6f8fa;
            border-bottom: 1px solid #e1e4e8;
            padding: 10px 15px;
            font-weight: 600;
            color: #24292f;
        }
        .file-body {
            padding: 15px;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        /* GitHub-like syntax highlighting */
        .hljs {
            display: block;
            overflow-x: auto;
            padding: 0;
        }
        .hljs-comment {
            color: #6e7781;
        }
        .hljs-keyword {
            color: #cf222e;
        }
        .hljs-string {
            color: #0a3069;
        }
        .hljs-number {
            color: #116329;
        }
        .hljs-function {
            color: #8250df;
        }
        .hljs-title {
            color: #6f42c1;
        }
        .hljs-params {
            color: #24292f;
        }
        .empty {
            padding: 40px;
            text-align: center;
            color: #656d76;
        }
        .current-path {
            padding: 10px;
            background-color: #ffffff;
            border-bottom: 1px solid #e1e4e8;
            margin-bottom: 10px;
        }
        .folder-open > .children {
            display: block;
        }
        .folder-closed > .children {
            display: none;
        }
        .arrow {
            display: inline-block;
            transition: transform 0.2s;
        }
        .folder-open .arrow {
            transform: rotate(90deg);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="padding: 10px 0; border-bottom: 1px solid #eee;">📁 Workspace</h3>
        <div id="tree"></div>
    </div>
    <div class="main">
        <div id="file-content" class="empty">
            👈 点击左侧文件预览内容
        </div>
    </div>

<script>
const baseDir = "{{ base_dir }}";

function renderTree(items, parent) {
    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.paddingLeft = '0';
    
    items.forEach(item => {
        const li = document.createElement('li');
        li.className = 'item ' + item.type;
        
        if (item.type === 'dir') {
            const arrow = document.createElement('span');
            arrow.className = 'arrow icon';
            arrow.textContent = '▶';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = ' 📁 ' + item.name;
            
            li.appendChild(arrow);
            li.appendChild(nameSpan);
            
            const childrenUl = document.createElement('div');
            childrenUl.className = 'children directory folder-closed';
            renderTree(item.children, childrenUl);
            li.appendChild(childrenUl);
            
            li.onclick = function(e) {
                e.stopPropagation();
                childrenUl.classList.toggle('folder-open');
                childrenUl.classList.toggle('folder-closed');
                arrow.parentElement.classList.toggle('folder-open');
                arrow.parentElement.classList.toggle('folder-closed');
            };
        } else {
            const icon = getFileIcon(item.ext);
            const nameSpan = document.createElement('span');
            nameSpan.textContent = ' ' + icon + ' ' + item.name;
            li.appendChild(nameSpan);
            
            li.onclick = function(e) {
                e.stopPropagation();
                loadFile(item.path);
            };
        }
        
        ul.appendChild(li);
    });
    
    parent.appendChild(ul);
}

function getFileIcon(ext) {
    const icons = {
        'md': '📝', 'markdown': '📝',
        'py': '🐍', 'python': '🐍',
        'js': '📜', 'javascript': '📜',
        'html': '🌐', 'htm': '🌐',
        'css': '🎨',
        'json': '📊',
        'txt': '📄',
        'gitignore': '📇',
        'md': '📝',
        'sh': '⚙️', 'bash': '⚙️',
        'zip': '🗜️', 'tar': '🗜️', 'gz': '🗜️',
        'jpg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'jpeg': '🖼️',
        'pdf': '📕',
        'doc': '📘', 'docx': '📘',
        'xls': '📗', 'xlsx': '📗',
    };
    return icons[ext] || '📄';
}

function loadFile(path) {
    fetch('/api/file?path=' + encodeURIComponent(path)).then(resp => resp.json()).then(data => {
        const main = document.getElementById('file-content');
        main.innerHTML = '';
        
        if (data.error) {
            main.innerHTML = `<div class="empty">❌ ${data.error}</div>`;
            return;
        }
        
        if (data.type === 'binary') {
            main.innerHTML = `<div class="empty">📦 Binary file, cannot preview</div>`;
            return;
        }
        
        const container = document.createElement('div');
        container.className = 'file-content';
        
        const header = document.createElement('div');
        header.className = 'file-header';
        header.textContent = path;
        container.appendChild(header);
        
        const body = document.createElement('div');
        body.className = 'file-body';
        
        if (path.endsWith('.md')) {
            // markdown rendered as html
            const div = document.createElement('div');
            div.innerHTML = data.content_html;
            body.appendChild(div);
        } else {
            // code with pre
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.className = 'hljs';
            code.textContent = data.content;
            pre.appendChild(code);
            body.appendChild(pre);
        }
        
        container.appendChild(body);
        main.appendChild(container);
    });
}

// Initial load
fetch('/api/tree').then(resp => resp.json()).then(data => {
    const tree = document.getElementById('tree');
    renderTree(data, tree);
});
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, base_dir=BASE_DIR)

@app.route('/api/tree')
def tree():
    structure = get_directory_structure(BASE_DIR)
    return jsonify(structure)

@app.route('/api/file')
def file():
    path = request.args.get('path', '')
    if not path.startswith(BASE_DIR):
        return jsonify({"error": "Access denied"})
    
    if not os.path.exists(path):
        return jsonify({"error": "File not found"})
    
    if os.path.isdir(path):
        return jsonify({"error": "This is a directory, click to expand in left sidebar"})
    
    content, type = get_file_content(path)
    
    if type == "binary":
        return jsonify({"error": "Binary file, preview not available", "type": "binary"})
    
    if type == "error":
        return jsonify({"error": content, "type": "error"})
    
    # markdown 转 html
    if path.lower().endswith('.md'):
        content_html = markdown.markdown(content)
        return jsonify({
            "content": content, 
            "content_html": content_html, 
            "type": "text", 
            "path": path
        })
    
    return jsonify({
        "content": content, 
        "type": "text", 
        "path": path
    })

if __name__ == '__main__':
    print("🚀 Workspace File Browser starting...")
    print("📝 Open: http://127.0.0.1:5000")
    print(f"📂 Base directory: {BASE_DIR}")
    app.run(host='0.0.0.0', port=5000, debug=False)
