#include "test_model_utils.h"

namespace {
    const float kTolerance = 1e-5;
}


TEST(ModelUtilsTest, AnchorToBoxTest) {
    // Create sample anchor box for testing
    Prediction anchor_box = { 0.4392157, 0.59607846, 0.18039216, 0.12941177, 0.5019608, {0.01960784, 0.57254905, 0.48235294} };
    // Perform anchor to box conversion
    std::vector<float> result = anchor_to_box(96, 96, anchor_box);
    // Validate the result based on your expectations
    std::vector<float> expected_output = { 33.505882, 51.011765, 50.82353, 63.435295 };

    ASSERT_EQ(result.size(), expected_output.size());  // Replace with your expected result size

    // Add more specific validation based on your expectations
    for (size_t i = 0; i < expected_output.size(); i++) {
        ASSERT_NEAR(result[i], expected_output[i], kTolerance);
    }
}

TEST(ModelUtilsTest, CalculateIouTest) {
    // Create sample predictions for testing
    Prediction prediction1 = { 0.4392157, 0.59607846, 0.1764706, 0.1254902, 0.6156863, {0.01960784, 0.62352943, 0.5019608} };
    Prediction prediction2 = { 0.4392157, 0.59607846, 0.15294118, 0.16470589, 0.54901963, {0.01960784, 0.5803922, 0.50980395} };
    // Perform IOU calculation
    float result = calculate_iou(prediction1, prediction2, 96, 96);
    // Validate the result based on your expectations
    float expected_output = 0.6980392;

    ASSERT_NEAR(result, expected_output, kTolerance);
}


TEST(ModelUtilsTest, NonMaximumSuppressionTest) {
    // Create sample predictions for testing
    std::vector<Prediction> predictions = { 
        { 0.21960784, 0.3137255, 0.16078432, 0.17254902, 0.84705883, {0.00784314, 0.62352943, 0.62352943} },
        { 0.21960784, 0.3137255, 0.18039216, 0.12941177, 0.85882354, {0.00784314, 0.6431373, 0.6745098} },
        { 0.21960784, 0.3137255, 0.16078432, 0.17254902, 0.6901961, {0.00784314, 0.5803922, 0.54901963} },
        { 0.21960784, 0.3137255, 0.18039216, 0.12941177, 0.72156864, {0.01176471, 0.59607846, 0.5294118} },
        { 0.627451, 0.3764706, 0.16078432, 0.17254902, 0.6509804, {0.02352941, 0.6313726, 0.49019608} },
        { 0.627451, 0.3764706, 0.18039216, 0.12941177, 0.6666667, {0.01176471, 0.5294118, 0.49019608} },
        { 0.21960784, 0.3137255, 0.16078432, 0.17254902, 0.59607846, {0.03137255, 0.5568628, 0.45882353} },
        { 0.21960784, 0.3137255, 0.18039216, 0.12941177, 0.59607846, {0.02352941, 0.49019608, 0.49019608} },
        { 0.627451, 0.3764706, 0.16078432, 0.17254902, 0.6901961, {0.03921569, 0.49019608, 0.50980395} },
        { 0.627451, 0.3764706, 0.18039216, 0.12941177, 0.6509804, {0.03529412, 0.50980395, 0.44313726} },
        { 0.627451, 0.3764706, 0.16078432, 0.17254902, 0.79607844, {0.00784314, 0.6901961, 0.5568628} },
        { 0.627451, 0.3764706, 0.18039216, 0.12941177, 0.80784315, {0.00784314, 0.65882355, 0.5568628} },
        { 0.4392157, 0.59607846, 0.16078432, 0.17254902, 0.5803922, {0.01568628, 0.59607846, 0.52156866} },
        { 0.4392157, 0.59607846, 0.18039216, 0.12941177, 0.54901963, {0.01568628, 0.59607846, 0.5372549} },
        { 0.4392157, 0.59607846, 0.16078432, 0.17254902, 0.50980395, {0.01960784, 0.5882353, 0.49019608} },
        { 0.4392157, 0.59607846, 0.18039216, 0.12941177, 0.5294118, {0.01960784, 0.5803922, 0.4745098} },
        { 0.4392157, 0.59607846, 0.16078432, 0.11372549, 0.5882353, {0.01568628, 0.6313726, 0.48235294} },
        { 0.4392157, 0.59607846, 0.18039216, 0.12941177, 0.59607846, {0.01960784, 0.6313726, 0.5019608} }
    };

    // Perform non-maximum suppression
    std::vector<Prediction> result = non_maximum_suppression(predictions, 0.5, 0.3, 96, 96);

    // Validate the result based on your expectations
    size_t expected_result_size = 3;
    std::vector<Prediction> expected_output = {
        { 0.21960784, 0.3137255, 0.18039216, 0.12941177, 0.85882354, {0.00784314, 0.6431373, 0.6745098} },
        { 0.627451, 0.3764706, 0.18039216, 0.12941177, 0.80784315, {0.00784314, 0.65882355, 0.5568628} },
        { 0.4392157, 0.59607846, 0.18039216, 0.12941177, 0.59607846, {0.01960784, 0.6313726, 0.5019608} }
    };

    ASSERT_EQ(result.size(), expected_result_size);  // Replace with your expected result size

    // Add more specific validation based on your expectations
    for( size_t i = 0; i < expected_result_size; i++ ) {
        ASSERT_NEAR(result[i].x, expected_output[i].x, kTolerance);
        ASSERT_NEAR(result[i].y, expected_output[i].y, kTolerance);
        ASSERT_NEAR(result[i].width, expected_output[i].width, kTolerance);
        ASSERT_NEAR(result[i].height, expected_output[i].height, kTolerance);
        ASSERT_NEAR(result[i].confidence, expected_output[i].confidence, kTolerance);
        for( size_t j = 0; j < result[i].class_confidences.size(); j++ ) {
            ASSERT_NEAR(result[i].class_confidences[j], expected_output[i].class_confidences[j], kTolerance);
        }
    }
}

// TODO: this when there are zeros in width or height


