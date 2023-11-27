from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox as msgbox
from tkinter import ttk
from tklinenums import TkLineNumbers
from tkhtmlview import HTMLLabel
import requests
from pkg_resources import working_set
import idlelib.colorizer as ic
import idlelib.percolator as ip
import re
from os import system
import json
from threading import Thread
import subprocess
import ast
import webbrowser
import markdown

global file_path, edited, config
file_path = ''
edited = False
config = {
        "default.python.command": "py",
        "terminal.color.hex": "F",
        "recent.file.path": None,
        "pause.terminal.onend": True,
        "newline.with.tabs": True,
        "always.open.recent": True,
        "save.on.run": True,
        "auto.save": False
} 

def messagebox(content: str, type: str):
    if (type == 'info'):
        msgbox.showinfo('SparklyPython - Info', content)
    elif (type == 'err'):
        msgbox.showerror('SparklyPython - Error', content)
    elif (type == 'warn'):
        msgbox.showwarning('SparklyPython - Warning', content)
    else:
        pass

class CustomTopLevel:
    def __init__(self, title, geometry, settings, on_ok):
        self.settings = settings
        self.result = []
        self.root = Toplevel()
        self.root.geometry(geometry)
        self.root.resizable(0, 0)
        self.root.title(title)
        self.on_ok = on_ok

        try:
            self.root.iconbitmap('icon.ico')
        except:
            self.root.iconbitmap(None)

        self.create_widgets()

    def create_widgets(self):
        for label, widget_type, options, default_value, config_value in self.settings:
            frame = Frame(self.root)
            frame.pack(pady=5, padx=10, fill=X)

            if widget_type == "Entry":
                self.create_entry(frame, label, default_value, config_value)
            elif widget_type == "Checkbutton":
                self.create_checkbutton(frame, label, default_value, config_value)
            elif widget_type == "Dropdown":
                self.create_dropdown(frame, label, options, default_value, config_value)

        btns_frame = Frame(self.root)
        btns_frame.pack(side=BOTTOM, pady=10, padx=10)

        save_button = Button(btns_frame, width=10, text="OK", command=lambda: self.on_ok(self.result, self.root))
        save_button.pack(side=RIGHT, padx=5)

        cancel_button = Button(btns_frame, width=10, text="Cancel", command=self.root.destroy)
        cancel_button.pack(side=LEFT, padx=5)
 
    def create_entry(self, frame, label, default_value, config_value):
        Label(frame, text=label).pack(side=LEFT)
        entry_var = StringVar(value=default_value)

        if (default_value): entry_var.set(default_value)

        entry = Entry(frame, textvariable=entry_var)
        entry.pack(side=RIGHT, padx=5)
        self.result.append((entry_var, config_value))

    def create_checkbutton(self, frame, label, default_value, config_value):
        check_var = BooleanVar(value=default_value)

        if (default_value): check_var.set(default_value)

        checkbutton = Checkbutton(frame, text=label, variable=check_var)
        checkbutton.pack(side=LEFT)
        self.result.append((check_var, config_value))

    def create_dropdown(self, frame, label, options, default_value, config_value):
        Label(frame, text=label).pack(side=LEFT)
        dropdown_var = StringVar()

        if (default_value): dropdown_var.set(default_value)

        dropdown = ttk.Combobox(frame, textvariable=dropdown_var, values=options, state='readonly')
        dropdown.pack(side=RIGHT, padx=5)
        self.result.append((dropdown_var, config_value))
        

def save_config(data):
    try:
        with open('sparklypython-config.json', 'w') as file:
            string = json.dumps(data)

            file.write(string)
            file.close()
    except:
        messagebox('Failed to save the configuration, please enable the program to read, write, and create files.', 'err')

try:
    with open('sparklypython-config.json', 'r') as file:
        config = json.load(file)
except:
    try:
        open('sparklypython-config.json', "x")

        save_config(config)
    except:
        messagebox('Failed to start the program, please enable the program to read, write, and create files.', 'err')
        exit()

