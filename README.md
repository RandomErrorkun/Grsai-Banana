# Grsai Banana Image Generator

一个基于 PySide6 和 Fluent-Widgets 构建的 Windows 桌面客户端，专为国产中转网站 [Grsai](https://grsai.com/zh/) 的 `Banana` 图像生成模型设计。

![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202512121249034.png)

## ✨ 功能特性

- **现代化 UI**: 采用 Windows 11 风格的 Fluent Design 界面。
- **多图参考**: 支持拖拽/粘贴最多 13 张参考图片进行生成。
- **参数调整**: 
  - 模型选择 (nano-banana, nano-banana-fast, nano-banana-pro, nano-banana-pro-vt)
  - 宽高比 (1:1, 16:9, 9:16 等多种比例)
  - 图片尺寸 (1K, 2K, 4K)
- **历史记录**: 
![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202512121249482.png)
  - 本地保存生成记录。
  - 支持分页浏览。
  - **一键重绘**: 可以直接从历史记录中恢复参数和参考图重新生成。
- **便捷操作**:
  - 支持剪贴板粘贴图片 (Ctrl+V)。
  - 拖拽上传。
  - 自动保存生成的图片到本地。

## 🛠️ 安装与运行

### Windows 用户 (推荐)
直接前往 [GitHub Releases](https://github.com/Moeary/Grsai-Banana/releases) 下载最新的 `.exe` 安装包，解压即用，无需配置 Python 环境。

### 开发者 / 其他系统用户
本项目使用 `pixi` 进行环境管理，确保开发环境的一致性。

1. **安装 Pixi**
   请参考 [Pixi 官方文档](https://pixi.sh/) 安装。

2. **克隆仓库**
   ```bash
   git clone https://github.com/Moeary/Grsai-Banana.git
   cd Grsai-Banana
   ```

3. **运行项目**
   Pixi 会自动下载并配置所需的 Python 环境和依赖：
   ```bash
   pixi run start
   ```

4. **打包 (可选)**
   如果你想自己编译 exe 文件：
   ```bash
   pixi run build
   ```
   编译产物将位于 `dist/` 目录下。

## ⚙️ 配置
首次运行后会在根目录生成 `config.json`，你可以在设置页面或直接修改文件来配置 API Key。
![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202512121250479.png)
## 📝 目录结构
- `ui/`: 界面代码 (主窗口, 生成页, 历史页, 设置页)
- `core/`: 核心逻辑 (API 客户端, 历史记录管理, 配置管理)
- `assets/`: 资源文件
- `main.py`: 程序入口

---
*本项目非 Grsai 官方客户端，仅供学习交流使用。*

## 更新记录

- 2025-12-15: 添加"nano-banana-pro-vt"模型支持
- 2025-12-15: 修改了生成页面的UI，加长了Prompt窗口，加宽了左边面板，减小了Prompt窗口的字体
- 2025-12-15: 添加了修改程序主题色的入口并修改了主题色
- 2025-12-16: 添加了可以收缩/展开生成页面中预览窗口的按钮（收缩会导致窗口变窄，会影响其他页面的显示，手动将窗口拉宽或者展开后在前往其他页面即可）
- 2025-12-17: 添加了对Grsai中GPT Image的支持; 让目前所在子页面的名称会显示在窗口的标题栏了