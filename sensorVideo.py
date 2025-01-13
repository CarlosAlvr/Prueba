import time
import cv2
import itertools
import zenoh
import numpy as np

def main(conf: zenoh.Config):
    # Configurar sesión de Zenoh
    zenoh.init_log_from_env_or("error")

    print("Opening session...")
    with zenoh.open(conf) as session:

        #print("Declaring Subscriber on 'casa/persona1/caida'...")
        #print("Declaring Publisher on 'casa/habitacion1/video'...")
        pub_video = session.declare_publisher("casa/habitacion1/video")

        # Inicializar cámara
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: No se pudo abrir la cámara.")
            return

        def listener_caida(sample: zenoh.Sample):
            #print(f"Received fall detection data on '{sample.key_expr}': {sample.payload.to_string()}")

            # Convertir el dato recibido a entero
            fall_detected = int(sample.payload.to_string())

            if fall_detected == 1:
                print("Fall detected. Capturing and sending video frame.")
                # Capturar un solo frame de la cámara
                ret, frame = cap.read()
                if not ret:
                    print("Error: No se pudo leer el frame de la cámara.")
                    return

                # Procesar y enviar el frame
                _, buffer = cv2.imencode('.jpg', frame)
                frame_data = buffer.tobytes()
                pub_video.put(frame_data)
                print("Published processed video frame.")

        # Declarar el suscriptor
        session.declare_subscriber("casa/persona1/caida", listener_caida)

        print("Listening for fall detection... Press CTRL-C to quit.")
        try:
            while True:
                time.sleep(1)  # Mantener el programa en ejecución
        except KeyboardInterrupt:
            print("Exiting...")

        # Liberar recursos
        cap.release()

# --- Command line argument parsing --- --- --- --- --- ---
if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(prog="fall_video_detection", description="Listen for fall detection and send video frames.")
    common.add_config_arguments(parser)

    args = parser.parse_args()
    conf = common.get_config_from_args(args)

    main(conf)

