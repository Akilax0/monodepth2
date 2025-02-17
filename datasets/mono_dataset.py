# Copyright Niantic 2019. Patent Pending. All rights reserved.
#
# This software is licensed under the terms of the Monodepth2 licence
# which allows for non-commercial use only, the full terms of which are made
# available in the LICENSE file.

from __future__ import absolute_import, division, print_function

import os
import random
import numpy as np
import copy
from PIL import Image  # using pillow-simd for increased speed

import torch
import torch.utils.data as data
from torchvision import transforms


def pil_loader(path):
	# open path as file to avoid ResourceWarning
	# (https://github.com/python-pillow/Pillow/issues/835)
	with open(path, 'rb') as f:
		with Image.open(f) as img:
			return img.convert('RGB')


class MonoDataset(data.Dataset):
	"""Superclass for monocular dataloaders

	Args:
		data_path
		filenames
		height
		width
		frame_idxs
		num_scales
		is_train
		img_ext
	"""

	def __init__(self,
              data_path,
              filenames,
              height,
              width,
              frame_idxs,
              num_scales,
              is_train=False,
              img_ext='.jpg'):
		super(MonoDataset, self).__init__()

		self.data_path = data_path
		self.filenames = filenames
		self.height = height
		self.width = width
		self.num_scales = num_scales
		self.interp = Image.ANTIALIAS

		self.frame_idxs = frame_idxs

		self.is_train = is_train
		self.img_ext = img_ext

		self.loader = pil_loader
		self.to_tensor = transforms.ToTensor()

		# We need to specify augmentations differently in newer versions of torchvision.
		# We first try the newer tuple version; if this fails we fall back to scalars
		try:
			self.brightness = (0.8, 1.2)
			self.contrast = (0.8, 1.2)
			self.saturation = (0.8, 1.2)
			self.hue = (-0.1, 0.1)
			transforms.ColorJitter.get_params(
                            self.brightness, self.contrast, self.saturation, self.hue)
		except TypeError:
			self.brightness = 0.2
			self.contrast = 0.2
			self.saturation = 0.2
			self.hue = 0.1

		# scaled images
		self.resize = {}
		for i in range(self.num_scales):
			s = 2 ** i
			self.resize[i] = transforms.Resize((self.height // s, self.width // s),
                                      interpolation=self.interp)
			# Checking for velodyne file
		self.load_depth = self.check_depth()

	def preprocess(self, inputs, color_aug):
		"""Resize colour images to the required scales and augment if required

		We create the color_aug object in advance and apply the same augmentation to all
		images in this item. This ensures that all images input to the pose network receive the
		same augmentation.
		"""
		# print("Preprocessing inputs: ",inputs)
		for k in list(inputs):
			frame = inputs[k]
			if "color" in k:
				n, im, i = k
				for i in range(self.num_scales):
					inputs[(n, im, i)] = self.resize[i](inputs[(n, im, i - 1)])

		for k in list(inputs):
			f = inputs[k]
			if "color" in k:
				n, im, i = k
				inputs[(n, im, i)] = self.to_tensor(f)
				inputs[(n + "_aug", im, i)] = self.to_tensor(color_aug(f))

		# print("Preprocessing outputs: ",inputs)

	def __len__(self):
		return len(self.filenames)

	def __getitem__(self, index):
		"""Returns a single training item from the dataset as a dictionary.

		Values correspond to torch tensors.
		Keys in the dictionary are either strings or tuples:

			("color", <frame_id>, <scale>)          for raw colour images,
			("color_aug", <frame_id>, <scale>)      for augmented colour images,
			("K", scale) or ("inv_K", scale)        for camera intrinsics,
			"stereo_T"                              for camera extrinsics, and
			"depth_gt"                              for ground truth depth maps.

		<frame_id> is either:
			an integer (e.g. 0, -1, or 1) representing the temporal step relative to 'index',
		or
			"s" for the opposite image in the stereo pair.

		<scale> is an integer representing the scale of the image relative to the fullsize image:
			-1      images at native resolution as loaded from disk
			0       images resized to (self.width,      self.height     )
			1       images resized to (self.width // 2, self.height // 2)
			2       images resized to (self.width // 4, self.height // 4)
			3       images resized to (self.width // 8, self.height // 8)
		"""
		inputs = {}

		do_color_aug = self.is_train and random.random() > 0.5
		do_flip = self.is_train and random.random() > 0.5

		line = self.filenames[index].split()
		# Example line
		# ['2011_10_03/2011_10_03_drive_0034_sync', '306', 'r']
		# print("frame_idxs",self.frame_idxs)
		# print("==================line : ",line)
		folder = line[0]
		cam_T_cam = "/storage/datasets/kitty/kitti_data/"

		cam_T_cam += line[0].split("/")[0]

		cam_T_cam += "/calib_cam_to_cam.txt"
# print("cam_T_cam: ",cam_T_cam)

		# open the sample file used
		file = open(cam_T_cam)

		# read the content of the file opened
		cam = file.readlines()

		if len(line) == 3:
			frame_index = int(line[1])
		else:
			frame_index = 0

		if len(line) == 3:
			side = line[2]
		else:
			side = None

		if (side == "l"):
			cam = cam[19].split()
# print("left:" ,cam)
		elif (side == "r"):
			cam = cam[27].split()
# print("right:",cam)

		for i in self.frame_idxs:
			if i == "s":
				other_side = {"r": "l", "l": "r"}[side]
				inputs[("color", i, -1)] = self.get_color(folder,
                                              frame_index, other_side, do_flip)
			else:
				inputs[("color", i, -1)] = self.get_color(folder,
												frame_index + i, side, do_flip)

                # Width and height from kitti loaderwidth = 1242 height = 375

                # adjusting intrinsics to match each scale in the pyramid
		for scale in range(self.num_scales):

			# load intrinsic matrix instead of copying the average - akilax0
			# P2/3 from cam_T_cam

			K = np.array([[cam[1], cam[2], cam[3], 0], [cam[4], cam[5], cam[6], 0], [
			             cam[7], cam[8], cam[9], 0], [0, 0, 0, 1]], dtype=np.float32)

			width = 1242
			height = 375

			# Normalizing
			# Divide 1st row with width
			K[0, :] /= width
			# Divide 2nd row with height
			K[1, :] /= height
			# print("K:",K)

			# K = self.K.copy()

			# K[0, :] *= self.width // (2 ** scale)
			# K[1, :] *= self.height // (2 ** scale)

			K[0, :] *= width // (2 ** scale)
			K[1, :] *= height // (2 ** scale)

			inv_K = np.linalg.pinv(K)

			inputs[("K", scale)] = torch.from_numpy(K)
			inputs[("inv_K", scale)] = torch.from_numpy(inv_K)

		if do_color_aug:
			color_aug = transforms.ColorJitter.get_params(
						self.brightness, self.contrast, self.saturation, self.hue)
		else:
			color_aug = (lambda x: x)

		self.preprocess(inputs, color_aug)

		for i in self.frame_idxs:
			del inputs[("color", i, -1)]
			del inputs[("color_aug", i, -1)]

		if self.load_depth:
			depth_gt = self.get_depth(folder, frame_index, side, do_flip)
			inputs["depth_gt"] = np.expand_dims(depth_gt, 0)
			inputs["depth_gt"] = torch.from_numpy(inputs["depth_gt"].astype(np.float32))

		if "s" in self.frame_idxs:
			stereo_T = np.eye(4, dtype=np.float32)
			baseline_sign = -1 if do_flip else 1
			side_sign = -1 if side == "l" else 1
			stereo_T[0, 3] = side_sign * baseline_sign * 0.1

			inputs["stereo_T"] = torch.from_numpy(stereo_T)

		# added pose information - akilax0
		# read pose file

		pose_file = "/storage/datasets/kitty/kitti_data/"

		pose_file += line[0]
		pose_file += "/"

		if line[2] == "r":
			pose_file += "image_03/Pose.txt"
		elif line[2] == "l":
			pose_file += "image_02/Pose.txt"

		# print("Pose file", pose_file)

		# open the sample file used
		file = open(pose_file)

		# read the content of the file opened
		poses = file.readlines()
		# print(len(poses))

		if (len(poses) < int(line[1])+1):
			print("No forward")
		else:
			# print("Poses 0 1")
			r1, r2, r3, t1, r4, r5, r6, t2, r7, r8, r9, t3 = list(
				map(float, poses[int(line[1])+1].split(' ')))

			pose1 = torch.tensor([[r1, r2, r3, t1], [r4, r5, r6, t2], [
									r7, r8, r9, t3], [0., 0., 0., 1.]])
			# inputs[('pose',0,1)] = pose1

			# print(pose1)

		if int(line[1])-1 < 0:
			print("No back")
		else:
			# print("Poses 0 -1")
			r1, r2, r3, t1, r4, r5, r6, t2, r7, r8, r9, t3 = list(
				map(float, poses[int(line[1])].split(' ')))

			pose2 = torch.tensor([[r1, r2, r3, t1], [r4, r5, r6, t2], [
									r7, r8, r9, t3], [0., 0., 0., 1.]])
			pose2 = torch.inverse(pose2)
			# print(pose2)

			# inputs[('pose',0,-1)] = pose2

		return inputs

	def get_color(self, folder, frame_index, side, do_flip):
		raise NotImplementedError

	def check_depth(self):
		raise NotImplementedError

	def get_depth(self, folder, frame_index, side, do_flip):
		raise NotImplementedError
