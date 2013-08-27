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

from utilsSmali import *

def getNativeCallWrapper(nativeMethod, wrapperName):
    """Return the wrapper string for a given method."""
    wrapper = '\n.method public static '
    for i in nativeMethod:
        if i in AccessFlag:
            nativeMethod.remove(i)
        else:
            break
    returnType = nativeMethod[-1]
    nativeMethod.remove(returnType)
    nativeClass = nativeMethod[0];
    nativeMethod.remove(nativeClass)
    nativeName = nativeMethod[0];
    nativeMethod.remove(nativeName)

    nativeArgs = ''
    if len(nativeMethod) > 0:
        nativeArgs = nativeMethod[0]
    nativeRegsCnt = getNumberOfRegisters(nativeArgs)

    # add native class as argument
    wrapper = wrapper + wrapperName + '(' + nativeClass + nativeArgs
    wrapper = wrapper + ')' + returnType + '\n'

    # add extra registers for new args
    wrapper = wrapper + '.registers ' + str(nativeRegsCnt + 2) + '\n'
    i = 0
    while i < nativeRegsCnt + 1:
        # list all parameters
        wrapper = wrapper + '.parameter \"v' + str(i+1) + '\"\n'
        i += 1

    # call native method
    wrapper = wrapper + '\n.prologue\n\ninvoke-virtual'    
    wrapper = wrapper + '/range {p0 .. p' + str(nativeRegsCnt) 
    wrapper = wrapper + '}, ' + nativeClass + '->' + nativeName + '('

    for i in nativeMethod:
        wrapper = wrapper + i
    wrapper = wrapper + ')' + returnType + '\n'
    # D, J = double, long -> (64 bits), 2 registers
    if returnType == 'D' or returnType == 'J':
        wrapper = wrapper + '\n\nmove-result-wide v0\n\nreturn-wide v0\n'
    else:
        # V = void 
        if returnType == 'V':
            wrapper = wrapper + '\n\nreturn-void\n'
        else: 
            # starts with L -> result is an object
            if returnType[0] == 'L':
                wrapper = wrapper + 'move-result-object v0\n\nreturn-object v0\n'
            else:
                wrapper = wrapper + 'move-result v0\n\nreturn v0\n'
    wrapper = wrapper + '.end method\n'
    return wrapper


def getInvokeStatic(name, parsed, virtualCall, wrapperClass):
    contentClassName = 'L'+ wrapperClass.replace('.', '/') + ';'
    directCall = virtualCall.replace('invoke-virtual', 'invoke-static')
    directCall = directCall.replace(parsed[1], contentClassName).replace(parsed[2], name)
    directCall = directCall.replace('(', '('+parsed[1])
    return directCall


def invokeDictToFlatList(virtualInvokes):
    invokes = []
    for cl in virtualInvokes.keys():
        for method in virtualInvokes[cl]:
            invokes.append((cl, method))
    return invokes


def appendMethodToClass(className, method, methodName, directory):
    filename = directory+className+'.smali' 
    with open(filename, 'r') as smaliFile:
        lines = smaliFile.readlines()

    if isMethodInClass(lines, methodName):
        return False

    lines.append(method);
        
    with open(filename, 'w') as smaliFile:
        smaliFile.writelines(lines)
    return True;
        

def addNativeWrappers(directory):
    """Add native wrappers to all matched methods in the backsmali dir."""
    nativeMethods, apkClasses = extractAllNativeMethods(directory)
    virtualInvokes = extractAllNativeCalls(directory, nativeMethods)
    publicClasses = extractPublicClasses(directory)
    
    inv = invokeDictToFlatList(virtualInvokes)
    names = generateNames(5*len(inv))
    random.shuffle(names)
    
    random.shuffle(publicClasses)
    wrappers = {}
    
    if directory[len(directory)-1] != '/':
        directory += '/'

    nameIndex = 0;
    for index, invocation in enumerate(inv):
        wrappers[invocation] = []
        parsed = Invokation.parseString(inv[index][1], parseAll=True)
        for dup in range (random.randint(1, 3)):
            method = getNativeCallWrapper(list(parsed)[1:], names[nameIndex]);
            if appendMethodToClass(publicClasses[nameIndex], method, names[nameIndex], directory):
                wrappers[invocation].append((publicClasses[nameIndex], names[nameIndex]))
            nameIndex += 1
    
    for useClass in virtualInvokes.keys():
        filename = directory + useClass.replace('.','/') + '.smali'
        calls = virtualInvokes[useClass]
        
        with open(filename, 'r') as smaliFile:
            lines = smaliFile.readlines()

        #replace all native calls
        for i in range(len(calls)):
            for index, line in enumerate(lines):
                line = line.strip().strip('\n')
                if line in calls:
                    stat, reg = isCalledFromStatic(lines, index)
                    if reg <= 15 and '/range' not in line: # smali is tricky with reg > 15
                        idx = calls.index(line)
                        parsed = Invokation.parseString(calls[idx], parseAll=True)
                        if getRegsParsed(list(parsed)[1:]) <= 4: 
                            pair = (useClass, calls[idx])
                            wrapperClasses = wrappers[pair]
                            wrapperIdx = random.randint(1, len(wrapperClasses)) - 1;
                            lines[index] = getInvokeStatic(wrapperClasses[wrapperIdx][1], parsed, lines[index], wrapperClasses[wrapperIdx][0])
                        break
                
        #write back the file
        with open(filename, 'w') as smaliFile:
            for line in lines:
                smaliFile.write(line)
    print apkClasses  # used for performance measurements

def usage():
    print "python ", sys.argv[0], " <input folder>"
    print "Please specify a path to dir with smali files."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    else:
        addNativeWrappers(sys.argv[1])

