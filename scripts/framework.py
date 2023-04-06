import os
import sys
import glob

ITERATIONS = 1
DOCKER_CONTAINER = 'trusting_volhard'
MONODEPTH_ROOT_DIR = '~/Documents/ntu/monodepth2'
LOG_DIR = '~/Documents/ntu/results'
DATASET = '/storage/datasets/kitty/kitti_data'
TRAINED_MODEL_PATH = '~/Documents/ntu/monodepth2/models/mono_640x192'
TEST_MODEL = '~/Documents/ntu/results/mono_model/models/weights_19'
ASSOCIATON_PY = '~/Documents/ntu/monodepth2/scripts/associate.py'


def run_orbslam(path):
    # Running ORB_SLAM in docker container 
        print("Running ORB_SLAM2")

        # Should happen for all sequences
        # TODO: Automate iteration through all subdirs

        path = subdir.split('/')
        seq_path = path[:-1]
        sequence = "/".join(seq_path)
        seq_path.append("associate.txt")
        path = "/".join(seq_path)
        print("ORB_SLAM read path:",seq_path)

        #cmd = 'docker exec -it determined_nobel bash -c "cd ORB_SLAM2; ls"'

        cmd = 'docker exec -it ' + DOCKER_CONTAINER + ' bash -c "cd ORB_SLAM2;\
         ./Examples/RGB-D/rgbd_tum Vocabulary/ORBvoc.txt\
         Examples/RGB-D/KITTI00-02.yaml '+sequence+' ' + path + ';"'

#			/storage/rgbd_dataset_freiburg1_xyz\
        #			Examples/RGB-D/associations/fr1_xyz.txt;"'

        print("ORBSLAM command:",cmd)

        os.system(cmd)

        path = "/".join(seq_path[:-1])
        print("Pose file read path:",path)

        cmd1 = 'docker exec -it ' + DOCKER_CONTAINER + ' bash -c "cd ORB_SLAM2;\
                cp Pose.txt ' + path + ';"'

        os.system(cmd1)


def train_monodepth():
    # Training monodepth2 model

        print("Training Monodepth2")

        cmd ='CUDA_VISIBLE_DEVICES=0 python ' +\
                MONODEPTH_ROOT_DIR + '/train_depth_ref.py\
                --model_name mono_model\
                --log_dir ' + LOG_DIR +' --data_path\
                ' + DATASET

        print("Train command :",cmd)
        os.system(cmd)


def test_monodepth(pose_net):
    # Test  monodepth2 model

        print("Testing with Monodepth2")

        print("Use posenet?", pose_net)

        print("monodepth read path:",DATASET) 

        if pose_net:
            cmd ='python3 ' + MONODEPTH_ROOT_DIR + '/test.py\
                    --model_name '+TRAINED_MODEL_PATH+' --image_path\
                    ' + DATASET + ' --pred_metric_depth'
        else:
            cmd ='python3 '+ MONODEPTH_ROOT_DIR + '/test.py\
                    --model_name '+TEST_MODEL+' --image_path'\
                    + DATASET + ' --pred_metric_depth'

        print("Test command:",cmd)
        #os.system(cmd)

def eval_depth():
    print("Evaluate Depth")

def assoc(path):
    print("Running association.py")

    path = path.split("/")[:-1]
    path.append("timestamps.txt")
    path = "/".join(path)

    cmd = 'python3 ' + ASSOCIATON_PY + ' -i ' + path 

    print("Association input path: ",path)
    os.system(cmd)

if __name__ == "__main__":

    # Debug: current working directory
    print(os.getcwd())

    for i in range(ITERATIONS):
        print("======================Evaluation step: ",i)  

        if i==0:
            test_monodepth(True)
        else:
            test_monodepth(False)

        for subdir, dirs, files in os.walk(DATASET):
            path = subdir.split('/')
            # image_02 = 'l'
            # image_03 = 'r'
            if path[-1] == 'data' and ( path[-2]=="image_02" \
                    or path[-2]=="image_03"):

                path = "/".join(path)
                # print("Itearation input path: ",path)

                #assoc(path)

                #run_orbslam(path)

        print("===================Training with ORBSLAM pose data :",i)
        train_monodepth()

        eval_depth()

