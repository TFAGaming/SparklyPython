from tkinter import *
from tkinter import messagebox as tkinter_messagebox
from tkinter import filedialog
from tkinter import colorchooser
from tklinenums import TkLineNumbers
from threading import Thread, Event
from typing import Callable
import ttkthemes
import tkinter.ttk as ttk
import idlelib.colorizer as idlecolorizer
import idlelib.percolator as idlepercolator
import requests, webbrowser
import re
import json
import subprocess
import platform
import os
import difflib
import ast
import importlib.util as importlib_util
import keyword, builtins, pkg_resources

__version__ = 'v1.4.0-beta-3'

def messagebox(content: str, type: str, title=None):
    if (type == 'info'):
        tkinter_messagebox.showinfo(title or 'SparklyPython - Info', content)
    elif (type == 'error'):
        tkinter_messagebox.showerror(title or 'SparklyPython - Error', content)
    elif (type == 'warning'):
        tkinter_messagebox.showwarning(title or 'SparklyPython - Warning', content)
    else:
        pass
    
def find_best_matching_keys(string, array, threshold=0.5):
    similar_keys = []
    for key in array:
        similarity_ratio = difflib.SequenceMatcher(None, string, key).ratio()
        if similarity_ratio >= threshold:
            similar_keys.append((key, similarity_ratio))
        
    similar_keys.sort(key=lambda x: x[1], reverse=True)
        
    return similar_keys
    
def center(win:Toplevel|Tk):
    win.update_idletasks()

    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width

    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width

    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2

    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

class SparklyPythonNotebookWindow(Toplevel):
    def __init__(self, master:Tk, title:str, settings, on_ok: Callable[[Toplevel, list], None], geometry=None):
        super().__init__()

        self.result = []
        self.master = master

        self.geometry(geometry or '400x300')
        self.resizable(False, False)
        self.title(title)

        self.loading = None

        try:
            self.iconbitmap('./icon.ico')
        except: pass

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=TRUE, fill=BOTH, padx=5, pady=5)

        self.results = []

        self.split_notebooks(settings)

        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(side=BOTTOM, pady=10, padx=10)

        save_button = ttk.Button(buttons_frame, width=10, text='OK', command=lambda: on_ok(self, self.results))
        save_button.pack(side=RIGHT, padx=5)

        cancel_button = ttk.Button(buttons_frame, width=10, text='Cancel', command=self.destroy)
        cancel_button.pack(side=LEFT, padx=5)

        self.notebook.bind('<Button-1>', lambda _: self.notebook.focus_set()) 

        center(self)

    def split_notebooks(self, settings):
        for setting in settings:
            page_name = setting[0]
            page_settings = setting[1]

            page_frame = self.create_widgets(page_settings)
            page_frame.pack(expand=TRUE, fill=BOTH)

            self.notebook.add(page_frame, text=page_name, state=DISABLED if len(page_settings) <= 0 else NORMAL)

    def create_widgets(self, page_settings):
        main_frame = ttk.Frame(self.notebook)

        for setting in page_settings:
            secondary_frame = ttk.Frame(main_frame)

            widget_type = setting[1]

            if widget_type == 'Entry':
                label, _, default_value, config_value = setting

                self.create_entry(secondary_frame, label, default_value, config_value)
            elif widget_type == 'Checkbutton':
                label, _, default_value, config_value = setting

                self.create_checkbutton(secondary_frame, label, default_value, config_value)
            elif widget_type == 'Dropdown':
                label, _, options, default_value, config_value = setting

                self.create_dropdown(secondary_frame, label, options, default_value, config_value)
            elif widget_type == 'Color':
                label, _, default_value, config_value = setting

                self.create_colorchooser(secondary_frame, label, default_value, config_value)
            else:
                label = setting

                self.create_label(secondary_frame, label)
            
            secondary_frame.pack(fill=X, side=TOP, padx=5, pady=5)
        
        return main_frame
    
    def create_label(self, secondary_frame, label):
        label_widget = ttk.Label(secondary_frame, text=label, justify=LEFT)
        label_widget.pack(side=LEFT, fill=X)

        label_widget.bind('<Configure>', lambda _: label_widget.config(wraplength=self.winfo_width() - 50))

    def create_entry(self, secondary_frame, label, default_value, config_value):
        ttk.Label(secondary_frame, text=label).pack(side=LEFT)
        entry_var = StringVar(self.notebook, value=default_value)

        entry = ttk.Entry(secondary_frame, textvariable=entry_var, width=35)
        entry.pack(side=RIGHT, padx=5)
        self.results.append((entry_var, config_value))

    def create_checkbutton(self, secondary_frame, label, default_value, config_value):
        checkbutton_var = BooleanVar(self.notebook, value=default_value)

        checkbutton = ttk.Checkbutton(secondary_frame, text=label, variable=checkbutton_var)
        checkbutton.pack(side=LEFT)
        self.results.append((checkbutton_var, config_value))

    def create_dropdown(self, secondary_frame, label, options, default_value, config_value):
        ttk.Label(secondary_frame, text=label).pack(side=LEFT)
        dropdown_var = StringVar(self.notebook, value=default_value)

        dropdown = ttk.Combobox(secondary_frame, textvariable=dropdown_var, values=options, state='readonly', width=32)
        dropdown.pack(side=RIGHT, padx=5)
        self.results.append((dropdown_var, config_value))

    def create_colorchooser(self, secondary_frame, label, default_value, config_value):
        ttk.Label(secondary_frame, text=label).pack(side=LEFT)
        entry_var = StringVar(self.notebook, value=default_value)

        def open_color_chooser():
            res = colorchooser.askcolor(default_value)

            if (res[1] == None): return

            entry_var.set(res[1].upper())

        def reset_color():
            for key in self.master.default_settings:
                if (key[0] == config_value):
                    entry_var.set(key[1])
                
        reset_button = ttk.Button(secondary_frame, text='Reset', command=reset_color, width=10)
        reset_button.pack(side=RIGHT, padx=5)

        chooser_button = ttk.Button(secondary_frame, text='Edit', command=open_color_chooser, width=10)
        chooser_button.pack(side=RIGHT, padx=5)

        entry = ttk.Entry(secondary_frame, textvariable=entry_var, width=10, state=DISABLED)
        entry.pack(side=RIGHT, padx=5)

        self.results.append((entry_var, config_value))

class SparklyPythonTooltip:
    def __init__(self, widget:Button, text:str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)

    def show_tooltip(self):
        x, y, _, _ = self.widget.bbox(INSERT)
        x += self.widget.winfo_rootx() + 80
        y += self.widget.winfo_rooty() + 30

        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip_window, text=self.text, background='#FFFFE0', relief=SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()

    def enter(self, event):
        self.id = self.widget.after(1000, self.show_tooltip)

    def leave(self, event):
        if self.id:
            self.widget.after_cancel(self.id)
        self.hide_tooltip()

