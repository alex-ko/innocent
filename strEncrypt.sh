#!/bin/bash

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

. options.config

FULL_PATH="$1"
APK=$(basename $FULL_PATH)
WORK_DIR=$(echo $FULL_PATH | sed 's|\(.*\)/.*|\1|')
BAKSMALI=$baksmali
SMALI=$smali
ENC="strEncrypt.py"
ENC_CLASS="decryptTemplate.smali"
KEY=$key
PASS=$keypass

echo -n $APK >> $WORK_DIR/strEncryptPerformance.txt
echo -n ' ' $(du -s $FULL_PATH | awk '{print $1}') >> $WORK_DIR/strEncryptPerformance.txt

echo 'Extracting .dex file...'
unzip $FULL_PATH classes.dex
APK=${APK%%????}
ORIGINAL_DEX=$APK-classes.dex
ENC_DIR=baksmali-$APK
mv classes.dex $ORIGINAL_DEX

echo 'Baksmaling...'
java -jar $BAKSMALI -o $ENC_DIR $ORIGINAL_DEX

echo 'Encrypting strings...'
(/usr/bin/time -f " \t%e \t%M" python $ENC $ENC_DIR/ $ENC_CLASS) &>> $WORK_DIR/$APK-strEncryptErr.txt
LINES=$(sed -n '$=' $WORK_DIR/$APK-strEncryptErr.txt)
if [ $LINES -eq 2 ]
  then
    FIRST=$(sed '$d' $WORK_DIR/$APK-strEncryptErr.txt)
    LAST=$(sed '1d' $WORK_DIR/$APK-strEncryptErr.txt)
    echo -n ' ' $FIRST ' ' $LAST >> $WORK_DIR/strEncryptPerformance.txt
    rm $WORK_DIR/$APK-strEncryptErr.txt #clear up 
  else
    rm -r $ENC_DIR #clear up
    rm $ORIGINAL_DEX
    echo 'Exception occured. Log file saved to '$WORK_DIR'/'$APK'-strEncryptErr.txt'
    exit
fi

echo 'Smaling...'
(java -jar $SMALI $ENC_DIR -o new-$ORIGINAL_DEX) &>> $WORK_DIR/$APK-strEncryptErr.txt
LINES=$(ls -l $WORK_DIR/$APK-strEncryptErr.txt | awk '{print $5}')
rm $ORIGINAL_DEX #clear up
if [ $LINES -eq 0 ]
  then
    rm $WORK_DIR/$APK-strEncryptErr.txt #clear up
    echo 'Replacing new .dex file...'
    zip -d $FULL_PATH classes.dex
    mv new-$ORIGINAL_DEX classes.dex
    zip -g $FULL_PATH classes.dex
    rm classes.dex #clear up
    rm -r $ENC_DIR #clear up

    echo 'Signing apk...'
    zip -d $FULL_PATH META-INF/*
    mkdir META-INF
    zip -g $FULL_PATH META-INF
    rm -r META-INF #clear up
    jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore $KEY -storepass PASS $FULL_PATH test

    echo 'Verifying signature...'
    jarsigner -verify -certs $FULL_PATH
    echo -n ' ' $(du -s $FULL_PATH | awk '{print $1}') >> $WORK_DIR/strEncryptPerformance.txt
    echo "" >> $WORK_DIR/strEncryptPerformance.txt
    echo 'Done!'
  else
    rm -r $ENC_DIR #clear up
    echo 'Error occured while assembling with smali. Log file saved to '$WORK_DIR'/'$APK'-strEncryptErr.txt'
    exit
fi

