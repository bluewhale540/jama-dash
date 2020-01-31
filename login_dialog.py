from tkinter.simpledialog import *


class LoginWindow(Dialog):
    def __init__(self, parent, window_title, user_title, pw_title):
        self.user_title = user_title
        self.pw_title = pw_title
        super().__init__(parent, title=window_title)

    def body(self, parent):
        Label(parent, text='').grid(row=0)
        Label(parent, text=self.user_title).grid(row=1)
        Label(parent, text='').grid(row=2)
        Label(parent, text=self.pw_title).grid(row=3)

        self.e1 = Entry(parent)
        self.e1.grid(row=1, column=1)
        self.e2 = Entry(parent, show='*')
        self.e2.grid(row=3, column=1)
        return self.e1 # initial focus

    def apply(self):
        first = str(self.e1.get())
        second = str(self.e2.get())
        self.result = (first, second) # or something

def run(window_title='Please Login', user_title='Login', pw_title='Password'):
    root = Tk()
    root.withdraw()  # hide the root window
    d = LoginWindow(parent=root, window_title=window_title, user_title=user_title, pw_title=pw_title)
    root.destroy()
    return d.result