def user_typed_event():
    editor.tag_remove('highlight', '1.0', END)

    change_syntax_highlighting(editor)

    linenums.redraw()

    set_edited(True)

    if (config['auto.save'] == True):
        save_file()

def save_file():
    if (len(file_path) < 1):
        save_as_file()

        return

    try:
        with open(file_path, 'w') as file:
            text = editor.get('1.0', END).strip()

            file.write(text)
            file.close()

            set_edited(False)

            status_bar.config(text='Saved: ' + file_path)
    except:
        messagebox('Unable to perform this action properly.', 'error')
    
def save_as_file():
    path = asksaveasfilename(filetypes=[('Python', '*py')], title=f'SparklyPython - Save as', defaultextension='py')

    if (len(path) < 1):
        return

    try:
        with open(path, 'w') as file:
            text = editor.get('1.0', END).strip()

            file.write(text)
            file.close()

            set_file_path(path)
            set_edited(False)

            status_bar.config(text='Saved: ' + path)
    except:
        messagebox('Unable to perform this action properly.', 'error')

def new_file():
    if (edited):
        res = msgbox.askyesno('SparklyPython - New File', 'Do you want to save the file before creating a new one?')

        if (res): save_file()

        set_file_path('')

        editor.delete('1.0', END)

        if (res):
            status_bar.config(text='Saved previous file and created a new one.')
        else: status_bar.config(text='Created a new file without saving previous file.')

    else:
        set_file_path('')

        editor.delete('1.0', END)

        status_bar.config(text='Created a new file.')

    set_edited(False)
    
def open_file():
    try:
        if (edited):
            res = msgbox.askyesno('SparklyPython - New File', 'Do you want to save the file before opening another one?')

            if (res): save_file()

        path = askopenfilename(filetypes=[('Python', '*py')], title=f'SparklyPython - Open file')

        if (len(path) <= 0): return

        with open(path, 'r') as file:
            if (file.readable() == False):
                return messagebox('The file is not readable, couldn\'t open the file.', 'err')

            text = file.read().strip()

            editor.delete('1.0', END)
            editor.insert('1.0', text)
            
            file.close()

            set_file_path(path)
            set_edited(False)

            status_bar.config(text='Opened: ' + path)

            change_syntax_highlighting(editor)
    except:
        messagebox('Unable to perform this action properly.', 'err')

def exit_project():
    if (edited):
        res = msgbox.askyesno('SparklyPython - Exit', 'Do you want to save the file before closing the program?')

        if (res):
            save_file()

            gui.destroy()
        else:
            gui.destroy()
    else:
        gui.destroy()
        
def run_project():
    try:
        if (len(editor.get('1.0', END)) <= 1):
            messagebox('You cannot run a Python program with an empty code.', 'warn')

            return

        if (config["save.on.run"] == True): save_file()

        redirect = file_path.split('/')
        path = ''

        for i in range(len(redirect) - 1):
            split = redirect[i].split(' ')
            if (len(split) > 1):
                second = ''

                for i in range(len(split)):
                    if (i == len(split) - 1):
                        second += split[i]
                    else:
                        second += split[i] + ' '

                path += '\"' + second + '\"' + '/'
            else: 
                path += redirect[i] + '/'

        file_name = f"\"{redirect[len(redirect) - 1].split('.')[0]}\""
        command = config['default.python.command'] or 'py'
        terminal_color = config['terminal.color.hex'] or 'F'

        cmd_str = f'start cmd /k "cd {path} && title SparklyPython && color {terminal_color} && {command} {file_name}'

        if (redirect[len(redirect) - 1].endswith('.py')):
            cmd_str += '.py'

        if (config['pause.terminal.onend'] == True):
            cmd_str += ' && (pause && exit) || (pause && exit)"'
        else: cmd_str += ' && (exit) || (exit)"'

        system(cmd_str)

        status_bar.config(text='Running: ' + file_path)
    except:
        messagebox('Failed to run the Python program, please check that the command \'py\' exist.', 'err')

