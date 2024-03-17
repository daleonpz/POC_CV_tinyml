import numpy as np
import tensorflow as tf
from PIL import Image
import sys
np.set_printoptions(threshold=np.inf)

CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5
Q_IUO_THRESHOLD = 0.3
Q_CONF_THRESHOLD = 0.5
INPUT_SIZE = 96

# For testing
# def representative_dataset():
#     dataset_path = 'images/val'
#     datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
#     dataset = datagen.flow_from_directory(dataset_path, target_size=(96, 96), batch_size=32, class_mode=None, shuffle=False)
# 
#     for imagebatch in dataset:
#         yield [imagebatch.astype(np.float32)]

def representative_dataset(): # TODO: improve this, may impact accuracy
    for _ in range(100):
          data = np.random.rand(1, 96, 96, 3)
          yield [data.astype(np.float32)]


def convert_quantized_model_to_tflite(quantized_model_path, tflite_model_path):
    # Convert the model
    converter = tf.lite.TFLiteConverter.from_saved_model(quantized_model_path)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8
    tflite_quant_model = converter.convert()

    # Save the model
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_quant_model)

    print('TFLite model saved!')

    return tflite_quant_model

def convert_float_model_to_tflite(float_model_path, tflite_model_path):
    # Convert the model
    converter = tf.lite.TFLiteConverter.from_saved_model(float_model_path)
    tflite_float_model = converter.convert()

    # Save the model
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_float_model)

    print('TFLite model saved!')

    return tflite_float_model

def plot_anchor_boxes(image, anchor_boxes, filename):
    # convert anchor boxes to float
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    fig, ax = plt.subplots(1)
    ax.imshow(image)
    image_width, image_height = image.size
    print(f'image_width: {image_width}, image_height: {image_height}')
    for anchor_box in anchor_boxes:
        print(f'anchor_box: {anchor_box}')
        x = ( anchor_box[0] - anchor_box[2] / 2 ) * image_width
        y = ( anchor_box[1] - anchor_box[3] / 2 ) * image_height
        w = anchor_box[2] * image_width
        h = anchor_box[3] * image_height
        # get class with highest probability
        class_id = np.argmax(anchor_box[5:])
        probability = anchor_box[5 + class_id]
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='r', facecolor='none')
        ax.text(x, y, f'{class_id}: {probability:.2f}', color='red')
        ax.add_patch(rect)
    plt.show()  

    # save the image
    fig.savefig(filename, bbox_inches='tight')

def anchor_to_box(image_width, image_height, anchor_box):
#     print(f"*"*30)
#     print(f'image_width: {image_width}, image_height: {image_height}')
#     print(f'anchor_box: {anchor_box}')
    x1 = ( anchor_box[0] - anchor_box[2] / 2 ) * image_width
    y1 = ( anchor_box[1] - anchor_box[3] / 2 ) * image_height
    x2 = ( anchor_box[0] + anchor_box[2] / 2 ) * image_width
    y2 = ( anchor_box[1] + anchor_box[3] / 2 ) * image_height
#     print(f'x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}')
    return [x1, y1, x2, y2]


def non_maximum_suppression(predictions, confidence_threshold=0.5, iou_threshold=0.5, image_width=416, image_height=416):
    # Define a helper function to calculate IoU (Intersection over Union)
    print(f'predictions.shape: {predictions.shape}')
    print(f'predictions: {predictions}')
    def calculate_iou(prediction1, prediction2):
#         print(f'***'*10)
#         print(f'prediction1: {prediction1}')
#         print(f'prediction2: {prediction2}')
        # Calculate intersection coordinates
        box1 = anchor_to_box(image_width, image_height, prediction1)
        box2 = anchor_to_box(image_width, image_height, prediction2)

        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        # Calculate intersection area
        intersection = max(0, x2 - x1 + 1) * max(0, y2 - y1 + 1)

        # Calculate areas of each box
        area_box1 = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
        area_box2 = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)

        # Calculate union area
        union = area_box1 + area_box2 - intersection

        # Calculate IoU
        iou = intersection / union
#         print(f'iou: {iou}')
        return iou

    # Filter predictions based on confidence threshold
    filtered_predictions = [prediction for prediction in predictions if prediction[4] >= confidence_threshold]

    # Sort predictions by confidence score (probability)
    filtered_predictions.sort(key=lambda x: x[4], reverse=True)

    # Apply Non-Maximum Suppression
    selected_predictions = []
    while len(filtered_predictions) > 0:
        selected_predictions.append(filtered_predictions[0])
        print(f'selected_predictions: {selected_predictions}')

        # Remove the selected prediction
        del filtered_predictions[0]

        # Apply NMS
        iou = [calculate_iou(selected_predictions[-1], prediction) for prediction in filtered_predictions]
        print(f'len(iou): {len(iou)}')
        print(f'iou: {iou}')

        filtered_predictions = [prediction for i, prediction in enumerate(filtered_predictions) if iou[i] < iou_threshold]
       
    return selected_predictions

