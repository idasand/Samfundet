from __future__ import print_function
import gzip
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
import urllib
import numpy
import matplotlib.image as mpimg
from PIL import Image
from pathlib import Path
import shutil
#from skimage.transform import resize
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img



def img_crop(im, w, h):
    list_patches = []
    imgwidth = im.shape[0]
    imgheight = im.shape[1]
    #print('IMGWIDTH: ', imgwidth)
    #print('IMGHEIGHT: ',  imgheight)
    is_2d = len(im.shape) < 3
    for i in range(0,imgheight,h):
        for j in range(0,imgwidth,w):
            if is_2d:
                im_patch = im[j:j+w, i:i+h]
            else:
                im_patch = im[j:j+w, i:i+h, :]
            list_patches.append(im_patch)
    return list_patches


def value_to_class(v):
    foreground_threshold = 0.25 # percentage of pixels > 1 required to assign a foreground label to a patch
    df = numpy.sum(v)
    if df > foreground_threshold:
        return [0, 1]
    else:
        return [1, 0]


def extract_data(filename, num_images, IMG_PATCH_SIZE, datatype):
    """Extract the images into a 4D tensor [image index, y, x, channels].
    Values are rescaled from [0, 255] down to [-0.5, 0.5].
    """
    imgs = []
    for i in range(1, num_images+1):
        if datatype == 'train':
            imageid = "satImage_%.3d" % i
            image_filename = filename + imageid + ".png"
        elif datatype == 'test':
            imageid = "/test_%d" % i
            image_filename = filename + imageid + imageid + ".png"
        if os.path.isfile(image_filename):
            #print ('Loading ' + image_filename)
            img = mpimg.imread(image_filename)
            imgs.append(img)
        else:
            print ('File ' + image_filename + ' does not exist')

    num_images = len(imgs)
    IMG_WIDTH = imgs[0].shape[0]
    IMG_HEIGHT = imgs[0].shape[1]
    N_PATCHES_PER_IMAGE = (IMG_WIDTH/IMG_PATCH_SIZE)*(IMG_HEIGHT/IMG_PATCH_SIZE)

    # makes a list of all patches for the image at each index
    img_patches = [img_crop(imgs[i], IMG_PATCH_SIZE, IMG_PATCH_SIZE) for i in range(num_images)]
    # "unpacks" the vectors for each image into a shared vector, where the entire vector for image 1 comes
    # befor the entire vector for image 2
    # i = antall bilder, j = hvilken patch
    data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]
    #print("data",data.shape)
    #shape of returned = (width_image/num_patches * height_image/num_patches*num_images), patch_size, patch_size, 3
    return numpy.asarray(data)