def open_command_prompt():
    try:
        system(f'start cmd /c "title SparklyPython && py && (pause && exit) || (pause && exit)"')
    except:
        messagebox('Failed to start a new Python prompt.', 'err')
    
def editor_undo():
    try:
        editor.edit_undo()
    except:
        pass

def editor_redo():
    try:
        editor.edit_redo()
    except:
        pass

def change_syntax_highlighting(txt: Text):
    try:
        cdg = ic.ColorDelegator()

        #cdg.prog = re.compile(r'\b(?P<Group>okbruh)\b|' + ic.make_pat().pattern, re.S)
        cdg.prog = re.compile(r'\b(?P<GroupForNumbers>\d+)\b|' + ic.make_pat().pattern, re.S)

        cdg.idprog = re.compile(r'\s+(\w+|\d+)', re.S)

        #cdg.tagdefs['Group'] = {'foreground': 'color', 'background': None}
        cdg.tagdefs['GroupForNumbers'] = {'foreground': '#ff6600', 'background': None}

        cdg.tagdefs['COMMENT'] = {'foreground': 'gray', 'background': None}
        cdg.tagdefs['KEYWORD'] = {'foreground': '#1220e6', 'background': None}
        cdg.tagdefs['BUILTIN'] = {'foreground': 'red', 'background': None}
        cdg.tagdefs['STRING'] = {'foreground': 'green', 'background': None}
        cdg.tagdefs['DEFINITION'] = {'foreground': '#7F7F00', 'background': None}

        ip.Percolator(txt).insertfilter(cdg)
    except:
        pass

def set_file_path(path: str):
    global file_path
    file_path = path

    config['recent.file.path'] = path

    save_config(config)

def set_edited(toggle: bool):
    global edited
    edited = toggle

def show_editor_commands(event):
    editor_commands.tk_popup(event.x_root, event.y_root)

def toggle_openrecent():
    value = openrecent_variable.get()

    config['always.open.recent'] = value

    save_config(config)

def toggle_autosave():
    value = autosave_variable.get()

    config['auto.save'] = value

    save_config(config)

def new_line():
    if (config["newline.with.tabs"] == False): return

    cursor_pos = editor.index(INSERT)
    current_line = editor.get(cursor_pos.split('.')[0] + ".0", cursor_pos)

    if current_line.strip().endswith(":"):
        if ('\t' in current_line):
            tabs_count = current_line.count('\t')
            editor.insert(INSERT, '\n' + '\t' * (tabs_count + 1))
        else:
            editor.insert(INSERT, '\n\t')
    else:
        cursor_pos = editor.index(INSERT)
        current_line = editor.get(cursor_pos.split('.')[0] + ".0", cursor_pos)

        if '\t' in current_line:
            tabs_count = current_line.count('\t')
            editor.insert(INSERT, '\n' + '\t' * (tabs_count))
        else:
            editor.insert(INSERT, '\n')

    return 'break'

