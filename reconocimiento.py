import time
import cv2
import numpy as np
import zenoh

def load_yolo_model():
    # Carga los pesos y configuraciones de YOLO
    net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
    layer_names = net.getLayerNames()

    # Manejar correctamente getUnconnectedOutLayers
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

    # Cargar las clases (COCO dataset)
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]

    return net, output_layers, classes

def detect_people(frame, net, output_layers, classes):
    height, width, _ = frame.shape

    # Crear un blob para YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (1280, 1280), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids, confidences, boxes = [], [], []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Filtrar detecciones de personas (clase 'person')
            if classes[class_id] == "person" and confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    return len(indexes) > 0 if len(indexes) > 0 else False

def main(conf: zenoh.Config, key: str):
    # Cargar modelo YOLO
    net, output_layers, classes = load_yolo_model()

    # Configurar sesión de Zenoh
    zenoh.init_log_from_env_or("error")

    #print("Opening session...")
    with zenoh.open(conf) as session:

        #print(f"Declaring Subscriber on '{key}'...")
        #print("Declaring Publisher on 'casa/habitacion1/deteccion'...")
        pub = session.declare_publisher("casa/**/deteccion")

        def listener(sample: zenoh.Sample):
            #print(f">> [Subscriber] Received data on '{sample.key_expr}'")

            # Decodificar frame recibido (asumiendo que es JPG)
            frame_data = sample.payload.to_bytes()
            np_arr = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Detectar personas en el frame
                detected = detect_people(frame, net, output_layers, classes)

                # Publicar 1 si se detecta alguien, 0 en caso contrario
                pub.put("1" if detected else "0")
                print(f"Published: {'1' if detected else '0'}")

        session.declare_subscriber(key, listener)

        print("Press CTRL-C to quit...")
        while True:
            time.sleep(1)

# --- Command line argument parsing --- --- --- --- --- ---
if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(prog="z_sub_detect_publish", description="Detect people in frames and publish detection status.")
    common.add_config_arguments(parser)
    parser.add_argument(
        "--key",
        "-k",
        dest="key",
        default="casa/**/video",
        type=str,
        help="The key expression to subscribe to.",
    )

    args = parser.parse_args()
    conf = common.get_config_from_args(args)

    main(conf, args.key)
