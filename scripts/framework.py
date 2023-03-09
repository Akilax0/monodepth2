import os

USE_POSENET = False
ITERATIONS = 1
DOCKER_CONTAINER = 'determined_nobel'
MONODEPTH_ROOT_DIR = '~/Documents/ntu/monodepth2'
LOG_DIR = '~/Documents/ntu/tmp'
DATASET = '/storage/datasets/kitty/kitti_data'


def run_orbslam():
    # Running ORB_SLAM in docker container 
    print("Running ORB_SLAM2")
    
    #cmd = 'docker exec -it determined_nobel bash -c "cd ORB_SLAM2; ls"'

    cmd = 'docker exec -it ' + DOCKER_CONTAINER + ' bash -c "cd ORB_SLAM2;\
            ./Examples/RGB-D/rgbd_tum Vocabulary/ORBvoc.txt\
            Examples/RGB-D/TUM1.yaml \
            /storage/rgbd_dataset_freiburg1_xyz\
            Examples/RGB-D/associations/fr1_xyz.txt;"'
            
    print(cmd)
    os.system(cmd)

def train_monodepth(pose_net):
    # Training monodepth2 model

    print("Training Monodepth2")

    print("Use posenet?", pose_net)

    cmd ='CUDA_VISIBLE_DEVICES=0 python ' + MONODEPTH_ROOT_DIR + '/train.py\
            --model_name mono_model --log_dir ' + LOG_DIR +' --data_path\
            ' + DATASET

    print(cmd)
    #os.system(cmd)


def test_monodepth():
    # Test  monodepth2 model

    print("Testing with Monodepth2")

    cmd ='CUDA_VISIBLE_DEVICES=0 python ' + MONODEPTH_ROOT_DIR + '/test.py\
            --model_name mono_model --log_dir ' + LOG_DIR +' --data_path\
            ' + DATASET

    print(cmd)
    #os.system(cmd)

if __name__ == "__main__":

    print(os.getcwd())

    for i in range(ITERATIONS):
        print("Training step: ",i)  

        if USE_POSENET == False:
            print("Using monodepth2 with pose network")
            USE_POSENET = True
            train_monodepth(True)

        else:
            print("Using monodepth2 with calculated poses")
            train_monodepth(False)
        
        test_monodepth()

        run_orbslam()
    
