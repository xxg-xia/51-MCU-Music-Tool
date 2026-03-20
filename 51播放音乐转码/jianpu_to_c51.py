"""
简谱字符串转 51 单片机蜂鸣器 C 数组工具（GUI 版）
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext


# =========================
# 参数配置区（全局变量分离）
# =========================

# 单片机晶振频率（12MHz）
OSC_FREQ = 12000000

# 字典：映射音符名称到对应的物理频率（Hz）
# L = 低音，M = 中音，H = 高音，0 = 休止符
NOTE_FREQ_MAP = {
    "0": 0,
    "L1": 131,
    "L2": 147,
    "L3": 165,
    "L4": 175,
    "L5": 196,
    "L6": 220,
    "L7": 247,
    "M1": 262,
    "M2": 294,
    "M3": 330,
    "M4": 349,
    "M5": 392,
    "M6": 440,
    "M7": 494,
    "H1": 523,
    "H2": 587,
    "H3": 659,
    "H4": 698,
    "H5": 784,
    "H6": 880,
    "H7": 988,
}


def parse_jianpu(jianpu_text):
    """
    解析简谱字符串。

    输入格式示例：
        M1:4 M1:4 M5:4 M5:4 0:4

    返回值示例：
        [("M1", 4), ("M1", 4), ("M5", 4)]
    """
    if not jianpu_text.strip():
        raise ValueError("请输入简谱内容。")

    notes = []
    tokens = jianpu_text.strip().split()

    for token in tokens:
        if ":" not in token:
            raise ValueError(f"音符格式错误：{token}，应为“音符:时值”。")

        note_name, duration_str = token.split(":", 1)
        note_name = note_name.strip().upper()
        duration_str = duration_str.strip()

        if note_name not in NOTE_FREQ_MAP:
            raise ValueError(f"未知音符：{note_name}")

        try:
            duration_value = int(duration_str)
        except ValueError as exc:
            raise ValueError(f"时值必须为整数：{token}") from exc

        if duration_value <= 0:
            raise ValueError(f"时值必须大于 0：{token}")

        notes.append((note_name, duration_value))

    return notes


def calculate_timer_reload(freq_hz):
    """
    计算 16 位定时器（模式 1）的重装载值，并拆分为 TH0、TL0。

    公式：
        计数脉冲数 = OSC_FREQ / 12 / 2 / 频率
        重装值 = 65536 - 计数脉冲数
    """
    if freq_hz <= 0:
        return 0x00, 0x00, 0

    pulse_count = OSC_FREQ / 12 / 2 / freq_hz
    reload_value = 65536 - int(round(pulse_count))

    if not (0 <= reload_value <= 0xFFFF):
        raise ValueError(f"定时器重装值超出 16 位范围：{reload_value}")

    th0 = (reload_value >> 8) & 0xFF
    tl0 = reload_value & 0xFF
    return th0, tl0, reload_value


def calculate_duration_ms(note_divisor, bpm):
    """
    根据 BPM 和音符时值，计算音符持续的毫秒数。

    规则：
        4 代表四分音符
        8 代表八分音符

    公式：
        四分音符时长(ms) = 60000 / BPM
        当前音符时长(ms) = 四分音符时长 * 4 / 音符时值
    """
    quarter_note_ms = 60000 / bpm
    duration_ms = quarter_note_ms * 4 / note_divisor
    return int(round(duration_ms))


def format_note_comment(note_name, freq_hz, duration_ms):
    """
    生成每个音符对应的注释文本，便于直接粘贴到 C 工程中查看。
    """
    if note_name == "0":
        return f"{note_name}, 休止符, {duration_ms}ms"
    return f"{note_name}, {freq_hz}Hz, {duration_ms}ms"


def convert_to_music_data(jianpu_text, bpm):
    """
    将简谱字符串转换为音乐数据列表。

    返回值格式：
        [
            (th0, tl0, duration_ms, comment_text),
            ...
        ]
    """
    parsed_notes = parse_jianpu(jianpu_text)
    music_data = []

    for note_name, note_divisor in parsed_notes:
        freq_hz = NOTE_FREQ_MAP[note_name]
        th0, tl0, _ = calculate_timer_reload(freq_hz)
        duration_ms = calculate_duration_ms(note_divisor, bpm)
        comment_text = format_note_comment(note_name, freq_hz, duration_ms)
        music_data.append((th0, tl0, duration_ms, comment_text))

    return music_data


def extract_array_body(c_code_text):
    """
    从完整的 C 数组文本中提取数组体内部的数据行。

    复制后仅保留：
        0xFC, 0x44, 125,  // ...
        ...
        0xFF, 0xFF, 0   // 结束标志
    """
    lines = c_code_text.splitlines()
    body_lines = []

    for line in lines[1:-1]:
        stripped_line = line.rstrip()
        if stripped_line:
            body_lines.append(stripped_line)

    return "\n".join(body_lines)


def generate_c_array(music_data, array_name="Music_Data"):
    """
    生成符合 Keil C51 语法的 C 数组字符串。

    注意：
    持续时间字段已改为 unsigned int 数组承载，避免低 BPM 时毫秒数溢出。
    """
    lines = [f"unsigned int code {array_name}[] = {{"]

    for th0, tl0, duration_ms, comment_text in music_data:
        lines.append(
            f"    0x{th0:02X}, 0x{tl0:02X}, {duration_ms},  // {comment_text}"
        )

    lines.append("    0xFF, 0xFF, 0   // 结束标志")
    lines.append("};")
    return "\n".join(lines)


class JianpuConverterApp:
    """
    简谱转 51 单片机 C 数组的桌面图形界面。
    """

    def __init__(self, root):
        self.root = root
        self.root.title("简谱转 51 单片机数组工具")
        self.root.geometry("900x680")
        self.root.minsize(760, 560)

        self._build_widgets()

    def _build_widgets(self):
        """
        构建界面控件。
        """
        title_label = tk.Label(
            self.root,
            text="简谱转 51 单片机蜂鸣器 C 数组工具",
            font=("Microsoft YaHei UI", 16, "bold"),
            pady=10,
        )
        title_label.pack()

        tip_label = tk.Label(
            self.root,
            text="输入格式示例：M1:4 M5:4 0:4 H1:8",
            font=("Microsoft YaHei UI", 10),
            fg="#444444",
        )
        tip_label.pack()

        input_frame = tk.Frame(self.root, padx=12, pady=10)
        input_frame.pack(fill="both", expand=False)

        bpm_frame = tk.Frame(input_frame)
        bpm_frame.pack(fill="x", pady=(0, 10))

        bpm_label = tk.Label(
            bpm_frame,
            text="设置 BPM 速度：",
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        bpm_label.pack(side="left")

        self.bpm_entry = tk.Entry(
            bpm_frame,
            width=10,
            font=("Consolas", 11),
            justify="center",
        )
        self.bpm_entry.pack(side="left", padx=(8, 0))
        self.bpm_entry.insert(0, "120")

        input_label = tk.Label(
            input_frame,
            text="简谱输入区：",
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        input_label.pack(fill="x")

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 11),
        )
        self.input_text.pack(fill="both", expand=True, pady=(6, 0))
        self.input_text.insert("1.0", "M1:4 M1:4 M5:4 M5:4 0:4")

        button_frame = tk.Frame(self.root, padx=12, pady=8)
        button_frame.pack(fill="x")

        generate_button = tk.Button(
            button_frame,
            text="生成 C 代码",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#1f6feb",
            fg="white",
            activebackground="#1557b0",
            activeforeground="white",
            padx=16,
            pady=8,
            command=self.generate_code,
        )
        generate_button.pack(side="left")

        copy_button = tk.Button(
            button_frame,
            text="一键复制",
            font=("Microsoft YaHei UI", 11),
            padx=16,
            pady=8,
            command=self.copy_output,
        )
        copy_button.pack(side="left", padx=(10, 0))

        output_frame = tk.Frame(self.root, padx=12, pady=10)
        output_frame.pack(fill="both", expand=True)

        output_label = tk.Label(
            output_frame,
            text="C 代码输出区：",
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        output_label.pack(fill="x")

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            state="disabled",
        )
        self.output_text.pack(fill="both", expand=True, pady=(6, 0))

    def generate_code(self):
        """
        点击按钮后执行简谱转换，并将结果显示在输出框中。
        """
        try:
            bpm = self._get_bpm_value()
            jianpu_text = self.input_text.get("1.0", tk.END).strip()
            music_data = convert_to_music_data(jianpu_text, bpm)
            c_code = generate_c_array(music_data)
            self._set_output_text(c_code)
        except ValueError as exc:
            messagebox.showerror("输入错误", str(exc))
        except Exception as exc:
            messagebox.showerror("程序错误", f"生成失败：{exc}")

    def copy_output(self):
        """
        将输出框中的 C 代码复制到系统剪贴板。
        """
        output_text = self.output_text.get("1.0", tk.END).strip()
        if not output_text:
            messagebox.showwarning("提示", "当前没有可复制的内容，请先生成 C 代码。")
            return

        array_body = extract_array_body(output_text)
        if not array_body:
            messagebox.showwarning("提示", "当前没有可复制的数据行，请先生成 C 代码。")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(array_body)
        self.root.update()
        messagebox.showinfo("复制成功", "数组内部数据行已复制到剪贴板。")

    def _get_bpm_value(self):
        """
        读取并校验界面中的 BPM 输入值。
        """
        bpm_text = self.bpm_entry.get().strip()
        if not bpm_text:
            raise ValueError("请输入 BPM 速度。")

        try:
            bpm = int(bpm_text)
        except ValueError as exc:
            raise ValueError("BPM 必须为正整数。") from exc

        if bpm <= 0:
            raise ValueError("BPM 必须为正整数。")

        return bpm

    def _set_output_text(self, content):
        """
        更新只读输出框内容。
        """
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", content)
        self.output_text.config(state="disabled")


def main():
    """
    程序入口。
    """
    root = tk.Tk()
    app = JianpuConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# 使用 PyInstaller 打包为单文件且不显示控制台黑框的命令：
# pyinstaller --onefile --noconsole jianpu_to_c51.py
