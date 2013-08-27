#!/usr/bin/env python

#   Copyright [2013] [alex-ko askovacheva<<at>>gmail<<dot>>com]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from Tkinter import *
import tkFileDialog, tkMessageBox
import sys, subprocess, threading

root = Tk()
root.geometry('600x350+100+100')

class ConsoleRedirector(object):
    def __init__(self, text):
        self.out = text
    def write(self, message):
        self.out.insert(END, message)

class InnocentObf(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)  
        self.parent = parent
        self.varAdd = IntVar()
        self.varBad = IntVar()
        self.varStr = IntVar()
        self.varPac = IntVar()
        self.consoleOut = Text(self, background='#A8DBA8', foreground='#0B486B', height=200, width=500)
        sys.stdout = ConsoleRedirector(self.consoleOut)
        self.fileToProcess = ''
        self.file_opt = options = {}
        options['defaultextension'] = '.apk'
        options['filetypes'] = [('Android APK', '.apk')]
        options['initialdir'] = '~'
        options['parent'] = root
        options['title'] = 'Open APK file'
        self.isStrObf = False
        self.isBadded = False
        self.isRunning = False
        self.initUI()

        
    def initUI(self):
        self.parent.title('Innocent dalvik obfuscator')
        self.pack(fill=BOTH, expand=1)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=7)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(7, pad=7)
        
        lbl = Label(self, text='Console output:')
        lbl.grid(sticky=W, pady=4, padx=5)
        self.consoleOut.grid(row=1, column=0, columnspan=3, rowspan=4, padx=5, sticky=E+W+S+N)

        transforms = Frame(self)
        transf = Label(transforms, height=2, text='Transformations:').pack()
        addBtn = Checkbutton(transforms, text='Add wrappers', variable=self.varAdd).pack()
        badBtn = Checkbutton(transforms, text='Inject bad code', variable=self.varBad).pack()
        strBtn = Checkbutton(transforms, text='Obfuscate strings', variable=self.varStr).pack()
        packBtn = Checkbutton(transforms, text='Pack constants', variable=self.varPac).pack()
        transforms.grid(row=1, column=3, pady=4, sticky=W)
        
        gogo = Frame(self, height=7)
        fileBtn = Button(gogo, text='Open .apk', command=self.askOpenFile).pack(side=LEFT)
        goBtn = Button(gogo, text='Go!', command=self.callTransformations).pack(side=LEFT)
        gogo.grid(row=5, column=0, padx=5)
        
        info = Frame(self, height=7)
        iBtn = Button(info, text='Info', command=self.showInfo).pack(side=LEFT)
        qBtn = Button(info, text='Quit', command=self.quit).pack(side=LEFT)
        info.grid(row=5, column=3)

    def askOpenFile(self):
        if self.isRunning:
            return
        self.fileToProcess = tkFileDialog.askopenfile(mode='r', **self.file_opt)
        if self.fileToProcess is not None:
            print "File to process: ", self.fileToProcess.name, "\n"
            print "Choose transformations and click on [Go!]\n"
        else:
            print "You have not selected an .apk file!"

    def showInfo(self):
        return tkMessageBox.showinfo(title='Innocent info', message='More technical details about transformations available at ...')

    def quit(self):
        if self.isRunning:
            return
        global root
        root.destroy()

    def applySingleTransform(self, transformCommand):
        self.isRunning = True
        print '|--------------------------------------------------|'
        print transformCommand
        pipe = subprocess.Popen(transformCommand,
                                shell = 'False',
                                bufsize = 1,
                                stderr = subprocess.PIPE,
                                stdout = subprocess.PIPE)
        while True:
            line = pipe.stdout.readline()
            if not line:
                break
            print line.strip('\n')
        print '|-------------------------------------------------|\n'
        self.isRunning = False

    def applyTransformations(self):
        if self.varAdd.get() + self.varStr.get() + self.varBad.get() + self.varPac.get() == 0:
            print "No transformations selected."
            return
    
        if self.isBadded == False:

            if self.isStrObf == True and self.varStr.get() == 1:
                 print "Sorry, you cannot apply \'Obfuscate strings\' twice. Unchecked!"
                 self.varStr.set(0)

            if self.varAdd.get() + self.varStr.get() + self.varBad.get() + self.varPac.get() > 0:
                self.applySingleTransform('./applyTransforms.sh ' + self.fileToProcess.name + ' ' +       \
                                           str(self.varAdd.get()) + ' ' + str(self.varPac.get())  + ' ' + \
                                           str(self.varStr.get()) + ' ' + str(self.varBad.get()))
            else:
                print "No transformation selected."
                return

            if self.varStr.get() == 1:
                self.isStrObf = True
            if self.varBad.get() == 1:
                self.isBadded = True
   
        else:
            print "Sorry, you cannot apply any transformation after you injected the bad code."
            return

    def callTransformations(self):
        if self.isRunning:
            print 'Already running...'
            return
        thread = threading.Thread(target=self.applyTransformations, args=tuple())
        thread.start();
        
      
def main():
    app = InnocentObf(root)
    root.mainloop()


if __name__ == '__main__':
    main()