class SparklyPythonLoadingTopLevel(Toplevel):
    def __init__(self, total:int):
        super().__init__()

        self.total = total

        self.step = 0

        self.title('Loading...')
        self.geometry('250x50')
        self.resizable(0, 0)

        try:
            self.iconbitmap('./icon.ico')
        except: pass
        
        def on_closing(): pass

        self.protocol("WM_DELETE_WINDOW", on_closing)

        self.label = ttk.Label(self, text='0%')
        self.label.pack(side=TOP)

        self.progress_bar_variable = IntVar(self)

        self.progress_bar = ttk.Progressbar(self, maximum=100, mode='determinate', value=0, variable=self.progress_bar_variable, length=250)
        self.progress_bar.pack(side=LEFT, fill=X, padx=5, pady=5)

        center(self)

    def set_values(self, total):
        self.total = total

    def reset(self, reset_total=False):
        self.step = 0

        if (reset_total): self.total = 0

    def add_step(self):
        self.step += 1

        res = (self.step / self.total) * 100
        
        try:
            self.label.config(text=f'{round(res)}%')
            self.progress_bar_variable.set(res)
        except: pass

    def reached_max(self):
        return True if self.step >= self.total else False

class SparklyPythonAutocomplete():
    def __init__(self, master:Tk, text:Text, keywords:list[str]):
        self.text = text
        self.default_keywords = keywords
        self.keywords = keywords
        self.master = master
        self.extracted_variables = []

        self.__version__ = '1.0.0-beta-3'

        self.listbox_frame = None
        self.listbox = None
        self.scrollbar = None
        
        self.details_label = None
        self.cache_details_variables = []
        self.cache_class_methods_details = []

        self.text.bind_all('<Key>', self.key_pressed)

    def extract_variables(self):
        try:
            code = self.text.get('1.0', END)

            parsed_code = ast.parse(code)
    
            result = []

            for node in ast.walk(parsed_code):
                if isinstance(node, ast.FunctionDef):
                    result.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    result.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result.append(target.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name):
                        result.append(node.target.id)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        result.append(alias.asname or alias.name)

            return result
        except:
            return []
        
    def get_members_from_module(self, module):
        try:
            spec = importlib_util.find_spec(module)

            if spec is None:
                return []
            
            with open(spec.origin, 'r') as f:
                source_code: str = f.read()

            exported_members = []
            source_code_splitted = source_code.split('\n')

            for line in source_code_splitted:
                if (line.startswith('#')): continue

                match = re.match(r"from\s+\w+(\.\w+)*\s+import\s+(\w+)", line)

                if match:
                    imported_module_name = match.group(2)

                    exported_members.append(imported_module_name)

            tree = ast.parse(source_code)
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    exported_members.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    exported_members.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exported_members.append(target.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name):
                        exported_members.append(node.target.id)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        exported_members.append(alias.asname or alias.name)
            
            return list(set(exported_members))
        except:
            return []
        
    def get_variable_details(self):
        try:
            code = self.text.get('1.0', END)

            parsed_code = ast.parse(code)
    
            result = []

            def extract_comments(node):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        return node.body[0].value.s.strip()
                return None

            for node in ast.walk(parsed_code):
                if isinstance(node, ast.FunctionDef):
                    args = []

                    for arg in node.args.args:
                        arg_annotation = getattr(arg, 'annotation', None)
                        annotation_type = ast.dump(arg_annotation) if arg_annotation else None

                        if (annotation_type):
                            match = re.search(r"id='(\w+)'", annotation_type)

                            args.append({ 'arg': arg.arg, 'annotation': match.group(1) if match else None })
                        else:
                            args.append({ 'arg': arg.arg, 'annotation': None })

                    return_type = ast.dump(node.returns) if node.returns else None
                    return_type_match = re.search(r"id='(\w+)'", return_type) if return_type else None

                    result.append({ 'name': node.name, 'type': 'function', 'args': args, 'returns': return_type_match.group(1) if return_type_match else None, 'comments': extract_comments(node) })
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                            args = []

                            for arg in item.args.args:
                                arg_annotation = getattr(arg, 'annotation', None)
                                annotation_type = ast.dump(arg_annotation) if arg_annotation else None

                                if (annotation_type):
                                    match = re.search(r"id='(\w+)'", annotation_type)

                                    args.append({ 'arg': arg.arg, 'annotation': match.group(1) if match else None })
                                else:
                                    args.append({ 'arg': arg.arg, 'annotation': None })

                            result.append({ 'name': node.name, 'type': 'class', 'args': args, 'returns': None, 'comments': extract_comments(node) })

            return result
        except:
            return []
        
    def get_class_methods_details(self):
        try:
            code = self.text.get('1.0', END)

            parsed_code = ast.parse(code)
    
            result = []

            def extract_comments(node):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        return node.body[0].value.s.strip()
                return None

            for node in ast.walk(parsed_code):
                if isinstance(node, ast.ClassDef):
                    functions = []
                    variables = []

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = []

                            for arg in item.args.args:
                                arg_annotation = getattr(arg, 'annotation', None)
                                annotation_type = ast.dump(arg_annotation) if arg_annotation else None

                                if (annotation_type):
                                    match = re.search(r"id='(\w+)'", annotation_type)

                                    args.append({ 'arg': arg.arg, 'annotation': match.group(1) if match else None })
                                else:
                                    args.append({ 'arg': arg.arg, 'annotation': None })

                            return_type = ast.dump(item.returns) if item.returns else None
                            return_type_match = re.search(r"id='(\w+)'", return_type) if return_type else None

                            functions.append({ 'name': item.name, 'args': args, 'returns': return_type_match.group(1) if return_type_match else None, 'comments': extract_comments(node) })
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    variables.append(target.id)

                    result.append({ 'name': node.name, 'functions': functions, 'variables': variables })

            return result
        except:
            return []
        
    def get_installed_packages(self):
        try:
            packages = list([i.key.replace('-', '_') for i in pkg_resources.working_set])
            return packages
        except:
            return []

    def show_popup(self, matching_keys):
        if not matching_keys:
            self.hide_popup()
            return

        cursor_index = self.text.index(INSERT)
        zoom = self.master.editor_font[1]

        try:
            x, y = self.text.bbox(cursor_index)[:2]
            x += self.text.winfo_x()

            x += self.master.linenumbers_frame.winfo_width() + self.master.explorer_frame.winfo_width()
            y += zoom * 2

            if not self.listbox_frame:
                self.listbox_frame = ttk.Frame(self.master)
                self.listbox_frame.place(x=x, y=y)

                self.listbox = Listbox(self.listbox_frame, background=self.master.style.lookup('TFrame', 'background'), width=30, font=(self.master.editor_font[0], self.master.editor_font[1] - 2))

                self.listbox.bind('<ButtonRelease-1>', self.on_listbox_select)

                self.text.bind('<Tab>', self.tab_or_enter_pressed)
                self.text.bind('<Up>', self.arrow_up_pressed)
                self.text.bind('<Down>', self.arrow_down_pressed)
                self.text.bind('<Button-1>', lambda _: self.hide_popup())

                self.listbox.pack(side=LEFT)

                self.scrollbar = ttk.Scrollbar(self.listbox_frame, command=self.listbox.yview)
                self.scrollbar.pack(side=RIGHT, fill=Y)
                self.listbox.config(yscrollcommand=self.scrollbar.set)
            else:
                self.listbox_frame.place_configure(x=x, y=y)

            self.listbox.delete(0, END)
            for key in matching_keys:
                self.listbox.insert(END, key)
        
            self.listbox.select_set(0)
        except: pass

    def show_popup_details_label(self, message: str):
        cursor_index = self.text.index(INSERT)
        zoom = self.master.editor_font[1]

        try:
            x, y = self.text.bbox(cursor_index)[:2]
            x += self.text.winfo_x()

            y += zoom * 2

            if not self.details_label:
                self.details_label = ttk.Label(self.text, text=message, background='#FFFFE0', font=self.master.editor_font, relief=SOLID, borderwidth=1)
                
                self.details_label.pack()

                self.details_label.place_configure(x=x, y=y)

                self.text.bind('<Tab>', lambda _: self.hide_popup_details_label())
                self.text.bind('<Up>', lambda _: self.hide_popup_details_label())
                self.text.bind('<Down>', lambda _: self.hide_popup_details_label())
                self.text.bind('<Enter>', lambda _: self.hide_popup_details_label())
                self.text.bind('<Button-1>', lambda _: self.hide_popup_details_label())          
            else:
                self.details_label.place_configure(x=x, y=y)
        except: pass

    def hide_popup(self):
        if self.listbox_frame:
            self.listbox_frame.destroy()
            self.listbox_frame = None
            self.listbox = None
            self.scrollbar = None

            self.text.unbind('<Tab>')
            self.text.unbind('<Up>')
            self.text.unbind('<Down>')

    def hide_popup_details_label(self):
        if self.details_label:
            self.details_label.destroy()
            self.details_label = None

    def key_pressed(self, event):
        if ('autocomplete.enabled' in self.master.settings and not self.master.settings['autocomplete.enabled']): return
        
        self.keywords = self.default_keywords
        variables = self.extract_variables()

        if (len(variables) > 0):
            self.extracted_variables = variables

        self.keywords += self.extracted_variables
        self.keywords = list(set(self.keywords)) # Removing duplicates

        self.master.after(10, self.get_current_text)

    def get_current_text(self):
        current_text = self.text.get('insert linestart', INSERT)

        if (len(current_text) <= 0):
            self.hide_popup()
            return
        
        splitted = current_text.split(' ')
        splitted = [s.replace('\t', '') for s in splitted]
        index = len(splitted) - 1

        _variables_details = self.get_variable_details()
        if _variables_details != []: self.cache_details_variables = _variables_details

        _class_methods_details = self.get_class_methods_details()
        if _class_methods_details != []: self.cache_class_methods_details = _class_methods_details

        if (current_text[len(current_text) - 1] == ' ' or current_text[len(current_text) - 1] == '\t'):
            self.hide_popup()
            return
        
        if index >= 0:
            previous_index = index - 1

            if (previous_index < 0): previous_index = 0
            
            previous_word = splitted[previous_index]
            current_word = splitted[index]

            if ('.' in current_word and len(current_word.split('.')) >= 2):
                if (current_word.split('.')[1] != ''):
                    self.hide_popup()

                    for detail in self.cache_class_methods_details:
                        if detail['name'] == current_word.split('.')[0]:
                            functions = detail['functions']

                            for function in functions:
                                if function['name'] == current_word.split('.')[1]:
                                    self.hide_popup_details_label()

                                    result = []

                                    for arg in function['args']:
                                        result.append(arg['arg'] + ': ' + ('any' if arg['annotation'] == None else arg['annotation']))

                                    string = '(' + ', '.join(result) + ') -> ' + (function['returns'] if function['returns'] != None else 'any') + (('\n' + function['comments']) if function['comments'] != None else '')

                                    self.show_popup_details_label(string)

                        break
                    return

            if (current_word.endswith('.') and current_word.split('.')[0] in [v['name'] for v in self.cache_class_methods_details]):
                self.hide_popup()

                for detail in self.cache_class_methods_details:
                    if detail['name'] == current_word.split('.')[0]:
                        variables = detail['variables']
                        functions = [v['name'] for v in detail['functions']]

                        self.show_popup_details_label(f'Methods and variables defined in \'' + detail['name'] + '\': \n' + '\n'.join(variables + functions) + '\n')
                        
                        break
                return
            else:
                self.hide_popup_details_label()
            
            if (current_word.endswith('(') and current_word.split('(')[0] in [v['name'] for v in self.cache_details_variables]):
                self.hide_popup()

                for detail in self.cache_details_variables:
                    if detail['name'] == current_word.split('(')[0]:
                        result = []

                        for arg in detail['args']:
                            result.append(arg['arg'] + ': ' + ('any' if arg['annotation'] == None else arg['annotation']))

                        string = '(' + ', '.join(result) + ') -> ' + (detail['returns'] if detail['returns'] != None else 'any') + (('\n' + detail['comments']) if detail['comments'] != None else '')

                        self.show_popup_details_label(string)
                        
                        break
                return
            else:
                self.hide_popup_details_label()

            if (current_word.endswith('(') or current_word.endswith(')') or current_word.endswith('"') or current_word.endswith('\'')):
                self.hide_popup()
                return

            packages_installed = self.get_installed_packages()

            keywords = self.keywords

            if (current_word.split('.')[0] in packages_installed):
                keywords = self.get_members_from_module(current_word.split('.')[0])

            if  (previous_word == 'import' or previous_word == 'from'):
                match = re.match(r"from\s+(\w+)\s+import", current_text)
                if match:
                    module_name = match.group(1)
                    module_members: list[str] = self.get_members_from_module(module_name)

                    keywords = module_members
                else:
                    keywords = packages_installed

            if any(keyword == current_word for keyword in keywords):
                self.hide_popup()
                return
        
            if (self.master.settings['autocomplete.matchcase']):
                matching_keys = [key for key in keywords if key.startswith(current_word)]
            else:
                matching_keys = []
                best_match = find_best_matching_keys(current_word, keywords, threshold=0.1)
            
                for match in best_match:
                    matching_keys.append(match[0])

            self.show_popup(matching_keys)

    def on_listbox_select(self, event):
        configured_indentation = self.master.settings['editor.indentation']

        global indentation
        indentation = '\t'
        
        if (configured_indentation != 'TAB' and configured_indentation.isdigit()):
            indentation = ' ' * int(configured_indentation)

        if self.listbox:
            selected_item: str = self.listbox.get(self.listbox.curselection())

            if selected_item:
                current_text = self.text.get('insert linestart', INSERT)
                splitted = current_text.split(' ')
                splitted = [s.replace('\t', '') for s in splitted]
                index = len(splitted) - 1
                insert_index = self.text.index(INSERT)

                if index >= 0:
                    tabs_count = current_text.count(indentation)

                    full_text = self.text.get('insert linestart', 'insert lineend')
                    second_splitted = full_text.split(' ')
                    second_splitted = [s.replace('\t', '') for s in second_splitted]

                    new_text = f'{indentation * tabs_count}' + ' '.join(splitted[:index] + [selected_item] + second_splitted[index + 1:])

                    self.text.replace(f'{INSERT} linestart', f'{INSERT} lineend', new_text)
                    # The undo and then redo makes Idlelib's colorizer to apply the colors again
                    self.text.edit_undo()
                    self.text.edit_redo()

                    selected_item_index = self.text.search(selected_item, insert_index, 'insert lineend')

                    if selected_item_index:
                        line, column = map(int, selected_item_index.split('.'))
                        new_index = f'{line}.{column + len(selected_item)}'
                        self.text.mark_set(INSERT, new_index)

                self.hide_popup()
                self.text.focus_set()

                return 'break'

    def tab_or_enter_pressed(self, event):
        self.master.after(10, self.pressed_after)

        return 'break'

    def pressed_after(self):
        configured_indentation = self.master.settings['editor.indentation']

        global indentation
        indentation = '\t'
        
        if (configured_indentation != 'TAB' and configured_indentation.isdigit()):
            indentation = ' ' * int(configured_indentation)

        if self.listbox:
            selected_item = self.listbox.get(self.listbox.curselection())

            if selected_item:
                current_text = self.text.get('insert linestart', INSERT)
                splitted = current_text.split(' ')
                splitted = [s.replace('\t', '') for s in splitted]
                index = len(splitted) - 1
                insert_index = self.text.index(INSERT)

                if index >= 0:
                    tabs_count = current_text.count(indentation)

                    full_text = self.text.get('insert linestart', 'insert lineend')
                    second_splitted = full_text.split(' ')
                    second_splitted = [s.replace('\t', '') for s in second_splitted]

                    new_text = f'{indentation * tabs_count}' + ' '.join(splitted[:index] + [selected_item] + second_splitted[index + 1:])

                    self.text.replace(f'{INSERT} linestart', f'{INSERT} lineend', new_text)
                    # The undo and then redo makes Idlelib's colorizer to apply the colors again
                    self.text.edit_undo()
                    self.text.edit_redo()

                    selected_item_index = self.text.search(selected_item, insert_index, 'insert lineend')

                    if selected_item_index:
                        line, column = map(int, selected_item_index.split('.'))
                        new_index = f'{line}.{column + len(selected_item)}'
                        self.text.mark_set(INSERT, new_index)

                self.hide_popup()

                return 'break'

    def arrow_up_pressed(self, event):
        if self.listbox:
            current_selection = self.listbox.curselection()

            if current_selection:
                if current_selection[0] > 0:
                    self.listbox.select_clear(current_selection[0])
                    self.listbox.select_set(current_selection[0] - 1)
                    self.listbox.see(current_selection[0] - 1)
                else:
                    self.listbox.select_clear(current_selection[0])
                    self.listbox.select_set(self.listbox.size() - 1)
            else:
                self.listbox.select_set(self.listbox.size() - 1)

        return 'break'
    
    def arrow_down_pressed(self, event):
        if self.listbox:
            current_selection = self.listbox.curselection()

            if current_selection:
                if current_selection[0] < self.listbox.size() - 1:
                    self.listbox.select_clear(current_selection[0])
                    self.listbox.select_set(current_selection[0] + 1)
                    self.listbox.see(current_selection[0] + 1)
                else:
                    self.listbox.select_clear(current_selection[0])
                    self.listbox.select_set(0)
        
        return 'break'

