# Grsai Banana Image Generator

一个基于 PySide6 和 Fluent-Widgets 构建的 Windows 桌面客户端，专为国产中转网站 [Grsai](https://grsai.com/zh/) 的生成模型设计。支持图像生成（Banana 系列、GPT Image 系列）、视频生成（minimax-h3）、漫画分页生成、历史记录管理和本地配置保存。

![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202512192008692.png)

## 核心功能

### 图像生成

- 多模型支持:
  - Banana 系列：`nano-banana`、`nano-banana-fast`、`nano-banana-2`、`nano-banana-2.1`、`nano-banana-2-lite`、`nano-banana-2-cl / -2k-cl / -4k-cl`、`nano-banana-pro`、`nano-banana-pro-vt / -cl / -vip / -4k-vip`
  - GPT Image 系列：`gpt-image-2`、`gpt-image-2-vip`、`gpt-image-2.5`、`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst`
- 参数灵活配置:
  - Banana 系列支持 1K / 2K / 4K 分辨率与宽高比选择（1:1、16:9、9:16、4:3、3:4、3:2、2:3、5:4、4:5、21:9 等）；`nano-banana-2` 系列额外支持 1:4、4:1、1:8、8:1 超宽比例
  - GPT Image 支持多种宽高比；vip 系模型按「宽高比 + 1K/2K/4K 档位」自动换算官方像素参考值
  - `gpt-image-2.5-flare / -sunburst` 支持质量参数（low / medium / high / xhigh / max）
  - vip 系模型支持透明背景开关
- 每个模型选项卡记忆上次选择的模型与参数
- 多图参考:
  - 支持拖拽、点击选择、Ctrl+V 粘贴参考图片
  - 图像生成最多支持 14 张参考图片

### 视频生成

- `minimax-h3` 模型，独立「视频」页面，交互与图像生成页一致
- 画面比例：portrait（竖屏）/ landscape（横屏）/ square（方屏）
- 分辨率：480p / 768p / 1080p（1080p 下最长 10 秒）
- 时长 1–15 秒；支持随机种子，留空自动生成，重试 / 重新生成复用同一种子
- 参考图最多 9 张，参考音频最多 3 个（mp3 / wav / m4a / aac / flac / ogg）
- 参考音频自动探测时长，支持本地试听（播放 / 暂停 / 停止）
- 视频任务完成后点击任务卡片即可调用系统播放器播放

### 漫画功能

- 使用剧情模型（gemini 系列）自动规划漫画分页脚本
- 支持项目保存、项目读取和分页内容继续编辑
- 每页可单独生成，也可以一键生成全部页面
- 出图模型支持 Banana 系列和 GPT Image 系列全部模型（vip 系按档位换算像素值）
- 支持多张人物参考图，并可为每页指定参考图序号，减少角色混淆
- 生成结果会按项目保存到本地页面目录

### 任务管理

- 实时任务列表，展示任务状态和进度
- 支持手动重试和失败自动重试，可配置最大重试次数
- 支持并行任务处理（图像 / 漫画 / 视频并行数独立配置）
- GPT Image 多变体改为提交多个独立任务，可并行执行、可单独重试
- VIP 模型的违规（violation）失败自动重试可在设置中单独控制

### 历史记录

- 使用本地 SQLite 数据库保存生成记录，旧版 JSON 历史自动迁移
- 支持分页浏览，可配置每页显示数量
- 支持从历史记录恢复参数并重新生成
- 视频任务记录时长、随机种子与参考音频，缩略图带视频标识，点击直接播放
- 支持打开生成文件所在文件夹
- 提供历史数据库清理功能:
  - 清理运行中任务，适合程序异常关闭后清除卡在 running 的记录
  - 清理失败任务
  - 清理违规（violation）任务
  - 清空全部历史记录，清空前需要二次确认

### 高级设置

- API Base URL 和 API Key 配置
- 输出文件夹配置
- 最大重试次数配置
- 历史记录每页数量配置
- 界面语言支持 English / 简体中文
- 文本格式化:
  - 字体大小调整
  - 字体选择
  - 自动换行支持
- 主题支持:
  - 亮色模式
  - 深色模式
  - 自动跟随系统
  - 右下角一键切换主题

## 安装与运行

### Windows 用户

直接前往 [GitHub Releases](https://github.com/RandomErrorkun/Grsai-Banana/releases) 下载最新的 exe 程序，双击即用，无需配置 Python 环境。推送 `v*` 标签后 CI 会自动构建 Windows exe 与 Linux RPM 并发布到 Release。

### 开发者 / 其他系统用户

本项目使用 `pixi` 进行环境管理，确保开发环境一致。

1. 安装 Pixi

   请参考 [Pixi 官方文档](https://pixi.sh/) 安装。

2. 克隆仓库

   ```bash
   git clone https://github.com/RandomErrorkun/Grsai-Banana.git
   cd Grsai-Banana
   ```

3. 运行项目

   Pixi 会自动下载并配置所需的 Python 环境和依赖：

   ```bash
   pixi run start    # pythonw 启动，无控制台窗口
   pixi run debug    # python 启动，保留控制台便于看日志
   ```

4. 打包

   如果你想自己编译 exe 文件：

   ```bash
   pixi run build
   ```

   使用 Nuitka 编译为单文件 exe，产物位于 `dist/` 目录下。

## 配置说明

首次运行后会在根目录生成 `grsai_config.json`。推荐在应用内的 Settings 页面修改配置：

- API Base URL 和 API Key
- 最大重试次数
- VIP 违规失败自动重试
- 历史记录每页显示数量
- 图像 / 漫画 / 视频并行任务数
- 文本格式化选项
- 输出文件夹位置
- 界面语言

如果需要，也可以直接编辑 `grsai_config.json`。注意该文件包含你的 API Key，已默认被 `.gitignore` 排除，请勿手动提交或外传。

## 项目结构

```text
Grsai-Banana/
├── ui/                          # 用户界面
│   ├── main_window.py           # 主窗口
│   ├── generator_page.py        # 图像生成页面
│   ├── video_page.py            # 视频生成页面
│   ├── comic_page.py            # 漫画生成页面
│   ├── history_page.py          # 历史记录页面
│   ├── settings_page.py         # 设置页面
│   └── components/              # UI 组件
│       ├── prompt_widget.py     # 提示词输入框
│       ├── image_drop_area.py   # 图片拖拽区域
│       ├── audio_drop_area.py   # 参考音频区域（视频页）
│       └── task_widget.py       # 任务卡片和任务列表
├── core/                        # 核心逻辑
│   ├── api_client.py            # API 调用客户端（官方统一接口）
│   ├── task_manager.py          # 任务管理和并行处理
│   ├── history_manager.py       # SQLite 历史记录管理
│   ├── comic_planner.py         # 漫画分页规划
│   ├── comic_project_manager.py # 漫画项目保存和读取
│   ├── model_catalog.py         # 模型目录与参数表
│   ├── i18n.py                  # 多语言文案
│   └── config.py                # 配置管理
├── export_history.py            # 历史记录导出工具（导出为 TSV）
├── output/                      # 生成结果输出目录（运行后生成）
├── main.py                      # 程序入口
├── grsai_config.json            # 配置文件（含 API Key，不入库）
├── grsai_history.db             # SQLite 历史记录数据库（不入库）
├── pixi.toml                    # Pixi 环境与任务配置
└── requirements.txt             # pip 依赖列表
```

## 快速开始

1. 设置 API Key

   打开设置页面，输入你的 Grsai API Base URL 和 API Key，然后点击 Save Settings。

2. 选择模型和参数

   图像生成页可在 Banana / GPT Image 选项卡间切换；视频页选择比例、分辨率和时长；漫画页可分别选择剧情模型和出图模型。

3. 上传参考素材

   拖拽图片到参考图区域，或使用 Ctrl+V 从剪贴板粘贴；视频页可额外添加参考音频。

4. 输入提示词或故事需求

   图像 / 视频生成输入 Prompt；漫画生成输入故事需求和可选的风格补充。

5. 生成并查看结果

   点击生成按钮后在任务列表查看进度；图像在输出目录查看，视频点击任务卡片播放。

6. 查看历史记录

   生成完成后可在 History 页面查看详情、打开文件夹或恢复参数重新生成。

## 使用技巧

- 普通生成适合单图快速出图，漫画页面适合连续分页和项目化保存
- `nano-banana-2` 系列才支持 1:4、4:1、1:8、8:1 超宽比例，其他 Banana 模型使用常规比例
- vip 系 GPT 模型不直接接受宽高比，程序会按「比例 + 1K/2K/4K 档位」自动换算官方像素值
- 如果生成失败，可以点击任务卡片上的重试按钮，或开启失败自动重试
- 批量生成时可以调高对应页面的并行任务数
- 视频生成想固定风格时填入同一个随机种子，配合相同参考图可复现相近结果
- 在历史页面点击 Regenerate 可以恢复提示词、模型、参数和参考素材

## 主题系统

支持亮色模式、深色模式和跟随系统。可以在应用右下角点击切换按钮快速切换主题，偏好会自动保存。

![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202512192004573.png)

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目采用 MIT 许可证，基于 [Moeary/Grsai-Banana](https://github.com/Moeary/Grsai-Banana) 二次开发，感谢原作者。

---

本项目非 Grsai 官方客户端，仅供学习交流使用。
