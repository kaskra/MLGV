import os
import sys
import argparse
import numpy as np
from matplotlib import pyplot as plt
from stereo_batch_provider import KITTIDataset
from scipy.signal import convolve


def add_padding(I, padding):
    """Adds zero padding to an RGB or grayscale image

    Arguments:
    ----------
        I (np.array): HxWx? numpy array containing RGB or grayscale image
    
    Returns:
    --------
        P (np.array): (H+2*padding)x(W+2*padding)x? numpy array containing zero padded image
    """
    if len(I.shape) == 2:
        H, W = I.shape
        padded = np.zeros((H+2*padding, W+2*padding), dtype=np.float32)
        padded[padding:-padding, padding:-padding] = I
    else:
        H, W, C = I.shape
        padded = np.zeros((H+2*padding, W+2*padding, C), dtype=I.dtype)
        padded[padding:-padding, padding:-padding] = I

    return padded

def match_on_scanline(left_patch, image_right, x, y, max_disparity, window_size):
    """Match along the horizontal scanlines, compute the SADs and return the minimal disparity.
    """
    minimal_sad = max_disparity + 1
    minimal_sad_d = 0
    for d in range(max_disparity):
        disp_x = x - d
        if disp_x < 0:
            break

        disp_right_image_region = image_right[y:y+window_size,disp_x:disp_x+window_size]
        diff = np.abs(left_patch - disp_right_image_region)

        sad = np.sum(diff)
        if sad < minimal_sad:
            minimal_sad = sad
            minimal_sad_d = d

    return minimal_sad_d

def sad(image_left, image_right, window_size=3, max_disparity=50):
    """Compute the sum of absolute differences between image_left and image_right.

    Arguments:
    ----------
        image_left (np.array): HxW numpy array containing grayscale right image
        image_right (np.array): HxW numpy array containing grayscale left image
        window_size: window size (default 3)
        max_disparity: maximal disparity to reduce search range (default 50)
    
    Returns:
    --------
        D (np.array): HxW numpy array containing the disparity for each pixel
    """

    D = np.zeros_like(image_left)

    # add zero padding
    padding = window_size // 2
    image_left = add_padding(image_left, padding).astype(np.float32)
    image_right = add_padding(image_right, padding).astype(np.float32)
    
    height = image_left.shape[0]
    width = image_left.shape[1]


    # TODO: ENTER CODE HERE (EXERCISE 4.1 a))

    for y in range(height-window_size+1):
        for x in range(width-window_size+1):
            left_image_region = image_left[y:y+window_size, x:x+window_size]
            # match patches along the horizontal axis 
            disparity = match_on_scanline(left_image_region, image_right, x, y, max_disparity, window_size)                
            
            D[y,x] = disparity
    return D


def visualize_disparity(disparity, title='Disparity Map', out_file='disparity.png', max_disparity=50):
    """Generates a visualization for the disparity map and saves it to out_file.

    Arguments:
    ----------
        disparity (np.array): disparity map
        title: plot title
        out_file: output file path
        max_disparity: maximum disparity
    """

    # TODO: ENTER CODE HERE (EXERCISE 4.1 b))

    plt.title(title)
    plt.imshow(disparity, vmin=0, vmax=max_disparity, cmap="rainbow_r") 
    plt.savefig(out_file, bbox_inches='tight')



def main(argv):
    parser = argparse.ArgumentParser(
        description=("Exercise_04 for the Machine Learning Course in Graphics and Vision 2020")
    )
    parser.add_argument("--input-dir", 
        type=str,
        default="./KITTI_2015_subset",
        help="Path to the KITTI 2015 subset folder.")
    parser.add_argument("--output-dir", 
        type=str,
        default="./output/handcrafted_stereo",
        help="Path to the output directory")
    parser.add_argument("--window-size", 
        type=int,
        default=3,
        help="The window size used for the sum of absolute differences")
    parser.add_argument("--max-disparity", 
        type=int,
        default=50,
        help="The maximum disparity size")
    args = parser.parse_args(argv)

    # Shortcuts
    input_dir = args.input_dir
    window_size = args.window_size
    max_disparity = args.max_disparity
    out_dir = os.path.join(args.output_dir, 'window_size_%d' % window_size)

    # Create output directory
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    # Load dataset
    dset = KITTIDataset(os.path.join(input_dir, "data_scene_flow/testing/"))
    for i in range(len(dset)):
        # Load left and right images
        im_left, im_right  = dset[i]
        im_left, im_right = im_left.squeeze(-1), im_right.squeeze(-1)

        # Calculate disparity
        D = sad(im_left, im_right, window_size=window_size, max_disparity=max_disparity)

        # Define title for the plot
        title = 'Disparity map for image %04d with block matching (window size %d)' % (i, window_size)
        # Define output file name and patch
        file_name = '%04d_w%03d.png' % (i, window_size)
        out_file_path = os.path.join(out_dir, file_name)

        # Visualize the disparty and save it to a file
        visualize_disparity(D, title=title, out_file=out_file_path, max_disparity=max_disparity)
        
    print('Finished generating disparity maps using the SAD method with a window size of %d.' % window_size)
    
if __name__ == "__main__":
    main(sys.argv[1:])
    
