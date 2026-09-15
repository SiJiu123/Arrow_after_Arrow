# 一箭又一箭

使用 Python 和 Pygame 编写的单格箭头点击解谜游戏。玩家需要判断箭头前方是否还有其他箭头，并按合适的顺序让所有箭头飞出棋盘。

## 实机演示

以下 GIF 来自本人录制的游戏过程，展示三关操作与页面切换。

![三关游戏演示](assets/videos/game-demo-full.gif)

## 功能

- 开始、游戏、通关和失败界面
- 上、下、左、右四种方向
- 同行或同列的路径阻挡检测
- 飞出动画、碰撞变色与晃动反馈
- 支持连续点击，多支箭头可以同时播放飞出动画
- 碰撞期间移走阻挡物后，可立即重新点击原箭头
- 每关 3 次失误机会和随时重新开始
- 3 个固定关卡，全部经过自动求解验证

## 开发环境

- Python 3.10 或更高版本
- pygame-ce 2.5.6

已验证环境：Windows、Python 3.12.14。当前中文字体优先读取 Windows 系统字体；其他系统的中文显示和小屏幕缩放尚未验证。

项目不使用外部图片、音效或商业游戏素材，箭头和界面均由程序绘制。

## 安装与运行

下载仓库 ZIP 并解压，或使用 Git 获取项目：

```bash
git clone https://github.com/SiJiu123/Arrow_after_Arrow.git
cd Arrow_after_Arrow
```

在项目目录打开终端，依次执行：

```bash
python -m pip install -r requirements.txt
python app.py
```

如果电脑上使用的是 `py` 启动器，也可以把上述命令中的 `python` 换成 `py`。

## 游戏操作

1. 点击“开始游戏”进入第一关。
2. 点击一支箭头。如果它前进方向直到棋盘边界都没有其他箭头，它会飞出并消失。
3. 如果前方存在其他箭头，它会变红并晃动，同时扣除一次失误机会。
4. 清除全部箭头后进入下一关；失误机会耗尽后可以重新挑战。
5. 游戏中可随时点击“重新开始”，恢复本关布局和 3 次失误机会。

## 游戏截图

<details>
<summary>展开查看开始、游戏、通关与失败界面</summary>

以下为程序生成的界面演示截图。

![开始界面](assets/screenshots/start-screen.png)

![游戏界面](assets/screenshots/game-screen.png)

![全部通关界面](assets/screenshots/complete-screen.png)

![失败界面](assets/screenshots/failed-screen.png)

</details>

## 测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖作业要求中的 T01—T06、四方向路径判断、最近阻挡物识别，以及三个关卡的完整求解。

保存带时间戳的测试结果与各关通关坐标：`python scripts/check_project.py`。
结果见 [测试报告](docs/TEST_REPORT.md) 和 [自动验证结果](docs/evidence/verification.json)。

## 开发与作业材料

- [作业博客](docs/BLOG_DRAFT.md)：项目介绍、实现思路、AIGC 使用、测试、PSP 与心得。
- [AIGC 开发记录](docs/DEVELOPMENT_LOG.md)
- [优化记录](docs/OPTIMIZATION_LOG.md)
- [测试报告](docs/TEST_REPORT.md)
- [作业检查清单](docs/SUBMISSION_CHECKLIST.md)

## 项目结构

```text
app.py                    Pygame 界面、点击与动画
game_core.py              路径检测和游戏状态
levels.py                 三个固定关卡及可解性检查
theme.py                  集中的配色和尺寸配置
tests/                    规则、求解器与界面流程测试
assets/screenshots/       界面截图
assets/videos/            实机演示 GIF
docs/DEVELOPMENT_LOG.md   AIGC 协作和阶段计时记录
docs/DESIGN.md            界面与交互设计说明
```
