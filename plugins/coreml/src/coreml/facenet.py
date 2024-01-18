import asyncio
import concurrent.futures
from typing import Any, Tuple, List

import coremltools as ct
import scrypted_sdk
from PIL import Image

from predict import Prediction, PredictPlugin, Rectangle
from scrypted_sdk.types import (ObjectDetectionResult, ObjectDetectionSession,
                                ObjectsDetected, Setting)

import numpy as np

predictExecutor = concurrent.futures.ThreadPoolExecutor(8, "CoreML-Predict")

class BlazeFace(PredictPlugin):
    def __init__(self, nativeId: str | None = None):
        super().__init__(nativeId=nativeId)

        model = "blazeface"
        modelFile = self.downloadFile(
            f"https://github.com/koush/coreml-models/raw/main/{model}/{model}.mlmodel",
            f"{model}.mlmodel",
        )

        self.model = ct.models.MLModel(modelFile)
        self.labels = {
            0: 'face',
        }

        self.modelspec = self.model.get_spec()
        self.inputdesc = self.modelspec.description.input[0]
        self.inputheight = self.inputdesc.type.imageType.height
        self.inputwidth = self.inputdesc.type.imageType.width

        self.loop = asyncio.get_event_loop()

    # width, height, channels
    def get_input_details(self) -> Tuple[int, int, int]:
        return (self.inputwidth, self.inputheight, 3)

    def get_input_size(self) -> Tuple[float, float]:
        return (self.inputwidth, self.inputheight)

    async def detect_once(self, input: Image.Image, settings: Any, src_size, cvss):
        if asyncio.get_event_loop() is self.loop:
            out_dict = await asyncio.get_event_loop().run_in_executor(
                predictExecutor, lambda: self.model.predict({'image': input})
            )
        else:
            out_dict = self.model.predict({'image': input})

        detections: List[Prediction] = []

        def torelative(value: float):
            return value * self.inputheight

        confidences = out_dict['1011'][0]
        for index, confidence_arr in enumerate(confidences):
            confidence = confidence_arr[0]
            if confidence < .2:
                continue

            face_info = out_dict['1477'][0][index]
            l = torelative(face_info[0])
            t = torelative(face_info[1])
            r = torelative(face_info[2])
            b = torelative(face_info[3])

            detections.append(Prediction(0, confidence.astype(float), Rectangle(
                l.astype(float),
                t.astype(float),
                r.astype(float),
                b.astype(float),
            )))

        ret = self.create_detection_result(detections, src_size, cvss)
        return ret

class Facenet(PredictPlugin):
    def __init__(self, nativeId: str | None = None):
        super().__init__(nativeId=nativeId)

        model = "facenet"
        modelFile = self.downloadFile(
            f"https://github.com/koush/coreml-models/raw/main/{model}/{model}.mlmodel",
            f"{model}.mlmodel",
        )

        self.model = ct.models.MLModel(modelFile)

        self.modelspec = self.model.get_spec()
        self.inputdesc = self.modelspec.description.input[0]
        self.inputheight = self.inputdesc.type.multiArrayType.shape[1]
        self.inputwidth = self.inputdesc.type.multiArrayType.shape[2]

        self.loop = asyncio.get_event_loop()

    # width, height, channels
    def get_input_details(self) -> Tuple[int, int, int]:
        return (self.inputwidth, self.inputheight, 3)

    def get_input_size(self) -> Tuple[float, float]:
        return (self.inputwidth, self.inputheight)

    async def detect_once(self, input: Image.Image, settings: Any, src_size, cvss):
        numpy_array = np.array(input)
        numpy_array = numpy_array.reshape((1,160,160,3)).astype(np.float32)

        if asyncio.get_event_loop() is self.loop:
            out_dict = await asyncio.get_event_loop().run_in_executor(
                predictExecutor, lambda: self.model.predict({'input': numpy_array})
            )
        else:
            out_dict = self.model.predict({'input': numpy_array})

        ret = self.create_detection_result([], src_size, cvss)
        return ret
