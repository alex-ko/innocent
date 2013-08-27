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

import sys, os, random
import utilsSmali, rc4

def generateStringFieldName(index):
    return '__' + chr(ord('a') + random.randint(0, 25)) + str(random.randint(100,999)) + str(index)


def generateStringField(name):
    return '.field private static ' + name + ':Ljava/lang/String;\n'


def generateKey():
    key = []
    keyLen = random.randint(128, 256)
    for i in range(keyLen):
       key.append(random.randint(0, 255))
    return key


def generateStringCreateCmd(className, strName, dataLen, index, decoderClass, decoderMethod):
    fullFieldName = 'L' + className + ';->' + strName + ':Ljava/lang/String;'
    return '\n\
    const/16 v1, ' + hex(dataLen) + '\n\
    new-array v1, v1, [B \n\
    fill-array-data v1, :array_ak' + str(index) + '\n\
    invoke-virtual {v0, v1}, L' + decoderClass + ';->' + decoderMethod + '([B)Ljava/lang/String; \n\
    move-result-object v1   \n\
    sput-object v1, ' + fullFieldName + '\n'


def generateDecoderCreateCmd(keyLen, index, decoderClass):
    return '\n\
    const/16 v1, ' + hex(keyLen) + '\n\
    new-array v1, v1, [B \n\
    fill-array-data v1, :array_ak' + str(index) + '\n\
    new-instance v0, L' + decoderClass + ';\n\
    invoke-direct {v0, v1}, L' + decoderClass + ';-><init>([B)V \n'


def generatePaddingLoad(keyLen, index):
    return '\n\
    const/16 v1, ' + hex(keyLen) + '\n\
    new-array v1, v1, [B \n\
    fill-array-data v1, :array_ak' + str(index) + '\n'


def generateArrayLoadData(data, index):
    code = '\n\
    :array_ak' + str(index) + '\n\
    .array-data 0x1'
    for d in data:
       code += '    ' + hex(d) + 't\n'
    code += '    .end array-data \n'
    return code


def getStringReplaceLine(line, stringName, className):
    newLine = '    sget-object '+ getRegisterFromConstLine(line) +', L' + className + ';->' + stringName + ':Ljava/lang/String; \n'
    return newLine


def getStringFromConstLine(line):
    string = line[len('const-string'):]
    pos = string.find(',')
    string = string[pos+1:].strip().strip('"')
    return string

    
def getRegisterFromConstLine(line):
    line = line.strip()
    string = line[len('const-string'):]
    pos = string.find(',')
    reg = string[:pos].strip()
    return reg

    
def isStringAscii(string):
    """Checks if a string is in extended ASCII code."""
    for c in string:
        if ord(c) > 255:
            return False
    return len(string) >= 3


def unescapeChars(string):
    esc = {'\\t' : '\t',
           '\\b' : '\b',
           '\\n' : '\n',
           '\\r' : '\r',
           "\\'" : "\'",
           '\\"' : '\"',
           '\\\\' : '\\',
          }

    for seq in esc.keys():
        string = string.replace(seq, esc[seq])
    return string


def findStringsInClass(lines):
    strings = {}
    
    inMethod = False;
    index = 0
    for line in lines:
        line = line.strip()
        if line.startswith('.method'):
            inMethod = True;
        if inMethod and line.startswith('const-string'):
            string = getStringFromConstLine(line)
            if isStringAscii(string):
                strings[index] = unescapeChars(string)
                
        if (line.startswith('.end method')):
            inMethod = False        
        index += 1

    return strings


def okToProcessClass(className, lines):
    return className.find('/') >= 0


def findStringConsts(directory):
    strings = {}
    
    baseDir = sys.argv[1].strip().strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    classes = 0
    
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            className = fullPath[len(baseDir):]
            with open(fullPath, 'r') as smaliFile:
                lines = smaliFile.readlines()            
                
            if okToProcessClass(className, lines):
                stringMap = findStringsInClass(lines)
                if len(stringMap) > 0:
                    strings[className] = stringMap
    return strings, baseDir


def findExistingStaticCtor(lines):
    for i in range(len(lines)):
        if lines[i].strip().startswith('.method static constructor'):
            return i
    return -1


def generateStaticCtorCode(className, key, stringNames, stringCodes, decoderClass, decoderMethod):
    code = generateDecoderCreateCmd(len(key), len(stringCodes)+1, decoderClass)
    
    for i in range(len(stringNames)):
        code += generateStringCreateCmd(className, stringNames[i], len(stringCodes[i]), i, decoderClass, decoderMethod)
    code += '\n'
    return code
        

def generateLoadDataPart(key, stringCodes):
    data = generateArrayLoadData(key, len(stringCodes)+1);
    for i in range(len(stringCodes)):
        data += generateArrayLoadData(stringCodes[i], i);
    return data


def fixRegisterCount(lines, index, count):
    if index < 0:
        raise Exception("Bad call - no registers line found to fix.")

    line = lines[index].strip();    
    if line.startswith('.registers'):
        lines[index] = '.registers ' + str(count)
    else:
        lines.insert(index, '.registers ' + str(count))
        