def parse_image(image_path):
    image = Image.open(input_image_path)

    # convert image to numpy array
    image_data = np.asarray(image)
    
    print(f'image_data.shape: {image_data.shape}')
    if ( image.mode == 'RGBA' ):
        image_data_raw = image_data[:, :, :3]
    else:
        image_data_raw = image_data

    imagef32= image_data_raw.astype(np.float32)
    imagef32 = imagef32 / 255.0
    imagef32 = np.expand_dims(imagef32, axis=0)

    imagei8 = image_data_raw.astype(np.uint8)
    imagei8 = np.expand_dims(imagei8, axis=0)

    return image, imagef32, imagei8

def parse_model(model_path, tflite_format = 'int8'):
    model = tf.saved_model.load(model_path)

    if ( tflite_format == 'int8' ):
        q_model = convert_quantized_model_to_tflite(model_path, 'quantized_model.tflite')
    else:
        q_model = convert_float_model_to_tflite(model_path, 'float_model.tflite')

    return model, q_model

def get_predictionf32( model, image ):
    out = model(image)

    # convert tuple to numpy array
    out = np.array(out) # shape 1x1x432x9 , 432 = 12x12x3 (3 anchors, 12x12 grid)

    # delete all predictions with low confidence score
    # YOLO = [ x, y, w, h, confidence, class1, class2, ... ]
    candidates = out[out[:, :, :, 4] >= CONF_THRESHOLD]
    pred = non_maximum_suppression(candidates, CONF_THRESHOLD, IOU_THRESHOLD, INPUT_SIZE, INPUT_SIZE)

    return pred

def get_predictioni8(model, image):
    # Test 8bit quantized model
    interpreter = tf.lite.Interpreter(model_content=model)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], image)
    interpreter.invoke()
    out = interpreter.get_tensor(output_details[0]['index']) # shape 1x432x9

    # convert tuple to numpy array
    out = np.array(out)/255.0

    candidates = out[out[:, :, 4] >= CONF_THRESHOLD]
    # delete candidates where w and h are 0, due to quantization
    candidates = candidates[candidates[:, 2] > 0]
    candidates = candidates[candidates[:, 3] > 0]

    # convert candidates to float
    candidates = candidates.astype(np.float32)

    q_pred = non_maximum_suppression(candidates, Q_CONF_THRESHOLD, Q_IUO_THRESHOLD, INPUT_SIZE, INPUT_SIZE)
    return q_pred


model_path=sys.argv[1]
input_image_path=sys.argv[2]

image_raw, imagef32, imagei8 = parse_image(input_image_path)
modelf32, q_model = parse_model(model_path, 'int8')

predictionf32 = get_predictionf32(modelf32, imagef32)
print("-----------------")
print(f'predictionf32: {predictionf32}')
plot_anchor_boxes( image_raw, predictionf32, 'outputf32.png' )

predictioni8 = get_predictioni8(q_model, imagei8)
print("-----------------")
print(f'predictioni8: {predictioni8}')
plot_anchor_boxes( image_raw, predictioni8, 'outputi8.png' )

# 
# output_data.shape: (1, 1, 432, 9)
# candidates.shape: (8, 9)
# iou: 0.8842370203182425
# iou: 0.8784716902923578
# iou: 0.8571810827368751
# iou: 0.8573730387153684
# iou: 0.8015924903806488
# iou: 0.9533240480713717
# iou: 0.8867582785000717
# len(iou): 7
# iou: [0.8842370203182425, 0.8784716902923578, 0.8571810827368751, 0.8573730387153684, 0.8015924903806488, 0.9533240480713717, 0.8867582785000717]
# pred.shape: (1, 9)
# image_width: 96, image_height: 96
# anchor_box: [6.8003815e-01 4.2761764e-01 3.0366233e-01 4.7105575e-01 9.0793806e-01
#               4.2614993e-03 9.9946988e-01 1.5662542e-03 2.2652441e-04]


# INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
# Q>>> output_data.shape: (1, 432, 9)
# Q>>> candidates.shape: (8, 9)
# iou: 0.4847750683997904
# iou: 0.8746634026927783
# iou: 0.4847750683997904
# iou: 0.7525374577090383
# iou: 0.4847750683997904
# iou: 0.6685854341046581
# iou: 0.4847750683997904
# len(iou): 7
# iou: [0.4847750683997904, 0.8746634026927783, 0.4847750683997904, 0.7525374577090383, 0.4847750683997904, 0.6685854341046581, 0.4847750683997904]
# Q>>> q_pred.shape: (1, 9)
# image_width: 96, image_height: 96
# anchor_box: [0.69803922 0.42352941 0.21176471 0.45882353 0.90980392 
#              0.00392157 0.99607843 0.         0.        ]
# 
