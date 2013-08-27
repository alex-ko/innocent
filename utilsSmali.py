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

import sys, os
from pyparsing import *
from random import randint

#-------------------------------#
# grammar to parse .smali files #
#-------------------------------#
MethodToken = Literal(".method")
AccessFlag  = Literal("public")    | Literal("private") | \
              Literal("protected") | Literal("abstract") | \
              Literal("static")    | Literal("constructor") | \
              Literal("final")     | Literal("native") | \
              Literal("bridge")    | Literal("synthetic") | \
              Literal("varargs")   | Literal("declared-synchronized")
InvokeToken = Literal("invoke-")
InvokeKind  = Literal("virtual")   | Literal("super") | \
              Literal("direct")    | Literal("static") | \
              Literal("interface")
RegType     = Literal("v")         | Literal("p")

JavaType        = Word(alphas+"[", alphanums +"_$[;/", min=1)
MethodName      = Word(alphas+"$_<", alphanums +"_>$", min=1).setResultsName("MethodName")
ArgList         = JavaType
MethodProtoType = MethodName + Suppress("(") + Optional(ArgList) + Suppress(")") + JavaType
MethodDecl      = Suppress(MethodToken) + ZeroOrMore(AccessFlag) + OneOrMore(MethodProtoType)
Register        = RegType + Word(nums, min=1)
Registers       = Register + Optional(",") + Optional(ZeroOrMore("."))
RegisterList    = Registers
ClassName       = JavaType.setResultsName("class")
Invokation      = Suppress(InvokeToken) + InvokeKind + Suppress(ZeroOrMore("/range")) + Suppress("{") + Suppress(ZeroOrMore(RegisterList)) + \
                  Suppress("},") + ClassName + Suppress("->") + MethodProtoType

#----------------------------------------------#
# extract various infromation from smali files #
#----------------------------------------------#

def extractNativeMethods(filename):
    """Return a list of all public native methods in a class."""
    nativeMethods = []
    with open(filename, 'r') as smaliFile:
        lines = smaliFile.readlines()
    for index, line in enumerate(lines):
        if line.startswith('.method'):
            try:
                method = list(MethodDecl.parseString(line.strip('\n'),parseAll=True))
            except Exception as e:
                print line
                raise e
            if 'native' in method and 'public' in method:
                nativeMethods.append(line)
    return nativeMethods


def isMethodInList(methodName, nativeCalls):
    """Check if a method with a given name is
       present in a list of native calls."""
    for call in nativeCalls:
        parsed = MethodDecl.parseString(call, parseAll=True)
        if parsed['MethodName'] == methodName:
            return True
    return False


def extractVirtualInvokes(filename, nativeCalls):
    """Return a list of all virtual invokes of native methods in a class."""
    virtualInvokes = []
    with open(filename, 'r') as smaliFile:
        lines = smaliFile.readlines()
    for index, line in enumerate(lines):
        line = line.strip().strip('\n')
        if line.startswith('invoke-'):
            try:
                parsed = Invokation.parseString(line, parseAll=True)
                invokes = list(parsed)
            except Exception as e:
                print line
                raise e
            if 'virtual' in invokes:
                # remove L and ; from name
                className = parsed['class'][1:-1].replace('/', '.')
                methodName = parsed['MethodName']
                if className in nativeCalls:
                    if isMethodInList(methodName, nativeCalls[className]):
                        virtualInvokes.append(line)
    return virtualInvokes


def extractAllNativeMethods(directory):
    """Browse the entire baksmali dir. Look for .smali (class) files. 
       Returns (1) a dictionary of all public native method declarations
       with <key> = class file; <value> = list of native declarations;
       (2) the total number of classes in the apk [used to measure the
       performance]."""
    apkClasses = 0
    nativeMethods = {}
    baseDir = directory.strip().strip('.').strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            native = extractNativeMethods(fullPath)
            className = fullPath.replace('/', '.').strip('.')
            if '$' not in className:
                apkClasses = apkClasses+1
            if len(native) > 0:
                className = smaliFilePathToClassName(baseDir, className)
                nativeMethods[className] = native
    return nativeMethods, apkClasses


def extractAllNativeCalls(directory, natives):
    """Browse the entire baksmali dir. Look for .smali (class) files. Return
       a dictionary of all virtual invocations of public native methods with
       <key> = class file; <value> = list of virtual calls of native methods."""
    virtualInvokes = {}
    baseDir = directory.strip().strip('.').strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            invoke = extractVirtualInvokes(fullPath, natives)
            className = fullPath.replace('/', '.').strip('.')
            if len(invoke) > 0:
                virtualInvokes[smaliFilePathToClassName(baseDir, className)] = invoke
    return virtualInvokes


def isPublicClass(filename):
    with open(filename, 'r') as smaliFile:
        lines = smaliFile.readlines()
        
    for index, line in enumerate(lines):
        line = line.strip().strip('\n')
        if line.startswith('.class'):
            return ('public' in line) and (not 'abstract' in line) and (not 'interface' in line)
    return False


