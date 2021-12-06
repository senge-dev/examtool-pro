import getpass  # 获取用户名
import pyperclip  # 剪贴板复制
import wx  # GUI支持
from threading import Thread  # GUI界面防假死、实时检测剪贴板
from pubsub import pub  # GUI界面内容转发
import json  # 文件内容格式化
import platform  # 确保软件兼容Windows、macOS和Linux

file_data = ''  # 全局变量存储题库内容


# 核心代码，查找题目
def topic_search(tp):
    # 读取文件目录
    global file_data
    success = False
    # 尝试读取文件
    topic = file_data
    # 清空结果
    result = ''
    for item in topic:
        # 如果在题目中找到结果
        if tp in str(item['question']) or tp in str(item['answer']):
            question = item['question']
            answer = item['answer']
            # 判断答案是否为列表
            if isinstance(answer, list):
                result += f'问题：{question}\n答案：'
                count = 0
                for ans in answer:
                    count += 1
                    result += f'{count}. {ans}\n'
                result += '\n'
            else:
                result += f'问题：{question}\n答案：{answer}\n\n'
            success = True
    # 无法搜到题目时返回的结果
    if not success:
        result = '题目搜索失败，如果需要添加题目，您可以将题目和答案填写到json文件中，多选题请用列表的形式保存。'
    # 将搜题结果返回
    return result


# 使用多线程实现实时检测剪贴板，防止程序假死
class TpSearchThread(Thread):
    def __init__(self):
        # 线程实例化时立即启动
        Thread.__init__(self)
        self.start()

    def run(self):
        # 线程执行的代码
        pyperclip.copy('1')
        clipboard = '1'
        # 使用死循环来不停的检测剪贴板的内容
        while True:
            new_cb = pyperclip.paste()
            # 使用剪贴板内容终止线程
            if pyperclip.paste() == 'exit':
                break
            if new_cb != clipboard:
                clipboard = new_cb
                result = topic_search(tp=clipboard)
                # 将检测的结果发送到程序的文本框中
                wx.CallAfter(pub.sendMessage, 'update', msg=result)