class SparklyPythonExplorer():    
    def __init__(self, treeview: ttk.Treeview, root: Tk):
        self.treeview = treeview
        self.root = root

        self.treeview.bind("<<TreeviewSelect>>", self.on_select)

    def populate(self, parent: str, folder: str, path_so_far=''):
        if (len(folder) <= 0): return

        items = os.listdir(folder)

        for item in items:
            item_path = os.path.join(folder, item)
            full_path = os.path.join(path_so_far, item)

            if os.path.isdir(item_path):
                folder_icon = self.treeview.insert(parent, 'end', text=f' {item}', open=False, values=(full_path, 'dir'))

                self.populate(folder_icon, item_path, path_so_far=full_path)
            else:
                if (str(item).endswith('.py')): 
                    self.treeview.insert(parent, 'end', text=f' {item}', values=(full_path, 'file'))
                else:
                    self.treeview.insert(parent, 'end', text=f' {item}', values=(full_path, 'file'))

    def on_select(self, event):
        selected_item = self.treeview.selection()

        if (not selected_item): return

        full_path: str = os.path.join(self.root.startup_explorer_dir, self.treeview.item(selected_item, 'values')[0]).replace('\\', '/')
        typeof = self.treeview.item(selected_item, 'values')[1]

        if (typeof == 'file'):
            if (full_path.endswith('.py')):
                self.root.open_file(custom_path=full_path)
            else:
                if (self.root.settings['filesexplorer.defaultopennonpythonfiles']):
                    os.startfile(full_path)

    def clear(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)