def augmentation(data_dir, imgDir, groundThruthDir, train_labels_filename, train_data_filename, TRAINING_SIZE, MAX_AUG):

    seed = 0
    datagenImg = ImageDataGenerator(
            rotation_range=180, #in radians
            zoom_range=0.4,
            fill_mode= 'reflect'
            #brightness_range=(0,2))
            #vertical_flip=True,
            #horizontal_flip=True,
            #shear_range=0.25,
            #width_shift_range=0.2,
            #height_shift_range=0.2,
            #channel_shift_range=10,
            )
    datagenGT = ImageDataGenerator(
            rotation_range=180, #in radians
            zoom_range=0.4,
            fill_mode= 'reflect'
            #brightness_range=(0,2))
            #vertical_flip=True,
            #horizontal_flip=True,
            #shear_range=0.25,
            #width_shift_range=0.2,
            #height_shift_range=0.2,
            #channel_shift_range=10,
            )

    data_gen_args = dict(featurewise_center=True,
                         featurewise_std_normalization=True,
                         rotation_range=90,
                         width_shift_range=0.1,
                         height_shift_range=0.1,
                         shear_range=0.15,
                         zoom_range=0.1,
                         channel_shift_range=10,
                         horizontal_flip=True,
                         vertical_flip=True)


    if os.path.exists(imgDir):
        shutil.rmtree(imgDir)
        print("Directory " , imgDir ,  " already exists, overwritten")
    os.makedirs(imgDir)
    if os.path.exists(groundThruthDir):
        shutil.rmtree(groundThruthDir)
        print("Directory " , groundThruthDir ,  " already exists, overwritten")
    os.makedirs(groundThruthDir)


    #image_datagen = ImageDataGenerator(**data_gen_args)
    #ground_thruth_datagen = ImageDataGenerator(**data_gen_args)

    #moving original pictures to augmentet position
    for i in range(1, TRAINING_SIZE+1):
      imageid = "satImage_%.3d" % i
      image_filename = train_data_filename + imageid + ".png"
      gt_filename = train_labels_filename + imageid + ".png"
      image_dest = imgDir + "/" + imageid + ".png"
      gt_dest = groundThruthDir + "/" + imageid + ".png"
      #print(image_dest,gt_dest)
      shutil.copyfile(image_filename, image_dest)
      shutil.copyfile(gt_filename, gt_dest)

    for i in range(1,TRAINING_SIZE+1):
      imageid = "satImage_%.3d" % i
      image_filename = train_data_filename + imageid + ".png"
      groundthruth_filename = train_labels_filename + imageid + ".png"
      trainImg = load_img(image_filename)
      trainLabel = load_img(groundthruth_filename,color_mode='grayscale')
      img_arr = img_to_array(trainImg)
      img_arr = img_arr.reshape((1,) + img_arr.shape)
      gT_arr = img_to_array(trainLabel)
      gT_arr = gT_arr.reshape((1,) + gT_arr.shape)
      #for j in range(5):
        #image_datagen.flow_from_directory(img_arr,batch_size=1, save_to_dir=imgDir, save_prefix=imageid,save_format='png', seed=j)
        #ground_thruth_datagen.flow_from_directory(gT_arr,batch_size=1, save_to_dir=groundThruthDir, save_prefix=imageid,save_format='png', seed=j)
      j = 0
      seed_array = numpy.random.randint(10000, size=(1,MAX_AUG), dtype='l')
      for batch in datagenImg.flow(
        img_arr,
        batch_size=1, 
        save_to_dir=imgDir, 
        save_prefix=imageid,
        save_format='png', 
        seed=seed_array[j]):
        j +=1
        if j>=MAX_AUG:
          break
      j = 0
      for batch in datagenGT.flow(
        gT_arr,
        batch_size=1, 
        save_to_dir=groundThruthDir, 
        save_prefix=imageid,
        save_format='png', 
        seed=seed_array[j]):
        j +=1
        if j>=MAX_AUG:
          break




def extract_aug_data_and_labels(filename, num_images, IMG_PATCH_SIZE):
    """Extract the images into a 4D tensor [image index, y, x, channels].
    Values are rescaled from [0, 255] down to [-0.5, 0.5].
    """
    imgs = []
    gt_imgs = []
    pathlist = Path(filename).glob('**/*.png')
    #goes through all the augmented images in image directory
    # must pair them with all the augmented groundthruth images
    for path in pathlist:
        # because path is object not string
        image_path = str(path)
        lhs,rhs = image_path.split("/images")
        img = mpimg.imread(image_path)
        imgs.append(img)
        gt_path = lhs + '/groundtruth' + rhs
        g_img = mpimg.imread(gt_path)
        gt_imgs.append(g_img)


    num_images = len(imgs)
    IMG_WIDTH = imgs[0].shape[0]
    IMG_HEIGHT = imgs[0].shape[1]
    N_PATCHES_PER_IMAGE = (IMG_WIDTH/IMG_PATCH_SIZE)*(IMG_HEIGHT/IMG_PATCH_SIZE)
    # makes a list of all patches for the image at each index
    img_patches = [img_crop(imgs[i], IMG_PATCH_SIZE, IMG_PATCH_SIZE) for i in range(num_images)]
    # "unpacks" the vectors for each image into a shared vector, where the entire vector for image 1 comes
    # befor the entire vector for image 2
    # i = antall bilder, j = hvilken patch
    data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]
    gt_patches = [img_crop(gt_imgs[i], IMG_PATCH_SIZE, IMG_PATCH_SIZE) for i in range(num_images)]
    data_gt = numpy.asarray([gt_patches[i][j] for i in range(len(gt_patches)) for j in range(len(gt_patches[i]))])
    labels = numpy.asarray([value_to_class(numpy.mean(data_gt[i])) for i in range(len(data_gt))])

    return numpy.asarray(data), labels.astype(numpy.float32)


