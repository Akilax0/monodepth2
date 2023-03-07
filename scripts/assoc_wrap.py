import time 
import math
from decimal import Decimal
import re
from datetime import datetime
import sys
import getopt
import os

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

    print("Input sequence: ", arg_input)

    for subdirs, dirs, files in os.walk(arg_input):
        for dir in dirs:
            if dir=="depth":
                arg_path = os.path.join(subdirs)
                arg_path += "/timestamps.txt"
                print("arg_path:",arg_path)

                arg_arr = arg_path.split('/')[:-1]
                arg_arr.append("associate.txt")
                output_file = '/'.join(arg_arr)
                print("Output file:",output_file)
                #output_file = arg_input + "/epoch_out.txt"
                f1 = open(output_file, "w")
                #f.write("Now the file has more content!")

                timestamps = []
                
                with open(arg_path) as f:
                    lines = f.readlines()
                    
                    for i in lines:
                        i = i.strip('\n')
                        time_arr = i.split('.')

                        #print(time_arr)
                        #print("Time: " + time_str)

                        utc_time = datetime.strptime(time_arr[0],\
                                "%Y-%m-%d %H:%M:%S")#.%f")
                        #print(utc_time)
                        epoch_time = (utc_time - datetime(1970, 1, 1)).\
                                total_seconds()
                        time_out = str(epoch_time) + str(time_arr[1][1:])
                        print(time_out)
                        timestamps.append(time_out)
                f.close()
                
                # rgb images
                path = arg_path.split('/')[:-1]
                path.append("data")
                path  = '/'.join(path)

                dir_list = os.listdir(path)
                dir_list.sort()
                
                # Depth images
                depth_path = arg_path.split('/')[:-1]
                depth_path.append("depth")
                depth_path  = '/'.join(depth_path)

                print("Depth path: ",depth_path)
                depth_dir_list = os.listdir(depth_path)
                depth_dir_list = list(filter(lambda f: f.lower().\
                        endswith(('.jpg','.jpeg','.png')),depth_dir_list))

                depth_dir_list.sort()
                for i in depth_dir_list:
                    print(i)
                print(len(depth_dir_list)) 

                for i in range(len(timestamps)):
                    assoc_out = str(timestamps[i]) + ' data/' +\
                            str(dir_list[i]) +" "+\
                            str(timestamps[i]) + ' depth/' +\
                            str(depth_dir_list[i])
                    f1.write(assoc_out+"\n")

                f1.close()