def install_libraries():
    toplvl = Toplevel()

    toplvl.title('Install packages')
    toplvl.geometry('400x150')
    toplvl.resizable(0, 0)

    try:
        toplvl.iconbitmap('icon.ico')
    except:
        toplvl.iconbitmap(None)

    global last_searched_package_name
    last_searched_package_name = None

    def main_search():
        global last_searched_package_name

        package_name = package_name_entry_var.get()

        if not package_name:
            messagebox('You must provide a package name to search and to install.', 'warn')
            return

        try:
            response = requests.get(f'https://pypi.org/pypi/{package_name}/json')
            response.raise_for_status()
            package_info = response.json()

            package_releases = list(package_info.get('releases', {}))
            package_releases_reversed = package_releases[::-1]

            last_searched_package_name = package_name

            package_version_entry_var.set(package_releases_reversed[0])
            package_version_entry.config(values=package_releases_reversed, state='readonly')
            install_btn.config(state=NORMAL)
        except:
            messagebox(f'Failed to search the package \'{package_name}\'.', 'err')
            return
        
    def main_install():
        package_name = last_searched_package_name
        package_version = package_version_entry_var.get()

        cmd_package_name = f"{package_name}=={package_version}"

        try:
            subprocess.run(['pip', 'install', cmd_package_name], check=True)

            messagebox(f'The package \'{package_name}\' has been installed successfully.', 'info')
        except subprocess.CalledProcessError as e:
            messagebox(f'Failed to install package \'{package_name}\'. Error: {e}', 'err')

    main_frame = Frame(toplvl)
    main_frame.pack(side=TOP, fill=X, padx=5, pady=5)

    Label(main_frame, text='Package name').pack(side=LEFT, fill=X)

    global package_name_entry_var, install_btn, package_version_entry, package_version_entry_var
    package_name_entry_var = StringVar()

    package_name_entry = Entry(main_frame, width=30, textvariable=package_name_entry_var)
    package_name_entry.pack(side=RIGHT, fill=X)

    second_main_frame = Frame(toplvl)
    second_main_frame.pack(side=TOP, fill=X, padx=5, pady=5)

    Label(second_main_frame, text='Select version').pack(side=LEFT, fill=X)

    install_btn = Button(second_main_frame, text='Install', state=DISABLED, width=10, command=main_install)
    install_btn.pack(side=RIGHT, padx=5, pady=5)

    package_version_entry_var = StringVar()

    package_version_entry = ttk.Combobox(second_main_frame, state=DISABLED, values=[], textvariable=package_version_entry_var)
    package_version_entry.pack(side=RIGHT, padx=5, pady=5)

    buttons_frame = Frame(toplvl)
    buttons_frame.pack(side=BOTTOM)

    search_btn = Button(buttons_frame, text='Search', width=10, command=main_search)
    search_btn.pack(side=RIGHT, padx=5, pady=5)

    cancel_btn = Button(buttons_frame, text='Cancel', width=10, command=toplvl.destroy)
    cancel_btn.pack(side=LEFT, padx=5, pady=5)

    installed_packages = list({ f'{package.project_name.lower()} ({package.version})' for package in working_set })

    Button(buttons_frame, text='View installed', width=15, command=lambda: messagebox('You can use \'pip list\' instead.\n\n' + '\n'.join(installed_packages), 'info')).pack(side=LEFT)

    toplvl.mainloop()

def editor_search():
    settings = [
        ("Keyword to search", "Entry", None, "", None),
        ("No case", "Checkbutton", None, False, None)
    ]

    def main(results, root):
        arr = []

        for result in results:
            arr.append(result[0].get())

        editor.tag_delete("highlight")

        editor.tag_configure('highlight', foreground=None, background='#00FFFF')

        start_pos = '1.0'
        while True:
            start_pos = editor.search(arr[0], start_pos, stopindex=END, nocase=arr[1])

            if not start_pos:
                break

            end_pos = f"{start_pos}+{len(arr[0])}c"
            editor.tag_add('highlight', start_pos, end_pos)
            start_pos = end_pos

    CustomTopLevel(title='Search keyword', geometry='300x120', settings=settings, on_ok=main)

def formatter():
    text = editor.get("1.0", END)

    text = text.replace("    ", "\t")

    editor.delete("1.0", END)
    editor.insert("1.0", text)

