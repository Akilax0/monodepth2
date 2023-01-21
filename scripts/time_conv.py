import time 
import math
from decimal import Decimal
import re
from datetime import datetime
import sys
import getopt

'''
input = 1305031128.6355
print(input)

frac = Decimal(str(input))%1
seconds = int(input)

gmt_time = time.gmtime(seconds)

year = gmt_time.tm_year
month = gmt_time.tm_mon
day = gmt_time.tm_mday
hour = gmt_time.tm_hour
min = gmt_time.tm_min
sec = gmt_time.tm_sec
'''
#time_str = str(year)+"-"+str(month)+"-"+str(day)+" "+str(hour)+":"+str(min)+\
 #     ":"+str(sec)+str(frac)[1:]





if __name__ == "__main__":
    argv = sys.argv

    arg_input = ""
    arg_help = "{0} -i <input>".format(argv[0])
    
    try:
        opts, args = getopt.getopt(argv[1:], "hi:", ["help", "input="])
    except:
        print(arg_help)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-i", "--input"):
            arg_input = arg
    
    arg_arr = arg_input.split('/')[:-1]
    arg_arr.append("epoch_out.txt")
    output_file = '/'.join(arg_arr)
    print(output_file)
    #output_file = arg_input + "/epoch_out.txt"
    f1 = open(output_file, "w")
    #f.write("Now the file has more content!")

    with open(arg_input) as f:
        lines = f.readlines()
        
        for i in lines:
            i = i.strip('\n')
            time_arr = i.split('.')
#            print(time_arr)
            #print("Time: " + time_str)

            utc_time = datetime.strptime(time_arr[0], "%Y-%m-%d %H:%M:%S")#.%f")
            #print(utc_time)
            epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
            time_out = str(epoch_time) + str(time_arr[1][1:])
#            print(time_out)
            f1.write(time_out+"\n")

    f1.close()