# Extract label images
def extract_labels(filename, num_images, IMG_PATCH_SIZE):
    """Extract the labels into a 1-hot matrix [image index, label index]."""
    gt_imgs = []
    for i in range(1, num_images+1):
        imageid = "satImage_%.3d" % i
        image_filename = filename + imageid + ".png"
        if os.path.isfile(image_filename):
            #print ('Loading ' + image_filename)
            img = mpimg.imread(image_filename)
            gt_imgs.append(img)
        else:
            print ('File ' + image_filename + ' does not exist')

    num_images = len(gt_imgs)
    gt_patches = [img_crop(gt_imgs[i], IMG_PATCH_SIZE, IMG_PATCH_SIZE) for i in range(num_images)]
    data = numpy.asarray([gt_patches[i][j] for i in range(len(gt_patches)) for j in range(len(gt_patches[i]))])
    labels = numpy.asarray([value_to_class(numpy.mean(data[i])) for i in range(len(data))])

    # Convert to dense 1-hot representation.
    return labels.astype(numpy.float32)


def load_data(train_data_filename, train_labels_filename, test_data_filename, TRAINING_SIZE, IMG_PATCH_SIZE, TESTING_SIZE, augment=False, MAX_AUG=1, augImgDir='', data_dir='', groundThruthDir=''):

    if augment == False:
        print('No augmenting of traing images')
        print('\nLoading training images')
        x_train = extract_data(train_data_filename, TRAINING_SIZE, IMG_PATCH_SIZE,  'train')
        #print(x_train[:10])

        print('Loading training labels')
        y_train = extract_labels(train_labels_filename, TRAINING_SIZE, IMG_PATCH_SIZE)
        #print(y_train[:20])
    elif augment == True:
        print('Augmenting traing images...')
        augmentation(data_dir, augImgDir, groundThruthDir, train_labels_filename, train_data_filename, TRAINING_SIZE, MAX_AUG)
        x_train, y_train = extract_aug_data_and_labels(augImgDir, TRAINING_SIZE*(MAX_AUG+1), IMG_PATCH_SIZE)

    
    print('Loading test images\n')
    x_test = extract_data(test_data_filename,TESTING_SIZE, IMG_PATCH_SIZE, 'test')
    #print(x_test[:10])

    print('Train data shape: ',x_train.shape)
    print('Train labels shape: ',y_train.shape)
    print('Test data shape: ',x_test.shape)

    [cl1,cl2] = numpy.sum(y_train, axis = 0, dtype = int)
    print('Number of samples in class 1 (background): ',cl1)
    print('Number of samples in class 2 (road): ',cl2, '\n')


    return x_train, y_train, x_test



def extract_data_pixelwise(filename, num_images, datatype, new_dim_train):
    """Extract the images into a 4D tensor [image index, y, x, channels].
    Values are rescaled from [0, 255] down to [-0.5, 0.5].
    """
    imgs = []
    for i in range(1, num_images+1):
        if datatype == 'train':
            imageid = "satImage_%.3d" % i
            image_filename = filename + imageid + ".png"
        elif datatype == 'test':
            imageid = "/test_%d" % i
            image_filename = filename + imageid + imageid + ".png"
        
        if os.path.isfile(image_filename):
            # Add the image to the imgs-array
            #img = mpimg.imread(image_filename)
            img = Image.open(image_filename)
            if datatype == 'train':
                img = img.resize((new_dim_train , new_dim_train))
                if i == 1:
                    img.save('traintest.png')
            img = numpy.asarray(img)
            imgs.append(img)
        else:
            print ('File ' + image_filename + ' does not exist')

    return numpy.asarray(imgs)