# 主界面
class ExamToolPro(wx.Frame):
    def __init__(self, parent, uid):
        title = f"ExamToolPro for {'macOS' if platform.system() == 'Darwin' else platform.system()}"
        wx.Frame.__init__(self, parent, uid, title, pos=wx.DefaultPosition, size=(640, 480),
                          style=wx.STAY_ON_TOP | wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)  # 禁止改变窗口大小，同时置顶窗口
        panel = wx.Panel(self)
        # 设置程序图标
        self.icon = wx.Icon('search.png', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.Center()  # 程序居中
        # 添加按钮和输入框等元素
        self.file = wx.StaticText(panel, pos=(20, 20), label='文件')
        self.file_input = wx.TextCtrl(panel, pos=(60, 20), size=(450, 25), style=wx.TE_READONLY)
        self.file_load = wx.Button(panel, pos=(530, 20), size=(90, 25), label='读取文件')
        self.topic = wx.StaticText(panel, pos=(20, 50), label='题目')
        self.tp_input = wx.TextCtrl(panel, pos=(60, 50), size=(305, 25))
        self.search = wx.Button(panel, pos=(385, 50), size=(90, 25), label='搜索')
        self.cb_setting = wx.CheckBox(panel, -1, '启用自动搜题模式', pos=(490, 50))
        self.answer = wx.StaticText(panel, pos=(20, 80), label='搜题结果')
        self.ans_box = wx.TextCtrl(panel, pos=(20, 100), size=(600, 320), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tp_edit = wx.Button(panel, pos=(310, 435), size=(90, 25), label='题库编辑')
        self.tp_edit.Bind(wx.EVT_BUTTON, self.tps_edit)
        self.help = wx.Button(panel, pos=(420, 435), size=(90, 25), label='帮助')
        self.clear = wx.Button(panel, pos=(530, 435), size=(90, 25), label='清除')
        self.cb_setting.Bind(wx.EVT_CHECKBOX, self.cb_switch)
        self.status = wx.StaticText(panel, pos=(20, 435), label='请先导入文件')
        # 禁用按钮
        self.tp_input.Disable()
        self.search.Disable()
        self.cb_setting.Disable()
        # 从类外获取输入框的内容
        pub.subscribe(self.update_display, 'update')
        # 绑定事件
        self.file_load.Bind(wx.EVT_BUTTON, self.file_loading)
        self.clear.Bind(wx.EVT_BUTTON, self.clear_message)  # 清除
        self.Bind(wx.EVT_CLOSE, self.exit_app)  # 关闭程序，防止程序因为线程启动而无法关闭
        self.search.Bind(wx.EVT_BUTTON, self.tp_search)  # 搜索按钮
        self.help.Bind(wx.EVT_BUTTON, self.how_to_use)  # 帮助按钮

    def tps_edit(self, event):
        wx.MessageBox(message='题库编辑功能正在开发中')

    def file_loading(self, event):
        default_dir = ''
        if platform.system() == 'Windows':
            default_dir = f'C:/Users/{getpass.getuser()}'
        elif platform.system() == 'Darwin':
            default_dir = f'/Users/{getpass.getuser()}'
        elif platform.system() == 'Linux':
            default_dir = f'/home/{getpass.getuser()}'
        else:
            print(f'该软件不支持{platform.system()}')
            exit(1)
        file_dialog = wx.FileDialog(
            self,
            message=f"读取题库，ExamToolPro for {'macOS' if platform.system() == 'Darwin' else platform.system()}",
            defaultDir=default_dir,
            wildcard='题库(*.json)|*.json|所有文件(*.*)|*.*'
        )
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetPath()
            self.file_input.SetValue(filename)
            try:
                with open(filename, 'r') as file:
                    global file_data
                    file_data = json.loads(file.read())
            except FileNotFoundError:
                wx.MessageBox(message=f'错误：文件”{filename}“不存在！')
            except UnicodeDecodeError:
                wx.MessageBox(message=f'错误：文件”{filename}“解码失败！')
            except json.decoder.JSONDecodeError:
                wx.MessageBox(message=f'错误：文件”{filename}“不是标准的Json文件！')
            except PermissionError:
                wx.MessageBox(message=f'错误：文件“{filename}”无访问权限')
            except Exception as e:
                wx.MessageBox(message=f'错误：未知的错误，错误代码“{e}”')
            else:
                try:
                    # 逐一检测题库是否有错误
                    for item in file_data:
                        a = item['question']
                        b = item['answer']
                except Exception:
                    wx.MessageBox(f'错误：文件“{filename}”不符合要求！')
                else:
                    self.tp_input.Enable()
                    self.search.Enable()
                    self.cb_setting.Enable()
                    self.file_input.Disable()
                    self.file_load.Disable()
                    self.status.SetLabel('手动搜题模式')
        else:
            wx.MessageBox('请至少选择一个文件')
        file_dialog.Destroy()

    # 帮助内容
    def how_to_use(self, event):
        author = '森哥'
        open_source_license = 'GPL v3'
        email = 'a1356872768@gmail.com'
        introduction = '基于Python 3.9开发的开源搜题软件，支持剪贴板一键复制和手动搜题功能'
        attention = '本软件采用GPL v3协议开源，可以自行修改源代码进行二次发布，但是二次发布' \
                    '的代码必须开源并注明原作者，如因使用本APP而产生的一切问题，作者不承担任何责任'
        usage = '请使用json文件保存题库，文件格式如下：\n' \
                '[{"question": "问题", "answer": "答案"},\n' \
                ' {"question": "问题", "answer": ["答案1", "答案2", "答案3"]}...]'
        hint = f'作者：{author}\n许可证：{open_source_license}\n邮箱：{email}' \
               f'\n介绍：{introduction}\n注意：{attention}\n如何使用：{usage} '
        self.ans_box.SetValue(hint)

    # 手动搜索按钮
    def tp_search(self, event):
        tp = self.tp_input.GetValue()
        if tp == '':
            self.ans_box.SetValue('题目不能为空！')
        else:
            result = topic_search(tp=tp)
            self.ans_box.SetValue(result)

    # 清除内容并切换为手动搜索
    def clear_message(self, event):
        pyperclip.copy('exit')
        self.tp_input.SetValue('')
        self.cb_setting.SetValue(False)
        self.file_input.Enable()
        self.file_input.SetValue('')
        self.tp_input.SetValue('')
        self.ans_box.SetValue('')
        self.tp_input.Disable()
        self.search.Disable()
        self.cb_setting.Disable()
        self.file_load.Enable()
        self.status.SetLabel('手动搜题模式')

    # 退出程序
    def exit_app(self, event):
        pyperclip.copy('exit')  # 使用剪贴板触发线程终止操作
        exit(0)  # 终止整个Python程序

    # 将内容发送到文本框
    def update_display(self, msg):
        if msg != '':  # 如果信息不为空，说明正在检测剪贴板，开始进行搜题操作
            self.ans_box.SetValue(msg)

    # 搜题模式切换
    def cb_switch(self, event):
        # 自动搜题模式
        if self.cb_setting.GetValue():
            self.search.Disable()
            self.tp_input.SetValue('')
            self.tp_input.Disable()
            TpSearchThread()  # 在启动自动搜题模式时启动线程
            self.status.SetLabel('自动搜题模式')
        # 手动搜题模式
        else:
            pyperclip.copy('exit')
            pyperclip.copy('')
            self.search.Enable()
            self.tp_input.Enable()
            self.tp_input.SetValue('')
            self.ans_box.SetValue('')
            self.status.SetLabel('手动搜题模式')


# 主函数
if __name__ == '__main__':
    app = wx.App()
    frame = ExamToolPro(parent=None, uid=-1)
    frame.Show()
    app.MainLoop()
