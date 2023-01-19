cd ./monodepth2
CUDA_VISIBLE_DEVICES=0 python train.py --model_name mono_model --png --log_dir ./tmp/ --data_path ~/Documents/ntu/kitti_data
