import os; 
import sys;

for file in sys.argv[1:]:
    print("{0} {1}.ogg".format(file, file.split(".")[0]))
    os.system("ffmpeg -i {0}  -ss 00:00:03 -t 00:00:08 -async 1 {1}.ogg".format(file, file.split(".")[0]))