def extract_variables_functions_classes():
    class Table:
        def __init__(self, root: Toplevel or Tk, total_rows: int, total_columns: int, lst: list):
            self.tree = ttk.Treeview(root, columns=("Variable", "Type", "ID"), show="headings")

            for col in ("Variable", "Type", "ID"):
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor="center")

            for i in range(total_rows):
                self.tree.insert("", "end", values=lst[i])

            self.tree.pack(fill="both", expand=True)

    def get_readable_type(type_node):
        if isinstance(type_node, ast.Name):
            return type_node.id
        elif isinstance(type_node, ast.Subscript):
            if isinstance(type_node.value, ast.Name) and type_node.value.id == 'list':
                return 'list[' + get_readable_type(type_node.slice) + ']'
        else:
            return 'Unknown'

    code = editor.get('1.0', END)

    parsed_code = ast.parse(code)
    
    result = []

    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            result.append({"name": node.name, "type": 'Function', "id": hex(id(node)).upper().replace('X', 'x')})
        elif isinstance(node, ast.ClassDef):
            result.append({"name": node.name, "type": 'Class', "id": hex(id(node)).upper().replace('X', 'x')})
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.append({"name": target.id, "type": 'Unknown', "id": hex(id(target)).upper().replace('X', 'x')})
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                result.append({"name": node.target.id, "type": get_readable_type(node.annotation), "id": hex(id(node.target)).upper().replace('X', 'x')})

    if (len(result) <= 0):
        messagebox('There are currently no variables in the code.', 'info')
        return

    toplvl = Toplevel()

    toplvl.title('Variables')
    toplvl.geometry('500x300')

    try:
        toplvl.iconbitmap('icon.ico')
    except:
        toplvl.iconbitmap(None)

    Table(toplvl, len(result), 3, [[var['name'], var['type'], var['id']] for var in result])

    toplvl.mainloop()

def show_settings():
    colors_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

    settings = [
        ("Default Python command", "Entry", None, config['default.python.command'] or 'py', 'default.python.command'),
        ("Terminal prompt color", "Dropdown", colors_list, config['terminal.color.hex'] or 'F', 'terminal.color.hex'),
        ("Terminal: Pause Terminal on end", "Checkbutton", None, config['pause.terminal.onend'], 'pause.terminal.onend'),
        ("Editor: Add TABs on a new line", "Checkbutton", None, config['newline.with.tabs'], 'newline.with.tabs'),
        ("Editor: Save file on Run", "Checkbutton", None, config['save.on.run'], 'save.on.run')
    ]

    def main(results, root):
        for variable, config_value in results:
            config[config_value] = variable.get()

        save_config(config)

        root.destroy()

        messagebox('Successfully saved the new settings.', 'info')

    CustomTopLevel(title='Settings configuration', geometry='300x230', settings=settings, on_ok=main)

def scroll_both_y(action, position, type=None):
    editor.yview_moveto(position)

def scroll_both_x(action, position, type=None):
    editor.xview_moveto(position)

def update_scroll_y(first, last, type=None):
    editor.yview_moveto(first)
    scrollbar_yview.set(first, last)
    linenums.redraw()

def update_scroll_x(first, last, type=None):
    editor.xview_moveto(first)
    scrollbar_xview.set(first, last)
    linenums.redraw()

def show_about():
    toplvl = Toplevel()

    toplvl.title('SparklyPython - About')
    toplvl.geometry('800x500')
    toplvl.resizable(0, 0)

    try:
        toplvl.iconbitmap('icon.ico')
    except:
        toplvl.iconbitmap(None)

    main_frame = Frame(toplvl)
    main_frame.pack(side=TOP)

    def display_markdown():
        try:
            with open('ABOUT.md', 'r', encoding='utf-8') as file:
                markdown_content = file.read()

                html_content = markdown.markdown(markdown_content)

                html_label.set_html(html_content)
        except:
            messagebox('Failed to display the markdown file.', 'err')

            toplvl.destroy()

    global html_label
    html_label = HTMLLabel(main_frame, html="")
    html_label.pack(padx=10, pady=10, side=LEFT, expand=True, fill=BOTH)

    display_markdown()

    second_main_frame = Frame(toplvl)
    second_main_frame.pack(side=BOTTOM)

    ok_button = Button(second_main_frame, width=10, text='OK', command=toplvl.destroy)
    ok_button.pack(side=BOTTOM, padx=5, pady=5)