class StoppableThread(Thread):
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class SparklyPythonIDE(Tk):    
    def __init__(self):
        super().__init__()

        self.style = ttkthemes.ThemedStyle(self)
        self.style.set_theme(theme_name='arc')

        try:
            self.iconbitmap('./icon.ico')
        except: pass

        self.current_file_path = ''
        self.startup_explorer_dir = ''
        self.current_main_dir = ''
        self.text_edited = False
        self.settings = {
            'previous_file_path': '',
            'startup_explorer_dir': ''
        }
        self.default_settings = [
            ('window.update_check', True),
            ('terminal.python_command', 'python'), ('terminal.pause', True), ('terminal.save_file', True),
            ('linenumbers.enabled', True), ('linenumbers.justify', 'Right'),
            ('filesexplorer.enabled', True), ('filesexplorer.defaultopennonpythonfiles', True),
            ('editor.indentation', 'TAB'), ('editor.indentation_on_line', True), ('editor.open_previous_file', True), ('editor.font_name', 'Courier New'), ('editor.autosave', False),
            ('highlighter.comment', '#808080'), ('highlighter.keyword', '#1220E6'), ('highlighter.builtin', '#FF0000'), ('highlighter.string', '#008000'), ('highlighter.def', '#7F7F00'), ('highlighter.number', '#FF6600'),
            ('autocomplete.enabled', True), ('autocomplete.matchcase', False),
        ]
        self.python_process = None
        self.loading = None

        for setting in self.default_settings:
            self.settings[setting[0]] = setting[1]

        self.title('SparklyPython')
        self.geometry('1200x700')

        self.check_configuration_file()
        
        # Menu bar configuration
        self.menu_bar = Menu(self)
        
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label='New', command=self.new_file, accelerator='Ctrl+N')
        file_menu.add_separator()
        file_menu.add_command(label='Open File', command=lambda: self.open_file(explorer=True), accelerator='Ctrl+O')
        file_menu.add_separator()
        file_menu.add_command(label='Save', command=self.save_file, accelerator='Ctrl+S')
        file_menu.add_command(label='Save As...', command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.exit_program, accelerator='Alt+F4')

        self.menu_bar.add_cascade(label='File', menu=file_menu)

        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label='Undo', command=self.editor_undo, accelerator='Ctrl+Z')
        edit_menu.add_command(label='Redo', command=self.editor_redo, accelerator='Ctrl+Y')
        edit_menu.add_separator()
        edit_menu.add_command(label='Zoom In', command=self.editor_zoom_in, accelerator='Ctrl+Plus')
        edit_menu.add_command(label='Zoom Out', command=self.editor_zoom_out, accelerator='Ctrl+Minus')
        edit_menu.add_separator()
        edit_menu.add_command(label='Format Indentation', command=self.editor_format_indentation, accelerator='Shift+Alt+F')
        edit_menu.add_separator()
        edit_menu.add_command(label='Copy', command=lambda: self.editor.event_generate("<<Copy>>"), accelerator='Ctrl+C')
        edit_menu.add_command(label='Cut', command=lambda: self.editor.event_generate("<<Cut>>"), accelerator='Ctrl+X')
        edit_menu.add_command(label='Paste', command=lambda: self.editor.event_generate("<<Paste>>"), accelerator='Ctrl+V')

        self.menu_bar.add_cascade(label='Edit', menu=edit_menu)

        python_menu = Menu(self.menu_bar, tearoff=0)
        python_menu.add_command(label='New Prompt', command=self.python_new_prompt)
        python_menu.add_separator()
        python_menu.add_command(label='Run Python', command=self.python_run, accelerator='F5')
        python_menu.add_command(label='Stop Python', command=self.python_stop)

        self.menu_bar.add_cascade(label='Python', menu=python_menu)
        
        self.menu_bar.add_command(label='Settings', command=self.open_settings)

        self.menu_bar.add_command(label='About', command=self.open_about)

        # Add menus to the menu bar
        self.config(menu=self.menu_bar)

        # All required frames
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=X, pady=5, side=BOTTOM)

        self.main = ttk.Frame(self)
        self.main.pack(expand=TRUE, fill=BOTH)

        self.editor_frame = ttk.Frame(self.main)
        self.editor_frame.pack(side=RIGHT, expand=TRUE, fill=BOTH)

        self.explorer_frame = ttk.Frame(self.main)
        self.explorer_frame.pack(side=LEFT, fill=Y)

        self.linenumbers_frame = ttk.Frame(self.main)
        self.linenumbers_frame.pack(side=LEFT, fill=Y)

        # Adding scroll bars
        self.editor_scrollbar_yview = ttk.Scrollbar(self.editor_frame, orient=VERTICAL)
        self.editor_scrollbar_yview.pack(side=RIGHT, fill=Y)

        self.editor_scrollbar_xview = ttk.Scrollbar(self.editor_frame, orient=HORIZONTAL)
        self.editor_scrollbar_xview.pack(side=BOTTOM, fill=X)

        # Create the editor and ballon tip
        self.editor_font = (self.settings['editor.font_name'], 10)

        self.editor = Text(self.editor_frame, undo=True, wrap=NONE, font=self.editor_font, background=self.style.lookup('TFrame', 'background'))
        self.editor.pack(side=RIGHT, expand=TRUE, fill=BOTH, padx=5, pady=5)

        # Autocomplete
        self.python_keywords = sorted(keyword.kwlist + dir(builtins))

        self.autocomplete = SparklyPythonAutocomplete(self, self.editor, self.python_keywords)

        # Bindings configuration
        self.editor.bind('<Return>', lambda _: self.editor_new_line())
        self.editor.bind('<Button-3>', self.editor_show_rightclick_commands)
        self.editor.bind('<Button-1>', lambda _: self.editor_update_line_info())
        self.editor.bind('<Control-Key-s>', lambda _: self.save_file())
        self.editor.bind('<Control-Key-o>', lambda _: self.save_as_file())
        self.editor.bind('<Control-Key-n>', lambda _: self.new_file())
        self.editor.bind('<Control-Key-f>', lambda _: self.editor_search_keyword())
        self.editor.bind('<Shift-Alt-F>', lambda _: self.editor_format_indentation())

        self.editor.bind('<Key>', lambda _: self.after(10, self.editor_key_pressed))

        self.bind('<Alt-F4>', lambda _: self.exit_program())
        self.bind('<F8>', lambda _: self.python_new_prompt())
        self.bind('<F5>', lambda _: self.python_run())
        self.bind('<Control-KeyPress-plus>', lambda _: self.editor_zoom_in())
        self.bind('<Control-KeyPress-minus>', lambda _: self.editor_zoom_out())

        self.protocol('WM_DELETE_WINDOW', self.exit_program)

        # Main line numbers widget
        self.linenumbers = TkLineNumbers(self.linenumbers_frame, textwidget=self.editor, justify=RIGHT if self.settings['linenumbers.justify'] == 'Right' else LEFT)

        if (self.settings['linenumbers.enabled']): self.linenumbers.pack(expand=TRUE, fill=Y, padx=5, pady=5)

        # Explorer
        self.explorer = ttk.Treeview(self.explorer_frame)
        self.explorer.heading('#0', text='Files Explorer')

        if (self.settings['filesexplorer.enabled']): self.explorer.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        
        self.explorer_manager = SparklyPythonExplorer(self.explorer, self)

        # Configuring scroll bar
        self.editor_scrollbar_yview.config(command=self.scroll_both_y)
        self.editor_scrollbar_xview.config(command=self.scroll_both_x)
        self.editor.config(yscrollcommand=self.update_scroll_y, xscrollcommand=self.update_scroll_x)

        # Status frame
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X)

        status_frame_run_button = ttk.Button(self.status_frame, text='Run', width=10, command=self.python_run)
        status_frame_run_button.pack(side=LEFT, padx=10)
        ttk.Separator(self.status_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        SparklyPythonTooltip(status_frame_run_button, 'Starts a new Python prompt and runs the code.')

        self.status_text = ttk.Label(self.status_frame, text='Getting everything ready...', justify=LEFT)
        self.status_text.pack(side=LEFT, padx=10)

        ttk.Label(self.status_frame, text='Version: ' + __version__, justify=RIGHT).pack(side=RIGHT, padx=10)
        ttk.Separator(self.status_frame, orient=VERTICAL).pack(side=RIGHT, fill=Y, padx=10)

        self.line_info_text = ttk.Label(self.status_frame, text='Ln 0, Col 0, Char 0', justify=RIGHT)
        self.line_info_text.pack(side=RIGHT, padx=10)
        ttk.Separator(self.status_frame, orient=VERTICAL).pack(side=RIGHT, fill=Y, padx=10)

        # Open previous file
        if (self.settings['editor.open_previous_file'] and len(self.settings['previous_file_path']) > 0):
            try:
                with open(self.settings['previous_file_path'], 'r') as file:
                    text = file.read().strip()

                    self.editor.delete('1.0', END)
                    self.editor.insert('1.0', text)
            
                    file.close()

                self.current_file_path = self.settings['previous_file_path']
                self.startup_explorer_dir = self.settings['startup_explorer_dir']

                self.set_window_title_status(edited=False)

                self.highlight_python_source()
                self.linenumbers.redraw()

                self.editor.edit_reset()

                self.update_status_message('Loaded previous file: ' + self.current_file_path)
            except:
                self.update_status_message('Failed to open previous file; The file was deleted or it\'s path was modified.')
        else:
            self.update_status_message('SparklyPython is now ready.')

        self.config(background=self.style.lookup('TFrame', 'background'))

        center(self)

        global explorer_thread

        def explorer_main():
            self.explorer_manager.populate('', self.startup_explorer_dir)
            explorer_thread.stop()
        
        explorer_thread = StoppableThread(target=explorer_main)
        explorer_thread.start()

        if (self.settings['window.update_check']):
            self.check_updates()
    
    def check_configuration_file(self):
        try:
            with open('sparklypython-config.json', 'r') as file:
                loaded_config = json.load(file)

                global has_all_keys
                has_all_keys = True
                array_settings = []

                for key in self.settings: array_settings.append(key)

                for key in loaded_config:
                    if key in array_settings: continue

                    has_all_keys = False
                    break

                if (has_all_keys):
                    self.settings = loaded_config
                else:
                    self.write_configuration_file(self.settings)
        except:
            try:
                open('sparklypython-config.json', 'x')
                
                self.write_configuration_file(self.settings)

                self.check_configuration_file()
            except:
                messagebox('Error', 'err')

    def write_configuration_file(self, data):
        try:
            with open('sparklypython-config.json', 'w') as file:
                string = json.dumps(data, indent=4)

                file.write(string)
                file.close()

                self.update_status_message('Your changes has been successfully saved.')
        except:
            messagebox('Failed to save the configuration, please enable the program to read, write, and create files.', 'err')

    def update_widgets_from_configuration_file(self):
        restart_message = False

        if (self.settings['linenumbers.enabled']):
            self.linenumbers.pack(expand=TRUE, fill=Y, padx=5, pady=5)
        else:
            restart_message = True

        self.linenumbers.justify = RIGHT if self.settings['linenumbers.justify'] == 'Right' else LEFT
        self.linenumbers.redraw()

        self.editor_font = (self.settings['editor.font_name'], self.editor_font[1])
        self.editor.config(font=self.editor_font)

        if (restart_message):
            messagebox('You must restart the app to apply these changes.', 'warning')

    def new_file(self):
        def main():
            self.current_file_path = ''
            self.text_edited = False

            self.editor.delete('1.0', END)

            self.set_window_title_status(edited=False)
            self.write_configuration_file(self.settings)

            self.editor.edit_reset()

        if (self.text_edited):
            res = tkinter_messagebox.askyesnocancel('SparklyPython - New File', 'Do you want to save the current file before creating a new file?')

            if (res == True):
                self.save_file()

                main()
            elif (res == False):
                main()
            else: return
        else:
            main()

    def save_file(self):
        if (len(self.current_file_path) <= 0):
            self.save_as_file()
        else:
            try:
                with open(self.current_file_path, 'w') as file:
                    text = self.editor.get('1.0', END).strip()

                    file.write(text)
                    file.close()

                self.text_edited = False

                self.set_window_title_status(edited=False)
            except:
                self.save_as_file()

    def save_as_file(self):
        selected_path = filedialog.asksaveasfilename(filetypes=[('Python', '*py')], title=f'SparklyPython - Save as', defaultextension='py')

        if (len(selected_path) <= 0): return

        try:
            with open(selected_path, 'w') as file:
                text = self.editor.get('1.0', END).strip()

                file.write(text)
                file.close()

            self.current_file_path = selected_path
            self.text_edited = False

            self.set_window_title_status(edited=False)
            self.write_configuration_file(self.settings)
        except:
            messagebox('Unable to perform this action properly.', 'error')

    def open_file(self, custom_path=None, explorer=False):
        if (self.text_edited):
            response = tkinter_messagebox.askyesno('SparklyPython - Open File', 'Do you want to save the current file before opening another one?')

            if (response): self.save_file()

        try:
            selected_path = custom_path if custom_path else filedialog.askopenfilename(filetypes=[('Python', '*py')], title=f'SparklyPython - Open File')

            if (len(selected_path) <= 0): return

            with open(selected_path, 'r') as file:
                text = file.read().strip()
                
                self.editor.delete('1.0', END)
                self.editor.insert('1.0', text)
                self.editor.edit_reset()
            
                file.close()

            self.current_file_path = selected_path
            self.settings['previous_file_path'] = selected_path

            if (explorer):
                self.startup_explorer_dir = os.path.dirname(self.current_file_path)
                self.settings['startup_explorer_dir'] = self.startup_explorer_dir

                self.explorer_manager.clear()

                global explorer_thread

                def explorer_main():
                    self.explorer_manager.populate('', self.startup_explorer_dir)
                    explorer_thread.stop()
        
                explorer_thread = StoppableThread(target=explorer_main)
                explorer_thread.start()

            self.text_edited = False

            self.set_window_title_status(edited=False)

            self.highlight_python_source()
            self.linenumbers.redraw()

            self.editor.edit_reset()

            self.write_configuration_file(self.settings)
        except:
            messagebox('Unable to perform this action properly.', 'error')

    def highlight_python_source(self):
        try:
            self.editor.tag_delete('highlight_search_keyword')

            cdg = idlecolorizer.ColorDelegator()

            #cdg.prog = re.compile(r'\b(?P<Group>okbruh)\b|' + idlecolorizer.make_pat().pattern, re.S)
            cdg.prog = re.compile(r'\b(?P<NUMBER>\d+|((0[bB]|0[xX]|0[oO])+[0-9a-fA-F]+))\b|' + idlecolorizer.make_pat().pattern, re.S)

            cdg.idprog = re.compile(r'\s+(\w+|\d+)', re.S)

            #cdg.tagdefs['Group'] = {'foreground': 'color', 'background': None}
            cdg.tagdefs['NUMBER'] = {'foreground': self.settings['highlighter.number'], 'background': None}
            #cdg.tagdefs['HEXBINOCT'] = {'foreground': self.settings['highlighter.hexbinoct'], 'background': None}

            cdg.tagdefs['COMMENT'] = {'foreground': self.settings['highlighter.comment'], 'background': None}
            cdg.tagdefs['KEYWORD'] = {'foreground': self.settings['highlighter.keyword'], 'background': None}
            cdg.tagdefs['BUILTIN'] = {'foreground': self.settings['highlighter.builtin'], 'background': None}
            cdg.tagdefs['STRING'] = {'foreground': self.settings['highlighter.string'], 'background': None}
            cdg.tagdefs['DEFINITION'] = {'foreground': self.settings['highlighter.def'], 'background': None}

            idlepercolator.Percolator(self.editor).insertfilter(cdg)
        except: pass
        
    def open_settings(self):
        settings = [
            (
                'Window', [
                    ('Check updates on startup', 'Checkbutton', self.settings['window.update_check'], 'window.update_check')
                ]
            ),
            (
                'Text Editor', [
                    ('Font name', 'Entry', self.settings['editor.font_name'], 'editor.font_name'),
                    ('Python Indentation', 'Dropdown', ['TAB', 1, 2, 3, 4, 5, 6, 7, 8], self.settings['editor.indentation'], 'editor.indentation'),
                    ('Add Python Indentation on a new line', 'Checkbutton', self.settings['editor.indentation_on_line'], 'editor.indentation_on_line'),
                    ('Open previous file on startup', 'Checkbutton', self.settings['editor.open_previous_file'], 'editor.open_previous_file'),
                    ('Auto-save the current file', 'Checkbutton', self.settings['editor.autosave'], 'editor.autosave')
                ]
            ),
            (
                'Highlighter', [
                    ('If you change one of the settings below, you must restart the app to fully apply the changes.'),
                    ('Comment color', 'Color', self.settings['highlighter.comment'], 'highlighter.comment'),
                    ('Keyword color', 'Color', self.settings['highlighter.keyword'], 'highlighter.keyword'),
                    ('Built-in color', 'Color', self.settings['highlighter.builtin'], 'highlighter.builtin'),
                    ('String color', 'Color', self.settings['highlighter.string'], 'highlighter.string'),
                    ('Definition color', 'Color', self.settings['highlighter.def'], 'highlighter.def'),
                    ('Number (Decimal), Hexadecimal, Binary, Octal color', 'Color', self.settings['highlighter.number'], 'highlighter.number')
                ]
            ),
            (
                'Terminal', [
                    ('Default Python command', 'Entry', self.settings['terminal.python_command'], 'terminal.python_command'),
                    ('Pause before exiting the command prompt', 'Checkbutton', self.settings['terminal.pause'], 'terminal.pause'),
                    ('Save edited file before opening Terminal', 'Checkbutton', self.settings['terminal.save_file'], 'terminal.save_file')
                ]
            ),
            (
                'Line Numbers', [
                    ('If you change one of the settings below, you must restart the app to fully apply the changes.'),
                    ('Enable Line Numbers', 'Checkbutton', self.settings['linenumbers.enabled'], 'linenumbers.enabled'),
                    ('Justify numbers', 'Dropdown', ['Left', 'Right'], self.settings['linenumbers.justify'], 'linenumbers.justify')
                ]
            ),
            (
                'Files Explorer', [
                    ('If you change one of the settings below, you must restart the app to fully apply the changes.'),
                    ('Enable Explorer', 'Checkbutton', self.settings['filesexplorer.enabled'], 'filesexplorer.enabled'),
                    ('Open non-python files', 'Checkbutton', self.settings['filesexplorer.defaultopennonpythonfiles'], 'filesexplorer.defaultopennonpythonfiles')
                ]
            ),
            (
                'Autocomplete', [
                    ('Enable Autocomplete', 'Checkbutton', self.settings['autocomplete.enabled'], 'autocomplete.enabled'),
                    ('Match case each keyword', 'Checkbutton', self.settings['autocomplete.matchcase'], 'autocomplete.matchcase')
                ]
            )
        ]
        
        def on_ok(root:Toplevel, results:list):
            global thread

            def main():
                self.loading = SparklyPythonLoadingTopLevel(len(results))

                for result in results:
                    variable = result[0]
                    key = result[1]

                    if (key in self.settings):
                        self.settings[key] = variable.get()

                        self.loading.add_step()

                self.write_configuration_file(self.settings)
                self.update_widgets_from_configuration_file()
                root.destroy()

                self.loading.destroy()
                self.loading = None

                thread.stop()
            
            thread = StoppableThread(target=main)
            thread.start()

        SparklyPythonNotebookWindow(master=self, title='SparklyPython - Settings', geometry='620x400', settings=settings, on_ok=on_ok)

    def open_about(self):
        settings = [
            (
                f'SparklyPython ({__version__})', [
                    (f'The most powerful, beginner-friendly, and open-source Python IDE.'),
                    (f'Tk version: {TkVersion}\nPython version: {platform.python_version()}\nAutocomplete version: {self.autocomplete.__version__}'),
                    (f'OS: {platform.system()} {platform.release()} {platform.win32_edition()}\nArchitecture: {platform.architecture()[0]}'),
                    (f'Developer: TFAGaming')
                ]
            )
        ]

        def on_ok(root:Toplevel, _):
            root.destroy()

        SparklyPythonNotebookWindow(master=self, title='SparklyPython - About', geometry='300x300', settings=settings, on_ok=on_ok)

    def editor_undo(self):
        try:
            self.editor.edit_undo()
        except: pass

    def editor_redo(self):
        try:
            self.editor.edit_redo()
        except: pass

    def editor_zoom_in(self):
        if (self.editor_font[1] >= 24): return

        self.autocomplete.hide_popup()

        old_value = self.editor_font[1]
        self.editor_font = (self.editor_font[0], old_value + 1)

        self.editor.config(font=self.editor_font)

        self.update_status_message(f'Zoom in ({old_value + 1}%)')
    
    def editor_zoom_out(self):
        if (self.editor_font[1] <= 1): return

        self.autocomplete.hide_popup()

        old_value = self.editor_font[1]
        self.editor_font = (self.editor_font[0], old_value - 1)

        self.editor.config(font=self.editor_font)

        self.update_status_message(f'Zoom out ({old_value - 1}%)')

    def editor_key_pressed(self):
        self.text_edited = True

        self.set_window_title_status(edited=True)

        self.highlight_python_source()

        self.linenumbers.redraw()
        self.editor_update_line_info()

        if (self.settings['editor.autosave']):
            self.after(10, lambda: self.save_file())
        
    def editor_new_line(self):
        self.autocomplete.hide_popup()

        if (not self.settings['editor.indentation_on_line']): return

        configured_indentation = self.settings['editor.indentation']

        global indentation
        indentation = '\t'
        
        if (configured_indentation != 'TAB' and configured_indentation.isdigit()):
            indentation = ' ' * int(configured_indentation)

        cursor_pos = self.editor.index(INSERT)
        current_line = self.editor.get(cursor_pos.split('.')[0] + '.0', cursor_pos)

        if current_line.strip().endswith(':'):
            if (indentation in current_line):
                tabs_count = current_line.count(indentation)
                self.editor.insert(INSERT, '\n' + indentation * (tabs_count + 1))
            else:
                self.editor.insert(INSERT, f'\n{indentation}')
        else:
            cursor_pos = self.editor.index(INSERT)
            current_line = self.editor.get(cursor_pos.split('.')[0] + '.0', cursor_pos)

            if indentation in current_line:
                tabs_count = current_line.count(indentation)
                self.editor.insert(INSERT, '\n' + indentation * (tabs_count))
            else:
                self.editor.insert(INSERT, '\n')

        self.linenumbers.redraw()
        self.editor_update_line_info()

        return 'break'
    
    def editor_format_indentation(self):
        if (self.settings['editor.indentation'] != 'TAB'):
            res = tkinter_messagebox.askokcancel('SparklyPython - Formatter', 'This method will replace any configured indentation to TABs, are you sure about that?')

            if (not res or res == None): return

            text = self.editor.get('1.0', END)

            text = text.replace(' ' * int(self.settings['editor.indentation']), '\t')

            self.editor.delete('1.0', END)
            self.editor.insert('1.0', text)

    def editor_show_rightclick_commands(self, event):
        editor_commands = Menu(self, tearoff=0)
        editor_commands.add_command(label='Undo', command=self.editor_undo, accelerator='Ctrl+Z')
        editor_commands.add_command(label='Redo', command=self.editor_redo, accelerator='Ctrl+Y')
        editor_commands.add_separator()
        editor_commands.add_command(label='Copy', command=lambda: self.editor.event_generate("<<Copy>>"), accelerator='Ctrl+C')
        editor_commands.add_command(label='Cut', command=lambda: self.editor.event_generate("<<Cut>>"), accelerator='Ctrl+X')
        editor_commands.add_command(label='Paste', command=lambda: self.editor.event_generate("<<Paste>>"), accelerator='Ctrl+V')
        editor_commands.add_separator()
        editor_commands.add_command(label='Search Keyword', command=self.editor_search_keyword, accelerator='CTRL+F')
        editor_commands.add_command(label='Run', command=self.python_run, accelerator='F5')
        editor_commands.add_command(label='Format Indentation', command=self.editor_format_indentation)
        editor_commands.add_separator()
        editor_commands.add_command(label='Select All', command=lambda: self.editor.event_generate("<<SelectAll>>"))
        editor_commands.add_command(label='Delete', command=lambda: self.editor.event_generate("<<Clear>>"), accelerator='Del')

        editor_commands.tk_popup(event.x_root, event.y_root)

    def editor_update_line_info(self):
        def main():
            index = self.editor.index(CURRENT)

            row, column = map(int, index.split('.'))

            line_content = self.editor.get(f'{row}.0', f'{row + 1}.0')

            self.line_info_text.config(text=f'Ln {row}, Col {column + 1}, Char {len(line_content)}')

        self.after(10, main)

    def scroll_both_y(self, action, position, type=None):
        self.editor.yview_moveto(position)

    def scroll_both_x(self, action, position, type=None):
        self.editor.xview_moveto(position)

    def update_scroll_y(self, first, last, type=None):
        self.editor.yview_moveto(first)
        self.editor_scrollbar_yview.set(first, last)
        self.linenumbers.redraw()

    def update_scroll_x(self, first, last, type=None):
        self.editor.xview_moveto(first)
        self.editor_scrollbar_xview.set(first, last)
        self.linenumbers.redraw()

    def editor_search_keyword(self):
        settings = [
            (
                'Search Keyword', [
                    ('Keyword to search', 'Entry', '', ''),
                    ('Match case', 'Checkbutton', False, ''),
                    ('Match whole keyword', 'Checkbutton', False, ''),
                    ('Use RegExp (Regular Expression)', 'Checkbutton', False, '')
                ]
            )
        ]

        def on_ok(root, results):
            arr = []

            for result in results:
                arr.append(result[0].get())

            self.editor.tag_delete('highlight_search_keyword')

            self.editor.tag_configure('highlight_search_keyword', foreground='', background='#00FFFF')

            start_pos = '1.0'

            if (len(arr[0]) <= 0 or arr[0] == ''):
                messagebox('You cannot search nothing.', 'warning')
                return

            while True:
                start_pos = self.editor.search(arr[0], start_pos, stopindex=END, nocase=not arr[1], exact=arr[2], regexp=arr[3])

                if not start_pos: break

                end_pos = f"{start_pos}+{len(arr[0])}c"
                self.editor.tag_add('highlight_search_keyword', start_pos, end_pos)
                start_pos = end_pos

        SparklyPythonNotebookWindow(master=self, title='SparklyPython - Search Keyword', settings=settings, on_ok=on_ok)

    def python_run(self):
        if (self.settings['terminal.save_file']): self.save_file()

        if (len(self.current_file_path) <= 0): return

        def func(system: str):
            python_command = 'python' if not 'terminal.python_command' in self.settings else self.settings['terminal.python_command']
            pause_and_exit = '&& (pause && exit) || (pause && exit)' if 'terminal.pause' in self.settings and self.settings['terminal.pause'] == True else '&& (exit) || (exit)'

            if (system.lower() == 'windows'):
                return f'start cmd /k "title SparklyPython && {python_command} "{self.current_file_path}" {pause_and_exit}"'
            else:
                messagebox(f'Unsupported platform \'{system}\', please use Microsoft Windows instead.', 'error')
                return None

        system = platform.system()
        command = func(system)

        if (command == None): return

        self.python_process = subprocess.Popen(command, shell=True)

    def python_stop(self):
        if (self.python_process):
            try:
                self.python_process.terminate()
            except:
                messagebox('Unable to kill the Python process.', 'error')
        else:
            messagebox('The Python process isn\'t running now.', 'info')

    def python_new_prompt(self):
        def func(system: str):
            python_command = 'python' if not 'terminal.python_command' in self.settings else self.settings['terminal.python_command']
            pause_and_exit = '&& (pause && exit) || (pause && exit)' if 'terminal.pause' in self.settings and self.settings['terminal.pause'] == True else '&& (exit) || (exit)'
        
            if (system.lower() == 'windows'):
                return f'start cmd /k "{python_command} {pause_and_exit}"'
            else:
                messagebox(f'The following command cannot be runned for the platform \'{system}\', please use Microsoft Windows instead.', 'error')
                return None

        system = platform.system()
        command = func(system)

        if (command == None): return

        subprocess.Popen(command, shell=True)

    def file_size_format(self):
        def sizeof(num, suffix='b'):
            for unit in ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z'):
                if abs(num) < 1024.0:
                    return f"{num:3.1f}{unit}{suffix}"
                num /= 1024.0

            return f"{num:.1f}Y{suffix}"

        return sizeof(os.path.getsize(self.current_file_path)) if len(self.current_file_path) > 0 else '0Kb'

    def exit_program(self):
        if (self.text_edited):
            res = tkinter_messagebox.askyesnocancel('SparklyPython - End Program', 'Do you want to save the current file before closing the program?')

            if (res == True):
                self.save_file()

                self.destroy()
            elif (res == False):
                self.destroy()
            else:
                return
        else:
            self.destroy()

    def check_updates(self):
        global thread

        try:
            def main():
                try:
                    response = requests.get('https://api.github.com/repos/TFAGaming/SparklyPython/releases')
                    response.raise_for_status()
                    github_info = response.json()

                    if (len(github_info) > 0):
                        latest = github_info[0]['tag_name']

                        if (latest != __version__):
                            res = tkinter_messagebox.askyesno('SparklyPython - Update', 'The version that you are currently using is not the latest version of SparklyPython, do you want to see the latest release?')

                            if (res):
                                webbrowser.open('https://github.com/TFAGaming/SparklyPython/releases/tag/' + latest)
                except:
                    pass
                
                thread.stop()

            thread = StoppableThread(target=main)
            thread.start()
        except:
            pass

    def set_window_title_status(self, file_path=None, edited=None):
        if (len(self.current_file_path) <= 0):
            self.title('SparklyPython - Untitled' + ('*' if edited else '') + ' (' + (self.file_size_format()) + ')')
        else:
            self.title('SparklyPython - ' + (os.path.basename(file_path) if file_path else os.path.basename(self.current_file_path)) + ('*' if edited else '') + ' (' + (self.file_size_format()) + ')')
    
    def update_status_message(self, string: str):
        self.status_text.config(text=string)

app = SparklyPythonIDE()
app.mainloop()
