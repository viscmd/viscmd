import functools
import os
import sys
import tkinter as tk
from difflib import SequenceMatcher
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

from viscmd import type
from viscmd import xterm
from viscmd.cmd import Argument, ArgValue, Command, load_command

from .config import config

_TITLE = 'Visual Command'
_ICON = '/usr/share/icons/viscmd.png'


class ArgBinding:
    def __init__(self):
        self.arg: Argument = None
        self.arg_value: ArgValue = None
        self.checked: tk.BooleanVar = None
        self.tk_value = None
        self.parent: ArgBinding = None
        self.children = []


# VerticalScrolledFrame
#   https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
# Based on
#   https://web.archive.org/web/20170514022131id_/http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame

class VerticalScrolledFrame(ttk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame.
    * Construct and pack/place/grid normally.
    * This frame only allows vertical scrolling.
    """

    def __init__(self, parent, *args, **kw):
        ttk.Frame.__init__(self, parent, *args, **kw)

        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # Reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        self.interior = interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar.
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame.
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the inner frame's width to fill the canvas.
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)
        self.canvas = canvas


# Combobox
# https://stackoverflow.com/questions/59763822/show-combobox-drop-down-while-editing-text-using-tkinter

class Combobox(ttk.Combobox):
    def _tk(self, cls, parent):
        obj = cls(parent)
        obj.destroy()
        if cls is tk.Toplevel:
            obj._w = self.tk.call('ttk::combobox::PopdownWindow', self)
        else:
            obj._w = '{}.{}'.format(parent._w, 'f.l')
        return obj

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.popdown = self._tk(tk.Toplevel, parent)
        self.listbox: tk.Listbox = self._tk(tk.Listbox, self.popdown)
        self.main_cmd: Command = None

        self.bind("<KeyPress>", self.on_keypress, '+')
        self.bind("<KeyRelease>", self.on_keyup, '+')
        self.listbox.bind("<Up>", self.on_keypress)

    def on_keyup(self, event):
        if event.widget == self:
            self.listbox.curselection()
            if self.main_cmd is not None:
                line = self.get()
                # new_values = [s for s in self.main_cmd.subcommands.keys() if s.statswith(line)]
                # self.configure(values=new_values)
            else:
                self.configure(values=())

    def on_keypress(self, event):
        if event.widget == self:
            state = self.popdown.state()

            if state == 'withdrawn' \
                    and event.keysym not in ['BackSpace', 'Up']:
                self.event_generate('<Button-1>')
                self.after(0, self.focus_set)
            if event.keysym == 'Down':
                self.after(0, self.listbox.focus_set)

        else:  # self.listbox
            curselection = self.listbox.curselection()

            if event.keysym == 'Up' and curselection[0] == 0:
                self.popdown.withdraw()


def find_longest(items, s) -> int:
    max_match_idx = -1
    max_match_size = -1
    for i in range(len(items)):
        match = SequenceMatcher(
            None, items[i], s).find_longest_match(0, -1, 0, -1)
        if match.size > max_match_size:
            max_match_size = match.size
            max_match_idx = i
    return max_match_idx


class MainWindow:
    def __init__(self):
        self.name: str = ""  # command name
        self.root_win: tk.Tk = None
        self.cmd_box: ttk.Combobox = None
        self.cmd_box_value = None
        self.tab_ctrl: ttk.Notebook = None
        self.tab_pages = []
        self.main_cmd: Command = None
        self.cmd: Command = None
        self.sub_cmd_names = []
        self.ignore_value_change = False

        if len(sys.argv) >= 2:
            self.init_cmd = sys.argv[1]  # os.environ.get('READLINE_LINE', '')
        else:
            self.init_cmd = ''

    @staticmethod
    def load(name):
        main_cmd = load_command(name, config.lang_prefer)
        if main_cmd is None:
            main_cmd = load_command(name, config.lang_alt)
        # todo interact when fail to load
        return main_cmd

    def btn_clicked(self):
        self.root_win.destroy()
        cmdline = self.cmd_box_value.get()
        if cmdline != '':
            if self.init_cmd != "":  # completion mode
                print(cmdline)
            else:  # run mode
                xterm.run(cmdline)

    def set_parent_checked(self, ab):
        if ab.parent is not None:
            ab.parent.checked.set(True)
            self.set_parent_checked(ab.parent)

    def arg_checked(self, ab: ArgBinding, name, index, mode):
        if ab.checked.get() and ab.parent is not None \
                and ab in ab.parent.children and len(ab.parent.arg.one_of) > 0:  # is in the one_of list
            sibling: ArgBinding
            for sibling in ab.parent.children:
                if sibling != ab:
                    sibling.checked.set(False)
        ab.arg_value.update_status(ab.checked.get())
        ab.arg_value.set_value(ab.tk_value.get())
        if ab.checked.get() and not self.ignore_value_change:
            self.set_parent_checked(ab)
        s = self.cmd.get_cmd_line()
        self.cmd_box.set(s)

    def arg_value_changed(self, ab: ArgBinding, name, index, mode):
        if self.ignore_value_change:
            return
        # auto check when user made some change
        if not ab.checked.get():
            ab.checked.set(True)
        # to update the cmd box
        self.arg_checked(ab, None, None, None)

    def cmd_box_value_changed(self, name, index, mode):
        line = self.cmd_box.get()
        self.reload_cmd(line)  # load or reload
        if self.main_cmd is not None:
            new_values = [s for s in self.sub_cmd_names if s.find(line) >= 0]
            self.cmd_box.configure(values=new_values)
        else:
            self.cmd_box.configure(values=())

    def cmd_box_key_pressed(self, event):
        if event.char == '\r':
            self.btn_clicked()

    def reset_cmd(self):
        self.main_cmd = None
        self.cmd = None
        self.sub_cmd_names = []
        self.name = ""

    def reset_arg_widgets(self):
        if len(self.tab_pages) > 0:
            for i in self.tab_pages:
                i.destroy()
            self.tab_pages = []

    def reload_cmd(self, cmdline):
        ss = cmdline.split()
        if len(ss) == 0:
            self.reset_cmd()
            self.reset_arg_widgets()
            return

        name = ss[0]
        if name != self.name:  # possibly to reload
            if self.main_cmd is not None:
                self.reset_cmd()
            if name != "":
                # reload
                self.main_cmd = self.load(name)
                if self.main_cmd is not None:
                    self.sub_cmd_names = list(self.main_cmd.subcommands.keys())
                    self.cmd_box.config(values=self.sub_cmd_names)
            self.name = name

        # cmd defaults to main_cmd
        cmd = self.main_cmd

        # try to locate subcommand
        if self.main_cmd is not None and len(self.main_cmd.subcommands) > 0:
            for n in range(2, min(len(ss), 3) + 1):
                parts = ss[:n]
                sub_cmd_name = ' '.join(parts)
                sub_cmd = self.main_cmd.subcommands.get(sub_cmd_name)
                if sub_cmd is not None:
                    cmd = sub_cmd
                    break

        if cmd != self.cmd:
            if self.cmd is not None:
                self.reset_arg_widgets()
                self.cmd.values.clear()

            # create arg list
            if cmd is not None:
                self.cmd = cmd
                self.create_tabs(self.tab_ctrl)

    @staticmethod
    def openfile_btn_clicked(ab: ArgBinding):
        if len(ab.arg.file_extensions) > 0:
            exts = ' '.join(ab.arg.file_extensions)
            filetypes = [('Files', exts), ('All Files', '*')]
        else:
            filetypes = [('All Files', '*')]
        filename = filedialog.askopenfilename(title=_TITLE, filetypes=filetypes)
        if filename != '':
            if filename.find(' ') >= 0:
                filename = '"' + filename + '"'
            ab.tk_value.set(filename)

    @staticmethod
    def openfiles_btn_clicked(ab: ArgBinding):
        if len(ab.arg.file_extensions) > 0:
            exts = ' '.join(ab.arg.file_extensions)
            filetypes = [('Files', exts), ('All Files', '*')]
        else:
            filetypes = [('All Files', '*')]
        filenames = filedialog.askopenfilenames(title=_TITLE, filetypes=filetypes)
        if filenames:
            ss = []
            for filename in filenames:
                if filename.find(' ') >= 0:
                    filename = '"' + filename + '"'
                ss.append(filename)
            ab.tk_value.set(' '.join(ss))

    @staticmethod
    def savefile_btn_clicked(ab: ArgBinding):
        kwargs = {}
        if len(ab.arg.file_extensions) > 0:
            exts = ' '.join(ab.arg.file_extensions)
            kwargs['filetypes'] = [('Files', exts), ('All Files', '*')]
            kwargs['defaultextension'] = ab.arg.file_extensions[0]
        else:
            kwargs['filetypes'] = [('All Files', '*')]
        filename = filedialog.asksaveasfilename(title=_TITLE, **kwargs)
        if filename != '':
            if filename.find(' ') >= 0:
                filename = '"' + filename + '"'
            ab.tk_value.set(filename)

    @staticmethod
    def dir_btn_clicked(ab: ArgBinding):
        filename = filedialog.askdirectory(title=_TITLE)
        if filename != '':
            ab.tk_value.set(filename)

    def create_var_widget(self, ab: ArgBinding, parent):
        arg = ab.arg
        ab.tk_value.trace("w", functools.partial(self.arg_value_changed, ab))

        frm = tk.Frame(parent)

        values = arg.get_choices()
        if len(values) > 3:
            cb = ttk.Combobox(frm, values=values,
                              state="readonly", textvariable=ab.tk_value)
            cb.pack(side=tk.LEFT, fill=tk.X)
            if arg.default is not None:
                try:
                    n = arg.choices.index(arg.default)
                except IndexError:
                    n = 0
                cb.current(n)
        elif len(values) > 0:
            for v in values:
                rb = ttk.Radiobutton(frm, text=v, variable=ab.tk_value, value=v)
                rb.pack(side=tk.LEFT, padx=5)
        else:
            entry = tk.Entry(parent, textvariable=ab.tk_value)
            entry.pack(side=tk.LEFT, fill=tk.X)
            if arg.default is not None:
                entry.insert(0, arg.default)
            else:
                entry.insert(0, arg.variable)

        if arg.type == type.file and not arg.repeatable:
            btn = ttk.Button(frm, text='...', command=functools.partial(
                self.openfile_btn_clicked, ab))
            btn.pack(side=tk.LEFT, padx=5)
        if arg.type == type.file and arg.repeatable:
            btn = ttk.Button(frm, text='...', command=functools.partial(
                self.openfiles_btn_clicked, ab))
            btn.pack(side=tk.LEFT, padx=5)
        if arg.type == type.savefile:
            btn = ttk.Button(frm, text='...', command=functools.partial(
                self.savefile_btn_clicked, ab))
            btn.pack(side=tk.LEFT, padx=5)
        if arg.type == type.directory:
            btn = ttk.Button(frm, text='...', command=functools.partial(
                self.dir_btn_clicked, ab))
            btn.pack(side=tk.LEFT, padx=5)

        return frm

    def create_tabs(self, tab_ctrl):
        self.ignore_value_change = True
        for group in self.cmd.groups.keys():
            args = self.cmd.get_group(group)
            tab_scroller = VerticalScrolledFrame(tab_ctrl)
            self.tab_pages.append(tab_scroller)
            tab_ctrl.add(tab_scroller, text=group)
            tab_content = tab_scroller.interior

            self.create_arg_widgets(tab_content, args, None, 0)

        self.ignore_value_change = False

    def create_arg_widgets(self, tab_content, args: list, parent: ArgBinding, indent: int):
        for i in range(len(args)):
            arg: Argument = args[i]

            text = ""
            if arg.keyword != "":
                if arg.alias != "":
                    text = "%s (%s)" % (arg.keyword, arg.alias)
                else:
                    text = arg.keyword
            if text == '' and arg.variable != '':
                text = '(%s)' % arg.variable
            help_shown = False
            if text == '' and arg.help != '':
                text = arg.help
                help_shown = True
            if text == '':
                text = '(no help text)'
            text = "%s   " % text

            ab = ArgBinding()
            ab.arg = arg

            ab.tk_value = tk.StringVar()
            ab.checked = tk.BooleanVar()
            ab.checked.trace_add("write", functools.partial(self.arg_checked, ab))

            if parent:
                ab.arg_value = parent.arg_value.new_arg_value(arg)
                ab.parent = parent
                parent.children.append(ab)
            else:
                ab.arg_value = self.cmd.new_arg_value(arg)

            if arg.required:
                ab.checked.set(True)

            if i != 0:
                separator = ttk.Separator(tab_content, orient='horizontal')
                separator.pack(anchor=tk.W, fill=tk.X)

            arg_frm = ttk.Frame(tab_content)
            arg_frm.pack(anchor=tk.W, fill=tk.X, padx=3+indent*20)

            btn = ttk.Checkbutton(arg_frm, text=text, variable=ab.checked, onvalue=True, offvalue=False)
            btn.pack(side=tk.LEFT)

            if arg.variable != "":
                w = self.create_var_widget(ab, arg_frm)
                w.pack(side=tk.LEFT)

            if arg.help != "" and not help_shown:
                ttk.Label(tab_content, text=arg.help, wraplength=800, justify=tk.LEFT) \
                    .pack(anchor=tk.W, fill=tk.X, padx=3+indent*20)

            if len(arg.args) > 0:
                self.create_arg_widgets(tab_content, arg.args, ab, indent + 1)
            elif len(arg.one_of) > 0:
                self.create_arg_widgets(tab_content, arg.one_of, ab, indent + 1)

    def on_mouse_wheel(self, event):
        tab_no = self.tab_ctrl.index(self.tab_ctrl.select())
        tab: VerticalScrolledFrame = self.tab_pages[tab_no]
        if event.num == 5 or event.delta == -120:  # wheel down
            tab.canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:  # wheel up
            tab.canvas.yview_scroll(-1, "units")

    def show(self):
        self.root_win = tk.Tk()
        self.root_win.geometry('1000x600')
        self.root_win.title(_TITLE)
        if os.path.exists(_ICON):
            self.root_win.iconphoto(False, tk.PhotoImage(file=_ICON))

        # with Windows OS
        self.root_win.bind("<MouseWheel>", self.on_mouse_wheel)
        self.root_win.bind("<MouseWheel>", self.on_mouse_wheel)
        # with Linux OS
        self.root_win.bind("<Button-4>", self.on_mouse_wheel)
        self.root_win.bind("<Button-5>", self.on_mouse_wheel)

        main_frm = ttk.Frame(self.root_win, padding=10)
        main_frm.pack(fill=tk.BOTH, expand=1)

        if self.cmd is not None or self.name == "":
            ttk.Label(main_frm, text=f"Command: {self.name}").pack(anchor=tk.W)
        else:
            ttk.Label(main_frm, text=f"Command: {self.name} (Not found)").pack(
                anchor=tk.W)

        if self.cmd is not None and len(self.cmd.subcommands) > 0:
            names = [c.name for c in self.cmd.subcommands]
            sub_cmd_box = ttk.Combobox(main_frm, values=names, width=80)
            sub_cmd_box.pack()

        cmd_frm = ttk.Frame(main_frm)
        cmd_frm.pack(fill=tk.X)

        if self.init_cmd != "":
            btn_text = "OK"
        else:
            btn_text = 'Run'
            if not xterm.check():
                messagebox.showinfo('Supported x terminal not found')
        ttk.Button(cmd_frm, text=btn_text,
                   command=self.btn_clicked).pack(side=tk.RIGHT)

        self.cmd_box_value = tk.StringVar()
        self.cmd_box_value.set(self.init_cmd)
        self.cmd_box_value.trace_add("write", self.cmd_box_value_changed)
        self.cmd_box = ttk.Combobox(cmd_frm, textvariable=self.cmd_box_value)
        self.cmd_box.pack(side=tk.RIGHT, fill=tk.X, expand=1, padx=5)
        self.cmd_box.bind('<Key>', self.cmd_box_key_pressed, add=True)
        self.cmd_box.focus_set()
        self.cmd_box.icursor(len(self.init_cmd))

        self.tab_ctrl = ttk.Notebook(main_frm, width=600)
        self.tab_ctrl.pack(fill=tk.BOTH, expand=tk.TRUE, pady=3)

        self.reload_cmd(self.init_cmd)

        self.root_win.mainloop()