def modifyStaticCtor(lines, position, className, key, stringNames, stringCodes, decoderClass, decoderMethod):
    #parse method body - we need to know where it starts, ends and where is register declaration
    start = position + 1
    end = -1
    regLine = -1
    for i in range(position, len(lines)):
        line = lines[i].strip()
        if line.startswith('.registers'):
            regLine = i
        if line.startswith('.end method'):
            end = i
            break;
    if end < 0:
        raise Exception("Broken Smali! No end of static ctor found.")
                
    #insert new code and array data
    #first data at the end of method to protect start and end line numbers 
    lines.insert(end, generateLoadDataPart(key, stringCodes))
    #locate begining of the code - our code will be first
    start = utilsSmali.getFirstCodeLineIndex(lines, start)

    #insert string decode code
    lines.insert(start, generateStaticCtorCode(className, key, stringNames, stringCodes, decoderClass, decoderMethod))

    lastReturn = utilsSmali.getLastReturn(lines, start, end)
    if lastReturn > start:
        lines.insert(lastReturn-1, generatePaddingLoad(len(key), len(stringCodes)+1))
        
    #if not enough registers - fix that - we need 2
    if regLine < 0:
        regLine = start
        regNum = 0
    else:
        regNum = int(lines[regLine].strip().replace('.registers ', ''))

    if (regNum < 2):
        fixRegisterCount(lines, regLine, 2)


def appendNewStaticCtor(lines, className, key, stringNames, stringCodes, decoderClass, decoderMethod):
    index = utilsSmali.getFirstMethodIndex(lines, 0)
    code = '.method static constructor <clinit>()V \n\
    .registers 2    \n\
    .prologue   \n'
    
    code += generateStaticCtorCode(className, key, stringNames, stringCodes, decoderClass, decoderMethod)
    code += '    return-void \n'
    code += generateLoadDataPart(key, stringCodes)
    code += '.end method\n'
    
    lines.insert(index, code)

            
def generateStaticConstructor(lines, className, key, stringNames, stringCodes, decoderClass, decoderMethod):
    startpos = findExistingStaticCtor(lines)
    if startpos >= 0:
        modifyStaticCtor(lines, startpos, className, key, stringNames, stringCodes, decoderClass, decoderMethod)
    else:
        appendNewStaticCtor(lines, className, key, stringNames, stringCodes, decoderClass, decoderMethod)


def appendFields(lines, stringNames):
    index = utilsSmali.getFirstMethodIndex(lines, 0)
    for name in stringNames:
        lines.insert(index, generateStringField(name))


def processClass(baseDir, className, strings, decoderClass, decoderMethod):
    fileName = baseDir[:-1] + '/' + className
    className = className[:-len('.smali')]
    with open(fileName, 'r') as smaliFile:
        lines = smaliFile.readlines()

    key = generateKey();
    encoder = rc4.rc4(key)
    
    stringNames = []
    encStrings = []
    index = 0;
    
    for lineNum in strings.keys():
        stringNames.append(generateStringFieldName(index))
        encStrings.append(encoder.encode(strings[lineNum]))
        newLine = getStringReplaceLine(lines[lineNum], stringNames[index], className)        
        lines[lineNum] = newLine
        index += 1
    
    appendFields(lines, stringNames)
    generateStaticConstructor(lines, className, key, stringNames, encStrings, decoderClass, decoderMethod)
    
    with open(fileName, 'w') as smaliFile:
        smaliFile.writelines(lines)


def getDecoderClass(decoders):
    return decoders[random.randint(0, len(decoders)-1)]


def prepareDecoder(code, name, className):
    result = []
    className = 'L'+className+';'
    for line in code:
        line = line.replace('<CLASS_NAME>', className).replace('<METHOD>', name)
        result.append(line)
    return result
    

def generateDecoders(baseDir, code, count):
    if baseDir[len(baseDir)-1] != '/':
        baseDir = baseDir+'/'

    decoders = []
    publicClasses = utilsSmali.extractPublicClasses(baseDir);
    random.shuffle(publicClasses)
    names = utilsSmali.generateNames(len(publicClasses))
    random.shuffle(names)
    
    count = min(count, len(publicClasses))
    
    for i in range(count):
        directory = publicClasses[i][:publicClasses[i].strip('/').rfind('/')]
        className = utilsSmali.generateClassName(directory)
        while className in publicClasses:
            className = utilsSmali.generateClassName(directory)

        fixedDecoder = prepareDecoder(code, names[i], className)
        decoderFileName = baseDir+className+'.smali'
        with open(decoderFileName, 'w') as decFile:
            decFile.writelines(fixedDecoder)
        decoders.append((className, names[i]))
    return decoders


def encryptStrings(directory, decoder):
    strings, baseDir = findStringConsts(directory)

    decLines = []
    with open(decoder, 'r') as decoderFile:
        decLines = decoderFile.readlines()
    decoders = generateDecoders(directory, decLines, random.randint(3, 30))

    for classes in strings.keys():
        decClass, decMethod = getDecoderClass(decoders)
        processClass(baseDir, classes, strings[classes], decClass, decMethod);
    print len(strings)


def usage():
    print "python ", sys.argv[0], " <input folder> <decoder file>"
    print "Please specify a path to dir with smali files."

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()      
    else:
        encryptStrings(sys.argv[1], sys.argv[2])