class IDE:
    global gui
    gui = Tk()

    gui.geometry('1000x600')
    gui.title('SparklyPython')

    try:
        gui.iconbitmap('icon.ico')
    except:
        gui.iconbitmap(None)

    # Menu bar
    menu_bar = Menu(gui)

    global openrecent_variable, autosave_variable
    openrecent_variable = BooleanVar()
    autosave_variable = BooleanVar()

    openrecent_variable.set(config['always.open.recent'])
    autosave_variable.set(config['auto.save'])

    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label='New', command=new_file, accelerator='Ctrl+N')
    file_menu.add_separator()
    file_menu.add_command(label='Open file', command=open_file, accelerator='Ctrl+O')
    file_menu.add_separator()
    file_menu.add_command(label='Save', command=save_file, accelerator='Ctrl+S')
    file_menu.add_command(label='Save as', command=save_as_file)
    file_menu.add_separator()
    file_menu.add_checkbutton(label='Auto-save', command=toggle_autosave, variable=autosave_variable)
    file_menu.add_checkbutton(label='Open recent', command=toggle_openrecent, variable=openrecent_variable)
    file_menu.add_separator()
    file_menu.add_command(label='Exit', command=exit_project, accelerator='Alt+F4')

    menu_bar.add_cascade(label='File', menu=file_menu)

    edit_menu = Menu(menu_bar, tearoff=0)
    edit_menu.add_command(label='Undo', command=lambda: editor_undo(), accelerator='Ctrl+Z')
    edit_menu.add_command(label='Redo', command=lambda: editor_redo(), accelerator='Ctrl+Y')
    edit_menu.add_separator()
    edit_menu.add_command(label='Search keyword', command=lambda: editor_search(), accelerator='Ctrl+F')
    edit_menu.add_command(label='Format code', command=lambda: formatter())
    edit_menu.add_separator()
    edit_menu.add_command(label='Copy', command=lambda: editor.event_generate("<<Copy>>"), accelerator='Ctrl+C')
    edit_menu.add_command(label='Cut', command=lambda: editor.event_generate("<<Cut>>"), accelerator='Ctrl+X')
    edit_menu.add_command(label='Paste', command=lambda: editor.event_generate("<<Paste>>"), accelerator='Ctrl+V')

    menu_bar.add_cascade(label='Edit', menu=edit_menu)

    python_menu = Menu(menu_bar, tearoff=0)
    python_menu.add_command(label='New prompt', command=open_command_prompt)
    python_menu.add_command(label='Run', command=run_project, accelerator='F5')
    python_menu.add_separator()
    python_menu.add_command(label='Install packages', command=install_libraries, accelerator='Ctrl+L')
    python_menu.add_command(label='Settings', command=show_settings, accelerator='F8')

    menu_bar.add_cascade(label='Python', menu=python_menu)

    help_menu = Menu(menu_bar, tearoff=0)
    help_menu.add_command(label='About', command=lambda: show_about())
    help_menu.add_command(label='Source (GitHub)', command=lambda: webbrowser.open('https://github.com/TFAGaming/SparklyPython'))

    menu_bar.add_cascade(label='Help', menu=help_menu)

    gui.config(menu=menu_bar)

    # Main frame
    main_frame = Frame(gui)
    main_frame.pack(expand=True, fill=BOTH)

    # Scroll bar
    global scrollbar_yview, scrollbar_xview
    scrollbar_yview = Scrollbar(main_frame, orient=VERTICAL)
    scrollbar_yview.pack(side=RIGHT, fill=Y)

    scrollbar_xview = Scrollbar(main_frame, orient=HORIZONTAL)
    scrollbar_xview.pack(side=BOTTOM, fill=X)

    # Editor and line numbers
    global editor, linenums
    editor = Text(main_frame, undo=True, yscrollcommand=scrollbar_yview.set, xscrollcommand=scrollbar_xview.set, wrap=NONE)
    editor.pack(padx=5, pady=5, fill=BOTH, side=RIGHT, expand=True)

    linenums = TkLineNumbers(main_frame, editor, justify=RIGHT)
    linenums.pack(fill=Y, side=LEFT, padx=5, pady=5)

    global editor_commands
    editor_commands = Menu(gui, tearoff=0)
    editor_commands.add_command(label='Undo', command=editor_undo, accelerator='Ctrl+Z')
    editor_commands.add_command(label='Redo', command=editor_redo, accelerator='Ctrl+Y')
    editor_commands.add_separator()
    editor_commands.add_command(label='Copy', command=lambda: editor.event_generate("<<Copy>>"), accelerator='Ctrl+C')
    editor_commands.add_command(label='Cut', command=lambda: editor.event_generate("<<Cut>>"), accelerator='Ctrl+X')
    editor_commands.add_command(label='Paste', command=lambda: editor.event_generate("<<Paste>>"), accelerator='Ctrl+V')
    editor_commands.add_separator()
    editor_commands.add_command(label='Search keyword', command=lambda: editor_search(), accelerator='CTRL+F')
    editor_commands.add_command(label='Run', command=lambda: run_project(), accelerator='F5')
    editor_commands.add_command(label='Format code', command=lambda: formatter())
    editor_commands.add_command(label='Variables', command=lambda: extract_variables_functions_classes())
    editor_commands.add_separator()
    editor_commands.add_command(label='Select all', command=lambda: editor.event_generate("<<SelectAll>>"))
    editor_commands.add_command(label='Delete', command=lambda: editor.event_generate("<<Clear>>"), accelerator='Del')

    # Configuring scroll bar
    scrollbar_yview.config(command=scroll_both_y)
    scrollbar_xview.config(command=scroll_both_x)
    editor.config(yscrollcommand=update_scroll_y, xscrollcommand=update_scroll_x)
    
    # Seperator
    separator = ttk.Separator(gui, orient=HORIZONTAL)
    separator.pack(fill=X)

    # Status frame
    status_frame = Frame(gui)
    status_frame.pack(fill=X, pady=5)

    # Status bar
    global status_bar, status_run_btn
    status_run_btn = Button(status_frame, text='Run', width=10, command=run_project)
    status_run_btn.pack(side=LEFT, padx=10)

    status_seperator = ttk.Separator(status_frame, orient=VERTICAL)
    status_seperator.pack(side=LEFT, fill=Y)

    status_bar = Label(status_frame, text='Ready!', anchor=E)
    status_bar.pack(fill=X, side=LEFT, ipady=3, padx=10)

    # Bindings
    def return_key(event):
        if event.keysym == 'Return':
            editor.after(1, lambda: editor.see(END))

    editor.bind('<Key>', lambda _: user_typed_event())
    editor.bind('<Button-3>', show_editor_commands)
    editor.bind('<Control-Key-s>', lambda _: save_file())
    editor.bind('<Control-Key-o>', lambda _: open_file())
    editor.bind('<Control-Key-n>', lambda _: new_file())
    editor.bind('<Control-Key-f>', lambda _: editor_search())
    editor.bind('<Return>', lambda _: new_line())

    gui.bind('<Alt-F4>', lambda _: exit_project())
    gui.bind('<Control-Key-l>', lambda _: install_libraries())
    gui.bind('<F8>', lambda _: show_settings())
    gui.bind('<F5>', lambda _: run_project())

    gui.protocol('WM_DELETE_WINDOW', exit_project)

    # Open recent file
    recent_filepath = config['recent.file.path']

    if (recent_filepath and config['always.open.recent']):
        try:
            with open(recent_filepath, 'r') as file:
                if (file.readable() == False):
                    messagebox('The recent file is not readable, couldn\'t open the file.', 'err')
                else:
                    text = file.read()

                    editor.delete('1.0', END)
                    editor.insert('1.0', text)
            
                    file.close()

                    set_file_path(recent_filepath)
                    set_edited(False)

                    status_bar.config(text='Opened recent file: ' + recent_filepath)

                    change_syntax_highlighting(editor)
        except:
            pass

    gui.mainloop()

IDE()