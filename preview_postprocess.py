import os; 
import sys;

for file in sys.argv[1:]:
    print("{0} {1}.ogg".format(file, file.split(".")[0]))
    os.system("ffmpeg -ss 00 -i {0} -t 02  {1}.ogg".format(file, file.split(".")[0]))
