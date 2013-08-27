
#  Innocent Dalvik Obfuscator  #


This is a proof-of-concept Dalvik bytecode obfuscator which performs four transformations. It's called half-jokingly Innocent Dalvik Obfuscator for two reasons:
(1) None of the transformations applied alone is robust enough against an experienced reverser armed with multiple analysis tools.
(2) Combined together, the transformations have a very reasonable impact on the processed application: no more than 1Mb of additional memory altogether and no noticeable CPU slowdown when tested with an old phone.


#  Brief Info on Transformations  #


(1) Add Native Call Wrappers -> hides the calls to native libraries in newly created external methods which we call "wrappers". Scatters the wrappers through random classes of the application.

(2) Obfuscate Strings -> encrypts all hardcoded strings in the app with RC4. Assigns a unique key for each class which contains strings. Adds between 3-10 replicas of the decryptTemplate.smali and each classes chooses at random its corresponding decryptor.

(3) Pack Numeric Constants -> hides some of the 4-bit and 16-bit constants in the code in an external class which we call "packer". Removes duplicating constants, applies a simple modification to hide the actual value and shuffles the constants. Adds between 3-10 packer replicas with a get-const method called at random when constant is needed.

(4) Add Bad Code -> performs a very similar junk code injection to what is described as an efficient approach in a previous post [1]


#  How To Use  #


(1) You need to have: 
    - python 2.7
    - (bak)smali [2]

(2) Modify the options.config file to change relevant paths. 
(3) A testKey is available by default for the APK signing, replace with your own key if you want.
(4) Two ways to use:

    (4.1) ./gui (make sure you have python Tkinter -> apt-get install python-tk
         Start the gui, select the transformations and your APK. Click on [Go!]

    (4.2) Standalone transforms (produces a txt file for measuring performance):
         ./<scriptName.sh> <APK-file>
         Example:
         ./addWrappers.sh com.obladi.oblada.apk

         NOTE: There is a recommended order to apply the transformations standalone.
               Add Wrappers -> Encrypt Strings -> Pack Numbers -> Add Bad Code
               Always execute addBadCode.sh last, because it breaks baksmali!!
               The APK file should not be in the same dir as the script files.


#  Further Info  #


This code was written for my master thesis. I plan to publish it openly, the share link will appear in this section soon. In the thesis you will find more info about the transformations, how to reverse engineer them and their evaluation on multiple freely available static analysis tools.


#  References  #

[1] Android Bytecode Obfuscation, Patrick Schulz, 2012, http://www.dexlabs.org/blog/bytecode-obfuscation

[2] Smali Project Home Page: https://code.google.com/p/smali/