def extractPublicClasses(directory):
    pubClasses = []
    baseDir = directory.strip().strip('.').strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            if isPublicClass(fullPath):
                pubClasses.append(smaliFilePathToClassName(baseDir, fullPath))
    return pubClasses

#-----------------#
# general purpose #
#-----------------#

def getNumberOfRegisters(args):
    """Return the number of registers needed to 
       represent the input arguments."""
    if len(args) == 0:
        return 0
    cnt = 0
    # one register genetic types for DVM
    # bool, byte, char, short, integer, float
    oneRegisterTypes=['Z', 'B', 'C', 'S', 'I', 'F']
    # two register genetic types for DVM
    # long, double
    twoRegisterTypes=['J', 'D']
    inType = False
    for c in args:
        if c == ';': inType = False
        else:
            if not inType:
                if c in oneRegisterTypes:
                    cnt += 1
                else:
                    if c in twoRegisterTypes:
                        cnt += 2
                    else:
                        if c == 'L':
                            inType = True
                            cnt += 1
    return cnt


def getRegsParsed(method):
    """Return the number of registers needed for
       the arguments of the parsed method."""
    for i in method:
         if i in AccessFlag:
             method.remove(i)
         else:
             break
    method.remove(method[-1]) # return type
    method.remove(method[0])  # native class
    method.remove(method[0])  # native method name
    args = ''
    if len(method) > 0:
        args = method[0]
    return getNumberOfRegisters(args)


def getNumParamRegisters(proto):
    """Return the number of input args from the method's prototype string."""
    args = proto[proto.index('(')+1:proto.index(')')]
    return getNumberOfRegisters(args)


def getFreeRegs(lines, startIndex):
    """Return the number of free registers in a method. """
    regs = 0
    params = getNumParamRegisters(lines[startIndex])
    for pos in range(startIndex, len(lines)):
        line = lines[pos].strip()
        if line.startswith('.end method'):
            return 0
        if line.startswith('.registers '):
            regs = int(line.replace('.registers ', ''))
            return regs - params - 1 # subtract 1 for the 'this'-register
    raise Exception("Bad smali file! no '.end method' expected!")


def generateNames(count):
    """Generate #<count> unique names/strings.
       Alphanumeric generation, max len = 3."""
    names = []
    alphabet = 'abcdefghijklmnopqrstuvwxyz_'
    for c in alphabet:
        if count == 0:
            break
        names += c
        count -= 1
    if count == 0:
        return names
    for c1 in alphabet:
        for c2 in alphabet:
            if count == 0:
                break
            names.append(''+c1+c2)
            count -= 1
    for c1 in alphabet:
        for c2 in alphabet:
            for c3 in alphabet:
                if count == 0:
                    break
                names.append(''+c1+c2+c3)
                count -= 1
    return names


def methodProtoTypeBuild(args):
    """Build a method prototype sting."""
    protoType = '.method '
    i = 0
    for arg in args:
        if arg in AccessFlag:
            protoType = protoType + arg + ' '
            i = i+1
        else:
            break
    protoType = protoType + args[i] + '('
    i = i+1
    while i < len(args)-1:
        protoType = protoType + args[i]
        i = i+1
    protoType = protoType + ')' + args[-1]
    return protoType


def isMethodInClass(lines, searchedMethod):
    """Check if a given method already exists in a class.
       Used to avoid name conflicts when injecting code."""
    for line in lines:
        line = line.strip().strip('\n')
        if line.startswith('.method'):
            try:
                method = list(MethodDecl.parseString(line.strip('\n'),parseAll=True))
            except Exception as e:
                print line
                raise e
            for i in method:
                if i in AccessFlag:
                    method.remove(i)
                else:
                    break
            for i in searchedMethod:
                if i in AccessFlag:
                    searchedMethod.remove(i)
                else:
                    break
            if method[0] == searchedMethod[0]:
                return True
    return False


def isCalledFromStatic(lines, index):
    """Check whether a method invocation is within a static method.
       Static methods do not have a this-register. Returns also  the 
       method registers number. Smali is tricky with registers > 15."""
    reg = 0
    while index > 0:
        line = lines[index].strip()
        if line.startswith('.registers '):
            reg = int(line.replace('.registers ', ''))
        if line.startswith('.method'):
            if 'static' in line:
                return True, reg
            else:
                return False, reg
        index = index-1


def getFirstCodeLineIndex(lines, startIndex):
    inAnnotation = False
    for pos in range(startIndex, len(lines)):
        line = lines[pos].strip()
        if line.startswith('.annotation'):
            inAnnotation = True
        elif line.startswith('.end annotation'):
            inAnnotation = False
        elif line.startswith('.end method'):
            return pos #empty method - can insert code anyway, because should not be native or abstract.
        elif not inAnnotation and line != '' and not line.startswith('#') and not line.startswith('.'):
            return pos
    raise Exception("Bad smali file! no '.end method' expected!")
    
    
