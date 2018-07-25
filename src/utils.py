#utils.py

import os
import cv2
import numpy as np 
import matplotlib.image as mpimg

IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_CHANNELS = 66, 200, 3
INPUT_SHAPE = (IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_CHANNELS)

def load_image(data_dir, image_file):
    """
    Reads the image
    """
    #TODO: mpimg->cv2
    return mpimg.imread(os.path.join(data_dir, image_file.strip()))

def choose_image(data_dir, center, left, right, steering_angle):
    """
    Random selection of image from center, left or right and adust the steerig angle
    """
    choice = np.random.choice(3)
    if choice==0:
        return load_image(data_dir, left), steering_angle + 0.2
    elif choice==1:
        return load_image(data_dir, right), steering_angle -0.2
    return load_image(data_dir, center), steering_angle

def random_flip(image, steering_angle):
    """
    Apply image flip (50% randomness)
    """
    if np.random.rand() <0.5:
        image = cv2.flip(image, 1)
        steering_angle = -steering_angle
    return image, steering_angle

def random_translate(image, steering_angle, range_x, range_y):
    """
    Apply random x,y translations to images
    """
    trans_x = range_x* (np.random.rand() - 0.5)
    trans_y = range_y* (np.random.rand() - 0.5)
    steering_angle += trans_x * 0.002
    trans_m = np.float32([[1,0,trans_x], [0,1,trans_y]])
    height, width = image.shape[:2]
    image = cv2.warpAffine(image, trans_m, (width, height))
    return image,steering_angle

def random_shadow(image):
    """
    Generate and adds random shadow
    """
    #(x1, y1) and (x2,y2) forms a line
    #xm, ym gives all locations on the image
    x1, y1 = IMAGE_WIDTH * np.random.rand(), 0
    x2, y2 = IMAGE_WIDTH * np.random.rand(), IMAGE_HEIGHT
    xm, ym = np.mgrid[0:IMAGE_HEIGHT, 0:IMAGE_WIDTH]

    mask = np.zeros_like(image[:,:,1])
    #set mask = 0 for all the pixels which are left/above to the line p1 and p2; else 1
    mask[ (ym-y1)*(x2-x1) - (y2-y1)*(xm-x1) > 0] = 1
    
    #choose which side should have shadow and adjust saturation
    # cond = mask == np.random.randint(2)
    cond = mask == np.random.choice(2)
    s_ratio = np.random.uniform(low=0.2, high=0.5)

    #adjust saturation in HLS //hue, light, sat
    hls = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
    hls[:,:,1][cond] = hls[:,:,1][cond]*s_ratio
    return cv2.cvtColor(hls, cv2.COLOR_HLS2RGB)

def random_brightness(image):
    """
    Apply random brighness variations 
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    ratio = 1.0 + 0.4*(np.random.rand()-0.5)
    hsv[:,:,2] = hsv[:,:,2]*ratio
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

def augment(data_dir, center, left, right, steering_angle, range_x =100, range_y= 10):
    """
    Augment input data set with variations in the data.

    # Called during classifier training phase
    # Chooses random images out of three(center, left and right)
    # Apply geometrical transformations
    # Apply intensity variations

    """
    image, steering_angle = choose_image(data_dir, center, left, right, steering_angle)
    image, steering_angle = random_flip(image, steering_angle)
    image, steering_angle = random_translate(image, steering_angle, range_x, range_y)
    image = random_shadow(image)
    image = random_brightness(image)
    return image, steering_angle

def preprocess(image):
    """
    Preprocess the images

    #Resize to (IMAGE_WIDTH, IMAGE_HEIGHT). Color converted to YUV
    #Convert RBG to YUV color space
    """
    image = image[60:-25, : ,:] #crop out sky and car hood regions
    image = cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT), cv2.INTER_CUBIC) #resize cropped image back to input size
    image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV) #Convert the image from RGB to YUV (This is what the NVIDIA model does)
    return image

def batch_generator(data_dir, image_paths, steering_angles, batch_size, is_training):
    """
    Generate batches of data to fed for training

    #Generate batch of [batch_size] samples
    #Preprocess input images
    #Yield generator iterates over the data. read more: https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do
    """
    
    images = np.empty([batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_CHANNELS])
    steers = np.empty(batch_size)
    
    nb_batches = 0
    while True:
        i=0
        for idx in np.random.permutation(image_paths.shape[0]):
            center, left, right = image_paths[idx]
            steering_angle = steering_angles[idx]
            
            #augmentation
            if is_training and np.random.rand()<0.6:
                image, steering_angle = augment(data_dir, center, left, right, steering_angle)
            else:
                image = load_image(data_dir, center)
            images[i] = preprocess(image)
            steers[i] = steering_angle
            i += 1
            if i == batch_size:
                nb_batches +=1
                print(' Batch #{}'.format(nb_batches))
                break
        yield images, steers