# Extract label images
def extract_labels_pixelwise(filename, num_images, new_dim_train):
    """Extract the labels into a 1-hot matrix [image index, label index]."""
    """ We want the images with depth = 2, one for each class, one of the depths is 1 and the other 0"""
    gt_imgs = []
    for i in range(1, num_images+1):
        imageid = "satImage_%.3d" % i
        image_filename = filename + imageid + ".png"
        
        if os.path.isfile(image_filename):
            # Add the image to the imgs-array
            #img = mpimg.imread(image_filename)
            img = Image.open(image_filename)
            #print(img.shape)
            img.resize((new_dim_train , new_dim_train))
            img = img.resize((new_dim_train , new_dim_train))
            if i == 1:
                img.save('labeltest.png')
            img = numpy.asarray(img)
            #print(img.shape)
            gt_imgs.append(img)
        else:
            print ('File ' + image_filename + ' does not exist')

    gt_imgs = numpy.asarray(gt_imgs)
    #print(len(gt_imgs))
    labels = numpy.zeros((num_images,new_dim_train,new_dim_train,2))

    foreground_threshold = 0.5
    labels[gt_imgs > foreground_threshold] = [1,0]
    labels[gt_imgs <= foreground_threshold] = [0,1]

    # Convert to dense 1-hot representation.
    return labels.astype(numpy.float32)


def load_data_img(train_data_filename, train_labels_filename, test_data_filename, TRAINING_SIZE, TESTING_SIZE, new_dim_train):
    x_test_img = extract_data_pixelwise(test_data_filename, TESTING_SIZE,  'test', new_dim_train)
    x_test_img = numpy.transpose(x_test_img, (0, 3, 1, 2))
    print('Test data shape: ',x_test_img.shape)

    x_train_img = extract_data_pixelwise(train_data_filename, TRAINING_SIZE,  'train', new_dim_train)
    x_train_img = numpy.transpose(x_train_img, (0, 3, 1, 2))
    print('Train data shape: ',x_train_img.shape)
    y_train_img = extract_labels_pixelwise(train_labels_filename, TRAINING_SIZE, new_dim_train)
    y_train_img = numpy.transpose(y_train_img, (0, 3, 1, 2))
    print('Train labels shape: ',y_train_img.shape)


    road = numpy.sum(y_train_img[:,1,:,:], dtype = int)
    background = numpy.sum(y_train_img[:,0,:,:], dtype = int)
    print('Number of samples in class 1 (background): ',road)
    print('Number of samples in class 2 (road): ',background, '\n')


    return x_train_img, y_train_img, x_test_img


def error_rate(predictions, labels):
    """Return the error rate based on dense predictions and 1-hot labels."""
    return 100.0 - (
        100.0 *
        numpy.sum(numpy.argmax(predictions, 1) == numpy.argmax(labels, 1)) /
        predictions.shape[0])

# Write predictions from neural network to a file
def write_predictions_to_file(predictions, labels, filename):
    max_labels = numpy.argmax(labels, 1)
    max_predictions = numpy.argmax(predictions, 1)
    file = open(filename, "w")
    n = predictions.shape[0]
    for i in range(0, n):
        file.write(max_labels(i) + ' ' + max_predictions(i))
    file.close()

# Print predictions from neural network
def print_predictions(predictions, labels):
    max_labels = numpy.argmax(labels, 1)
    max_predictions = numpy.argmax(predictions, 1)
    print (str(max_labels) + ' ' + str(max_predictions))

def img_float_to_uint8(img, PIXEL_DEPTH):
    rimg = img - numpy.min(img)
    rimg = (rimg / numpy.max(rimg) * PIXEL_DEPTH).round().astype(numpy.uint8)
    return rimg

