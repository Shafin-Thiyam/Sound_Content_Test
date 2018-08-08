import os; 
import sys;

for file in sys.argv[1:]:
    file_name=file.split(".")[0]
    print("{0} {1}.ogg".format(file,file.split(".")[0]))

    os.system("ffmpeg -ss 00  -i {0}  -t 12 -af \"afade=t=out:st=11.2:d=1\" {1}.ogg".format(file,file_name))