def getFirstMethodIndex(lines, startIndex):
   for pos in range(startIndex, len(lines)):
        line = lines[pos].strip()
        if line.startswith('.method'):
            return pos
   return len(lines)


def getMethodStart(lines, index):
    while index >= 0:
        line = lines[index].strip()
        if line.startswith('.method'):
            break
        index -= 1
    if index < 0:
        return -1
    return getFirstCodeLineIndex(lines, index)
    

def getLastReturn(lines, start, end):
    last = -1
    while end > start:
        line = lines[end].strip()
        if line.startswith('return'):
            #multiple return statements
            if last > 0: return -1
            last = end
        end -= 1
    return last


def extractLabel(line):
    lab = line[line.index(':')+1:]
    return lab.strip()


def locateLabel(lines, index, lab):
    lab = ':' + lab;
    start = getMethodStart(lines, index)
    while start < len(lines):
        line = lines[start].strip()
        if line.startswith(lab):
            return start
        if line.startswith('.end method'):
            return -1
        start += 1
    return -1


def usesRegister(line, reg):
    if '/range' not in line:
        parts = line.split()
        for i in range(1, len(parts)):
            if parts[i].strip(',').strip('{').startswith(reg):
                return True
        return False
    else:
        rng = line[line.index('{')+1:line.index('}')]
        first = rng.split('.')[0].strip()
        second = rng.split('.')[-1].strip()
        if first[0] != reg[0]:
            return 0
        first = int(first[1:])
        second = int(second[1:])
        reg = int(reg[1:])
        return reg >= first and reg <= second


# 1  -> first
# 2  -> second
# 3  -> third
# 13 -> first and third, etc
# 6x -> X-th in range
# 0  -> unused
def getRegisterPosition(line, reg):
    result = 0
    if '/range' not in line:
        if '{' in line:
            line = line[line.index('{')+1:line.index('}')]
            line = 'instr ' + line # simulate instruction

        parts = line.split()
        for i in range(1, len(parts)):
            if parts[i].strip(',').strip() == reg:
                result = 10*result+i
        return result    
    else:
        rng = line[line.index('{')+1:line.index('}')]
        first = rng.split('.')[0].strip()
        second = rng.split('.')[-1].strip()
        if first[0] != reg[0]:
            return 0
        first = int(first[1:])
        second = int(second[1:])
        reg = int(reg[1:])
        if reg >= first and reg <= second:
            return 60 + reg-first
    return 0


def smaliFilePathToClassName(baseDir, path):
    return path[len(baseDir):-len('.smali')]


def generateClassName(directory):
    prefix = ['Get','Basic','Set','Check','']
    infix1 = ['Random','Internal','Global','Base','']
    infix2 = ['Response','Request','Event','Exception','Implementation']
    postfix = ['Handler','Wrapper','Processor','Logger','Client','Generator','Modifier']
    
    directory += '/'
    directory += prefix[randint(0, len(prefix)-1)]
    directory += infix1[randint(0, len(infix1)-1)]
    directory += infix2[randint(0, len(infix2)-1)]
    directory += postfix[randint(0, len(postfix)-1)]
    return directory


def getFunctionPrototype(lines, index):
    while index >= 0:
        line = lines[index].strip()
        if line.startswith('.method'):
            break
        index -= 1
    if index < 0: return ''
    return lines[index].strip()


def jvmTypeToAnType(tp):
    if tp == 'L' or tp == '[': return 'o'
    if tp == 'F': return 'f'
    if tp == 'D': return ['f', 'f']
    if tp == 'J': return ['l', 'l']
    if tp == 'I': return 'i'
    if tp == 'S': return 's'
    if tp == 'B': return 'b'
    if tp == 'C': return 'c'
    if tp == 'Z': return 'B'

def extractResultType(proto):
    res = proto[proto.index(')')+1]
    return jvmTypeToAnType(res[0])
    

def splitArgs(args):
    res = []
    i = 0
    while i < len(args):
        c = args[i]
        if c == 'L':
            while args[i] != ';': i += 1
            res += 'o'
        elif c == '[':
            while args[i] == '[': i += 1
            if args[i] == 'L':
                while args[i] != ';': i += 1
            res += 'o'
        else:
            res += jvmTypeToAnType(c)
        i += 1
    return res
    
def getFillType(line):
    tp = line[line.index('['):][0]
    if tp == 'L' or tp == '[':
        return 'o'
    return str(jvmTypeToAnType(tp)[0])
    
def getArgumentType(line, pos):
    args = line[line.index('(')+1:line.index(')')]
    argArray = splitArgs(args)
    if line.startswith('invoke') and not line.startswith('invoke-static'):
        argArray.insert(0, 'o')

    if pos >= 60 and pos < 100:
        return argArray[pos-60]
   
    pos = str(pos)
    for i in range(1, 6):
        if str(i) in pos:
            return argArray[i-1]

