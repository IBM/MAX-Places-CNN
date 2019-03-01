from core.model import ModelWrapper, read_image

from maxfw.core import MAX_API, PredictAPI, MetadataAPI

from flask_restplus import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage


model_wrapper = ModelWrapper()

# === Labels API

model_label = MAX_API.model('ModelLabel', {
    'id': fields.String(required=True, description='Label identifier'),
    'name': fields.String(required=True, description='Class label')
})

labels_response = MAX_API.model('LabelsResponse', {
    'count': fields.Integer(required=True, description='Number of labels returned'),
    'labels': fields.List(fields.Nested(model_label), description='Class labels that can be predicted by the model')
})

class ModelLabelsAPI(MetadataAPI):
    '''API for getting information about available class labels'''

    id_to_class = {i: c for i, c in enumerate(model_wrapper.classes)}

    @MAX_API.doc('get_labels')
    @MAX_API.marshal_with(labels_response)
    def get(self):
        '''Return the list of labels that can be predicted by the model'''
        result = {}
        result['labels'] = [{'id': l[0], 'name': l[1]} for l in self.id_to_class.items()]
        result['count'] = len(self.id_to_class)
        return result


# === Predict API 

label_prediction = MAX_API.model('LabelPrediction', {
    'label_id': fields.String(required=False, description='Label identifier'),
    'label': fields.String(required=True, description='Class label'),
    'probability': fields.Float(required=True, description='Predicted probability for the class label')
})

predict_response = MAX_API.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted labels and probabilities')
})

# set up parser for image input data
image_parser = MAX_API.parser()
image_parser.add_argument('image', type=FileStorage, location='files', required=True, 
                            help='An image file (encoded as PNG or JPG/JPEG)')

class ModelPredictAPI(PredictAPI):

    @MAX_API.doc('predict')
    @MAX_API.expect(image_parser)
    @MAX_API.marshal_with(predict_response)
    def post(self):
        '''Make a prediction given input data'''
        result = {'status': 'error'}

        args = image_parser.parse_args()
        image_data = args['image'].read()
        image = read_image(image_data)
        preds = model_wrapper.predict(image)
        
        label_preds = [{'label_id': p[0], 'label': p[1], 'probability': p[2]} for p in [x for x in preds]]
        result['predictions'] = label_preds
        result['status'] = 'ok'

        return result   