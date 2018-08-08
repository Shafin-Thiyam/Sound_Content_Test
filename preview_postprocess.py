import os; 
import sys;

for file in sys.argv[1:]:
    print("{0} {1}.ogg".format(file, file.split(".")[0]))
    os.system("ffmpeg -i {0} -ss 00 -t 12 {1}.ogg".format(file, file.split(".")[0]))
