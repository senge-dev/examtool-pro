# ExamTool Pro使用技巧
## 从github克隆插件
```bash
git clone https://github.com/senge-studio/examtool-pro.git
```
## 安装扩展
- wxpython python图形化扩展
- pyperclip 实现剪贴板复制粘贴
- pypubsub 防止程序假死
安装以下插件以后，请直接运行`python examtool-pro,git`
## 兼容的操作系统
支持的操作系统如下
- Windows XP或更新的版本
- macOS
- Linux
> 注意：
> 本程序已经完美支持Linux系统，在Windows或macOS上理论可以运行，但是兼容性未测试
## 使用方法
1. 新建json文档，多选题请以列表的形式保存，标准格式见`example.json`
2. 运行后输入文件路径并读取，如需实时检测剪贴板请点击`启用自动搜题模式`
3. 如需恢复初始设置，请点击清除按钮
4. 如果搜索到多个答案，请在文本框中查看其他的答案
