 # -*- coding: ascii -*-

""" Provide a tree viewer of context tree

Requires ttk
"""

from tkinter import *
from tkinter.ttk import *

from .binaryparser import ArrayContext, StructContext

class ContextViewer(Frame):

    def __init__(self):
        super().__init__()
        self.createVariable()
        self.createWidgets()
        self.grid(sticky=E + W + N + S)
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

    def createVariable(self):
        pass

    def createWidgets(self):

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        treeFrame = LabelFrame(self, text='Context Viewer')
        treeFrame.grid(column=0, row=0, sticky=E + W + N + S)

        self.tree = Treeview(treeFrame)
        self.tree.grid(column=0, row=0, sticky=E + W + N + S)
        scroll_x = Scrollbar(treeFrame, orient=HORIZONTAL, command=self.tree.xview)
        scroll_y = Scrollbar(treeFrame, orient=VERTICAL, command=self.tree.yview)
        scroll_x.grid(column=0, row=1, sticky=E + W)
        scroll_y.grid(column=1, row=0, sticky=N + S)
        self.tree.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        treeFrame.rowconfigure(0, weight=1)
        treeFrame.columnconfigure(0, weight=1)


        controlFrame = Frame(self)
        controlFrame.grid(column=0, row=2, columnspan=2, sticky=E + W)
        Label(controlFrame, text='Search: ').pack(side=LEFT)
        Entry(controlFrame, text='not implemented yet', width='40').pack(side=LEFT, fill=BOTH)
        Button(controlFrame, text='Next Key').pack(side=LEFT)
        Button(controlFrame, text='Next Value').pack(side=LEFT)

    def createTree(self, context):
        tree = self.tree
        tree['columns'] = ['Key', 'Value', 'Trail']
        tree.heading('#0', text='Key', anchor=W)
        tree.heading('#1', text='Value', anchor=W)
        tree.heading('#2', text='Trail', anchor=W)
        self._insert_item('', '', context)

    def _insert_item(self, parent, trail, context, n=0):
        if isinstance (context.get_parent(), ArrayContext):
            my_trail = '{}{}#{}/'.format(trail, context.get_name(), n)
            self.tree.insert(parent, 'end', iid=my_trail, text=context.get_name(), value=[n, my_trail])
        else:
            my_trail = '{}{}/'.format(trail, context.get_name())
            self.tree.insert(parent, 'end', iid=my_trail, text=context.get_name(), value=['', my_trail])

        for n, (k, v) in enumerate(context.get_ordered_items()):
            if isinstance(v, (ArrayContext, StructContext)):
                self._insert_item(my_trail, my_trail, v, n)
            else:
                leaf_trail = my_trail + str(k)

                if isinstance(v, bytes):
                    value = repr(v).replace('\\', '\\\\')
                else:
                    value = repr(v)
                self.tree.insert(my_trail, 'end', iid=leaf_trail, text=k, value=[value])

def view_context(context):
    root = Tk()
    root.title('Context Viewer')
    app = ContextViewer()
    app.createTree(context)
    app.mainloop()