def concatenate_images(img, gt_img):
    nChannels = len(gt_img.shape)
    w = gt_img.shape[0]
    h = gt_img.shape[1]
    if nChannels == 3:
        cimg = numpy.concatenate((img, gt_img), axis=1)
    else:
        gt_img_3c = numpy.zeros((w, h, 3), dtype=numpy.uint8)
        gt_img8 = img_float_to_uint8(gt_img)          
        gt_img_3c[:,:,0] = gt_img8
        gt_img_3c[:,:,1] = gt_img8
        gt_img_3c[:,:,2] = gt_img8
        img8 = img_float_to_uint8(img)
        cimg = numpy.concatenate((img8, gt_img_3c), axis=1)
    return cimg

# def make_img_overlay(img, predicted_img):
#     w = img.shape[0]
#     h = img.shape[1]
#     color_mask = numpy.zeros((w, h, 3), dtype=numpy.uint8)
#     color_mask[:,:,0] = predicted_img*PIXEL_DEPTH

#     img8 = img_float_to_uint8(img)
#     background = Image.fromarray(img8, 'RGB').convert("RGBA")
#     overlay = Image.fromarray(color_mask, 'RGB').convert("RGBA")
#     new_img = Image.blend(background, overlay, 0.2)
#     return new_img

def make_img_binary(img, predicted_img):
    w = img.shape[0]
    h = img.shape[1]
    color_mask = numpy.zeros((w, h, 3), dtype=numpy.uint8)
    color_mask[:,:,0] = predicted_img*PIXEL_DEPTH

    img8 = img_float_to_uint8(img)
    background = Image.fromarray(img8, 'RGB').convert("RGBA")
    overlay = Image.fromarray(color_mask, 'RGB').convert("RGBA")
    new_img = Image.blend(background, overlay, 0.2)
    return new_img

#######

# Convert array of labels to an image
def label_to_img(imgwidth, imgheight, w, h, output_prediction):

    # Defines the "black white" image that is to be saved
    predict_img = numpy.zeros([imgwidth, imgheight])

    # Fills image with the predictions for each patch, so we have a int at each position in the (608,608) array
    ind = 0
    for i in range(0,imgheight,h):
        for j in range(0,imgwidth,w):
            predict_img[j:j+w, i:i+h] = output_prediction[ind]
            ind += 1

    return predict_img

def get_prediction(img, model, IMG_PATCH_SIZE):
    
    # Turns the image into its data patches
    data = numpy.asarray(img_crop(img, IMG_PATCH_SIZE, IMG_PATCH_SIZE))
    #shape ((38*38), 16,16,3)

    # Data now is a vector of the patches from one single image in the testing data
    output_prediction = model.predict(data)
    #predictions have shape (1444,), a prediction for each patch in the image

    return output_prediction

def get_prediction_unet(img, model, IMG_PATCH_SIZE):
    
    # Turns the image into its data patches
    data = numpy.asarray(img_crop(IMG_PATCH_SIZE, IMG_PATCH_SIZE, img))
    #shape ((38*38), 16,16,3)

    # Data now is a vector of the patches from one single image in the testing data
    output_prediction = model.predict(data)
    #predictions have shape (1444,), a prediction for each patch in the image

    return output_prediction

def get_predictionimage(filename, image_idx, datatype, model, IMG_PATCH_SIZE, PIXEL_DEPTH):

    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    img = mpimg.imread(image_filename)
    #data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]

    output_prediction = get_prediction(img, model, IMG_PATCH_SIZE)
    predict_img = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    
    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((img.shape[0],img.shape[1], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(predict_img, PIXEL_DEPTH)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)

    return imgpred

def get_predictionimage_unet(filename, image_idx, datatype, model, IMG_PATCH_SIZE, PIXEL_DEPTH):

    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    img = mpimg.imread(image_filename)
    #data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]

    output_prediction = get_prediction_unet(img, model, IMG_PATCH_SIZE)
    predict_img = label_to_img(img.shape[1],img.shape[2], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    
    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((img.shape[1],img.shape[2], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(predict_img, PIXEL_DEPTH)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)

    return imgpred

def make_img_overlay(img, predicted_img, PIXEL_DEPTH):
    w = img.shape[0]
    h = img.shape[1]
    color_mask = numpy.zeros((w, h, 3), dtype=numpy.uint8) #samme størrelse som bildet
    color_mask[:,:,0] = predicted_img*PIXEL_DEPTH #0 eller 3 Endrer bare R i rgb, altså gjør bildet 

    img8 = img_float_to_uint8(img, PIXEL_DEPTH)
    background = Image.fromarray(img8, 'RGB').convert("RGBA")
    overlay = Image.fromarray(color_mask, 'RGB').convert("RGBA")
    new_img = Image.blend(background, overlay, 0.2)
    return new_img


# Get prediction overlaid on the original image for given input file
def get_prediction_with_overlay(filename, image_idx, datatype, model, IMG_PATCH_SIZE, PIXEL_DEPTH):

    i = image_idx
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')

    img = mpimg.imread(image_filename)


    # Returns a vector with a prediction for each patch
    output_prediction = get_prediction(img, model, IMG_PATCH_SIZE) 
    
    # Returns a representation of the image as a 2D vector with a label at each pixel
    img_prediction = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)
    

    oimg = make_img_overlay(img, img_prediction, PIXEL_DEPTH)

    return oimg

def save_overlay_and_prediction(filename, image_idx,datatype,model,IMG_PATCH_SIZE,PIXEL_DEPTH, prediction_training_dir):
    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    img = mpimg.imread(image_filename)

    # Returns a vector with a prediction for each patch
    output_prediction = get_prediction(img, model, IMG_PATCH_SIZE)
    # Returns a representation of the image as a 2D vector with a label at each pixel
    img_prediction = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((img.shape[0],img.shape[1], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(img_prediction, PIXEL_DEPTH)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)
    oimg = make_img_overlay(img, img_prediction, PIXEL_DEPTH)

    oimg.save(prediction_training_dir + "overlay_" + str(i) + ".png")
    imgpred.save(prediction_training_dir + "predictimg_" + str(i) + ".png")

    return
''' Not finished
def save_overlay_and_prediction_pixel(filename, image_idx,datatype,model,IMG_PATCH_SIZE,PIXEL_DEPTH, prediction_training_dir):
    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    img = mpimg.imread(image_filename)

    # Returns a vector with a prediction for each patch
    output_prediction = get_prediction_pixel(img, model, NEW_DIM_TRAIN)
    # Returns a representation of the image as a 2D vector with a label at each pixel
    img_prediction = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((img.shape[0],img.shape[1], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(img_prediction, PIXEL_DEPTH)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)
    oimg = make_img_overlay(img, img_prediction, PIXEL_DEPTH)

    oimg.save(prediction_training_dir + "overlay_" + str(i) + ".png")
    imgpred.save(prediction_training_dir + "predictimg_" + str(i) + ".png")

    return
'''


# Get prediction overlaid on the original image for given input file
def get_prediction_with_overlay_unet(filename, image_idx, datatype, model, IMG_PATCH_SIZE, PIXEL_DEPTH):

    i = image_idx
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')

    img = mpimg.imread(image_filename)


    # Returns a vector with a prediction for each patch
    output_prediction = get_prediction_unet(img, model, IMG_PATCH_SIZE) 
    
    # Returns a representation of the image as a 2D vector with a label at each pixel
    img_prediction = label_to_img(img.shape[1],img.shape[2], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)
    


def get_prediction_pixel(img, model, NEW_DIM_TRAIN):
    
    #img has shape (608, 608, 3)
    a = img
    #image = resize(img, (NEW_DIM_TRAIN , NEW_DIM_TRAIN,3))
    image= a.resize((NEW_DIM_TRAIN , NEW_DIM_TRAIN))#, refcheck=False)
    #img has shape (224, 224, 3)
    #image = img
    # Turns the image into matrix
    data = numpy.asarray(image)
    temp = numpy.zeros((1,NEW_DIM_TRAIN,NEW_DIM_TRAIN,3))
    temp[0,:,:,:] = data
    data = numpy.transpose(temp, (0, 3, 1, 2))

    # now img has shape (1, 3, 224, 224)
    #print("data",data.shape)
    # makes predictions on the image
    output_prediction = model.predict(data)
    output_prediction = output_prediction[:,0,:,:] # (1,224,224)
    #print('output_prediction: ', output_prediction.shape)
    #output_prediction = numpy.squeeze(output_prediction, axis=0) #(1,224,224)
    #print('output_prediction: ', output_prediction.shape)

    # output_prediction has shape (1,224,224), a prediction for each pixel in the reshaped image

    return output_prediction


def make_img_overlay_pixel(img, predicted_img, PIXEL_DEPTH):
    #w = img.shape[0]
    #h = img.shape[1]
    w, h = img.size
    #print(w,h)
    #pred_img = Image.fromarray(predicted_img)
    #pred_img = Image.fromarray(numpy.uint8(predicted_img*255))
    #print(shape.pred_img)
    #predicted_img = pred_img.resize((w,w))
    #predicted_img = numpy.asarray(predicted_img)
    #print('predicted img',predicted_img.shape)
    predicted_img = numpy.asarray(predicted_img)
    color_mask = numpy.zeros((w, h, 3), dtype=numpy.uint8) #samme størrelse som bildet
    color_mask[:,:,0] = predicted_img[:,:,0]*PIXEL_DEPTH #0 eller 3 Endrer bare R i rgb, altså gjør bildet 

    img8 = img_float_to_uint8(img, PIXEL_DEPTH)
    background = Image.fromarray(img8, 'RGB').convert("RGBA")
    overlay = Image.fromarray(color_mask, 'RGB').convert("RGBA")
    new_img = Image.blend(background, overlay, 0.2)
    return new_img



def get_predictionimage_pixelwise(filename, image_idx, datatype, model, PIXEL_DEPTH, NEW_DIM_TRAIN):

    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    img = mpimg.imread(image_filename)
    #data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]

    output_prediction = get_prediction_pixel(img, model, NEW_DIM_TRAIN) #(1,224,224)
    predict_img = output_prediction
    #predict_img = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    
    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((predict_img.shape[1],predict_img.shape[2], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(predict_img, PIXEL_DEPTH)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)
    imgpredict = imgpred.resize((608,608))

    return imgpredict

def get_pred_and_ysubmit_pixelwise(filename, image_idx, datatype, model, PIXEL_DEPTH, NEW_DIM_TRAIN, IMG_PATCH_SIZE, prediction_test_dir):

    i = image_idx
    # Specify the path of the 
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')      

    # loads the image in question
    #img = mpimg.imread(image_filename)
    img = Image.open(image_filename)
    #data = [img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))]

    output_prediction = get_prediction_pixel(img, model, NEW_DIM_TRAIN) #(1,224,224)
    predict_img = output_prediction

    #predict_img = label_to_img(img.shape[0],img.shape[1], IMG_PATCH_SIZE, IMG_PATCH_SIZE, output_prediction)

    #print(predict_img.shape)
    # Changes into a 3D array, to easier turn into image
    predict_img_3c = numpy.zeros((predict_img.shape[1],predict_img.shape[2], 3), dtype=numpy.uint8)
    predict_img8 = img_float_to_uint8(predict_img, PIXEL_DEPTH)
    #print(predict_img8)          
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)
    #imgpred.save(prediction_test_dir + "small_" + str(i) + ".png")
    imgpredict = imgpred.resize((608,608))
    imgpredict.save(prediction_test_dir + "gtimg_" + str(i) + ".png")

    img = mpimg.imread(prediction_test_dir + "gtimg_" + str(i) + ".png")


    label_patches = img_crop(img, IMG_PATCH_SIZE, IMG_PATCH_SIZE)
    data = numpy.asarray(label_patches)#([gt_patches[i][j] for i in range(len(gt_patches)) for j in range(len(gt_patches[i]))])
    labels = numpy.asarray([value_to_class(numpy.mean(data[i])) for i in range(len(data))])
    #print("bilde",imgpredict.shape)
    '''imgpredarr = numpy.asarray(imgpredict)
    imgpredarr = numpy.transpose(imgpredarr, (0, 3, 1, 2))
    print("array", imgpredarr.shape)
    labels = numpy.zeros((1,608,608,2))

    foreground_threshold = 0.5
    labels[imgpredarr > foreground_threshold] = [1,0]
    labels[imgpredarr <= foreground_threshold] = [0,1]'''

    return labels, imgpredict

def get_prediction_with_overlay_pixelwise(filename, image_idx, datatype, model, PIXEL_DEPTH, NEW_DIM_TRAIN):

    i = image_idx
    if (datatype == 'train'):
        imageid = "satImage_%.3d" % image_idx
        image_filename = filename + imageid + ".png"
    elif (datatype == 'test'):
        imageid = "/test_%d" % i
        image_filename = filename + imageid + imageid + ".png"
    else:
        print('Error: Enter test or train')

    #img = mpimg.imread(image_filename) # Reads out the original image
    img = Image.open(image_filename)
    #print(img.shape)

    # Returns a matrix with a prediction for each pixel
    output_prediction = get_prediction_pixel(img, model, NEW_DIM_TRAIN) #(1,224,224)
    output_prediction = numpy.transpose(output_prediction, (1, 2, 0)) #(224,224,1)


    predict_img_3c = numpy.zeros((output_prediction.shape[0],output_prediction.shape[1], 3), dtype=numpy.uint8)
    predict_img8 = numpy.squeeze(img_float_to_uint8(output_prediction, PIXEL_DEPTH))       
    predict_img_3c[:,:,0] = predict_img8
    predict_img_3c[:,:,1] = predict_img8
    predict_img_3c[:,:,2] = predict_img8

    imgpred = Image.fromarray(predict_img_3c)
    imgpredict = imgpred.resize((400,400))
    
    #gtimg = get_predictionimage_pixelwise(filename, image_idx, datatype, model, PIXEL_DEPTH, NEW_DIM_TRAIN)
    #wpred,hpred = imgpredict.size
    #w,h = img.size
    #print("wpred: ", wpred, "hpred: ", hpred, "w", w, "h: ", h)
    #img = mpimg.imread(image_filename) # Reads out the original image
    oimg = make_img_overlay_pixel(img, imgpredict, PIXEL_DEPTH)

    return oimg, imgpredict


#########

def pred_to_submission_strings(y_test):
    """Reads a single image and outputs the strings that should go into the submission file"""
    img_number = int(re.search(r"\d+", image_filename).group(0))
    im = mpimg.imread(image_filename)
    patch_size = 16
    for j in range(0, im.shape[1], patch_size):
        for i in range(0, im.shape[0], patch_size):
            patch = im[i:i + patch_size, j:j + patch_size]
            label = patch_to_label(patch)
            yield("{:03d}_{}_{},{}".format(img_number, j, i, label))


def pred_to_submission(submission_filename, y_test):
    """Converts images into a submission file"""
    with open(submission_filename, 'w') as f:
        f.write('id,prediction\n')
        for fn in image_filenames[0:]:
            f.writelines('{}\n'.format(s) for s in mask_to_submission_strings(fn))


def prediction_to_submission(filename, y_submit):
    with open(filename, 'w') as f:
        f.write('id,prediction\n')
        #for i in range(72200):
        i=0;
        for j in range(1,50+1):
          for k in range(0,593,16):
            for l in range(0,593,16): 
              strj = ''
            
              if len(str(j))<2:
                strj='00'
              elif len(str(j))==2:
                  strj='0'

              text = strj + str(j) + '_' + str(k) + '_' + str(l) + ',' + str(y_submit[i])
              f.write(text)
              f.write('\n')
              i=i+1;

def prediction_to_submission2(filename, y_submit):
    with open(filename, 'w') as f:
        f.write('id,prediction\n')
        #for i in range(72200):
        print(y_submit.shape)
        i=0;
        for j in range(1,50+1):
          for k in range(0,593,16):
            for l in range(0,593,16): 
              strj = ''
            
              if len(str(j))<2:
                strj='00'
              elif len(str(j))==2:
                  strj='0'

              text = strj + str(j) + '_' + str(k) + '_' + str(l) + ',' + str(y_submit[i,0])
              f.write(text)
              f.write('\n')
              i=i+1;




